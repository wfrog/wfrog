## Copyright 2009 Jordi Puigsegur <jordi.puigsegur@gmail.com>
##                Laurent Bovet <laurent.bovet@windmaster.ch>
##
##  This file is part of wfrog
##
##  wfrog is free software: you can redistribute it and/or modify
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

## TODO: Test exhaustively all functions from WxUtils. 
##       So far only the ones used by WFROG have been tested.

import math


###########################################################################################
## 1) This first part of this file is a translation to Python of  
##    uWxUtils (http://www.softwx.com/weather/uwxutils.html)      
###########################################################################################

## ----------------------------------------------------------------------------------------
## This source code may be freely used, including for commercial purposes
## Steve Hatchett, SoftWx, Inc.
## http://www.softwx.com/
##
##
##  This file contains functions for performing various weather related calculations.
##
##  Notes about pressure
##    Sensor Pressure           raw pressure indicated by the barometer instrument
##    Station Pressure          Sensor Pressure adjusted for any difference between sensor elevation and official station elevation
##    Field Pressure     (QFE)  Usually the same as Station Pressure
##    Altimeter Setting  (QNH)  Station Pressure adjusted for elevation (assumes standard atmosphere)
##    Sea Level Pressure (QFF)  Station Pressure adjusted for elevation, temperature and humidity
##
##  Notes about input parameters:
##  currentTemp -     current instantaneous station temperature
##  meanTemp -        average of current temp and the temperature 12 hours in
##                    the past. If the 12 hour temp is not known, simply pass
##                    the same value as currentTemp for the mean temp.
##  humidity -        Value should be 0 to 100. For the pressure conversion
##                    functions, pass a value of zero if you do not want to
##                    the algorithm to include the humidity correction factor
##                    in the calculation. If you provide a humidity value
##                    > 0, then humidity effect will be included in the
##                    calculation.
##  elevation -       This should be the geometric altitude of the station
##                    (this is the elevation provided by surveys and normally
##                    used by people when they speak of elevation). Some
##                    algorithms will convert the elevation internally into
##                    a geopotential altitude.
##  sensorElevation - This should be the geometric altitude of the actual
##                    barometric sensor (which could be different than the
##                    official station elevation).
##
##   Notes about Sensor Pressure vs. Station Pressure:
##    SensorToStationPressure and StationToSensorPressure functions are based
##    on an ASOS algorithm. It corrects for a difference in elevation between
##    the official station location and the location of the barometetric sensor.
##    It turns out that if the elevation difference is under 30 ft, then the
##    algorithm will give the same result (a 0 to .01 inHg adjustment) regardless
##    of temperature. In that case, the difference can be covered using a simple
##    fixed offset. If the difference is 30 ft or greater, there is some effect
##    from temperature, though it is small. For example, at a 100ft difference,
##    the adjustment will be .13 inHg at -30F and .10 at 100F. The bottom line
##    is that while ASOS stations may do this calculation, it is likely unneeded
##    for home weather stations, and the station pressure and the sensor pressure
##    can be treated as equivalent.



## Formulas / Algorithms
## Sea Level Pressure reduction algorithms
TSLPAlgorithm = [
        'paDavisVP',  ## algorithm closely approximates SLP calculation used inside Davis Vantage Pro weather equipment console (http:##www.davisnet.com/weather/)
        'paUnivie',   ## http:##www.univie.ac.at/IMG-Wien/daquamap/Parametergencom.html
        'paManBar'    ## from Manual of Barometry (1963)
        ]

## Altimeter algorithms
TAltimeterAlgorithm = [
        'aaASOS',     ## formula described in the ASOS training docs
        'aaASOS2',    ## metric formula that was likely used to derive the aaASOS formula
        'aaMADIS',    ## apparently the formula used by the MADIS system
        'aaNOAA',     ## essentially the same as aaSMT with any result differences caused by unit conversion rounding error and geometric vs. geopotential elevation
        'aaWOB',      ## Weather Observation Handbook (algorithm similar to aaASOS & aaASOS2 - main differences being precision of constants used)
        'aaSMT'       ## Smithsonian Meteorological Tables (1963)
        ]

