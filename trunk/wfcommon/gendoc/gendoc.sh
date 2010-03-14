 #!/bin/sh

WFROG_HOME=../../
footer="<br><hr><small><a href='http://www.wfrog.org'>wfrog</a> 0.5</small>"

$WFROG_HOME/wfrender/wfrender.py -H | python helpformat.py -H "<small>configuration > <b>wfrender</b> </small><h1>wfrender Configuration</h1>" -F "$footer" > index.html

for i in $($WFROG_HOME/wfrender/wfrender.py -H | grep "^\!.*" | cut -b2-); do
     echo $i; $WFROG_HOME/wfrender/wfrender.py -E $i | \
     python helpformat.py  \
     -H  "<small>configuration > <a href='index.html'>wfrender</a> > <b>"'!'"$i</b></small>" -F "$footer" -t > $i.html; done
