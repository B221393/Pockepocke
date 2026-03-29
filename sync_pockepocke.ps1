$sourceDir = "G:\マイドライブ\Pockepocke_MetaSimulator"
$targetDir = "C:\Users\Yuto\Desktop\app\apps\prototypes\pockepocke"

echo "Checking Google Drive for MetaSimulator logs... (Path: $sourceDir)"

if (Test-Path $sourceDir) {
    echo "Found Drive data! Syncing logs and gui..."
    
    # logs フォルダの同期
    if (Test-Path "$sourceDir\logs") {
        robocopy "$sourceDir\logs" "$targetDir\logs" /E /Z /R:5 /W:5
    }
    # gui フォルダ（state.json等）の同期
    if (Test-Path "$sourceDir\gui") {
        robocopy "$sourceDir\gui" "$targetDir\gui" /E /Z /R:5 /W:5
    }

    echo "Sync complete. Checking Git status..."
    
    # 差分があるときだけコミット
    $status = git status --porcelain
    if ($status) {
        git add "$targetDir\logs" "$targetDir\gui"
        git commit -m "AI_AUTO_SYNC: Combined Cloud power (Colab) results to Local Git"
        echo "Committed learned knowledge to Git repository."
    } else {
        echo "No new updates found in logs."
    }
} else {
    echo "ERROR: Google Drive folder not found yet. Make sure Colab has run at least once."
}
