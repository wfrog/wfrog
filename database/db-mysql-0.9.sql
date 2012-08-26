-- Copyright 2011 Jordi Puigsegur (jordi.puigsegur@gmail.com)
--
--  This file is part of WFrog
--
--  WFrog is free software: you can redistribute it and/or modify
--  it under the terms of the GNU General Public License as published by
--  the Free Software Foundation, either version 3 of the License, or
--  (at your option) any later version.
--
--  This program is distributed in the hope that it will be useful,
--  but WITHOUT ANY WARRANTY; without even the implied warranty of
--  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
--  GNU General Public License for more details.
--
--  You should have received a copy of the GNU General Public License
--  along with this program.  If not, see <http://www.gnu.org/licenses/>.


-- wfrog supports additional temperature & humidity sensors when using
-- database storages. Just uncomment the relevant lines and the sensor
-- values will be recorded.

CREATE TABLE METEO
( TIMESTAMP_UTC Timestamp NOT NULL,
  TIMESTAMP_LOCAL Timestamp NOT NULL,
  -- Uncomment to record sensor 0, interior TEMP/HUM
  -- TEMPINT Numeric(3,1), 
  -- HUMINT Numeric(3,1),
  -- Main TEMP/HUM sensor is sensor number 1
  TEMP Numeric(3,1),
  HUM Numeric(3,1),
  WIND Numeric(4,1),
  WIND_DIR Smallint,
  WIND_GUST Numeric(4,1),
  WIND_GUST_DIR Smallint,
  DEW_POINT Numeric(3,1),
  RAIN Numeric(4,1),
  RAIN_RATE Numeric(4,1),
  PRESSURE Numeric(5,1),
  -- Uncomment to record UV Index
  -- UV_INDEX Smallint,
  -- Uncomment to record Solar Radiation sensor
  -- SOLAR_RAD Numeric(5,1)
  -- Uncomment to record additional TEMP/HUM sensors
  -- TEMP2 Numeric(3,1), 
  -- HUM2 Numeric(3,1),
  -- TEMP3 Numeric(3,1), 
  -- HUM3 Numeric(3,1),
  -- TEMP4 Numeric(3,1), 
  -- HUM4 Numeric(3,1),
  -- TEMP5 Numeric(3,1), 
  -- HUM5 Numeric(3,1),
  -- TEMP6 Numeric(3,1), 
  -- HUM6 Numeric(3,1),
  -- TEMP7 Numeric(3,1), 
  -- HUM7 Numeric(3,1),
  -- TEMP8 Numeric(3,1), 
  -- HUM8 Numeric(3,1),
  -- TEMP9 Numeric(3,1), 
  -- HUM9 Numeric(3,1),
  PRIMARY KEY (TIMESTAMP_UTC),
  KEY METEO_IDX (TIMESTAMP_LOCAL));
