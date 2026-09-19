@echo off
echo Dang kiem tra va cai dat thu vien...
pip install pyinstaller

echo Dang bien dich ung dung thanh file .exe...
python -m pyinstaller --onefile --noconsole --icon=icon.ico manager_app.py

echo Hoan tat! File chay cua ban nam trong thu muc 'dist'.
pause
