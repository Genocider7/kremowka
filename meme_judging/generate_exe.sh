if [ $# -lt 1 ]
then
echo Usage: $0 python_script
exit 0
fi
name="${1%.*}"
temp_file=$name.output.temp
if [ -f "$name.exe" ]
then
rm "$name.exe"
fi
pip install pyinstaller==6.1.0
echo -n Creating $name.exe...
pyinstaller --onefile --log-level ERROR $1 &> $temp_file
if [ -f "dist/$name.exe" ]
then
echo -e "\tOK"
echo -n Moving and removing files and directories...
rm $temp_file
mv dist/* .
if [ -d dist ]
then
rm -r dist
fi
if [ -d build ]
then
rm -r build
fi
if [ -f "$name.spec" ]
then
rm "$name.spec"
fi
echo -e "\tOK"
else
echo ERROR
cat $temp_file
fi