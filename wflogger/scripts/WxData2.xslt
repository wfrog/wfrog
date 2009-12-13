<?xml version="1.0"?>

<!--Template for www.meteoclimatic.com-->

<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:output method="text"/>

<xsl:template match="WxData">
<xsl:text>*VER=DATA2*COD=ESIBA0700000107240B*UPD=</xsl:text>
<xsl:value-of select="substring(time,9,2)"/>
<xsl:text>/</xsl:text>
<xsl:value-of select="substring(time,6,2)"/>
<xsl:text>/</xsl:text>
<xsl:value-of select="substring(time,1,4)"/>
<xsl:text> </xsl:text>
<xsl:value-of select="substring(time,12,2)"/>
<xsl:text>:</xsl:text>
<xsl:value-of select="substring(time,15,2)"/>
<xsl:apply-templates select="current"/>
<xsl:apply-templates select="today"/>
<xsl:apply-templates select="month"/>
<xsl:apply-templates select="year"/>
<xsl:text>*EOT*</xsl:text>
</xsl:template>

<xsl:template match="current">
<xsl:text>*TMP=</xsl:text><xsl:value-of select="temperature"/>
<xsl:text>*WND=</xsl:text><xsl:value-of select="wind_gust/speed * 3.6"/>
<xsl:text>*AZI=</xsl:text><xsl:value-of select="wind_gust/dir"/>
<xsl:text>*BAR=</xsl:text><xsl:value-of select="pressure"/>
<xsl:text>*HUM=</xsl:text><xsl:value-of select="humidity"/>
<xsl:text>*SUN=</xsl:text>
</xsl:template>

<xsl:template match="today">
<xsl:text>*DHTM=</xsl:text><xsl:value-of select="temperature/max/value"/> 
<xsl:text>*DLTM=</xsl:text><xsl:value-of select="temperature/min/value"/> 
<xsl:text>*DHHM=</xsl:text><xsl:value-of select="humidity/max/value"/>   
<xsl:text>*DLHM=</xsl:text><xsl:value-of select="humidity/min/value"/>  
<xsl:text>*DHBR=</xsl:text><xsl:value-of select="pressure/max/value"/>    
<xsl:text>*DLBR=</xsl:text><xsl:value-of select="pressure/min/value"/> 
<xsl:text>*DGST=</xsl:text><xsl:value-of select="wind_gust/max/speed * 3.6"/>
<xsl:text>*DPCP=</xsl:text><xsl:value-of select="rain_fall/value"/>      
</xsl:template>

<xsl:template match="month">
<xsl:text>*MHTM=</xsl:text><xsl:value-of select="temperature/max/value"/> 
<xsl:text>*MLTM=</xsl:text><xsl:value-of select="temperature/min/value"/> 
<xsl:text>*MHHM=</xsl:text><xsl:value-of select="humidity/max/value"/>   
<xsl:text>*MLHM=</xsl:text><xsl:value-of select="humidity/min/value"/>  
<xsl:text>*MHBR=</xsl:text><xsl:value-of select="pressure/max/value"/>    
<xsl:text>*MLBR=</xsl:text><xsl:value-of select="pressure/min/value"/> 
<xsl:text>*MGST=</xsl:text><xsl:value-of select="wind_gust/max/speed * 3.6"/>
<xsl:text>*MPCP=</xsl:text><xsl:value-of select="rain_fall/value"/>      
</xsl:template>

<xsl:template match="year">
<xsl:text>*YHTM=</xsl:text><xsl:value-of select="temperature/max/value"/> 
<xsl:text>*YLTM=</xsl:text><xsl:value-of select="temperature/min/value"/> 
<xsl:text>*YHHM=</xsl:text><xsl:value-of select="humidity/max/value"/>   
<xsl:text>*YLHM=</xsl:text><xsl:value-of select="humidity/min/value"/>  
<xsl:text>*YHBR=</xsl:text><xsl:value-of select="pressure/max/value"/>    
<xsl:text>*YLBR=</xsl:text><xsl:value-of select="pressure/min/value"/> 
<xsl:text>*YGST=</xsl:text><xsl:value-of select="wind_gust/max/speed * 3.6"/>
<xsl:text>*YPCP=</xsl:text><xsl:value-of select="rain_fall/value"/>      
</xsl:template>

</xsl:stylesheet>


