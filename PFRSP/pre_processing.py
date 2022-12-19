import math

import numpy as np
import pandas as pd

from passenger import *
from flight import *
from airport import *
from timeWindowManagement import *
from constants import *


def is_priority_airport(x,list_hubs):
    if x.startswith('LF') or x in list_hubs:
        return True
    else:
        return False


def write_df_priority_airport():
    df = pd.read_csv("Data/airport-codes.csv")
    list_hubs = ['EGLL','EHAM','EDDF','LEMD'] #heathrow,amsterdam,frankfurt,madrid
    df.dropna(subset=['iata_code'],inplace=True)
    df['Priority'] = df['ident'].apply(lambda x: is_priority_airport(x,list_hubs))
    df = df[df['Priority']][['iata_code']]
    df.to_csv('priority_airport.csv',index=False)


# write_df_priority_airport()



def initialized_airport(airport):
    arr_runways = {'27R':0,'26L':1}
    dep_runways = {'26R':2,'27L':3}
    terminals = ['T1', 'T2A', 'T2B','T2C','T2D','T2E','T2F','T2G','T3']
    dico_terminals = dict(zip(terminals,np.arange(NB_TERMINALS)))
    for runway in arr_runways:
        airport.add_runway(Runway(id=arr_runways[runway],runway_name=runway,runway_type=0,capacity=0)) #capacity computed in set_max_capacity()
    for runway in dep_runways:
        airport.add_runway(Runway(id=dep_runways[runway],runway_name=runway,runway_type=1,capacity=0)) #capacity computed in set_max_capacity()
    for i,terminal in enumerate(terminals):
        airport.terminals.append(Terminal(terminal,i,0)) #capacity computed in set_max_capacity()
    airport.taxi.capacity = 0 #capacity computed in set_max_capacity
    airport.taxi_in_duration = np.zeros((NB_RUNWAYS,NB_TERMINALS)) #computed in compute_average_taxi_time()
    airport.taxi_out_duration = np.zeros((NB_TERMINALS,NB_RUNWAYS)) #computed in compute_average_taxi_time()
    df_taxi = pd.read_csv('Data/Taxi_time_CDG.csv')
    for terminal in dico_terminals:
        for runway in arr_runways:
            taxi_duration = df_taxi[(df_taxi['Terminal'] == terminal) & (df_taxi['QFU']==runway)]['TAXI_TIME'].values[0]
            airport.taxi_in_duration[arr_runways[runway]][dico_terminals[terminal]] = int(taxi_duration//TIME_STEP)
        for runway in dep_runways:
            taxi_duration = df_taxi[(df_taxi['Terminal'] == terminal) & (df_taxi['QFU']==runway)]['TAXI_TIME'].values[0]
            airport.taxi_out_duration[dico_terminals[terminal]][dep_runways[runway]] = int(taxi_duration//TIME_STEP)
    print('taxi in *** : ',airport.taxi_in_duration)
    print('taxi out *** : ', airport.taxi_out_duration)



def read_flightset_TrafiCDG(flightset, airport):
    df = pd.read_csv(f'Data/{SCENARIO}/Thesis-SariaRCDG_{YEAR}_{MONTH}_{DAY}.csv')
    df.dropna(axis=0, how='all')
    runways_dico = {'27R':0,'26L':1,'26R':2,'27L':3, '09L':0 , '08R':1, '08L':2, '09R':3}
    terminals_dico = {'T1': 0 , 'T2A': 1, 'T2B':2 , 'T2C':3 , 'T2D':4 ,'T2E':5,'T2F':6,'T2G':7, 'T3':8}
    # terminals_dico = {'T1':0,'T2':1,'T3':2}
    # min_turnaround = -1
    for row in df.iterrows():
        id_f = row[1]['INDEX']
        type_ad, type_mvmt, terminal, rwy,  horaire_bloc, priority = row[1]['TYPE_AD'], row[1]['MOUVEMENT_TYPE'], \
                                                                     row[1]['TERMINAL'], row[1]['QFU'], \
                                                                     row[1]['BLOCK_TIME'], row[1]['PRIORITY']
        id_rwy = runways_dico[rwy]
        id_term = terminals_dico[terminal]
        if type_mvmt == 'Arrival':
            if id_rwy == 2 :
                id_rwy = 1
                print(f"**** runway flight {id_f}  changed  since landing on departure runway 3 ")
            elif id_rwy == 3:
                id_rwy = 0
                print(f"**** runway flight {id_f}  changed  since landing on departure runway 4 ")
            ibt = horaire_bloc//TIME_STEP
            landing_time = ibt - airport.taxi_in_duration[id_rwy][id_term]
            f_i = Flight_A(id_f, id_term, id_rwy, int(landing_time), ibt, priority)
            flightset.add_flight(f_i, flight_type='A')
            if type_ad == 'AD':
                # print("****",id_f)
                # print(df[df['INDEX']==id_f])
                [time1,time2] = df[df['INDEX']==id_f]['BLOCK_TIME'].values
                turnaround = (time2 - time1)/TIME_STEP
                if turnaround >= MIN_TURNAROUND_TIME: #not always the case (ex:INDEX 746 on 2019/06/21,tail number:FHBLJ)
                    flightset.add_AD_flight(id_f)
        else:
            if id_rwy == 0 :
                id_rwy = 3
                print(f"**** runway flight {id_f}  changed  sinced take off on landing runway 1 ")
            elif id_rwy == 1:
                id_rwy = 2
                print(f"**** runway flight {id_f}  changed  since take off on landing runway 2 ")
            obt= horaire_bloc // TIME_STEP
            takeoff = int(obt + airport.taxi_out_duration[id_term][id_rwy])
            f_i = Flight_D(id_f, id_term, id_rwy, obt, takeoff, priority)
            flightset.add_flight(f_i, flight_type='D')




def read_ground_passengers(passenger,flightset):
    delta_boarding_close = 600//TIME_STEP
    step_hour = TIME_STEP / (60 * 60)
    filename= f'Data/{SCENARIO}/arrivingPaxGround_{MODE_DISRUPTED.lower()}_{DELAY}s_{START_MODE_DISRUPTION_HOUR}h_{END_MODE_DISRUPTION_HOUR}h_{YEAR}_{MONTH}_{DAY}.txt'
    with open(filename,'r') as file:
        for line in file:
            liste = line.split()
            id = int(liste[0])
            # if id == '-1':
            #     passenger.ground_pax_connected_table[i] = [0 for _ in range(DELTA_OBT+1)]
            # else:
            if id != -1:
                list_nb_missed_pax = []
                # idx = flightset.id_flights_d.index(id)
                pax_arrival_times = np.array([round(float(j))//TIME_STEP for j in liste[2:]])
                for t in range(0,DELTA_OBT+1):
                    obt =flightset.flights_d[id].obt + t
                    nb_missed_pax = np.sum([obt-pax_arrival_times<delta_boarding_close])
                    list_nb_missed_pax.append(nb_missed_pax)
                passenger.ground_pax_connected_table[id] = list_nb_missed_pax

def read_air_passengers(passenger,flightset):
    step_hour = TIME_STEP / (60 * 60)
    filename= f'Data/{SCENARIO}/airConnectedPax_{MODE_DISRUPTED.lower()}_{DELAY}s_{START_MODE_DISRUPTION_HOUR}h_{END_MODE_DISRUPTION_HOUR}h_{YEAR}_{MONTH}_{DAY}.txt'
    penalty_transfer = 0 // TIME_STEP # added in min transfer time to challenge algo
    with open(filename, 'r') as file:
        file.readline()
        for line in file:
            id_dep = int(line.split()[0])
            if id_dep != -1:
                nb_pax = line.split()[1]
                if nb_pax != '0':
                    terminal_dep = flightset.flights_d[id_dep].terminal
                    for element in line.split()[2:]:
                        [id_arr,nb_pax]= [int(e) for e in element.split(':')]
                        terminal_arr = flightset.flights_a[id_arr].terminal
                        # print(terminal_arr,terminal_dep)
                        min_connection_time =penalty_transfer+ (60*passenger.terminal_transit_times[terminal_arr][terminal_dep])//TIME_STEP
                        ibt = flightset.flights_a[id_arr].ibt
                        obt = flightset.flights_d[id_dep].obt
                        if obt-ibt < min_connection_time:
                            print(terminal_arr,terminal_dep, obt*TIME_STEP, ibt*TIME_STEP)
                            print(f' WARNING !!! connected flights:({id_dep},{id_arr}) --> mct:{min_connection_time} obt-ibt:{obt-ibt}')
                        passenger.add_air_connected_pax(id_dep,id_arr,min_connection_time,nb_pax)



def read_terminal_transit_time(passenger,filename='PASSENGERS/terminalsTransitTime.txt'):
    df_transfer =pd.read_csv('Data/terminals_transfer_time.csv', index_col=['Terminal'])
    passenger.terminal_transit_times = df_transfer.values
    # print("#################", passenger.terminal_transit_times)


def compute_initial_terminal_occupancy(flightset,apt):
    init_occupancies = np.zeros(len(apt.terminals))
    for flight in flightset.flights_d.values():
        if flight.id not in flightset.id_flights_ad:
            init_occupancies[flight.terminal] +=1
    for i in range(len(init_occupancies)):
        apt.terminals[i].nb_initial_departures = init_occupancies[i]
    print(f"initial terminal occupancies: {init_occupancies}")
    return apt

def set_max_capacities(flightset, airport):
    '''
    :param flightset: initial schedule flightset
    :return: for each terminal , taxi and each runway update a list of max capacities for each WINDOW SHIFT interval
    (len list = 48 if WINDOW-SHIFT = 30min)
    '''
    capa_taxi={} #dico id: time period, value: capacity
    capa_terms = [{} for _ in range(NB_TERMINALS)]
    capa_runways = [{} for _ in range(NB_RUNWAYS)]
    flights_a = flightset.flights_a
    flights_d = flightset.flights_d
    TIME_SCOPE = T_MAX - T_MIN +WINDOW_DURATION
    init_terminals_congestion = np.zeros((NB_TERMINALS, TIME_SCOPE))
    runways_mvmnt = np.zeros((4, TIME_SCOPE))
    # runways_throughputs = np.zeros((4, TIME_SCOPE))
    for k in range(NB_TERMINALS):
        init_terminals_congestion[k][:] = airport.terminals[k].nb_initial_departures
    init_taxi_congestion = np.zeros(TIME_SCOPE)
    for key in flights_a:
        terminal = flights_a[key].terminal
        idx_init_runway_in = flights_a[key].runway #car numero runway commence a 1
        init_landing_time = round(flights_a[key].landing_time)
        init_runway = flights_a[key].runway
        init_ibt = round(init_landing_time + airport.taxi_in_duration[idx_init_runway_in][terminal])
        # print(init_landing_time,idx_init_runway_in,terminal)
        init_terminals_congestion[terminal][init_ibt+1:] +=1
        init_taxi_congestion[init_landing_time+1:init_ibt+1] +=1
        runways_mvmnt[init_runway][init_landing_time] += 1
    for key in flights_d:
        terminal = flights_d[key].terminal
        init_obt =  round(flights_d[key].obt)
        idx_init_runway_out = flights_d[key].runway
        init_takeoff_time = round(init_obt + airport.taxi_out_duration[terminal][idx_init_runway_out])
        init_terminals_congestion[terminal][init_obt+1:] -= 1
        if init_takeoff_time < T_MAX + WINDOW_DURATION:
            runways_mvmnt[idx_init_runway_out][init_takeoff_time] += 1
            if init_takeoff_time < T_MAX+ WINDOW_DURATION:
                init_taxi_congestion[init_obt + 1:init_takeoff_time + 1] += 1

    # for r in range(0, 4):
    #     for i in range(TIME_SCOPE):
    #         throughput_bo = runways_mvmnt[r][i]
    #         runways_throughputs[r][i] = throughput_bo
    for t in range(T_MIN,T_MAX+WINDOW_DURATION,CAPACITY_WINDOW):
        capa_taxi[t//CAPACITY_WINDOW] = max(init_taxi_congestion[t:t + CAPACITY_WINDOW])
        for k in range(NB_TERMINALS):
            capa_terms[k][t//CAPACITY_WINDOW] = max(init_terminals_congestion[k][t:t+CAPACITY_WINDOW])
        for r in range(NB_RUNWAYS):
            capa_runways[r][t//CAPACITY_WINDOW] = max(runways_mvmnt[r][t:t+CAPACITY_WINDOW])
    for k in range(NB_TERMINALS):
        # capa_terms[k][T_MAX] = capa_terms[k][T_MAX-WINDOW_SHIFT]
        airport.terminals[k].capacities = capa_terms[k]
        airport.terminals[k].capacity = max(capa_terms[k].values())
        print(f'max terminal {k}  ({airport.terminals[k].terminal_name}) capacity : {airport.terminals[k].capacity}')
        # print(airport.terminals[k].capacities)

    airport.taxi.capacities = capa_taxi
    airport.taxi.capacity = max(capa_taxi.values())
    # print(airport.taxi.capacity)

    for r in range(NB_RUNWAYS):
        airport.runways[r].capacities = capa_runways[r]
        airport.runways[r].capacity = max(capa_runways[r].values())
        print(f'max {airport.runways[r].name} capacity : {airport.runways[r].capacity}')

    return capa_terms,capa_taxi,capa_runways

def reduce_capacity_runway(airport):
    if RESOURCE_TYPE == 'terminal':
        terminal_name = airport.terminals[RESOURCE_IDX].terminal_name
        capacity = airport.terminals[RESOURCE_IDX].capacity
        print(f'######### initial {terminal_name} capacity: ', capacity)
        capacity = int(capacity*(1-REDUCTION_PERCENT))
        print(f"##########  {terminal_name} capacity after reduction: ", capacity)
        for key in airport.terminals[RESOURCE_IDX].capacities:
            airport.terminals[RESOURCE_IDX].capacities[key] = min(airport.terminals[RESOURCE_IDX].capacities[key], capacity)
        # airport.terminals[RESOURCE_IDX].capacity = capacity
    elif RESOURCE_TYPE == 'runway':
        runway_name = airport.runways[RESOURCE_IDX].name
        capacity = airport.runways[RESOURCE_IDX].capacity
        print(f'initial  {runway_name} capacity: ', capacity)
        capacity = int(capacity*(1-REDUCTION_PERCENT))
        print(f"{runway_name} capacity after reduction: ", capacity)
        for key in airport.runways[RESOURCE_IDX].capacities:
            airport.runways[RESOURCE_IDX].capacities[key] = min(airport.runways[RESOURCE_IDX].capacities[key], capacity)
            # airport.runways[RESOURCE_IDX].capacity = capacity
    else: #taxi
        capacity = airport.taxi.capacity
        print('initial taxi capacity: ', capacity)
        capacity = int(capacity*(1-REDUCTION_PERCENT))
        print("taxi capacity after reduction: ", capacity)
        for key in airport.taxi.capacities:
            airport.taxi.capacities[key] = min(airport.taxi.capacities[key], capacity)
        # airport.taxi.capacity = capacity


def read_instance():
    airport = Airport()
    # read_airport(airport)
    initialized_airport(airport)
    # compute_average_taxi_time(airport)
    flightset = Flightset()
    read_flightset_TrafiCDG(flightset, airport)
    compute_initial_terminal_occupancy(flightset,airport)
    set_max_capacities(flightset, airport)
    # reduce_capacity_runway(airport)
    # reduce_capacity_runway(airport,3,5)

    passenger = Passenger(flightset)
    read_terminal_transit_time(passenger)
    read_ground_passengers(passenger,flightset)
    read_air_passengers(passenger,flightset)
    print("Instance successfully read")
    return airport,flightset,passenger


def crop_instance(airport,flightset, passenger, t_end): #only get on-going and active flights
    crop_flightset = Flightset()
    crop_flightset_og = Flightset()
    crop_flightset_planned = Flightset() #only planned with landing time or obt  < t_end

    # compute_initial_departure_throughputs(flightset, airport)
    for flight in flightset.flights_a.values():
        # if flight.status in [1,2]: #on going or active flight
        if flight.status ==1 :  #active flight
            crop_flightset.add_flight(flight, 'A')
        if flight.status == 2:
            crop_flightset_og.add_flight(flight,'A')
        if flight.status == 0 and flight.landing_time < t_end:
            crop_flightset_planned.add_flight(flight,'A')
    for flight in flightset.flights_d.values():
        # if flight.status in [1, 2]:  # on going or active flight
        if flight.status == 1:  # active flight
            crop_flightset.add_flight(flight, 'D')
        if flight.status == 2:
            crop_flightset_og.add_flight(flight, 'D')
        if flight.status == 0 and flight.obt < t_end :
            crop_flightset_planned.add_flight(flight,'D')
    crop_passenger = Passenger(crop_flightset)
    crop_passenger.terminal_transit_times = passenger.terminal_transit_times
    l2 = crop_flightset.flights_d
    # for i,f in enumerate(l2):
    for key in l2:
        crop_passenger.ground_pax_connected_table[key] = passenger.ground_pax_connected_table[key]
    for connected_pax in passenger.air_connected_pax_table.values():
        if (connected_pax.id_dep_flight in crop_flightset.flights_d) and (connected_pax.id_arr_flight in crop_flightset.flights_a):
            crop_passenger.add_air_connected_pax(connected_pax.id_dep_flight,connected_pax.id_arr_flight,connected_pax.min_connection_time,connected_pax.nb_pax)
    return crop_flightset, crop_passenger, crop_flightset_og, crop_flightset_planned





def compute_occupancies_ogp(airport,flightset_og,flightset_planned,t_start,t_end): #input to know ressources allocation dedicated to on-going flights
    dic_zeros = dict(zip([i for i in range(t_start,t_end)],[0 for _ in range(t_start,t_end)]))
    dic_zeros_runways = dict(zip([i for i in range(t_start,t_end)],[0 for _ in range(t_start,t_end)]))
    occupancy_terminals = [dict(dic_zeros) for _ in range(NB_TERMINALS)] # for each time step provide nb og_arr_flights - nb og_dep_flights
    occupancy_taxi_network = dict(dic_zeros)
    occupancy_runways = [dict(dic_zeros_runways) for _ in range(len(airport.runways))]
    for flight in flightset_og.flights_a.values():
        k = int(flight.terminal)
        landing_time = int(flight.final_landing_time)
        runway = flight.final_runway
        ibt = int(landing_time + airport.taxi_in_duration[runway][k])
        if landing_time >= t_start: #pas de condition sur t_end car on going flight, ne peut pas depasser fin fenetre glissante
            occupancy_runways[runway][landing_time] +=1 #throughput and not occupancy, direct impact on landing time and not landing time +1
            occupancy_taxi_network[landing_time+1] +=1
            occupancy_taxi_network[ibt+1] -= 1
        else:
            if ibt >= t_start:
                occupancy_taxi_network[t_start] += 1
                occupancy_taxi_network[ibt+1] -= 1
            # if landing_time  >= t_start - (RUNWAY_WINDOW_DURATION -1):
            #     occupancy_runways[runway - 1][landing_time] += 1
        if ibt >= t_start:
            occupancy_terminals[k][ibt+1] += 1
        else:
            occupancy_terminals[k][t_start] += 1
    for flight in flightset_og.flights_d.values():
        k = flight.terminal
        obt = int(flight.final_obt)
        runway = flight.final_runway
        take_off = int(obt + airport.taxi_out_duration[k][runway])
        if obt >= t_start:  # on recupere que on going n etant pas parti du block avant t start
            occupancy_terminals[k][obt+1] -= 1
            occupancy_taxi_network[obt+1] +=1
            occupancy_taxi_network[take_off+1] -=1
            occupancy_runways[runway][take_off] +=1
        else:
            occupancy_terminals[k][t_start] -= 1
            if take_off >= t_start:
                occupancy_taxi_network[t_start] += 1
                occupancy_taxi_network[take_off+1] -= 1
                occupancy_runways[runway][take_off] += 1
    for flight in flightset_planned.flights_d.values():
        k = int(flight.terminal)
        obt = int(flight.final_obt)
        runway = flight.final_runway
        take_off = int(obt + airport.taxi_out_duration[k][runway])
        if obt +1 < t_end:
            occupancy_terminals[k][obt + 1] -= 1
            occupancy_taxi_network[obt + 1] += 1
            if take_off < t_end:
                occupancy_runways[runway][take_off] +=1
                if take_off < t_end -1:
                    occupancy_taxi_network[take_off + 1] -= 1
    for flight in flightset_planned.flights_a.values():
        k = int(flight.terminal)
        landing_time = int(flight.landing_time)
        runway = flight.final_runway
        ibt = int(landing_time + airport.taxi_in_duration[runway][k])
        occupancy_runways[runway][landing_time] += 1
        if landing_time +1 < t_end:
            occupancy_taxi_network[landing_time+1] += 1
            if ibt +1 < t_end:
                occupancy_terminals[k][ibt + 1] += 1
                occupancy_taxi_network[ibt + 1] -= 1
    return occupancy_terminals,occupancy_taxi_network,occupancy_runways


# airport,flightset,passenger = read_instance()
# print(len(flightset.flights_a) + len(flightset.flights_d))