@echo off
echo Dang kiem tra va cai dat thu vien...
pip install pyinstaller

echo Dang bien dich ung dung thanh file .exe...
pyinstaller --onefile --noconsole manager_app.py

echo Hoan tat! File chay cua ban nam trong thu muc 'dist'.
pause
