"""Watch completed CONUS hours and publish without Codex. Ctrl+C stops."""
import argparse, json, logging, msvcrt, shutil, subprocess, time, urllib.request
from pathlib import Path
import source_reader as src
ROOT = Path(__file__).resolve().parent
REPO = 'jyang-osu/CONUS-Fire-Potential-Website'
URL = 'https://jyang-osu.github.io/CONUS-Fire-Potential-Website/catalog.json'
GH = shutil.which('gh') or r'C:\Program Files\GitHub CLI\gh.exe'

def complete_hour(items):
    hours = {}
    for item in items:
        hours.setdefault(item['time'], set()).add(item['variable'])
    return max((t for t, variables in hours.items() if set(src.META) <= variables), default='')

def published_hour():
    request = urllib.request.Request(URL + '?check=' + str(time.time_ns()), headers={'Cache-Control':'no-cache','User-Agent':'CONUS-Website-Watcher'})
    with urllib.request.urlopen(request, timeout=60) as response:
        return complete_hour(json.load(response)['items'])

def active_deployment():
    result = subprocess.run([GH,'run','list','--repo',REPO,'--workflow','pages.yml','--limit','30','--json','status'], capture_output=True,text=True,check=True,timeout=60)
    return any(r['status'] != 'completed' for r in json.loads(result.stdout))

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--check-only',action='store_true')
    parser.add_argument('--interval',type=int,default=300)
    args=parser.parse_args()
    if args.interval < 30: parser.error('Interval must be at least 30 seconds')
    logging.basicConfig(level=logging.INFO,format='%(asctime)s %(message)s',handlers=[logging.StreamHandler(),logging.FileHandler(ROOT/'website_watch.log',encoding='utf-8')])
    with (ROOT/'watch.lock').open('a+b') as lock:
        if lock.tell()==0: lock.write(b'0');lock.flush()
        lock.seek(0)
        try: msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
        except OSError: raise SystemExit('Another website watcher is already running.')
        logging.info('Watching completed simulation hours. Press Ctrl+C to stop. No Codex required.')
        pending=None
        while True:
            try:
                local=complete_hour(src.inventory().values())
                remote=published_hour()
                busy=active_deployment()
                logging.info('Newest complete UTC hour: local=%s, website=%s; deployment active=%s',local or 'none',remote or 'none',busy)
                if args.check_only: return
                if pending and remote >= pending[0]:
                    logging.info('Publication verified for %s UTC.',pending[0]);pending=None
                if local and local > remote and not busy:
                    if pending and time.monotonic()-pending[1] < 1800:
                        logging.info('Waiting for published catalog to reflect the requested update.')
                    else:
                        logging.info('Publishing latest completed results...')
                        result=subprocess.run(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',str(ROOT/'Update_Website.ps1')],cwd=ROOT)
                        if result.returncode:
                            logging.error('Update failed; will check again in %s seconds.',args.interval)
                        else:
                            pending=(local,time.monotonic())
                            logging.info('Update finished; published catalog will be checked next cycle.')
            except KeyboardInterrupt:
                raise
            except Exception as exc:
                logging.error('Check failed: %s; retry in %s seconds.',exc,args.interval)
                if args.check_only: raise SystemExit(1)
            time.sleep(args.interval)

if __name__=='__main__':
    try: main()
    except KeyboardInterrupt: print('\nWebsite watcher stopped.')
