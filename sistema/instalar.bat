@echo off
chcp 65001 >nul
echo Instalando o faster-whisper...
python -m pip install --upgrade faster-whisper tqdm "av<16"
echo.
echo Instalado em:
python -c "import faster_whisper, os; print(os.path.dirname(faster_whisper.__file__))"
pause
