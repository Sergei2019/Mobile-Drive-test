# Mobile-Drive-test


## Table of contents
* [General info](#general-info)
* [Technologies](#technologies)
* [Setup](#setup)
* [Example](#example)

## General info
Mobile drive test is a simple program to visualize the received signal (RSRP) of smartphones (User equipments) in the cell.

UE sends the measurement's report messages during the period with main characteristics of the cell (CELL IDENTIFICATION, RSRP, RSRQ) and GPS coordinates.
With a Nokia's Netact application Trace viewer the radio engineer can get the trace of the particular cell and then download in .csv.
	
## Technologies
Project is created with:
* Python >= 3.7
* folium == 0.12.0
* geopandas == 0.10.2
* h3pandas == 0.2.3
* tkinter(customtkinter)


## Setup
To run this project, install requirements.txt then compile it with auto-py-to-exe OR just run .exe file

Note: .exe file must be in the same directory as traces (.csv files)

## Example
![alt text](https://github.com/Sergei2019/Mobile-Drive-test/blob/main/Example.PNG?raw=true)