TVapAlgorithm = [
        'vaDavisVp',  ## algorithm closely approximates calculation used by Davis Vantage Pro weather stations and software
        'vaBuck',     ## this and the remaining algorithms described at http:##cires.colorado.edu/~voemel/vp.html
        'vaBuck81',
        'vaBolton',
        'vaTetenNWS',
        'vaTetenMurray',
        'vaTeten']

from math import exp, pow, log

DefaultSLPAlgorithm = 'paManBar';
DefaultAltimeterAlgorithm = 'aaMADIS';
DefaultVapAlgorithm = 'vaBolton';

## U.S. Standard Atmosphere (1976) constants
gravity = 9.80665            ## g at sea level at latitude 45.5 degrees in m/sec^2
uGC = 8.31432                ## universal gas constant in J/mole-K
moleAir = 0.0289644          ## mean molecular mass of air in kg/mole
moleWater = 0.01801528       ## molecular weight of water in kg/mole
gasConstantAir = uGC/moleAir ## (287.053) gas constant for air in J/kgK
standardSLP = 1013.25        ## standard sea level pressure in hPa
standardSlpInHg = 29.921     ## standard sea level pressure in inHg
standardTempK = 288.15       ## standard sea level temperature in Kelvin
earthRadius45 = 6356.766     ## radius of the earth at latitude 45.5 degrees in km
standardLapseRate = 0.0065   ## standard lapse rate (6.5C/1000m i.e. 6.5K/1000m)
standardLapseRateFt = standardLapseRate * 0.3048  ## (0.0019812) standard lapse rate per foot (1.98C/1000ft)
vpLapseRateUS = 0.00275      ## lapse rate used by Davis VantagePro (2.75F/1000ft)
manBarLapseRate = 0.0117     ## lapse rate from Manual of Barometry (11.7F/1000m, which = 6.5C/1000m)

def StationToSensorPressure(pressureHPa, sensorElevationM,  stationElevationM, currentTempC): 
    ## from ASOS formula specified in US units
    return InToHPa(HPaToIn(pressureHPa) / 
           pow(10, (0.00813 * MToFt(sensorElevationM - stationElevationM) / FToR(CToF(currentTempC)))))

def StationToAltimeter(PressureHPa, elevationM, algorithm = DefaultAltimeterAlgorithm):
    if algorithm == 'aaASOS':
        ## see ASOS training at http:##www.nwstc.noaa.gov
        ## see also http:##wahiduddin.net/calc/density_altitude.htm
        return InToHPa(Power(Power(HPaToIn(pressureHPa), 0.1903) + (1.313E-5 * MToFt(elevationM)), 5.255))
    elif algorithm == 'aaASOS2':
        geopEl = GeopotentialAltitude(elevationM)
        k1 = standardLapseRate * gasConstantAir / gravity   ## approx. 0.190263
        k2 = 8.41728638E-5   ## (standardLapseRate / standardTempK) * (Power(standardSLP,  k1)
        return Power(Power(pressureHPa, k1) + (k2 * geopEl), 1/k1)
    elif algorithm == 'aaMADIS':
        ## from MADIS API by NOAA Forecast Systems Lab, see http://madis.noaa.gov/madis_api.html
        k1 = 0.190284; ## discrepency with calculated k1 probably because Smithsonian used less precise gas constant and gravity values
        k2 = 8.4184960528E-5; ## (standardLapseRate / standardTempK) * (Power(standardSLP, k1)
        return Power(Power(pressureHPa - 0.3, k1) + (k2 * elevationM), 1/k1)
    elif algorithm == 'aaNOAA':
        ## see http://www.srh.noaa.gov/elp/wxcalc/formulas/altimeterSetting.html
        k1 = 0.190284  ## discrepency with k1 probably because Smithsonian used less precise gas constant and gravity values
        k2 = 8.42288069E-5  ## (standardLapseRate / 288) * (Power(standardSLP, k1SMT);
        return (pressureHPa - 0.3) * Power(1 + (k2 * (elevationM / Power(pressureHPa - 0.3, k1))), 1/k1)
    elif algorithm == 'aaWOB':
        ## see http://www.wxqa.com/archive/obsman.pdf
        k1 = standardLapseRate * gasConstantAir / gravity  ## approx. 0.190263
        k2 = 1.312603E-5  ##(standardLapseRateFt / standardTempK) * Power(standardSlpInHg, k1);
        return InToHPa(Power(Power(HPaToIn(pressureHPa), k1) + (k2 * MToFt(elevationM)), 1/k1))
    elif algorithm == 'aaSMT':
        ## see WMO Instruments and Observing Methods Report No.19 at http://www.wmo.int/pages/prog/www/IMOP/publications/IOM-19-Synoptic-AWS.pdf
        k1 = 0.190284; ## discrepency with calculated value probably because Smithsonian used less precise gas constant and gravity values
        k2 = 4.30899E-5; ## (standardLapseRate / 288) * (Power(standardSlpInHg, k1SMT));
        geopEl = GeopotentialAltitude(elevationM)
        return InToHPa((HPaToIn(pressureHPa) - 0.01) * Power(1 + (k2 * (geopEl / Power(HPaToIn(pressureHPa) - 0.01, k1))), 1/k1));
    else: 
        raise Exception('unknown algorithm')

