@echo off
setlocal enabledelayedexpansion

set CONFIG_FILE="C:\ProgramData\MySQL\MySQL Server 8.0\my.ini"
set BACKUP_FILE=%CONFIG_FILE%.backup

copy %CONFIG_FILE% %BACKUP_FILE%

powershell -Command "((Get-Content -LiteralPath \"%CONFIG_FILE%\") -replace 'bind-address=.*', 'bind-address = 0.0.0.0') | Set-Content -LiteralPath \"%CONFIG_FILE%\""
powershell -Command "((Get-Content -LiteralPath \"%CONFIG_FILE%\") -replace 'port=.*', 'port = 3306') | Set-Content -LiteralPath \"%CONFIG_FILE%\""
powershell -Command "((Get-Content -LiteralPath \"%CONFIG_FILE%\") -replace 'max_connections=.*', 'max_connections = 100') | Set-Content -LiteralPath \"%CONFIG_FILE%\""

echo Configuración actualizada.

echo Reiniciando servicio MySQL...
net stop MySQL80
net start MySQL80

echo Servicio MySQL reiniciado.
pause
