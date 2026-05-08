$ErrorActionPreference = "Stop"

$repo = "E:\DA IICT V.01\DA-IICT"
Set-Location $repo

# Free port 8001 if an old/stale server is running.
$owners = Get-NetTCPConnection -LocalPort 8001 -State Listen -ErrorAction SilentlyContinue |
    Select-Object -ExpandProperty OwningProcess -Unique
foreach ($procId in $owners) {
    try { Stop-Process -Id $procId -Force -ErrorAction Stop } catch {}
}

Start-Sleep -Seconds 1

& "$repo\venv\Scripts\python.exe" "manage.py" runserver 8001
