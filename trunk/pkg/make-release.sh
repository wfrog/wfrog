#!/bin/sh

repo=https://wfrog.googlecode.com/svn/
trunk=$repo/trunk
vfile=wfcommon/config.py
vline='wfrog_version = "\([^"]*\)"'
app=wfrog
checkout=$app

echo "Please make sure the version number is correctly set in $app/$vfile in the subversion repository."
echo Press enter to proceed with checkout or Ctrl-C to abort.
read key

cd build

echo Checking out $repo ...
[ "$checkout" != "" ] && rm -fr $checkout*
svn export $trunk $checkout

# Make the debian dir committable
rm -fr $checkout/debian
svn co $trunk/debian $checkout/debian

version=$(grep "$vline" $app/$vfile | sed "s/$vline/\\1/")

echo
echo '>>> Version is' $version
echo 
echo Press enter to proceed with package build or Ctrl-C to abort.
read key

tag=$repo/tags/$app-$version
archive=$app-$version.tgz

echo Building archive $archive
mv $checkout $checkout-$version
checkout=$checkout-$version

echo
echo "Press enter description line for this release:"
read summary

tar czf $archive $checkout

echo
echo "Please enter the build number [1]"
read build

if [ "$build" = "" ]; then
    build=1
fi

echo Creating debian archive

debversion=$version-$build
( cd $checkout; dch -v $debversion "$summary")
( cd $checkout; dch -a "See http://code.google.com/p/wfrog/wiki/ReleaseNotes")
( cd $checkout; dpkg-buildpackage )
debarchive=${app}_${debversion}_all.deb

echo
echo 'Version is' $version
echo 
echo Press enter to proceed with subversion tag or Ctrl-C to abort.
read key

svn ci $checkout/debian/changelog -m"[make-release] Release $app $version"

svn copy https://wfrog.googlecode.com/svn/trunk https://wfrog.googlecode.com/svn/tags/wfrog-$version -m"[make-release] Release $app $version"

echo
echo 'Version is' $version
echo 
echo Press enter to proceed with package upload on googlecode or Ctrl-C to abort.
read key

python ../googlecode_upload.py -s"$summary" -p $app -l Featured,Type-Archive $archive
python ../googlecode_upload.py -s"$summary" -p $app -l Featured,Type-Package,OpSys-Linux $debarchive

