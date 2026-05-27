$ErrorActionPreference = "Stop"

$mongoExe = "C:\Program Files\MongoDB\Server\8.3\bin\mongod.exe"
$root = Split-Path -Parent $PSScriptRoot
$dbPath = Join-Path $root "mongo-data-27018"
$logPath = Join-Path $root "mongo-27018.log"

if (-not (Test-Path $mongoExe)) {
  throw "MongoDB Server not found at: $mongoExe"
}

New-Item -ItemType Directory -Force -Path $dbPath | Out-Null

& $mongoExe --port 27018 --bind_ip 127.0.0.1 --dbpath $dbPath --logpath $logPath --logappend
