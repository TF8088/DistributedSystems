@echo off
ECHO Iniciando o projeto...

:: Iniciar a API Node.js
cd database
start "API Node.js" cmd /k npm run start

:: Aguardar 3 segundos
timeout /t 3

:: Iniciar o servidor Flask
cd ../app
:: Instalar dependências Flask (executa apenas uma vez, se necessário)
pip install -r requirements.txt
start "Servidor Flask" cmd /k python app.py

ECHO.
ECHO Servidores iniciados!
ECHO - API Node.js: http://localhost:3000
ECHO - Flask: http://localhost:5000
pause