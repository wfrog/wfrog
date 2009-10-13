<?xml version="1.0"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:output method="xml" version="1.0" encoding="UTF-8" doctype-public="-//W3C//DTD XHTML 1.0
Strict//EN" doctype-system="http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd" indent="yes"/>
<xsl:template match="WxData">
<html>
<head>
<title>WxData</title>
</head>
<body>
<p>Last update: <xsl:value-of select="time"/></p>
<xsl:apply-templates select="current"/>
<xsl:apply-templates select="today"/>
<xsl:apply-templates select="month"/>
<xsl:apply-templates select="year"/>
</body>
</html>
</xsl:template>

<xsl:template match="current">
<H3>Current values</H3>
<table>
    <tbody>
        <tr>
            <th width="50%"></th>
            <th width="50%">Value</th>
        </tr>
        <tr>
            <th>Temperature</th>
            <td><xsl:value-of select="temperature"/> <xsl:value-of select="temperature/@units"/></td>
        </tr>
        <tr>
            <th>Humidity</th>
            <td><xsl:value-of select="humidity"/> <xsl:value-of select="humidity/@units"/></td>
        </tr>
        <tr>
            <th>Dew point</th>
            <td><xsl:value-of select="dew_point"/> <xsl:value-of select="dew_point/@units"/></td>
        </tr>
        <tr>
            <th>Wind chill</th>
            <td><xsl:value-of select="wind_chill"/> <xsl:value-of select="wind_chill/@units"/></td>
        </tr>
        <tr>
            <th>Heat Index</th>
            <td><xsl:value-of select="heat_index"/> <xsl:value-of select="heat_index/@units"/></td>
        </tr>
        <tr>
            <th>Wind avg</th>
            <td>
                <xsl:value-of select="wind_avg/speed"/> <xsl:value-of select="wind_avg/speed/@units"/>
                (<xsl:value-of select="wind_avg/dir"/> <xsl:value-of select="wind_avg/dir/@units"/>)
            </td>
        </tr>
        <tr>
            <th>Wind gust</th>
            <td>
                <xsl:value-of select="wind_gust/speed"/> <xsl:value-of select="wind_gust/speed/@units"/>
                (<xsl:value-of select="wind_gust/dir"/> <xsl:value-of select="wind_gust/dir/@units"/>)
            </td>
        </tr>
        <tr>
            <th>Pressure (sea level)</th>
            <td><xsl:value-of select="pressure"/> <xsl:value-of select="pressure/@units"/></td>
        </tr>
        <tr>
            <th>UV Index</th>
            <td><xsl:value-of select="uv_index"/></td>
        </tr>
    </tbody>
</table>
</xsl:template>

<xsl:template match="today">
<H3>Today values</H3>
<xsl:call-template name="aggregate_values"/>
</xsl:template>

<xsl:template match="month">
<H3>This month values</H3>
<xsl:call-template name="aggregate_values"/>
</xsl:template>

<xsl:template match="year">
<H3>Current year values</H3>
<xsl:call-template name="aggregate_values"/>
</xsl:template>

<xsl:template name="aggregate_values">
<table>
    <tbody>
        <tr>
            <td></td>
            <th>Value</th>
            <th>Min.</th>
            <th>Max.</th>
        </tr>
        <tr>
            <th>Temperature</th>
            <td></td>
            <td>
                <xsl:value-of select="temperature/min/value"/> <xsl:value-of select="temperature/min/value/@units"/>
                (<small> <xsl:value-of select="temperature/min/time"/> </small>)
            </td>
            <td>
                <xsl:value-of select="temperature/max/value"/> <xsl:value-of select="temperature/max/value/@units"/>
                (<small> <xsl:value-of select="temperature/max/time"/> </small>) 
            </td>
        </tr>
        <tr>
            <th>Humidity</th>
            <td></td>
            <td>
                <xsl:value-of select="humidity/min/value"/> <xsl:value-of select="humidity/min/value/@units"/>
                (<small> <xsl:value-of select="humidity/min/time"/> </small>)
            </td>
            <td>
                <xsl:value-of select="humidity/max/value"/> <xsl:value-of select="humidity/max/value/@units"/>
                (<small> <xsl:value-of select="humidity/max/time"/> </small>) 
            </td>
        </tr>
        <tr>
            <th>Rain</th>
	    <td>
                <xsl:value-of select="rain_fall/value"/> <xsl:value-of select="rain_fall/value/@units"/>
            </td>
            <td></td>
            <td>
                <xsl:if test="rain_rate/max/value">
                    <xsl:value-of select="rain_rate/max/value"/> <xsl:value-of select="rain_rate/max/value/@units"/>
                    (<small> <xsl:value-of select="rain_rate/max/time"/> </small>)
                </xsl:if>
            </td>
        </tr>
        <tr>
            <th>Wind gust</th>
            <td></td>
            <td></td>
            <td>
                <xsl:value-of select="wind_gust/max/speed"/> <xsl:value-of select="wind_gust/max/speed/@units"/>
                (<small> <xsl:value-of select="wind_gust/max/dir"/> <xsl:value-of select="wind_gust/max/dir/@units"/>, 
                 <xsl:value-of select="wind_gust/max/time"/> </small>)
            </td>
        </tr>
        <tr>
            <th>Pressure</th>
            <td></td>
            <td>
                <xsl:value-of select="pressure/min/value"/> <xsl:value-of select="pressure/min/value/@units"/>
                (<small> <xsl:value-of select="pressure/min/time"/> </small>)
            </td>
            <td>
                <xsl:value-of select="pressure/max/value"/> <xsl:value-of select="pressure/max/value/@units"/>
                (<small> <xsl:value-of select="pressure/max/time"/> </small>) 
            </td>
        </tr>
    </tbody>
</table>
</xsl:template>

</xsl:stylesheet>



