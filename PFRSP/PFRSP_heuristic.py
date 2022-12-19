from constantes import *
from pre_processing import crop_instance,compute_occupancies_ogp
import numpy as np

def compute_init_terminals_occupancies(t_start,t_end,airport,flightset,occ_ogp_terms):
    occupancies_term =dict(zip([k for k in range(NB_TERMINALS)],[{} for _ in range(NB_TERMINALS)]))
    for k in range(NB_TERMINALS):
        occupancies_term[k][t_start] = int(airport.terminals[k].initial_occupancy + occ_ogp_terms[k][t_start])
        for t in range(t_start, t_end-1):
            flights_in = 0
            flights_out = 0
            for flight in flightset.flights_d.values():
                if (flight.terminal == k) and (flight.final_obt == t):
                    flights_out += 1
            for flight in flightset.flights_a.values():
                if (flight.terminal == k) and (flight.final_ibt == t):
                    flights_in += 1
            occupancies_term[k][t+1] = occupancies_term[k][t] + flights_in - flights_out + occ_ogp_terms[k][t+1]
    return occupancies_term

def compute_init_taxi_occupancies(t_start,t_end,flightset,occ_ogp_taxi):
    occupancies_taxi = {}
    occupancies_taxi[t_start] = occ_ogp_taxi[t_start]
    for t in range(t_start, t_end-1):
        flights_in = 0
        flights_out = 0
        for flight in flightset.flights_d.values():
            if flight.final_obt == t:
                flights_in += 1
            elif flight.final_takeoff == t:
                flights_out +=1
        for flight in flightset.flights_a.values():
            if flight.final_landing_time == t:
                flights_in += 1
            elif flight.final_ibt == t:
                flights_out +=1
        occupancies_taxi[t+1] = occupancies_taxi[t] + flights_in - flights_out + occ_ogp_taxi[t+1]
    return occupancies_taxi



