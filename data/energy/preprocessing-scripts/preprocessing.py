############# Packages Import ##############

import pandas
import numpy as np

############# Scripts to get data ##############

# Electricity price in NL
# from 2007-2005 half-yearly
# from https://ec.europa.eu/eurostat/databrowser/view/nrg_pc_205__custom_18701128/default/table
# in Euro per kWh
def get_electricity_price_data():
    with open('raw-data/nrg_pc_205__custom_18701019_linear.csv', mode ='r')as file:
        csvFile = pandas.read_csv(file)
    return np.array(csvFile['OBS_VALUE'].where(csvFile['tax']=='Excluding taxes and levies').dropna(), dtype=float)

# Greenhouse gases by electricity production in NL
# from 1990-2023
# from https://www.eea.europa.eu/en/analysis/maps-and-charts/greenhouse-gases-viewer-data-viewers
# in kt CO2 = 1.000.000 kg CO2
def get_greenhouse_gases_by_energy():
    with open('raw-data/S_Table.csv', mode ='r', encoding='utf-16')as file:
        csvFile = pandas.read_csv(file, sep="\t")
    arr =[]
    for x in np.array(csvFile['Emissions'].where((csvFile['Unnamed: 0']=="Netherlands") & (csvFile['Unnamed: 1']=="Energy supply")).dropna()):
        arr.append(float(x.replace('.','')))
    return arr

# Gross electricity production in NL
# from 1990-2023
# from https://ec.europa.eu/eurostat/databrowser/view/nrg_bal_c__custom_18717923/default/table
# in GWH = 1.000.000 KWH
def get_total_energy():
    with open('raw-data/nrg_bal_c__custom_18717923_linear_2_0.csv', mode ='r')as file:
        csvFile = pandas.read_csv(file)
    return np.array(csvFile['OBS_VALUE'], dtype=float)

# Greenhouse gases per energy production in NL
# from 1990-2023
# in kg CO2 per kWh
def get_greenhouse_gas_emissions_data():
    return get_greenhouse_gases_by_energy()/get_total_energy()

# Unit cost for PV panel worldwide
# from 1975-2024
# from https://ourworldindata.org/grapher/solar-pv-prices
# in USD / watt = approx. Euro / kW *(1/1000)*(1/0.87)
def get_pv_panel_unit_cost():
    with open('raw-data/solar-pv-prices.csv', mode ='r')as file:
        csvFile = pandas.read_csv(file)
    return np.array(csvFile['Solar photovoltaic module price'], dtype=float) * 1000 * 0.87