param([switch]$CheckOnly, [ValidateRange(30,86400)][int]$IntervalSeconds = 300)
$ErrorActionPreference = 'Stop'
$python = Join-Path $PSScriptRoot 'runtime\python.exe'
if (!(Test-Path -LiteralPath $python)) { throw 'Run from the complete Website_GitHub folder.' }
$arguments = @('-B', (Join-Path $PSScriptRoot 'watch_website.py'), '--interval', "$IntervalSeconds")
if ($CheckOnly) { $arguments += '--check-only' }
& $python @arguments
exit $LASTEXITCODE
