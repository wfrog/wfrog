@echo off

rem Todo:

rem yay! nothing todo :)

set version=1.2.2
set date=02.06.2011

set python="%cd:~0,1%:\Python26\"
set easyinst=%python%Scripts\easy_install.exe
set wget="%CD%\wget"
set sev_za="%CD%\7za"
set coredir="%CD%"

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
echo	1)	Enter normal mode (download and install)
echo.
echo	==================================================
echo.
echo	2)	Enter the download-only mode
echo.
echo	==================================================
echo.
echo	3)	Enter the install-only mode
echo.
echo	==================================================
echo.
echo	4)	(Try) to build wfrog for windows :)
echo		INSTALL DEPENDENCIES BEFORE RUN THIS MODE!
echo.
echo	==================================================
echo.
echo	i)	Station installer
echo.
echo	==================================================
echo.
echo	x)	Exit
echo.
set /p install=What do you want? [1-4,i,x]: 
if "%install%" == "4" goto cfg
if "%install%" == "3" goto install
if "%install%" == "x" exit
if "%install%" == "X" exit
if "%install%" == "i" goto dev_install
if "%install%" == "I" goto dev_install


cls
echo Step 1: Downloading tools
mkdir download
cd download
echo.
echo Python 2.6.6

%wget% -q %pkg_python% -O python26.msi
echo done..
echo.

echo SlikSVN
%wget% -q %pkg_sliksvn% -O sliksvn.msi
echo done..
echo.

echo easy_install
%wget% -q %pkg_easyinst% -O ez_setup.py
echo done..
echo.

echo cheetah template-engine
%wget% -q %pkg_cheetah% -O cheetah.tar.gz
echo done..
echo.

echo libusb1.0
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

echo PyWWS
%wget% -q %pkg_pywws% -O pywws.zip
echo done..
echo.

echo PyGoogleChart
%wget% -q %pkg_pygchart% -O pygchart.exe
echo done..
echo.

echo PySerial
%wget% -q %pkg_pyserial% -O pyserial.exe
echo done..
echo.

echo PyUSB
%wget% -q %pkg_pyusb% -O pyusb.exe
echo done..
echo.

echo NameMapper for Cheetah
%wget% -q %pkg_namemapper%
echo done..
echo.

echo PyWin32
%wget% -q %pkg_pywin32% -O pywin32.exe
echo done..
echo.

echo Step 1 finished...
cd ..\
pause

if "%install%" == "2" exit

cls

:install

cd download

echo Step 2: Install tools - PLEASE WAIT!
echo.

echo Python2.6.6
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

echo PyWin32
pywin32.exe
echo done..
echo.

echo easy_install
ez_setup.py
echo done..
echo.
cd ..




echo Cheetah template-system
mkdir cheetah
move download\cheetah.tar.gz cheetah
cd cheetah
%sev_za% x -y cheetah.tar.gz
%sev_za% x -y cheetah-2.2.2.tar
cd Cheetah-2.2.2
setup.py install
%easyinst% -q dist/Cheetah-2.2.2-py2.6.egg
cd ..\..\
echo done..
echo.

echo Move nameMapper for Cheetah
move download\_namemapper.pyd %python%Lib\site-packages\Cheetah-2.2.2-py2.6.egg\Cheetah
echo done..
echo.




echo libusb
mkdir libusb
move download\libusb.7z libusb
cd libusb
%sev_za% x -y libusb.7z
cd MS32\dll
xcopy /E "%CD%\*" %python%DLLs
cd ..\..\..\
echo done..
echo.


echo PyWWS
mkdir pywws
move download\pywws.zip pywws
cd pywws
%sev_za% x -y pywws.zip
xcopy /E "%CD%\pywws-11.05_r380\*" %python%Lib
cd ..\
echo done..
echo.
echo Step 2 finished...


pause
cls


echo Step 3: Install some tools through easy_install...
echo.
cd %python%
echo PyYAML
%easyinst% -q pyyaml
echo done..
echo.

echo LXML
%easyinst% -q %pkg_lxml%
echo done..
echo.
echo Step 3 finished...

pause
cls

set /p cleanup=Run complete cleanup? [Y/N]: 

if "%cleanup%" == "N" echo Please run me again with mode 3 (install-mode)
if "%cleanup%" == "n" echo Please run me again with mode 3 (install-mode)

echo Step 4: Cleanup
cd %coredir%
echo.

echo Delete downloaded files...
rmdir /S /Q download
echo done
echo.

echo Delete cheetah files...
rmdir /S /Q cheetah
echo done
echo.

echo Delete libusb files...
rmdir /S /Q libusb
echo done
echo.

echo Delete pywws files...
rmdir /S /Q pywws
echo done
echo.
echo Step 4 finished...
pause
cls

echo Please run me again with mode 4 (build-mode)

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
echo Step 5: Build wfrog for Windows
echo.
cd trunk
copy bin\wfrog .\wfrog.py
copy pkg\setup.py .\
%python%python.exe setup.py py2exe
echo Build finished!
echo	*** Go to: /trunk/dist to run wfrog.exe ;)
pause
cls

set /p stationInstaller=Run station installer? [Y/N]: 

if "%stationInstaller%" == "N" goto end
if "%stationInstaller%" == "n" goto end


:dev_install


cd %coredir%
cls
echo Station-installer
echo.
echo 1) WMRS200
echo.
set /p station=Which station do you want to use: 

if "%station%" == "1" (

    echo.
    echo Download zadig...
    %wget% -q %tool_zadig% -O zadig\zadig.7z
    echo done...
    echo.
    echo Unpack zadig...
    cd zadig
    %sev_za% x -y zadig.7z
    del zadig.7z
    echo done...
    echo.
    if not exist zadig.ini (
	echo ***W A R N I N G***
	echo No zadig.ini found, ignoring...
	echo.
    )
    pause
    cls
    echo INFO: In order to install the wmrs200, select
    echo.
    echo * USB-HID (Human Interface Device)
    echo.
    echo and click 'Install driver' on the next window!
    echo.
    pause
    zadig.exe
    echo done...
    echo.
    echo.
    echo Now re-plug the WMRS200 and start wfrog.exe, hope it works ;)
    pause

)

:end
cls
echo Thanks for using!!!
pause
exit