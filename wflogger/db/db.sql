-- Copyright 2009 Jordi Puigsegur (jordi.puigsegur@gmail.com)
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

-- TODO: Add support for UV sensor

CREATE TABLE METEO(
  TIMESTAMP_UTC Timestamp NOT NULL,
  TIMESTAMP_LOCAL Timestamp NOT NULL,
  TEMP Numeric(3,1),
  TEMP_MIN Numeric(3,1),
  TEMP_MIN_TIME Timestamp,
  TEMP_MAX Numeric(3,1),
  TEMP_MAX_TIME Timestamp,
  HUM Numeric(2,1),
  WIND Numeric(4,1),
  WIND_DIR Smallint,
  WIND_GUST Numeric(4,1),
  WIND_GUST_DIR Smallint,
  WIND_GUST_TIME Timestamp,
  DEW_POINT Numeric(3,1),
  RAIN Numeric(5,1),
  RAIN_RATE Numeric(5,1),
  RAIN_RATE_TIME Timestamp,
  PRESSURE Numeric(5,1),
  CONSTRAINT PK_METEO PRIMARY KEY (TIMESTAMP_UTC)
);

CREATE DESCENDING INDEX IDX_METEO1 ON METEO (TIMESTAMP_LOCAL);
