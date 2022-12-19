
from constantes import *
import numpy as np


def update_status_one_flight(ts_min,ts_max,te_max,t_start,t_end,flight):
    if te_max < t_start:  # completed
        flight.status = 3
    elif (ts_min < t_start) and (te_max >= t_start):  # on going
        flight.status = 2
    elif ts_min >= t_start and ts_max < t_end:  # active
        flight.status = 1
    else:  # planned
        flight.status = 0
    # if flight.type_ad == 0:
    #     if flight.final_landing_time == 239 or flight.id == 681:
    #         print(flight)


def set_status_flights(flightset,airport, t_start,t_end):
    # for id in flightset.id_flights_ad:
    #     flight_arr = flightset.flights_a[id]
    #     flight_dep = flightset.flights_d[id]
    #     ts_min = flight_arr.landing_time - DELTA_L_MIN
    #     ts_max = flight_arr.landing_time + DELTA_L_MAX
    #     te_max = flight_dep.obt + DELTA_OBT
    #     update_status_one_flight(ts_min,ts_max,te_max,t_start,t_end,flight_arr)
    #     update_status_one_flight(ts_min,ts_max,te_max,t_start,t_end,flight_dep)
    # for id in flightset.id_flights_only_a:
    for id in flightset.flights_a:
        flight = flightset.flights_a[id]
        ts_min = flight.landing_time - DELTA_L_MIN
        ts_max = flight.landing_time + DELTA_L_MAX
        te_max = int(ts_max + max(airport.taxi_in_duration[:,flight.terminal]))
        update_status_one_flight(ts_min,ts_max,te_max,t_start,t_end,flight)
    # for id in flightset.id_flights_only_d:
    for id in flightset.flights_d:
        flight = flightset.flights_d[id]
        ts_min = flight.obt
        ts_max = flight.obt + DELTA_OBT
        te_max = int(ts_max + max(airport.taxi_out_duration[flight.terminal,:]))
        update_status_one_flight(ts_min,ts_max,te_max,t_start,t_end,flight)


def compute_terminals_occupancy(flightset, apt):
    count = np.zeros(len(apt.terminals))
    for flight in flightset.flights_a.values():
        if flight.status == 3:
            count[flight.terminal] += 1
    for flight in flightset.flights_d.values():
        if flight.status == 3:
            count[flight.terminal] -=1
    for i in range(len(count)):
        apt.terminals[i].initial_occupancy = apt.terminals[i].nb_initial_departures + count[i]
    return apt




# def compute_initial_departure_throughputs(flightset,apt):
#     for i in range(len(apt.runways)):
#         apt.runways[i].init_throughput =0
#
#     for flight in flightset.flights_d.values():
#         if flight.status == 2:
#             id_runway = flight.runway -1
#             # if flight.type_ad == 0:
#             #     t_max = T_MIN
#             #     t_min = t_max - RUNWAY_WINDOW_DURATION
#             #     t = flight.landing_time
#             # else:
#             t_min = T_MIN - apt.taxi_out_duration[flight.terminal][id_runway] #car departure runways indicés 3 et 4
#             # print(apt.taxi_out_duration[flight.terminal][id_runway])
#             t_max = t_min + RUNWAY_WINDOW_DURATION
#             t = flight.obt
#             # print(t_min,'  ',t_max,'   ',t)
#             if (t< t_max) and (t >= t_min):
#                 apt.runways[id_runway].init_throughput +=1
