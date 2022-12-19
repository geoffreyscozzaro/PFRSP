import numpy as np
from constants import *

class Passenger():
    def __init__(self,flightset):
        self.terminal_transit_times = np.zeros((NB_TERMINALS,NB_TERMINALS))
        self.ground_pax_connected_table = {}
        self.air_connected_pax_table = {}
       
    def add_air_connected_pax(self,id_dep_flight,id_arr_flight,min_connection_time,nb_pax):
        connected_pax = Connected_pax(id_dep_flight,id_arr_flight,min_connection_time,nb_pax)
        self.air_connected_pax_table[(id_dep_flight,id_arr_flight)]=connected_pax

class Connected_pax():
    def __init__(self,id_dep_flight,id_arr_flight,min_connection_time,nb_pax):
        self.id_dep_flight=id_dep_flight
        self.id_arr_flight = id_arr_flight
        self.min_connection_time = min_connection_time
        self.nb_pax = nb_pax

    def __str__(self):
        return f'n°{self.id_arr_flight} -->n°{self.id_dep_flight} , connecting time:{self.min_connection_time},  nb pax: {self.nb_pax}'


# import pandas as pd
# df = pd.read_csv('Data/Thesis-SariaRCDG_2019_6_21.csv',usecols=['Horaire théorique','Numéro de vol',
#                                                                  'Terminal','Salle',
#                                                                  'Code aéroport IATA','Type de mouvement',
#                                                                  'Immatriculation','QFU','Nombre de passagers réalisés'])
#
#
#
#
# row = df.loc[10]
#
# df.loc[10,'Numéro de vol'] = 'id_vol_100'
# df.loc[10,'Immatriculation'] = 'id_aircraft_92'
# df.loc[10,'Nombre de passagers réalisés'] = 214
#
# print(df.loc[10])