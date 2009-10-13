#!/bin/bash
 
## Copyright 2009 Jordi Puigsegur <jordi.puigsegur@gmail.com>
##                Laurent Bovet <lbovet@windmaster.ch>
##
##  This file is part of WFrog
##
##  WFrog is free software: you can redistribute it and/or modify
##  it under the terms of the GNU General Public License as published by
##  the Free Software Foundation, either version 3 of the License, or
##  (at your option) any later version.
##
##  This program is distributed in the hope that it will be useful,
##  but WITHOUT ANY WARRANTY; without even the implied warranty of
##  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##  GNU General Public License for more details.
##
##  You should have received a copy of the GNU General Public License
##  along with this program.  If not, see <http://www.gnu.org/licenses/>.

 
###########################
##  BEGIN CONFIGURATION  ##
###########################
 
# Route to files to upload.
DIR="/var/local/meteo/wfrog/data"
 
# Remote route
RDIR="/"
 
# FTP Information
USER=""
PSWD=""
HOST=""
 
###########################
##   END CONFIGURATION   ##
###########################
 
OLD=""
while true
do
 
# Get max modification time of all files to upload
NEW=`stat --format="%y" ${DIR}/*  | sort -r | head -n 1`
 
# If some file has been modified run mirror
if [ "$NEW" != "$OLD" ]; then

# Print date
date

# then process xml file 
xsltproc -o ${DIR}/WxData.html WxData1.xslt ${DIR}/WxData.xml
xsltproc -o ${DIR}/WxData.txt WxData2.xslt ${DIR}/WxData.xml

# and mirror directory contains
lftp -u $USER,$PSWD $HOST <<EOF
cd $RDIR
lcd $DIR
put WxData.xml
put WxData.html
put WxData.txt
quit 0
EOF

fi
 
# Get max modification time again (xsltproc has created new files)
OLD=`stat --format="%y" ${DIR}/*  | sort -r | head -n 1`
 
#Check file changes every 30 seconds
sleep 30
done

