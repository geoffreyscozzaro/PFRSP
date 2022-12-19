from constantes import *

class Terminal():
    def __init__(self, terminal_name, terminal_number, capacity):
        self.terminal_name = terminal_name
        self.terminal_number = terminal_number
        self.capacity = capacity
        self.nb_initial_departures = 0 #nb a/c that slept on terminal, computed in read_flightset
        self.initial_occupancy = 0 #at beggining time window , computed in timeWindowManagement
        self.capacities = {} #per 30-min window, key: time start time window, value: capacity
    def __str__(self):
        return f"{self.terminal_name}, terminal number:{self.terminal_number}, nb initial departures: {self.nb_initial_departures}, initial occupancy:{self.initial_occupancy},  capacity:{self.capacity} "




class Runway():
    def __init__(self, id, runway_name, runway_type, capacity):  #type :  0 = landing, 1= takeoff, 2 = mixed_mode
        self.id = id
        self.name = runway_name
        self.type = runway_type
        self.capacity = capacity  # max throughput per 10-minute
        self.capacities = {} #per 30-min window, key: time start time window, value: capacity
        self.init_throughput = 0

    def __str__(self):
        return f"Runway {self.name}, init_throughput = {self.init_throughput} capacity = {self.capacity}"




class Taxi():
    def __init__(self,capacity):
        self.capacity = capacity
        self.initial_occupancy = 0
        self.capacities = {} #per 30-min window, key: time start time window, value: capacity
    def __str__(self):
        return f"Taxi network with capacity = {self.capacity}"



class Airport():
    def __init__(self):
        self.runways = []
        self.terminals = []
        self.taxi_in_duration = []
        self.taxi_out_duration = []
        self.taxi = Taxi(0)

    def add_runway(self, runway):
        self.runways.append(runway)

    def add_terminal(self, terminal):
        self.terminals.append(terminal)

    # def add_taxi(self, taxi):
    #     self.taxi = taxi


