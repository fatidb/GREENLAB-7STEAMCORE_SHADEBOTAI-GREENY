# start-greeny.ps1
Write-Host "=== GREENY BOT - DEMARRAGE ===" -ForegroundColor Green

# Arrêt et nettoyage
Write-Host ">>> Nettoyage des anciens containers..." -ForegroundColor Yellow
docker stop $(docker ps -a -q --filter ancestor=ghcr.io/fatidb/greeny:v7.3) 2>$null
docker rm $(docker ps -a -q --filter ancestor=ghcr.io/fatidb/greeny:v7.3) 2>$null

# Démarrage daemon
Write-Host ">>> Lancement de GREENY..." -ForegroundColor Cyan
docker run -d `
    --name greeny-bot `
    --restart always `
    --env-file "C:\BIG GREEN 2025 V01\t7steam-core\t7steam-c1-shadebot\config\.env" `
    ghcr.io/fatidb/greeny:v7.3

Start-Sleep -Seconds 2

# Logs
Write-Host ">>> Affichage des logs..." -ForegroundColor Green
Write-Host ">>> CTRL+C pour quitter les logs (le bot continue en arrière-plan)" -ForegroundColor Yellow
docker logs -f greeny-bot