def StationToSeaLevelPressure(pressureHPa, elevationM, currentTempC, meanTempC, humidity, algorithm = DefaultSLPAlgorithm):
    return pressureHPa * PressureReductionRatio(pressureHPa, elevationM, currentTempC, meanTempC, humidity, algorithm)


def SensorToStationPressure(pressureHPa, sensorElevationM, stationElevationM, currentTempC):
    ## see ASOS training at http://www.nwstc.noaa.gov
    ## from US units ASOS formula
    return InToHPa(HPaToIn(pressureHPa) * 
                  (10 * (0.00813 * MToFt(sensorElevationM - stationElevationM)/ FToR(CToF(currentTempC)))))

def SeaLevelToStationPressure(pressureHPa, elevationM, currentTempC, meanTempC, humidity, algorithm = DefaultSLPAlgorithm): 
    return pressureHPa / PressureReductionRatio(pressureHPa, elevationM, currentTempC, meanTempC, humidity, algorithm);

def PressureReductionRatio(pressureHPa, elevationM, currentTempC, meanTempC, humidity, algorithm = DefaultSLPAlgorithm): 
    if algorithm == 'paUnivie':
        ##  see http://www.univie.ac.at/IMG-Wien/daquamap/Parametergencom.html
        geopElevationM = GeopotentialAltitude(elevationM)
        return exp(((gravity/gasConstantAir) * geopElevationM)
                / (VirtualTempK(pressureHPa, meanTempC, humidity) + (geopElevationM * standardLapseRate/2)))
    elif algorithm == 'paDavisVP':
        ## see http://www.exploratorium.edu/weather/barometer.html
        if (humidity > 0):
          hcorr = (9/5) * HumidityCorrection(currentTempC, elevationM, humidity, 'vaDavisVP')
        else:
          hcorr = 0
        ## in the case of davisvp, take the constant values literally.
        return pow(10, (MToFt(elevationM) / (122.8943111 * (CToF(meanTempC) + 460 + (MToFt(elevationM) * vpLapseRateUS/2) + hcorr))))
    elif algorithm == 'paManBar':
        ## see WMO Instruments and Observing Methods Report No.19 at http://www.wmo.int/pages/prog/www/IMOP/publications/IOM-19-Synoptic-AWS.pdf
        if (humidity > 0):
              hCorr = (9/5) * HumidityCorrection(currentTempC, elevationM, humidity, 'vaBuck')
        else:
              hCorr = 0
        geopElevationM = GeopotentialAltitude(elevationM);
        return exp(geopElevationM * 6.1454E-2 / (CToF(meanTempC) + 459.7 + (geopElevationM * manBarLapseRate / 2) + hCorr))
    else:
        raise Exception('Unknown algorithm')

def ActualVaporPressure(tempC, humidity, algorithm = DefaultVapAlgorithm):
      return (humidity * SaturationVaporPressure(tempC, algorithm)) / 100