def test_departure_runway_constraint(airport, flightset, id_flight, occ_ogp_runways):
    res = True
    t = flightset.flights_d[id_flight].final_takeoff
    r = flightset.flights_d[id_flight].final_runway
    # print(occ_ogp_runways[r])
    throughput = occ_ogp_runways[r][t]
    for flight in flightset.flights_d.values():
        if (flight.final_takeoff == t) and (flight.final_runway == r):
            throughput += 1
    # print(" +++ ", throughput)
    if throughput > airport.runways[r].capacities[int(t // CAPACITY_WINDOW)]:
        res = False
    return res

def test_arrival_runway_constraint(airport,flightset,id_flight,occ_ogp_runways):
    res = True
    t = flightset.flights_a[id_flight].final_landing_time
    r = flightset.flights_a[id_flight].final_runway
    # print(occ_ogp_runways[r])
    throughput = occ_ogp_runways[r][t]
    for flight in flightset.flights_a.values():
        if (flight.final_landing_time == t) and (flight.final_runway == r):
            throughput += 1
    # print(" +++ ", throughput)
    if throughput > airport.runways[r].capacities[int(t // CAPACITY_WINDOW)]:
        res = False
    return res




def test_terminal_constraint(airport, flightset, occupancies_term, id_flight):#,id_flight_arr=-1):
    res = True
    k = flightset.flights_d[id_flight].terminal
    t_min = flightset.flights_d[id_flight].obt
    t_max = flightset.flights_d[id_flight].final_obt
    occupancy_k = dict(occupancies_term[k])
    # if id_flight_arr != -1:
    #     print("test1:",t_min==flightset.flights_a[id_flight_arr].ibt)
    #     print("test2:", t_max == flightset.flights_a[id_flight_arr].final_ibt)
    t_min_violation,t_max_violation = -1,-1
    for t in range(t_min+1,t_max+1):
        # print(occupancy_k)
        occupancy_k[t] +=1
        # print(occupancy_k==occupancies[k])
        if occupancy_k[t]  >  airport.terminals[k].capacities[int(t // CAPACITY_WINDOW)]:
            if (t_min_violation == -1):
                t_min_violation = t
            t_max_violation = t
            res = False
            # break
    print(t_min_violation,t_max_violation,'##########')
    return res,occupancy_k,t_min_violation,t_max_violation


def test_taxi_constraint(airport,flightset,init_occupancies_taxi,id_flight_dep,id_flight_arr=-1):
    res = True
    t_min_obt = flightset.flights_d[id_flight_dep].obt
    t_max_obt = flightset.flights_d[id_flight_dep].final_obt
    t_min_takeoff = flightset.flights_d[id_flight_dep].takeoff
    t_max_takeoff = flightset.flights_d[id_flight_dep].final_takeoff
    t_min, t_max = t_min_obt, t_max_takeoff
    occupancies_taxi = dict(init_occupancies_taxi)
    for t in range(t_min_obt+1,t_max_obt+1):
        occupancies_taxi[t] -=1
    for t in range(t_min_takeoff+1,t_max_takeoff+1):
        occupancies_taxi[t] += 1
    if id_flight_arr != -1:
        t_min_landing = flightset.flights_a[id_flight_arr].landing_time
        t_max_landing = flightset.flights_a[id_flight_arr].final_landing_time
        t_min_ibt = flightset.flights_a[id_flight_arr].ibt
        t_max_ibt = flightset.flights_a[id_flight_arr].final_ibt
        t_min = t_min_landing
        for t in range(t_min_landing + 1, t_max_landing + 1):
            occupancies_taxi[t] -= 1
        for t in range(t_min_ibt + 1, t_max_ibt + 1):
            occupancies_taxi[t] += 1
    for t in range(t_min,t_max+1):
        if occupancies_taxi[t]  >  airport.taxi.capacities[int(t // CAPACITY_WINDOW)]:
            res = False
            break
    return res,occupancies_taxi


def initialized_tabu_arr_flights(flightset,passengers):
    res = {}
    for delay in range(1,DELTA_L_MAX+1):
        res[delay]=[]
        for c in passengers.air_connected_pax_table.values():
            id_arr = c.id_arr_flight
            id_dep = c.id_dep_flight
            transfer_time  = flightset.flights_d[id_dep].obt - flightset.flights_a[id_arr].ibt
            if (transfer_time - c.min_connection_time < delay) and (id_arr not in res[delay]):
                res[delay].append(id_arr)
        for id in flightset.id_flights_ad:
            arr_flight = flightset.flights_a[id]
            dep_flight = flightset.flights_d[id]
            if (dep_flight.obt - arr_flight.ibt - MIN_TURNAROUND_TIME < delay) and (id not in res[delay]):
                res[delay].append(id)
        print("#############################  ", delay, len(res[delay]), len(flightset.flights_a))
    return res


def run_greedy(airport, flightset0, passengers0, t_start, t_end, list_tabu_dep_flights, dico_tabu_arr_flights):
    flightset, passengers, flightset_og, flightset_planned= crop_instance(airport,flightset0,passengers0,t_end)
    occ_ogp_terms, occ_ogp_tn, occ_ogp_runways = compute_occupancies_ogp(airport,flightset_og,flightset_planned,t_start,t_end)
    dico_departure_delays = {} #key: (id_f,slot_delay) value: score. (dico ordered from highest score to lowest one
    init_occupancies_term = compute_init_terminals_occupancies(t_start,t_end,airport,flightset,occ_ogp_terms)
    init_occupancies_taxi = compute_init_taxi_occupancies(t_start,t_end,flightset,occ_ogp_tn)
    for key in flightset.flights_d:
        if flightset.flights_d[key].takeoff + DELTA_OBT < t_end: #else will be considered during next time window, to avoid constraint violation after t_end
            list_nb_missed_pax = -1*np.array(passengers.ground_pax_connected_table[key])
            list_nb_missed_pax -= list_nb_missed_pax[0]
            for i in range(1,len(list_nb_missed_pax)):
                if list_nb_missed_pax[i] !=0:
                    if (flightset.flights_d[key].priority== False) or (i <= DELTA_SLOT): # slot violation for priority flight not authorized
                        dico_departure_delays[(key, i)] = round(list_nb_missed_pax[i] /(1+0.01*i),2) #lower term allow to favor selection of lower slot deviation for same nb of missed passengers
    dico_departure_delays = {k: v for k, v in sorted(dico_departure_delays.items(), key=lambda item: item[1],reverse=True)}
    for (key,delay) in dico_departure_delays.keys():
        arr_key = -1
        delay_arr = 0
        if key not in list_tabu_dep_flights:
            flightset.flights_d[key].final_obt += delay
            flightset.flights_d[key].final_takeoff += delay
            res_runway = True
            if flightset.flights_d[key].final_takeoff < t_end:
                res_runway = test_departure_runway_constraint(airport, flightset, key, occ_ogp_runways)
            res_terminal,occupancies_k,t_min_violation,t_max_violation = test_terminal_constraint(airport,flightset,init_occupancies_term,key)
            violation_constraint = False
            if res_runway:
                if not res_terminal:
                    i=0
                    arr_flights_keys = list(flightset.flights_a.keys())
                    while arr_key == -1 and i <len(flightset.flights_a):
                        key2 = arr_flights_keys[i]
                        flight = flightset.flights_a[key2]
                            # if (flight.ibt == flightset.flights_d[key].obt) and (flight.terminal == flightset.flights_d[key].terminal):
                            #     delay_arr = delay
                            #     flightset.flights_a[key2].final_ibt += delay_arr
                            #     flightset.flights_a[key2].final_landing_time += delay_arr
                            #     res_arrival_runway = test_arrival_runway_constraint(airport,flightset,key2,occ_ogp_runways)
                            #     if res_arrival_runway:
                            #         arr_key = key2
                            #         res_terminal = True
                            #         print('breeaaaaaaaak')
                            #     else:
                            #         flight.final_ibt -= delay_arr
                            #         flight.final_landing_time -=delay_arr
                        if (flight.terminal == flightset.flights_d[key].terminal) and (flight.ibt < t_min_violation) and (flight.ibt+ DELTA_L_MAX >= t_max_violation):
                            delay_arr = t_max_violation - flight.ibt
                            if delay_arr < DELTA_L_MAX:
                                if key2 not in dico_tabu_arr_flights[delay_arr]:
                                # while arr_key == -1:
                                    while(delay_arr <= DELTA_L_MAX) and (arr_key == -1):
                                        flightset.flights_a[key2].final_ibt += delay_arr
                                        flightset.flights_a[key2].final_landing_time += delay_arr
                                        res_arrival_runway = test_arrival_runway_constraint(airport,flightset,key2,occ_ogp_runways)
                                        if res_arrival_runway:
                                            arr_key = key2
                                            res_terminal = True
                                            print('breeaaaaaaaak')
                                        else:
                                            flight.final_ibt -= delay_arr
                                            flight.final_landing_time -=delay_arr
                                            delay_arr += 1

                        i += 1
                # res_terminal, occupancies_k = test_terminal_constraint(airport, flightset,init_occupancies_term,key)
                res_taxi, occupancies_taxi = test_taxi_constraint(airport, flightset, init_occupancies_taxi,key,arr_key)
                # print(res_taxi,res_terminal)
                if res_taxi and res_terminal:
                    print(f"++++ departure flight {key} delayed ")
                    list_tabu_dep_flights.append(key)
                    if arr_key != -1 :
                        print(f"++++ arrival flight {arr_key} delayed ")
                        for delay in range(1,DELTA_L_MAX+1):
                            dico_tabu_arr_flights[delay].append(arr_key)
                    init_occupancies_term[flightset.flights_d[key].terminal] = occupancies_k
                    init_occupancies_taxi = occupancies_taxi
                else:
                    violation_constraint = True
            else:
                violation_constraint = True
            if violation_constraint:
                flightset.flights_d[key].final_obt -= delay
                flightset.flights_d[key].final_takeoff -= delay
                if arr_key != -1:
                    flightset.flights_a[arr_key].final_ibt -= delay_arr
                    flightset.flights_a[arr_key].final_landing_time -= delay_arr


    return flightset.flights_a, flightset.flights_d, list_tabu_dep_flights, dico_tabu_arr_flights

