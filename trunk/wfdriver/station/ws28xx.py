## Copyright 2012 Eddi De Pieri <eddi@depieri.net>
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

##  To use this module you need to install somewhere 
##  the library available at https://github.com/dpeddi/ws-28xx.git
##  Before you start wfrog you need to export path to ws-28xx module
##  export PYTHONPATH=$PYTHONPATH:/path/to/ws-28xx-module
##  then you can start wfrog.

##  The ws-28xx at github and driver are still under heavy
##  development. Feel free to contribute.

##  2012-04-27: my station stopped working. I've imported a US unit
##              while I live in EU. I've asked support for my unit
##              both to lacrossetechnology.com and lacrossetecnhology.fr
##
##              Now I'm in the situation that both give email support
##              but I can't get my station back to repair.


import time
import logging

def detect():
	try:
		station = WS28xxStation()
	except:
		print "ws28xx: failed loading modules"
		station = None
	return station

class WS28xxStation(object):

	logger = logging.getLogger('station.ws28xx')

	name = "LaCrosse WS28xx"
	
	def run(self, generate_event, send_event, context={}):

		import HeavyWeatherService
		import CWeatherTraits

		CWeatherTraits = CWeatherTraits.CWeatherTraits()

		myCCommunicationService = HeavyWeatherService.CCommunicationService()
		HeavyWeatherService.CDataStore.setCommModeInterval(myCCommunicationService.DataStore,3)
		time.sleep(5)

		if HeavyWeatherService.CDataStore.getDeviceId(myCCommunicationService.DataStore) == -1:
			TimeOut = HeavyWeatherService.CDataStore.getPreambleDuration(myCCommunicationService.DataStore) + HeavyWeatherService.CDataStore.getRegisterWaitTime(myCCommunicationService.DataStore)
			ID=[0]
			ID[0]=0
			print "Press [v] key on Weather Station"
			HeavyWeatherService.CDataStore.FirstTimeConfig(myCCommunicationService.DataStore,ID,TimeOut)

		HeavyWeatherService.CDataStore.setDeviceRegistered(myCCommunicationService.DataStore, True);	#temp hack

		Weather = [0]
		Weather[0]=[0]

		TimeOut = HeavyWeatherService.CDataStore.getPreambleDuration(myCCommunicationService.DataStore) + HeavyWeatherService.CDataStore.getRegisterWaitTime(myCCommunicationService.DataStore)
		HeavyWeatherService.CDataStore.GetCurrentWeather(myCCommunicationService.DataStore,Weather,TimeOut)
		time.sleep(1)

		while True:
			if HeavyWeatherService.CDataStore.getRequestState(myCCommunicationService.DataStore) == HeavyWeatherService.ERequestState.rsFinished \
			       or HeavyWeatherService.CDataStore.getRequestState(myCCommunicationService.DataStore) == HeavyWeatherService.ERequestState.rsINVALID:
					TimeOut = HeavyWeatherService.CDataStore.getPreambleDuration(myCCommunicationService.DataStore) + HeavyWeatherService.CDataStore.getRegisterWaitTime(myCCommunicationService.DataStore)
					HeavyWeatherService.CDataStore.GetCurrentWeather(myCCommunicationService.DataStore,Weather,TimeOut)

			try:
				if abs(CWeatherTraits.TemperatureNP() - myCCommunicationService.DataStore.CurrentWeather._IndoorTemp ) > 0.001:
					e = generate_event('temp')
					e.sensor = 0
					e.value = myCCommunicationService.DataStore.CurrentWeather._IndoorTemp
					send_event(e)

				if abs(CWeatherTraits.HumidityNP() - myCCommunicationService.DataStore.CurrentWeather._IndoorHumidity ) > 0.001:
					e = generate_event('hum')
					e.sensor = 0
					e.value = myCCommunicationService.DataStore.CurrentWeather._IndoorHumidity
					send_event(e)

				if abs(CWeatherTraits.TemperatureNP() - myCCommunicationService.DataStore.CurrentWeather._OutdoorTemp ) > 0.001:
					e = generate_event('temp')
					e.sensor = 1
					e.value = myCCommunicationService.DataStore.CurrentWeather._OutdoorTemp
					send_event(e)

				if abs(CWeatherTraits.HumidityNP() - myCCommunicationService.DataStore.CurrentWeather._OutdoorHumidity ) > 0.001:
					e = generate_event('hum')
					e.sensor = 1
					e.value = myCCommunicationService.DataStore.CurrentWeather._OutdoorHumidity
					send_event(e)

				if abs(CWeatherTraits.PressureNP() - myCCommunicationService.DataStore.CurrentWeather._PressureRelative_hPa ) > 0.001:
					e = generate_event('press')
					e.value = myCCommunicationService.DataStore.CurrentWeather._PressureRelative_hPa
					send_event(e)

				if CWeatherTraits.RainNP() != myCCommunicationService.DataStore.CurrentWeather._RainTotal:
					e = generate_event('rain')
					e.rate = myCCommunicationService.DataStore.CurrentWeather._Rain1H
					e.total = myCCommunicationService.DataStore.CurrentWeather._RainTotal
					send_event(e)

				if abs(CWeatherTraits.WindNP() - myCCommunicationService.DataStore.CurrentWeather._WindSpeed) > 0.001:
	    				e = generate_event('wind')
					e.create_child('mean')
					e.mean.speed = myCCommunicationService.DataStore.CurrentWeather._WindSpeed
					e.mean.dir = myCCommunicationService.DataStore.CurrentWeather._WindDirection * 360 / 16
					e.create_child('gust')
					e.gust.speed = myCCommunicationService.DataStore.CurrentWeather._Gust
					e.gust.dir = myCCommunicationService.DataStore.CurrentWeather._GustDirection * 360 / 16
					send_event(e)

			except Exception, e:
				self.logger.error(e)

			time.sleep(5)

name = WS28xxStation.name
