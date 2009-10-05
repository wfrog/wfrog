#!/bin/bash
while [ "true" ]
do
  echo "========================="
  xsltproc -o WxData.html WxData1.xslt WxData.xml
  lftp -c "debug 3;open -u <user>,<pwd> <ftp_site>;put WxData.xml;put WxData.html;exit"
  date
  sleep 600
done
