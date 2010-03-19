 #!/bin/sh

WFROG_HOME=../../

version=$(grep wfrog_version $WFROG_HOME/wfcommon/config.py | cut -f2 -d'"')

date=$(date +%F)
footer="<br><hr><small><a href='http://www.wfrog.org'>wfrog</a> $version - $date</small>"

DOC_DIR=doc

mkdir -p $DOC_DIR

function gen_module()
{
    module=$1

     echo "--- $module ---"

    mkdir -p $DOC_DIR/$module

    python $WFROG_HOME/$module/$module.py -H | python helpformat.py -H "<small><a href='../index.html'>wfrog</a> > <b>$module</b> </small><h1>Configuration of $module</h1>" -F "$footer" > $DOC_DIR/$module/index.html

    for i in $(python $WFROG_HOME/$module/$module.py -H | grep "^\!.*" | cut -b2-); do
         echo $i; python $WFROG_HOME/$module/$module.py -E $i | \
        python helpformat.py  \
        -H  "<small><a href='../index.html'>wfrog</a> > <a href='index.html'>$module</a> > <b>"'!'"$i</b></small>" -F "$footer" -t > $DOC_DIR/$module/$i.html; done
}

for i in wfdriver wflogger wfrender; do
    gen_module $i
done

cat << EOF > $DOC_DIR/index.html

<html><head><title>wfrog - configuration</title></head><body>
<small><b>wfrog</b> </small>

<h1>Configuration of wfrog</h1>

<ul>
<li><a href="wfdriver/index.html">wfdriver</a>
<li><a href="wflogger/index.html">wflogger</a>
<li><a href="wfrender/index.html">wfrender</a>
</ul>

$footer

</body></html>
EOF
