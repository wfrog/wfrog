@echo off

rem Todo:

rem - libusb!!! WS32/libusb.* -> Python26/DLLs
rem - list software which will installed

set version=1.0.2
set date=28.05.2011

set python="%cd:~0,1%:\Python26\"
set easyinst=%python%Scripts\easy_install.exe
set wget="%CD%\wget"
set sev_za="%CD%\7za"

set upd_srv=http://wfrog.googlecode.com/svn/trunk/pkg/windows

rem ============ 7za & wget check ============
if not exist %wget%.exe (
	cls
	echo !!!! wget.exe not found !!!!
	echo	Please put wget.exe in this dir:
	echo	* %CD%
	pause
	exit
)

if not exist %sev_za%.exe (
	cls
	echo !!!! 7za.exe not found !!!!
	echo	Please put 7za.exe in this dir:
	echo	* %CD%
	pause
	exit
)

rem ============ S O F T W A R E ============
call links.bat


cls
echo ====================================================
echo	wfrog windows build-helper %version% - %date%
echo	by Robin Kluth - wfrog
echo ====================================================
pause
echo.
set /p update=Can I check for updates [Y/N]?

if "%update%" == "n" goto setup
if "%update%" == "N" goto setup

%wget% -q %upd_srv%/versions.bat -O versions.bat

call versions.bat

echo.

if "%new_core_version%" GTR "%version%" (
	echo New core version detected!
	echo	* Yours:	%version%
	echo	* New:		%new_core_version%
	echo.
	set upt_core=true
) ELSE (
	echo No update for core-version available...
	set upt_core=false
)

if "%new_link_version%" GTR "%link_version%" (
	echo New link-list version detected!
	echo	* Yours:	%link_version%
	echo	* New:		%new_link_version%
	echo.
	set upt_lnk_lst=true
) ELSE (
	echo No update for link-list available...
	set upt_lnk_lst=false
)

echo.
pause

if "%upt_core%" == "true" (
	echo.
	%wget% -q %upd_srv%/setup.bat -O setup.bat
	echo Core engine updated, start me again...
	pause
	exit
)



if "%upt_lnk_lst%" == "true" (
	echo.
	echo Link-list update...
	%wget% -q %upd_srv%/links.bat -O links.bat
	call links.bat
	echo	done.
	echo.
	pause
)


goto setup



:setup
cls
echo.
echo Please choose if you want the Installmode or not..
echo.
echo	Y	Enter the installmode to install
echo		PyThon, SlikSVN and other dependencies
echo.
echo	N	(Try) to build wfrog for windows :)
echo		INSTALL DEPENDENCIES BEFORE RUN THIS MODE!
echo.
set /p install=Enter Installmode? [Y/N]:
if "%install%" == "N" goto cfg
if "%install%" == "n" goto cfg




echo Step 1: Downloading tools
mkdir download
cd download
echo.
echo Python 2.6...

%wget% -q %pkg_python% -O python26.msi
echo done..
echo.

echo SlikSVN
%wget% -q %pkg_sliksvn% -O sliksvn.msi
echo done..
echo.

echo easy_install...
%wget% -q %pkg_easyinst%
echo done..
echo.

echo cheetah template-engine...
%wget% -q %pkg_cheetah% -O cheetah.tar.gz
echo done..
echo.

echo cheetah libusb1.0...
%wget% -q %pkg_libusb10% -O libusb.7z
echo done..
echo.

echo Py2EXE
%wget% -q %pkg_py2exe% -O py2exe.exe
echo done..
echo.

echo PyYAML
%wget% -q %pkg_pyyaml% -O pyyaml.exe
echo done..
echo.

echo PyWWS...
%wget% -q %pkg_pywws% -O pywws.zip
echo done..
echo.

echo PyGoogleChart...
%wget% -q %pkg_pygchart% -O pygchart.exe
echo done..
echo.

echo PySerial...
%wget% -q %pkg_pyserial% -O pyserial.exe
echo done..
echo.

echo PyUSB...
%wget% -q %pkg_pyusb% -O pyusb.exe
echo done..
echo.
rem ==== BUGGY! Does not support Python 2.6, ignored - NOT required for build - but a should-have feature - next version..
rem echo NameMapper for Cheetah...
rem %wget% -q %pkg_namemapper% -O _namemapper.pyd
rem echo done..
pause
cls





echo Step 2: Install tools - PLEASE WAIT!
echo.

echo Python2.6...
msiexec /i python26.msi /quiet
echo done..
echo.

echo SlikSVN
msiexec /i sliksvn.msi /quiet
echo done..
echo.

echo Py2EXE
py2exe.exe
echo done..
echo.

echo PyYAML
pyyaml.exe
echo done..
echo.

echo PyGChart
pygchart.exe
echo done..
echo.

echo PySerial
pyserial.exe
echo done..
echo.

echo PyUSB
pyusb.exe
echo done..
echo.

echo easy_install
ez_setup.py
echo done..
echo.
cd ..




echo Cheetah template-system...
mkdir cheetah
move download\cheetah.tar.gz cheetah
cd cheetah
%sev_za% x cheetah.tar.gz
%sev_za% x -y cheetah-2.2.2.tar
cd Cheetah-2.2.2
setup.py install
%easyinst% -q dist/Cheetah-2.2.2-py2.6.egg
cd ..\..\
echo done..
echo.
rem ==== BUGGY! Does not support Python 2.6, ignored - NOT required for build - but a should-have feature - next version..
rem echo Move nameMapper for Cheetah...
rem move download\_namemapper.pyd %python%Lib\site-packages\Cheetah-2.2.2-py2.6.egg\Cheetah
rem echo done..
rem echo.




rem echo libusb...
rem mkdir libusb
rem move download\libusb.7z libusb
rem cd libusb
rem %sev_za% x libusb.7z
rem cd MS32\dll
rem xcopy /E "%CD%\*" %python%DLLs
rem cd ..\
rem echo done..
rem echo.


echo PyWWS...
mkdir pywws
move download\pywws.zip pywws
cd pywws
%sev_za% x -y pywws.zip
xcopy /E "%CD%\pywws-11.02_r354\*" %python%Lib
cd ..
echo done..
pause
cls


echo Step 3: Install some tools through easy_install...
echo.
cd %python%
echo PyYAML...
%easyinst% -q pyyaml
echo done..
echo.

echo LXML
%easyinst% -q %pkg_lxml%
echo.
echo done..
echo.
sleep 2
cls
echo Please run me again with installmode = No
pause
exit

:cfg

cls
echo Get latest wfrog trunk...
svn checkout http://wfrog.googlecode.com/svn/trunk/ --quiet
echo.
echo done..
sleep 2
cls
echo Step 4: Build wfrog for Windows...
echo.
cd trunk
copy bin\wfrog .\wfrog.py
copy pkg\setup.py .\
%python%python.exe setup.py py2exe
echo Build finished!
echo	Go to: /trunk/dist to run wfrog.exe ;)
pause