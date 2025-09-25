@echo off
REM 

REM 
IF NOT EXIST ".venv" (
    echo Criando Ambiente Virtual...
    python -m venv .venv
    call .venv\Scripts\activate.bat
    echo Atualizando pip...
    python -m pip install --upgrade pip
    echo Instalando Dependencias...
    pip install -r requirements.txt
) ELSE (
    echo Ativando Servidor...
    call .venv\Scripts\activate.bat
)

python wsgi.py