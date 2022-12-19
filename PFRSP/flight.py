from constantes import *
from airport import *

class Flight_A():
    def __init__(self, id,  term, init_runway, landing_time, ibt, status = 0):
        self.id = id
        self.type_ad = 0
        self.terminal = term
        self.landing_time = landing_time
        self.runway = init_runway
        self.ibt = ibt
        self.final_landing_time = landing_time #after optim
        self.final_runway = init_runway #after optim
        self.final_ibt = ibt
        # self.priority = priority # depends flights characteristics
        self.status = status #4 statuses : completed, on going, active, planned, mise à jour avec timeWindowManagement
        # print(self.landing_time, min(self.landing_time_min), max(self.landing_time_max))

    def __str__(self):
        return f"flightId: {self.id} type_ad: {self.type_ad} terminal: {self.terminal} init_runway: {self.runway} " \
               f"init_landing_time: {self.landing_time} init_ibt: {self.ibt} status: {self.status} " \
               f"final_runway: {self.final_runway} final_landing_time: {self.final_landing_time}  " \
               f"final_ibt: {self.final_ibt}"

    def to_string(self):
        return f"flightId: {self.id} type_ad: {self.type_ad} terminal: {self.terminal} init_runway: {self.runway} " \
               f"init_landing_time: {self.landing_time} init_ibt: {self.ibt} status: {self.status} " \
               f"final_runway: {self.final_runway} final_landing_time: {self.final_landing_time}  " \
               f"final_ibt: {self.final_ibt}"


class Flight_D():
    def __init__(self, id, term, init_runway, obt, takeoff, priority, status =0):
        self.id = id
        self.type_ad = 1
        self.terminal = term
        self.obt = obt
        self.runway = init_runway
        self.takeoff= takeoff
        self.final_obt = obt #after optim
        self.final_runway = init_runway #after optim
        self.final_takeoff = takeoff
        self.priority = priority # =1 if flight has to respect its slot or not
        self.status = status #4 statuses : completed, on going, active, planned

    def __str__(self):
        return f"flightId: {self.id} type_ad: {self.type_ad} terminal: {self.terminal} init_runway: {self.runway}" \
               f" init_obt: {self.obt}  init_takeoff: {self.takeoff} status: {self.status}  " \
               f"final_runway: {self.final_runway} final_obt: {self.final_obt} final_takeoff: {self.final_takeoff}"

    def to_string(self):
        return f"flightId: {self.id} type_ad: {self.type_ad} terminal: {self.terminal} init_runway: {self.runway}" \
               f" init_obt: {self.obt}  init_takeoff: {self.takeoff} status: {self.status} priority: {self.priority} " \
               f"final_runway: {self.final_runway} final_obt: {self.final_obt} final_takeoff: {self.final_takeoff}"


class Flightset():

    def __init__(self):
        self.flights_a = {}
        self.flights_d = {}
        # self.flights = [] #all flights
        self.id_flights_ad=[]
        # self.id_flights_only_d = []
        # self.id_flights_only_a = []

        
    def add_flight(self, flight, flight_type):
        if flight_type == 'D':
            self.flights_d[flight.id] = flight
        else:
            self.flights_a[flight.id] = flight
        # self.flights.append(flight)

    def add_AD_flight(self,id_flight): # ajoute indice des flights AD pour ajouter contrainte turn around sur ceux ci
        self.id_flights_ad.append(id_flight)

    #
    # def add_only_A_flight(self,id_flight): # ajoute indice des flights AD pour ajouter contrainte turn around sur ceux ci
    #     self.id_flights_only_a.append(id_flight)
    #
    #
    # def add_only_D_flight(self,id_flight): # ajoute indice des flights AD pour ajouter contrainte turn around sur ceux ci
    #     self.id_flights_only_d.append(id_flight)