def SaturationVaporPressure(tempC, algorithm = DefaultVapAlgorithm): 
    ## see http://cires.colorado.edu/~voemel/vp.html   comparison of vapor pressure algorithms
    ## see (for DavisVP) http://www.exploratorium.edu/weather/dewpoint.html
    if algorithm == 'vaDavisVP': 
        return 6.112 * exp((17.62 * tempC)/(243.12 + tempC))  ## Davis Calculations Doc
    elif algorithm == 'vaBuck': 
        return 6.1121 * exp((18.678 - (tempC/234.5)) * tempC / (257.14 + tempC))  ## Buck(1996)
    elif algorithm == 'vaBuck81': 
        return 6.1121 * exp((17.502 * tempC)/(240.97 + tempC))  ## Buck(1981)
    elif algorithm == 'vaBolton': 
        return 6.112 * exp(17.67 * tempC / (tempC + 243.5))   ## Bolton(1980)
    elif algorithm == 'vaTetenNWS': 
        return 6.112 * pow(10,(7.5 * tempC / (tempC + 237.7)))  ## Magnus Teten see www.srh.weather.gov/elp/wxcalc/formulas/vaporPressure.html
    elif algorithm == 'vaTetenMurray': 
        return 10 *+ ((7.5 * tempC / (237.5 + tempC)) + 0.7858)  ## Magnus Teten (Murray 1967)
    elif algorithm == 'vaTeten': 
        return 6.1078 * pow(10, (7.5 * tempC / (tempC + 237.3))) ## Magnus Teten see www.vivoscuola.it/US/RSIGPP3202/umidita/attivita/relhumONA.htm
    else:
        raise Exception('Unknown algorithm')

def MixingRatio(pressureHPa, tempC, humidity): 
    ## see http://www.wxqa.com/archive/obsman.pdf
    ## see also http://www.vivoscuola.it/US/RSIGPP3202/umidita/attivita/relhumONA.htm
    k1 = moleWater / moleAir;  ## 0.62198
    vapPres = ActualVaporPressure(tempC, humidity, vaBuck)
    return 1000 * ((k1 * vapPres) / (pressureHPa - vapPres))

def VirtualTempK(pressureHPa, tempC, humidity):
    ## see http://www.univie.ac.at/IMG-Wien/daquamap/Parametergencom.html
    ## see also http://www.vivoscuola.it/US/RSIGPP3202/umidita/attivita/relhumONA.htm
    ## see also http://wahiduddin.net/calc/density_altitude.htm
    epsilon = 1 - (moleWater / moleAir)  ## 0.37802
    vapPres = ActualVaporPressure(tempC, humidity, vaBuck)
    return (CtoK(tempC)) / (1-(epsilon * (vapPres/pressureHPa)))

def HumidityCorrection(tempC, elevationM, humidity, algorithm = DefaultVapAlgorithm):
    vapPress = ActualVaporPressure(tempC, humidity, algorithm)
    return (vapPress * ((2.8322E-9 * (elevationM ** 2)) + (2.225E-5 * elevationM) + 0.10743))

def DewPoint(tempC, humidity, algorithm = DefaultVapAlgorithm):
    LnVapor = log(ActualVaporPressure(tempC, humidity, algorithm))
    if algorithm == 'vaDavisVP': 
        return ((243.12 * LnVapor) - 440.1) / (19.43 - LnVapor)
    else:
        return ((237.7 * LnVapor) - 430.22) / (19.08 - LnVapor)

def WindChill(tempC, windSpeedKmph):
    """
    Wind Chill
    Params:
        - tempC
        - windSpeedKmph

    Wind Chill algorithm is only valid for temperatures below 10C and wind speeds
    above 4,8 Km/h. Outside this range a None value is returned.
    
    see American Meteorological Society Journal
    see http://www.msc.ec.gc.ca/education/windchill/science_equations_e.cfm
    see http://www.weather.gov/os/windchill/index.shtml
    """
    if ((tempC >= 10.0) or (windSpeedKmph <= 4.8)):
        return None
    else:
        windPow = pow(windSpeedKmph, 0.16)
        Result = min([tempC, 13.12 + (0.6215 * tempC) - (11.37 * windPow) + (0.3965 * tempC * windPow)])
        return Result if Result < tempC else tempC

