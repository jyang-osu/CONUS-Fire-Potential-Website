param([switch]$CheckOnly)
$ErrorActionPreference = 'Stop'
$repo = 'jyang-osu/CONUS-Fire-Potential-Website'
$gh = 'C:\Program Files\GitHub CLI\gh.exe'
$python = Join-Path $PSScriptRoot 'runtime\python.exe'
$lock = $null
function Invoke-Checked {
    param([string]$Program, [string[]]$Arguments)
    & $Program @Arguments
    if ($LASTEXITCODE -ne 0) { throw "Command failed (exit $LASTEXITCODE): $Program $($Arguments -join ' ')" }
}
try {
    if (!(Test-Path -LiteralPath $gh)) {
        $gh = (Get-Command gh -ErrorAction Stop).Source
    }
    if (!(Test-Path -LiteralPath $python)) { throw 'Run this script from the complete Website_GitHub folder with its runtime.' }
    Set-Location -LiteralPath $PSScriptRoot
    Invoke-Checked $gh @('auth','status','--hostname','github.com')
    Invoke-Checked $gh @('release','view','web-data','--repo',$repo,'--json','tagName')
    Invoke-Checked $gh @('workflow','view','pages.yml','--repo',$repo)
    if ($CheckOnly) { Write-Host 'Checks passed. No data was exported or published.'; exit 0 }
    $lock = [System.IO.File]::Open((Join-Path $PSScriptRoot 'publish.lock'), 'OpenOrCreate', 'ReadWrite', 'None')
    Write-Host 'Exporting and verifying the latest completed simulation results...'
    foreach ($step in @('export_site.py','verify_site.py','package_site.py')) {
        Invoke-Checked $python @('-B',(Join-Path $PSScriptRoot $step))
    }
    Write-Host 'Uploading site.zip and replacing the previous release attachment...'
    Invoke-Checked $gh @('release','upload','web-data',(Join-Path $PSScriptRoot 'site.zip'),'--clobber','--repo',$repo)
    Write-Host 'Starting dashboard publication...'
    $dispatch = & $gh workflow run pages.yml --repo $repo --ref main -f release_tag=web-data 2>&1
    if ($LASTEXITCODE -ne 0) { throw "ZIP uploaded, but publication could not start: $dispatch" }
    $dispatch | ForEach-Object { Write-Host $_ }
    $match = [regex]::Match(($dispatch -join "`n"), '/actions/runs/(\d+)')
    if (!$match.Success) {
        Write-Host 'Publication requested. Check its result at:'
        Write-Host "https://github.com/$repo/actions/workflows/pages.yml"
        exit 0
    }
    Invoke-Checked $gh @('run','watch',$match.Groups[1].Value,'--repo',$repo,'--exit-status','--compact','--interval','15')
    Write-Host 'Dashboard published successfully. Refresh the website:'
    Write-Host 'https://jyang-osu.github.io/CONUS-Fire-Potential-Website/'
} catch {
    Write-Host "Update failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
} finally {
    if ($null -ne $lock) { $lock.Dispose() }
}
