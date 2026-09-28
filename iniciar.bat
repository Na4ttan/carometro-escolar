@echo off
:: ==============================================================================
:: Iniciar Carometro Escolar com Backend, Frontend e Localtunnel (Windows)
:: ==============================================================================
setlocal
title Carometro Escolar - Servidor e Tunel HTTPS

cd /d "%~dp0"

echo ==========================================================
echo   Iniciando Carometro Escolar
echo ==========================================================

:: 1. Compila o frontend se necessario
if not exist "frontend\dist\frontend\browser\index.html" (
    echo Compilando frontend Angular pela primeira vez...
    cd frontend
    call npm run build
    cd ..
)

:: 2. Inicia o Backend Django na porta 8000
echo Iniciando Backend Django (porta 8000)...
start "Backend Django" cmd /k "cd /d "%~dp0backend" && call venv\Scripts\activate && python manage.py runserver 0.0.0.0:8000"

:: 3. Inicia o Frontend Angular na porta 4200
echo Iniciando Frontend Angular (porta 4200)...
start "Frontend Angular" cmd /k "cd /d "%~dp0frontend" && call npx ng serve --host 0.0.0.0"

timeout /t 5 /nobreak >nul

echo.
echo ==========================================================
echo   SISTEMA PRONTO PARA USO!
echo ==========================================================
echo   Computador (Local):
echo     -^> http://localhost:4200 (Frontend Angular)
echo     -^> http://localhost:8000 (Django / Admin / API)
echo.
echo   Celular (HTTPS):
echo     -^> O link sera gerado pelo Localtunnel na linha abaixo.
echo     -^> ATENCAO: Veja o endereco exibido em 'your url is: ...'.
echo        Esse link pode variar a cada inicializacao e
echo        e exatamente ele que deve ser aberto no celular!
echo.
echo   IMPORTANTE PARA O CELULAR (Primeiro Acesso):
echo   Se o Localtunnel exibir uma tela pedindo IP (Tunnel Password),
echo   consulte seu IP em: https://loca.lt/mytunnelpassword
echo   digite no campo e clique no botao Continue.
echo ==========================================================
echo Mantenha as janelas abertas enquanto estiver utilizando.
echo.

:: 4. Inicia o tunel HTTPS
call npx localtunnel --port 8000 --subdomain sweet-hounds-flash
pause
