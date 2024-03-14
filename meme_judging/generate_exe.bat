@echo off
IF "%1"=="" GOTO NO_ARG
SET name=%~n1
SET temp_file=%name%.output.temp
IF EXIST %name%.exe DEL %name%.exe
pip install pyinstaller==6.1.0
ECHO | SET /p="Creating %name%.exe..."
pyinstaller --onefile --log-level ERROR %1 > %temp_file%
IF EXIST dist\%name%.exe GOTO SUCCESS ELSE GOTO FAILURE
:SUCCESS
ECHO 	OK
ECHO | SET /p="Moving and removing files and directories..."
DEL %temp_file%
MOVE dist\* .
IF EXIST dist RMDIR dist
IF EXIST build RMDIR build
if EXIST %name%.spec DEL %name%.spec
ECHO 	OK
GOTO END
:FAILURE
ECHO 	ERROR
TYPE %temp_file%
GOTO END
:NO_ARG
ECHO Usage: %0 python_script
GOTO END
:END