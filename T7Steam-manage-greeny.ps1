# Configuration de l'environnement T7STEAM
$projectPath = "C:\BIG GREEN 2025 V01\t7steam-core\t7steam-c1-shadebot"
$botFile = "shaderbot_greeny_v7.3.py"
$backupPath = "$projectPath\backups"
$logsPath = "$projectPath\logs"
$configPath = "$projectPath\config"

# Création des dossiers nécessaires
Write-Host "🔧 Création des dossiers du projet..." -ForegroundColor Cyan
@(
    "$backupPath",
    "$logsPath",
    "$configPath"
) | ForEach-Object {
    if (-not (Test-Path $_)) {
        New-Item -Path $_ -ItemType Directory -Force
        Write-Host "📁 Création du dossier: $_" -ForegroundColor Green
    }
}

# Fonction de backup
function Backup-BotFiles {
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $backupFile = "$backupPath\${botFile}_$timestamp.bak"
    
    Write-Host "💾 Création d'une sauvegarde..." -ForegroundColor Yellow
    Copy-Item "$projectPath\$botFile" $backupFile
    Write-Host "✅ Sauvegarde créée: $backupFile" -ForegroundColor Green
}

# Fonction de déploiement
function Deploy-Bot {
    param (
        [switch]$RestartBot
    )
    
    Write-Host "🚀 Déploiement du bot..." -ForegroundColor Cyan
    
    # Arrêt du bot si demandé
    if ($RestartBot) {
        Write-Host "🛑 Arrêt du bot en cours..." -ForegroundColor Yellow
        Get-Process python | Where-Object {$_.MainWindowTitle -like "*shaderbot*"} | Stop-Process -Force
        Start-Sleep -Seconds 2
    }
    
    # Démarrage du bot
    Write-Host "▶️ Démarrage du bot..." -ForegroundColor Yellow
    Start-Process python -ArgumentList "$projectPath\$botFile" -WindowStyle Hidden
    
    # Vérification
    Start-Sleep -Seconds 5
    $process = Get-Process python | Where-Object {$_.MainWindowTitle -like "*shaderbot*"}
    if ($process) {
        Write-Host "✅ Bot démarré avec succès!" -ForegroundColor Green
    } else {
        Write-Host "❌ Erreur lors du démarrage du bot!" -ForegroundColor Red
    }
}

# Fonction de monitoring
function Show-BotStatus {
    Write-Host "`n📊 État du bot:" -ForegroundColor Cyan
    
    # Vérification du processus
    $process = Get-Process python | Where-Object {$_.MainWindowTitle -like "*shaderbot*"}
    if ($process) {
        Write-Host "✅ Bot en cours d'exécution" -ForegroundColor Green
        Write-Host "   PID: $($process.Id)"
        Write-Host "   Mémoire: $([math]::Round($process.WorkingSet64 / 1MB, 2)) MB"
        Write-Host "   Temps d'exécution: $($process.TotalProcessorTime)"
    } else {
        Write-Host "❌ Bot arrêté" -ForegroundColor Red
    }
    
    # Affichage des derniers logs
    Write-Host "`n📜 Derniers logs:" -ForegroundColor Cyan
    Get-Content "$logsPath\bot_*.log" -Tail 10
}

# Menu principal
function Show-Menu {
    Write-Host "`n=== T7STEAM Bot Management ===" -ForegroundColor Cyan
    Write-Host "1. 📦 Déployer le bot"
    Write-Host "2. 🔄 Redémarrer le bot"
    Write-Host "3. 💾 Créer une sauvegarde"
    Write-Host "4. 📊 Afficher l'état du bot"
    Write-Host "5. ❌ Quitter"
    
    $choice = Read-Host "`nChoisissez une option (1-5)"
    
    switch ($choice) {
        "1" { Deploy-Bot }
        "2" { Deploy-Bot -RestartBot }
        "3" { Backup-BotFiles }
        "4" { Show-BotStatus }
        "5" { return $false }
        default { Write-Host "❌ Option invalide" -ForegroundColor Red }
    }
    return $true
}

# Boucle principale
Write-Host "🤖 T7STEAM Bot Management Tool" -ForegroundColor Cyan
do {
    $continue = Show-Menu
} while ($continue)