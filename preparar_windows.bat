@echo off
setlocal
title Preparar Carometro Escolar
cd /d "%~dp0"

echo ==========================================================
echo   Preparando o ambiente do Carometro Escolar
echo ==========================================================
echo.

where winget >nul 2>nul
if errorlevel 1 (
    echo ERRO: O Windows Package Manager ^(winget^) nao foi encontrado.
    echo Atualize o Instalador de Aplicativos pela Microsoft Store e tente novamente.
    echo Depois, execute este arquivo novamente.
    pause
    exit /b 1
)

set "INSTALOU=0"
py -3.12 --version >nul 2>nul
if errorlevel 1 (
    echo Instalando Python 3.12...
    winget install --id Python.Python.3.12 -e --silent --accept-package-agreements --accept-source-agreements
    if errorlevel 1 goto :falha_instalacao
    set "INSTALOU=1"
)

where node >nul 2>nul
if errorlevel 1 (
    echo Instalando Node.js LTS...
    winget install --id OpenJS.NodeJS.LTS -e --silent --accept-package-agreements --accept-source-agreements
    if errorlevel 1 goto :falha_instalacao
    set "INSTALOU=1"
)

where git >nul 2>nul
if errorlevel 1 (
    echo Instalando Git...
    winget install --id Git.Git -e --silent --accept-package-agreements --accept-source-agreements
    if errorlevel 1 goto :falha_instalacao
    set "INSTALOU=1"
)

if "%INSTALOU%"=="1" (
    echo.
    echo As ferramentas foram instaladas. Feche esta janela e execute
    echo preparar_windows.bat novamente para concluir a configuracao.
    echo O Windows precisa atualizar o PATH antes de usar os programas.
    pause
    exit /b 0
)

where py >nul 2>nul
if errorlevel 1 (
    echo ERRO: Python nao foi encontrado no PATH. Reinicie o Windows e tente novamente.
    pause
    exit /b 1
)
where node >nul 2>nul
if errorlevel 1 (
    echo ERRO: Node.js nao foi encontrado no PATH. Reinicie o Windows e tente novamente.
    pause
    exit /b 1
)
where npm >nul 2>nul
if errorlevel 1 (
    echo ERRO: npm nao foi encontrado. Reinstale o Node.js LTS e tente novamente.
    pause
    exit /b 1
)

echo [1/5] Criando ambiente virtual do Python...
if not exist "backend\venv\Scripts\python.exe" py -3.12 -m venv "backend\venv"
if errorlevel 1 goto :falha

echo [2/5] Instalando dependencias do backend...
call "backend\venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 goto :falha
call "backend\venv\Scripts\python.exe" -m pip install -r "backend\requirements.txt"
if errorlevel 1 goto :falha

echo [3/5] Instalando dependencias do frontend...
pushd frontend
call npm ci
if errorlevel 1 (popd & goto :falha)
popd

echo [4/5] Aplicando migracoes do banco de dados...
call "backend\venv\Scripts\python.exe" "backend\manage.py" migrate
if errorlevel 1 goto :falha

echo [5/5] Criando compilacao inicial do frontend...
pushd frontend
call npm run build
if errorlevel 1 (popd & goto :falha)
popd

echo.
echo ==========================================================
echo   Configuracao concluida!
echo ==========================================================
echo Para iniciar o sistema, execute iniciar.bat.
echo Na primeira configuracao, tambem sera preciso criar o administrador:
echo   backend\venv\Scripts\python.exe backend\manage.py createsuperuser
echo.
pause
exit /b 0

:falha_instalacao
echo.
echo ERRO: Nao foi possivel instalar uma das ferramentas pelo winget.
echo Confira sua conexao com a internet e tente novamente.
pause
exit /b 1

:falha
echo.
echo ERRO: A configuracao foi interrompida. Leia a mensagem acima,
echo corrija o problema e execute preparar_windows.bat novamente.
pause
exit /b 1
