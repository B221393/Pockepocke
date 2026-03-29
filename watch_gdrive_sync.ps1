$watchPath = "G:\マイドライブ\Pockepocke_MetaSimulator\logs"
$syncScript = "C:\Users\Yuto\Desktop\app\apps\prototypes\pockepocke\sync_pockepocke.ps1"

# フォルダが存在しない場合は作成を待機
while (-not (Test-Path $watchPath)) {
    Write-Host "Waiting for G-Drive folder to be created by Colab... ($watchPath)"
    Start-Sleep -Seconds 10
}

Write-Host "=== G-Drive Watcher Started: Monitoring $watchPath ==="

$watcher = New-Object System.IO.FileSystemWatcher
$watcher.Path = $watchPath
$watcher.Filter = "*.*"
$watcher.IncludeSubdirectories = $true
$watcher.EnableRaisingEvents = $true

$action = {
    $path = $Event.SourceEventArgs.FullPath
    Write-Host "Change detected in Drive! ($path) Updating local repo..." -ForegroundColor Cyan
    powershell -File "$syncScript"
}

Register-ObjectEvent $watcher "Changed" -Action $action
Register-ObjectEvent $watcher "Created" -Action $action

while ($true) { Start-Sleep -Seconds 5 }
