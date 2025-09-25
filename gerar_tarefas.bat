@echo off
echo ========================================
echo    GERADOR DE TAREFAS MENSAIS
echo ========================================
echo.

REM Verificar se precisa gerar tarefas
echo Verificando se precisa gerar tarefas para o mes atual...
python gerar_tarefas_mensais.py --verificar

echo.
echo Deseja gerar as tarefas para o mes atual? (S/N)
set /p resposta=

if /i "%resposta%"=="S" (
    echo.
    echo Gerando tarefas...
    python gerar_tarefas_mensais.py
    if %errorlevel%==0 (
        echo.
        echo ✅ Tarefas geradas com sucesso!
    ) else (
        echo.
        echo ❌ Erro ao gerar tarefas!
    )
) else (
    echo.
    echo Operacao cancelada.
)

echo.
pause