def HeatIndex(tempC, humidity):
    """
    Heat Index
    Params:
        - tempC
        - humidity 

    Heat index algorithm is only valid for temps above 26.7C / 80F. 
    Outside this range a None value is returned.

    see http://www.hpc.ncep.noaa.gov/heat_index/hi_equation.html
    """
    tempF = CToF(tempC)
    if (tempF < 80):
        return None
    else:
        tSqrd = tempF **2
        hSqrd = humidity **2
        Result = (0.0 - 42.379 + (2.04901523 * tempF) + (10.14333127 * humidity) -
                 (0.22475541 * tempF * humidity) - (0.00683783 * tSqrd) -
                 (0.05481717 * hSqrd) + (0.00122874 * tSqrd * humidity) +
                 (0.00085282 * tempF * hSqrd) - (0.00000199 * tSqrd * hSqrd))
        ## Rothfusz adjustments
        if ((humidity < 13) and (tempF >= 80) and (tempF <= 112)):
            Result -= ((13.0 - humidity)/4.0) * Sqrt((17.0 - Abs(tempf - 95.0))/17.0)
        elif ((humidity > 85) and (tempF >= 80) and (tempF <= 87)):
            Result += ((humidity - 85.0)/10.0) * ((87.0 - tempF)/5.0)
    return FToC(Result) if Result > tempF else tempC

def Humidex(tempC, humidity): 
    if tempC <= 20.0:
        return None
    else:
        humidex = tempC + ((5.0/9.0) * (ActualVaporPressure(tempC, humidity, 'vaTetenNWS') - 10.0))
        if humidex > tempC:
            return humidex
        else:
            return None

def GeopotentialAltitude(geometricAltitudeM): 
    return (earthRadius45 * 1000 * geometricAltitudeM) / ((earthRadius45 * 1000) + geometricAltitudeM)


###########################################################################################
## 2) Unit conversion functions, translated to Python from  
##    uWxUtils (http://www.softwx.com/weather/uwxutils.html)      
###########################################################################################

def FToC(value): 
    return (((value * 1.0) - 32.0) * 5.0) / 9.0

def CToF(value): 
    return  ((value * 9.0) / 5.0) + 32.0

def CToK(value): 
    return 273.15 + value

def KToC(value): 
    return value - 273.15

def FToR(value): 
    return value + 459.67

def RToF(value):
    return value - 459.67

def InToHPa(value):
    return value / 0.02953

def HPaToIn(value):
    return value * 0.02953

def FtToM(value):
    return value * 0.3048

def MToFt(value):
    return value / 0.3048

def InToMm(value): 
    return value * 25.4

def MmToIn(value): 
    return value / 25.4

def MToKm(value): # Miles !
    return value * 1.609344

def KmToM(value): # Miles !
    return value / 1.609344

def msToKmh(value):
    return value * 3.6


###########################################################################################
## 3) Wind calculations
###########################################################################################

WIND_DIRECTIONS = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW', 'N']


# http://www.procdev.com/downloads/windcalcs.zip
# http://www.webmet.com/met_monitoring/621.html

def WindX(v,d):
    """
    Extract X component of wind speed 
    (X and Y are standard rectangular coordinates, ie X = East, Y = North)
    """ 
    if d == None:
        return 0
    else:
        return v * math.cos(2.0 * math.pi * (90.0 - d) / 360.0)

def WindY(v,d):
    """
    Extract Y component of wind speed 
    (X and Y are standard rectangular coordinates, ie X = East, Y = North)
    """ 
    if d == None:
        return 0
    else:
        return v * math.sin(2.0 * math.pi * (90.0 - d) / 360.0)

def WindSpeed(x,y):
    """
    Obtains composite wind speed from x and y speeds
    """
    return math.sqrt(x**2 + y**2)


def WindDir(x,y):
    """
    Obtains composite wind direction from x and y speeds
    """
    # Calculate polar coordinate angle
    degrees = math.degrees(math.atan2(x, y))
    # Convert to compass bearing
    if degrees < 0.0:
        degrees += 360.0
    return degrees


def WindDirTxt(d):
    """
    Obtains textual representation of wind direction from a degree value (0 = 360 = N)
    """
    if d == None:
        return ''
    else:
        return WIND_DIRECTIONS[int(round(d / 22.5))]


def WindPredominantDirection(l):
    """
    Given a list of [(speed, dir)] returns predominant wind direction
    obtained by wind speed vectors composition.
    """
    # Step 1: (speed, dir) -> (speed, speedX, speedY)
    l1 = map(lambda (v,d): (WindX(v,d), WindY(v,d)), l)

    # Step 2: Calculate averages of speed, speedX, and speedY
    [avg_x, avg_y] = map(lambda L: sum(L)/len(L), zip(* l1))

    # Step 3: return average speed, composite average speed and composite wind direction
    return WindDir(avg_x, avg_y)


