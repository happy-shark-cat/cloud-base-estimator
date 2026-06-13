# cloud-base-estimator
A simple cloud base height estimator using temperature, dew point, location, time, and sky photos.


## Overview

Cloud Base Estimator is a small learning project that estimates cloud base height from surface temperature and dew point.

The first version uses weather data from Open-Meteo and calculates an approximate cloud base height using a simple LCL approximation.

## Features

- Fetch current weather data by latitude and longitude
- Estimate cloud base height from temperature and dew point
- Upload and display a sky photo
- Show calculation details
- Display safety disclaimer

## Formula

```text
Cloud base height ≒ 125 × (Temperature - Dew point)
