-- Copyright 2012 A Mennucc1
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

CREATE TABLE METEO(
  TIMESTAMP_UTC TIMESTAMP NOT NULL PRIMARY KEY,
  TIMESTAMP_LOCAL TIMESTAMP NOT NULL,
  -- Uncomment to record sensor 0, interior TEMP/HUM
  -- TEMPINT REAL,
  -- HUMINT REAL,
  -- Main TEMP/HUM sensor is sensor number 1
  TEMP REAL,
  HUM REAL,
  WIND REAL,
  WIND_DIR Smallint,
  WIND_GUST REAL,
  WIND_GUST_DIR Smallint,
  DEW_POINT REAL,
  RAIN REAL,
  RAIN_RATE REAL,
  PRESSURE Numeric
  -- Uncomment to record UV Index
  -- UV_INDEX Smallint,
  -- Uncomment to record Solar Radiation sensor
  -- SOLAR_RAD Numeric(5,1)
  -- Uncomment to record additional TEMP/HUM sensors
  -- TEMP2 REAL,
  -- HUM2 REAL,
  -- TEMP3 REAL,
  -- HUM3 REAL,
  -- TEMP4 REAL,
  -- HUM4 REAL,
  -- TEMP5 REAL,
  -- HUM5 REAL,
  -- TEMP6 REAL,
  -- HUM6 REAL,
  -- TEMP7 REAL,
  -- HUM7 REAL,
  -- TEMP8 REAL,
  -- HUM8 REAL,
  -- TEMP9 REAL,
  -- HUM9 REAL,
);
CREATE INDEX METEO_IDX ON METEO(TIMESTAMP_LOCAL);
