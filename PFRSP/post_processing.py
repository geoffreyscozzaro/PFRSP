import matplotlib.pyplot as plt
import numpy as np
from airport import *
from flight import *
from passenger import *
import pandas as pd
from pre_processing import crop_instance
from timeWindowManagement import set_status_flights

def update_flightset(flightset, flights_a, flights_d):  # ajoute information flights time window apres optimisation  au flightset entier
    for key in flights_a:
        flightset.flights_a[key] = flights_a[key]
    for key in flights_d:
        flightset.flights_d[key] = flights_d[key]
    return flightset


def write_solution(flightset, label):
    # filename = FOLDER_RESULTS + f'flightset_results_{SCENARIO}_capacity_reduction_{RESOURCE_TYPE}_{RESOURCE_IDX}_{100*REDUCTION_PERCENT}pct.txt'
    filename = FOLDER_RESULTS + f'flightset_results_{SCENARIO}.txt'
    with open(filename, 'w') as file:
        file.write(f"NbArrivalFlights: {len(flightset.flights_a)} \n")
        for key in flightset.flights_a:
            file.write(flightset.flights_a[key].to_string() + '\n')
        file.write(f"NbDepartureFlights: {len(flightset.flights_d)} \n")
        for key in flightset.flights_d:
            file.write(flightset.flights_d[key].to_string() + '\n')





def read_solution(filename):
    flights_a, flights_d = {}, {}
    with open(filename, 'r') as file:
        nbArrivalFlights = int(file.readline().split()[1])
        for i in range(nbArrivalFlights):
            features = file.readline().split()
            [id, type_ad, terminal, init_runway, init_landing_time, init_ibt, status, final_runway, final_landing_time, final_ibt] = \
                [int(features[1]), int(features[3]), int(features[5]), int(features[7]), float(features[9]),
                float(features[11]), float(features[13]), int(features[15]), float(features[17]), float(features[17])]
            flights_a[id] = Flight_A(id, terminal, init_runway, init_landing_time, init_ibt, status)
            flights_a[id].final_runway = final_runway
            flights_a[id].final_landing_time = final_landing_time
            flights_a[id].final_ibt = final_ibt
        nbDepartureFlights = int(file.readline().split()[1])
        for i in range(nbDepartureFlights):
            features = file.readline().split()
            [id, type_ad, terminal, init_runway, init_obt, init_takeoff, status, priority, final_runway, final_obt, final_takeoff] = \
            [int(features[1]), int(features[3]), int(features[5]), int(features[7]), float(features[9]),float(features[11]),
             float(features[13]), features[15], int(features[17]), float(features[19]),float(features[21])]
            priority = priority == 'True'
            flights_d[id] = Flight_D(id, terminal, init_runway, init_obt, init_takeoff, priority, status)
            flights_d[id].final_runway = final_runway
            flights_d[id].final_obt = final_obt
            flights_d[id].final_takeoff = final_takeoff
            print(flights_d[id])
    return flights_a, flights_d


def compute_throughput_runway(airport, flightset):  # time window to compute throughput
    TIME_SCOPE = (25 * 60 * 60)//TIME_STEP
    flights_a = flightset.flights_a
    flights_d = flightset.flights_d
    runways_bo, runways_ao = np.zeros((4, TIME_SCOPE)), np.zeros((4, TIME_SCOPE))
    # throughputs_bo, throughputs_ao = np.zeros((4, TIME_SCOPE - RUNWAY_WINDOW_DURATION)), np.zeros(
    #     (4, TIME_SCOPE - RUNWAY_WINDOW_DURATION))
    for key in flights_a:
        if flights_a[key].status not in [-1]:  # not planned, used if simulation stop before T_MAX= 24h
            init_landing_time = int(flights_a[key].landing_time)
            final_landing_time = int(flights_a[key].final_landing_time)
            init_runway = flights_a[key].runway
            final_runway = flights_a[key].final_runway
            runways_bo[init_runway][init_landing_time] += 1
            runways_ao[final_runway][final_landing_time] += 1

    for key in flights_d:
        if flights_d[key].status not in [-1]:  # not planned, used if simulation stop before T_MAX= 24h
            terminal = int(flights_d[key].terminal)
            init_obt = int(flights_d[key].obt)
            final_obt = int(flights_d[key].final_obt)
            init_runway = flights_d[key].runway
            final_runway = flights_d[key].final_runway
            init_takeoff = int(init_obt + airport.taxi_out_duration[terminal][init_runway])
            final_takeoff = int(final_obt + airport.taxi_out_duration[terminal][final_runway])
            runways_bo[init_runway][init_takeoff] += 1
            runways_ao[final_runway][final_takeoff] += 1

    # for r in range(0, 4):
    #     for i in range(len(runways_bo[r]) - RUNWAY_WINDOW_DURATION):
    #         throughput_bo = np.sum(runways_bo[r][i:i + RUNWAY_WINDOW_DURATION])
    #         throughputs_bo[r][i] = throughput_bo
    #         throughput_ao = np.sum(runways_ao[r][i:i + RUNWAY_WINDOW_DURATION])
    #         throughputs_ao[r][i] = throughput_ao
    # for i in range(len(throughputs_bo[1])):
    #     print(throughputs_bo[1][i])
    return runways_bo,runways_ao


def display_throughput_constraints(airport, runways_bo, runways_ao, is_step_constraint, savefig=False):
    fig, axs = plt.subplots(4, figsize=(10, 6))
    plt.subplots_adjust(left=0.125,
                        bottom=0.1,
                        right=0.9,
                        top=0.9,
                        wspace=0.2,
                        hspace=0.45)
    # idx_runways = [0,1,2,3]
    for i in range(NB_RUNWAYS):
        if airport.runways[i].type == 0:
            runway_type = 'landing'
        else:
            runway_type = 'takeoff'
        axs[i].step(np.arange(len(runways_bo[i])), runways_bo[i],
                    label=f'Initial ({airport.runways[i].name})',where='post')
        axs[i].step(np.arange(len(runways_ao[i])), runways_ao[i],
                    label=f'Optimized ({airport.runways[i].name})',where='post')
        # axs[idx].set_title(labels_runways[idx],fontsize=12,y=-0.55)
        axs[i].set_ylabel('Number of \n movements', fontsize=12)
        if is_step_constraint == True:
            x = np.arange(T_MIN,T_MAX+WINDOW_DURATION,CAPACITY_WINDOW)
            Y = list(airport.runways[i].capacities.values())
            Y_step = Y #+ [Y[-1]]#to handle deviation step function
            axs[i].step(x, Y_step, c='r', linestyle='--',where='post')
        else:
            axs[i].axhline(airport.runways[i].capacity, c='r', linestyle='--')
        axs[i].legend(loc='lower left')
        # axs[i].axhline(airport.runways[idx].capacity, c='r', linestyle='--')  # ,label='{0} capacity'.format(name))
        axs[i].set_xticks(np.arange(0, T_MAX + 60*60//TIME_STEP, 60*60//TIME_STEP))

        axs[i].set_xticklabels(["{0}h".format(e) for e in range(0, 25)], rotation=45)
        axs[i].set_xlim(START_MODE_DISRUPTION_TIME,T_MAX)
        # axs[i].set_yticks([i for i in range(0, 13, 2)])
    if savefig:
        plt.savefig(FOLDER_RESULTS + f'throughput_constraints_{SCENARIO}.png', bbox_inches='tight')
    else:
        plt.show()


def compute_congestion(airport, flightset):  # time window to compute throughput
    flights_a = flightset.flights_a
    flights_d = flightset.flights_d
    TIME_SCOPE = (T_MAX - T_MIN +WINDOW_DURATION)
    init_terminals_congestion = np.zeros((NB_TERMINALS, TIME_SCOPE))
    final_terminals_congestion = np.zeros((NB_TERMINALS, TIME_SCOPE))
    for k in range(NB_TERMINALS):
        init_terminals_congestion[k][:] = airport.terminals[k].nb_initial_departures
        final_terminals_congestion[k][:] = airport.terminals[k].nb_initial_departures
    init_taxi_congestion = np.zeros(TIME_SCOPE)
    final_taxi_congestion = np.zeros(TIME_SCOPE)
    for key in flights_a:
        # if flights_a[key].status != 0  : # 0 not planned, used if simulation stop before T_MAX= 24h
        terminal = flights_a[key].terminal
        # print(terminal)
        idx_init_runway_in = flights_a[key].runway # car numero runway commence a 1
        idx_final_runway_in = flights_a[key].final_runway   # car numero runway commence a 1
        init_landing_time = round(flights_a[key].landing_time)
        final_landing_time = round(flights_a[key].final_landing_time)
        init_ibt = round(init_landing_time + airport.taxi_in_duration[idx_init_runway_in][terminal])
        final_ibt = round(final_landing_time + airport.taxi_in_duration[idx_final_runway_in][terminal])
        init_terminals_congestion[terminal][init_ibt+1:] += 1
        init_taxi_congestion[init_landing_time+1:init_ibt+1] += 1
        final_terminals_congestion[terminal][final_ibt+1:] += 1
        final_taxi_congestion[final_landing_time+1:final_ibt+1] += 1
    for key in flights_d:
        # if flights_d[key].status != 0 : #not planned, used if simulation stop before T_MAX= 24h
        terminal = flights_d[key].terminal
        init_obt = round(flights_d[key].obt)
        final_obt = round(flights_d[key].final_obt)
        idx_init_runway_out = flights_d[key].runway
        idx_final_runway_out = flights_d[key].final_runway
        init_takeoff_time = round(init_obt + airport.taxi_out_duration[terminal][idx_init_runway_out])
        final_takeoff_time = round(final_obt + airport.taxi_out_duration[terminal][idx_final_runway_out])
        init_terminals_congestion[terminal][init_obt+1:] -= 1
        init_taxi_congestion[init_obt+1:init_takeoff_time+1] += 1
        final_terminals_congestion[terminal][final_obt+1:] -= 1
        final_taxi_congestion[final_obt+1:final_takeoff_time+1] += 1
    # for i in range(NB_TERMINALS):
    #     print(f'max congestion Terminal {i}: {max(init_terminals_congestion[i])}')
    # return init_terminals_congestion[0:T_MAX], final_terminals_congestion[0:T_MAX], init_taxi_congestion[
    #                                                                                 0:T_MAX], final_taxi_congestion[0:T_MAX]
    return init_terminals_congestion, final_terminals_congestion, init_taxi_congestion, final_taxi_congestion


def display_capacity_constraint(airport, init_terminals_congestion, final_terminals_congestion, init_taxi_congestion,
                                final_taxi_congestion, is_taxi_step_constraint, is_terminal_step_constraint,
                               savefig=False):
    subset_terminals = ['T1','T2E','T2F','T3']
    # subset_terminals = []

    nb_terminals = len(subset_terminals)
    fig, ax = plt.subplots(nb_terminals+1, figsize=(12, 6))
    # fig, ax = plt.subplots(nb_terminals+1, figsize=(8, 4))

    # ax = [ax]
    plt.subplots_adjust(left=0.125,
                        bottom=0.1,
                        right=0.9,
                        top=0.9,
                        wspace=0.2,
                        hspace=0.6)
    x_capacity = np.arange(T_MIN, T_MAX+WINDOW_DURATION, CAPACITY_WINDOW)
    X = np.arange(T_MIN, T_MAX+WINDOW_DURATION)
    for i,terminal in enumerate(subset_terminals):
        k=0
        for j in range(NB_TERMINALS):
            if airport.terminals[j].terminal_name == terminal:
                k =j
                break
        ax[i].step(X,init_terminals_congestion[k], label=f"Initial occupancy {terminal}",where='post')
        ax[i].step(X,final_terminals_congestion[k], label=f"Optimized occupancy {terminal}",where='post')
        if is_terminal_step_constraint:
            Y_k = list(airport.terminals[k].capacities.values())
            Y_k_step = Y_k # + [Y_k[-1]]
            ax[i].step(x_capacity, Y_k_step, c='r', linestyle='--',where='post')
        else:
            ax[i].axhline(airport.terminals[k].capacity, c='r', linestyle='--')
        ax[i].set_xticks(np.arange(0, T_MAX + 60*60//TIME_STEP, 60*60//TIME_STEP))
        ax[i].set_xticklabels(["{0}h".format(e) for e in range(0, 25)], rotation=45)
        # ax[k].set_xticks(np.arange(0, 25 * 60, 60))
        # ax[k].set_xticklabels(["{0}h".format(e) for e in range(0, 25)], rotation=45)
        ax[i].legend(loc=1)
        ax[i].set_xlim(START_MODE_DISRUPTION_TIME, T_MAX)
        # ax[i].set_ylabel('Number of aircraft')


    ax[nb_terminals].step(X,init_taxi_congestion, label=f'initial taxi occupancy', where='post',color='r')
    ax[nb_terminals].step(X,final_taxi_congestion, label=f'optimized taxi occupancy',where='post',color='g')
    # ax.step(X, init_taxi_congestion, label=f'Initial taxi occupancy', where='post', color='C0')
    # ax.step(X, final_taxi_congestion, label=f'Optimized taxi occupancy', where='post', color='C1')
    if is_taxi_step_constraint:
        Y_taxi = list(airport.taxi.capacities.values())
        Y_taxi_step = Y_taxi # + [Y_taxi[-1]]
        ax[nb_terminals].step(x_capacity, Y_taxi_step, c='r', linestyle='--',where='post')
        # ax.step(x_capacity, Y_taxi_step, c='r', linestyle='--',where='post',label='Reduced capacity')
    else:
        ax[nb_terminals].axhline(airport.taxi.capacity, c='r', linestyle='--')  # ,label='{0} capacity'.format(name))
    ax[nb_terminals].set_xticks(np.arange(0, T_MAX + 60*60//TIME_STEP, 60*60//TIME_STEP))
    ax[nb_terminals].set_xticklabels(["{0}h".format(e) for e in range(0, 25)], rotation=45)
    ax[nb_terminals].legend(loc=1)
    ax[nb_terminals].set_xlim(START_MODE_DISRUPTION_TIME, T_MAX)
    # ax.set_xticks(np.arange(0, T_MAX + 60*60//TIME_STEP, 60*60//TIME_STEP))
    # ax.set_xticklabels(["{0}h".format(e) for e in range(0, 25)], rotation=45)
    # ax.set_ylabel("Number of aircraft")
    # ax.legend(loc=1)
    # ax.legend(loc='lower left')
    # ax.set_xlim(START_MODE_DISRUPTION_TIME, T_MAX)

    if savefig:
        plt.savefig( FOLDER_RESULTS + f'capacities_constraints_{SCENARIO}.png', bbox_inches='tight')
    else:
        plt.show()


def compute_missed_passengers(flightset, passenger):
    flights_d = flightset.flights_d
    step = 60
    # init_missed_pax = np.zeros(25)
    # final_missed_pax = np.zeros(25)
    # init_missed_pax = np.zeros(T_MAX-T_MIN)
    # final_missed_pax = np.zeros(T_MAX-T_MIN)
    init_missed_pax = np.zeros((END_AIRPORT_DISRUPTION_TIME-START_AIRPORT_DISRUPTION_TIME))
    final_missed_pax = np.zeros((END_AIRPORT_DISRUPTION_TIME-START_AIRPORT_DISRUPTION_TIME))
    for key in flights_d:
        init_takeoff = int(flights_d[key].takeoff)
        if (init_takeoff >= START_AIRPORT_DISRUPTION_TIME) and (init_takeoff < END_AIRPORT_DISRUPTION_TIME):
            init_obt = int(flights_d[key].obt)
            final_obt = int(flights_d[key].final_obt)
            init_missed_pax_i = passenger.ground_pax_connected_table[key][0]
            # print(final_obt,init_obt,'======')
            final_missed_pax_i = passenger.ground_pax_connected_table[key][final_obt - init_obt]
        # init_missed_pax[(init_takeoff * TIME_STEP) // (60*60)] += init_missed_pax_i
        # final_missed_pax[(init_takeoff * TIME_STEP) // (60 *60) ] += final_missed_pax_i
            init_missed_pax[init_takeoff-START_AIRPORT_DISRUPTION_TIME] += init_missed_pax_i
            final_missed_pax[init_takeoff-START_AIRPORT_DISRUPTION_TIME] += final_missed_pax_i
    return init_missed_pax, final_missed_pax


def display_cumul_passengers(init_missed_pax, final_missed_pax, ax):
    x = np.arange(T_MIN,T_MAX)
    x = x * (TIME_STEP/(60*60))
    y_init_cumul = np.cumsum(init_missed_pax)
    y_final_cumul = np.cumsum(final_missed_pax)
    ax.plot(x,y_init_cumul, label='before optim', alpha=0.5)
    ax.plot(x,y_final_cumul, label='after optim', alpha=0.5)
    # ax.bar(x, init_missed_pax, label='before optim', alpha=0.5)
    # ax.bar(x, final_missed_pax, label='after optim', alpha=0.5)
    # ax.set_xticks(np.arange(T_MIN,T_MAX, 60*60//TIME_STEP))
    ax.set_xticks(np.arange(24))
    ax.set_ylabel('Cumulative number of stranded passengers', fontsize=12)
    ax.set_xticklabels(["{0}h".format(e) for e in range(0, 24)], rotation=45)
    ax.legend(loc=2)



def display_missed_passengers(init_missed_pax, final_missed_pax, ax):
    # x = np.arange(0, 24)
    t_start,t_end  = START_AIRPORT_DISRUPTION_TIME, END_AIRPORT_DISRUPTION_TIME
    step_hour = 60*60//TIME_STEP
    x = np.arange(t_start,t_end,step_hour)
    y_init = [np.sum(init_missed_pax[i:i+step_hour]) for i in range(0,t_end-t_start,step_hour)]
    # print(init_missed_pax)
    # print(len(y_init))
    y_final = [np.sum(final_missed_pax[i:i+step_hour]) for i in range(0,t_end-t_start,step_hour)]
    ax.bar(x, y_init, width=5,label='before optim', alpha=0.5)
    ax.bar(x, y_final, width=5,label='after optim', alpha=0.5)
    ax.set_xticks(np.arange(t_start,T_MAX,step_hour))
    ax.set_ylabel('Number of stranded \n outbound passengers', fontsize=12)
    # ax.set_xticklabels(["{0}h".format(e) for e in range(0, 24)], rotation=45)
    ax.set_xticklabels(["{0}h".format(e) for e in range(t_start*TIME_STEP//(60*60), T_MAX*TIME_STEP//(60*60))], rotation=45)
    ax.legend(loc=2)
    ax.set_xlim(t_start-step_hour , T_MAX)



# def compute_average_delay(flightset):
#     slots_landing = dict(zip(np.arange(0, 25), [[] for _ in range(25)]))
#     slots_pushback = dict(zip(np.arange(0, 25), [[] for _ in range(25)]))
#     total_delay_landing = 0
#     total_delay_takeoff = 0
#     nb_slots_violated = 0
#     for flight in flightset.flights_a.values():
#         if flight.landing_time >0:
#             slots_landing[(flight.landing_time*TIME_STEP)//(60*60)].append(np.abs(flight.final_landing_time - flight.landing_time) * TIME_STEP//60)  # in minutes
#     for flight in flightset.flights_d.values():
#         delay = np.abs(flight.final_takeoff - flight.takeoff)
#         if delay > DELTA_SLOT:
#             nb_slots_violated += 1
#         slots_pushback[(flight.takeoff*TIME_STEP)//(60*60)].append(delay * TIME_STEP//60) # in minutes
#     y_landing = np.zeros(25)
#     y_takeoff = np.zeros(25)
#     for key in slots_landing:
#         if len(slots_landing[key]) > 0:
#             y_landing[key] = np.mean(slots_landing[key])
#             total_delay_landing += np.sum(np.abs(slots_landing[key]))
#         else:
#             y_landing[key] = 0
#     for key in slots_pushback:
#         if len(slots_pushback[key]) > 0:
#             y_takeoff[key] = np.mean(slots_pushback[key])
#             total_delay_takeoff += np.sum(slots_pushback[key])
#         else:
#             y_takeoff[key] = 0
#     return y_landing, y_takeoff, total_delay_landing, total_delay_takeoff, nb_slots_violated

def compute_delay_disruption(flightset):
    delays_landing = {}
    delays_takeoff = {}
    total_delay_landing = 0
    total_delay_takeoff = 0
    nb_slots_violated = 0
    for flight in flightset.flights_a.values():
        if (flight.landing_time >= START_AIRPORT_DISRUPTION_TIME) and (flight.landing_time < END_AIRPORT_DISRUPTION_TIME) :
            delay = np.abs(flight.final_landing_time - flight.landing_time) * TIME_STEP//60
            delays_landing[flight.id] = delay# in minutes
            total_delay_landing += delay
    for flight in flightset.flights_d.values():
        if (flight.takeoff >= START_AIRPORT_DISRUPTION_TIME) and (flight.takeoff < END_AIRPORT_DISRUPTION_TIME) :
            delay = np.abs(flight.final_takeoff - flight.takeoff)
            if delay > DELTA_SLOT:
                nb_slots_violated += 1
            delay = delay * TIME_STEP//60
            delays_takeoff[flight.id] = delay # in minutes
            total_delay_takeoff += delay
    return delays_landing, delays_takeoff, total_delay_landing, total_delay_takeoff, nb_slots_violated



def display_histogram_delay(flightset,delay_landing, delay_takeoff,  ax):
    hours = np.arange(0, 24)
    y_landing = np.zeros((T_MAX-T_MIN)*TIME_STEP//(60*60))
    nb_landings =  np.zeros((T_MAX-T_MIN)*TIME_STEP//(60*60))
    y_takeoff =  np.zeros((T_MAX-T_MIN)*TIME_STEP//(60*60))
    nb_takeoffs =  np.zeros((T_MAX-T_MIN)*TIME_STEP//(60*60))
    for key in delay_landing:
        h = int(flightset.flights_a[key].landing_time*TIME_STEP//(60*60))
        y_landing[h] += delay_landing[key]
        nb_landings[h] += 1
    for key in delay_takeoff:
        h = int(flightset.flights_d[key].takeoff*TIME_STEP//(60*60))
        y_takeoff[h] += delay_takeoff[key]
        nb_takeoffs[h] += 1
    for i in range(len(y_landing)):
        if nb_landings[i] != 0:
            y_landing[i] /= nb_landings[i]
    for i in range(len(y_takeoff)):
        if  nb_takeoffs[i] != 0:
            y_takeoff[i] /= nb_takeoffs[i]
    # X_landing_cumul = np.cumsum(X_landing)
    # ax.plot(np.arange(T_MIN,T_MAX),X_landing_cumul,color='C1',label='Departure flights')
    # X_takeoff_cumul = np.cumsum(X_takeoff)
    # ax.plot(np.arange(T_MIN,T_MAX),X_takeoff_cumul,color='C0',label='Arrival flights')
    ax.bar(hours - 0.2, y_landing, width=0.4, alpha=0.5, label='Arriving flights', color='r')
    ax.bar(hours + 0.2, y_takeoff, width=0.4, alpha=0.5, label='Departing flights', color='g')
    ax.set_ylabel('Cumulative delay (min)', fontsize=12)
    ax.legend(loc=2)
    # ax.set_xticks(np.arange(T_MIN,T_MAX, 60*60//TIME_STEP))
    ax.set_xticks(hours)
    ax.set_xticklabels(["{0}h".format(e) for e in range(0, 24)], rotation=45)
    step_hour = TIME_STEP/(60*60)
    ax.set_xlim(int(START_AIRPORT_DISRUPTION_TIME*step_hour)-0.9,int(T_MAX*step_hour))
#
# def display_histogram_delay(y_landing, y_pushback,  ax, label=''):
#     hours = np.arange(0, 25)
#     ax.bar(hours - 0.2, y_landing, width=0.4, alpha=0.5, label='Arriving flights', color='r')
#     ax.bar(hours + 0.2, y_pushback, width=0.4, alpha=0.5, label='Departing flights', color='g')
#     ax.set_ylabel('Average deviation \n per flight (min)', fontsize=12)
#     ax.legend()
#     ax.set_xlabel("Hour", fontsize=12)
#     ax.set_xticks(np.arange(0, 25, 1))
#     ax.set_xticklabels(["{0}h".format(e) for e in range(0, 25)], rotation=45)






# def display_histogram_delay(y_landing, y_pushback,  ax, label=''):
#     hours = np.arange(0, 25)
#     ax.bar(hours - 0.2, y_landing, width=0.4, alpha=0.5, label='Arriving flights', color='r')
#     ax.bar(hours + 0.2, y_pushback, width=0.4, alpha=0.5, label='Departing flights', color='g')
#     ax.set_ylabel('Average deviation \n per flight (min)', fontsize=12)
#     ax.legend()
#     ax.set_xlabel("Hour", fontsize=12)
#     ax.set_xticks(np.arange(0, 25, 1))
#     ax.set_xticklabels(["{0}h".format(e) for e in range(0, 25)], rotation=45)
#

def display_slot_violation(flightset,savefig):
    fig,ax = plt.subplots()
    X = np.arange(24)
    nb_flights = np.arange(24)
    Y = np.zeros(24)
    for flight in flightset.flights_d.values():
        if np.abs(flight.final_takeoff-flight.takeoff) > DELTA_SLOT:
            Y[int(flight.takeoff * TIME_STEP//(60*60))] +=1
        nb_flights[int(flight.takeoff * TIME_STEP//(60*60))] +=1
    # for i in range(24):
    #     if nb_flights[i] > 0:
    #         Y[i] *= 100/nb_flights[i]
    ax.bar(X,nb_flights-Y,label='Number of slots respected')
    ax.bar(X,Y,bottom=nb_flights-Y,label='Number of slots violated')
    ax.legend()
    xticks = np.arange((START_AIRPORT_DISRUPTION_TIME*TIME_STEP)//3600, (END_AIRPORT_DISRUPTION_TIME*TIME_STEP)//3600+1)
    ax.set_xticks(xticks)
    ax.set_xticklabels(["{0}h".format(e) for e in xticks], rotation=45)
    ax.set_xlim((START_AIRPORT_DISRUPTION_TIME*TIME_STEP)//3600+0.5, (END_AIRPORT_DISRUPTION_TIME*TIME_STEP)//3600+0.5)
    if savefig:
        plt.savefig( FOLDER_RESULTS + f'slots_violation_histogram_{SCENARIO}.png', bbox_inches='tight')
    else:
        plt.show()


def is_slot_constraint_satisfied(flightset):
    res = True
    for flight in flightset.flights_d.values():
        init_takeoff = flight.takeoff
        final_takeoff = flight.final_takeoff
        if flight.priority and ((final_takeoff - init_takeoff) > DELTA_SLOT):
            print(flight.priority)
            print(f'**** slot violation for flight {flight.id} init takeoff: {flight.takeoff}  final_takeoff: {final_takeoff}')
            res = False
            break
    print(f'Slot constraint satisfied: {res}')

    return res


def is_turn_around_constraint_satisfied(flightset, airport):
    res = True
    for key in flightset.id_flights_ad:
        flight_arr = flightset.flights_a[key]
        flight_dep = flightset.flights_d[key]
        if flight_dep.status != 1:
            turn_around = flight_dep.final_obt - flight_arr.final_landing_time + \
                          airport.taxi_in_duration[flight_arr.final_runway-1][flight_arr.terminal]
            if turn_around < MIN_TURNAROUND_TIME:
                res = False
                print(f'turn around violated on flight {key} with turn around time = {turn_around}min')
    print(f"Is turn around constraint  satisfied: {res} ")
    return res


def is_air_connecting_pax_satisfied(flightset, passengers):
    res = True
    for key in passengers.air_connected_pax_table:
        (id_dep_flight, id_arr_flight) = key
        if flightset.flights_d[id_dep_flight].status != -1:
            ibt = flightset.flights_a[id_arr_flight].final_landing_time
            obt = flightset.flights_d[id_dep_flight].final_obt
            if obt - ibt < passengers.air_connected_pax_table[key].min_connection_time:
                res = False
                print(obt - ibt, '  ', passengers.air_connected_pax_table[key].min_connection_time)
    print(f"Is air connecting pax constraint satisfied: {res}")
    return res


def is_runway_throughput_satisfied(airport, throughputs_ao, is_step_constraint):
    res = [True for _ in range(NB_RUNWAYS)]
    for r in range(NB_RUNWAYS):
        runway_constraint = True
        if is_step_constraint:
            for t in range(T_MIN, T_MAX, CAPACITY_WINDOW):
                if max(throughputs_ao[r][t:t + CAPACITY_WINDOW]) > airport.runways[r].capacities[t//CAPACITY_WINDOW]:
                    runway_constraint = False
                    print(airport.runways[r].name, "  violation at ", round(t*TIME_STEP/3600,2),'h')
                    break
        else:
            if max(throughputs_ao[r]) > airport.runways[r].capacity:
                runway_constraint = False
        res[r] = runway_constraint
    if res == [True for _ in range(NB_RUNWAYS)]:
        print(f'Is runway throughput constraint  satisfied: True')
    else:
        print(f'Is runway throughput constraint  satisfied: False')

        # print(f'runway {airport.runways[r].name} max throughput {max(throughputs_bo[r])}')
    return res


def is_taxi_capacity_satisfied(airport, final_taxi_congestion, is_step_constraint):
    taxi_constraint = True
    if is_step_constraint:
        for t in range(T_MIN, T_MAX, CAPACITY_WINDOW):
            if max(final_taxi_congestion[t:t + CAPACITY_WINDOW]) > airport.taxi.capacities[t//CAPACITY_WINDOW]:
                taxi_constraint = False
                print(f"Taxi violation at  {t*TIME_STEP/(60*60)}h")
                break
    else:
        if max(final_taxi_congestion) > airport.taxi.capacity:
            taxi_constraint = False
    print(f"Is  taxi capacity constraint satisfied : {taxi_constraint}")
    return taxi_constraint


def is_terminal_capacity_satisfied(airport, final_terminals_congestion, is_step_constraint):
    res = [True for _ in range(NB_TERMINALS)]
    for i in range(NB_TERMINALS):
        is_satisfied = True
        if is_step_constraint:
            for t in range(T_MIN, T_MAX, CAPACITY_WINDOW):
                if max(final_terminals_congestion[i][t:t + CAPACITY_WINDOW]) > airport.terminals[i].capacities[t//CAPACITY_WINDOW]:
                    is_satisfied = False
                    print(f"Terminal {airport.terminals[i].terminal_name} violation at {t*TIME_STEP/(60*60)}h")
                    break
        else:
            if max(final_terminals_congestion[i]) > airport.terminals[i].capacity:
                is_satisfied = False
        res[i] = is_satisfied
    if res ==[True for _ in range(NB_TERMINALS)]:
        print(f"Terminal capacity constraint satisfied : True ")
    else:
        print(f"Terminal capacity constraint satisfied : False ")
    return res






def post_processing(airport, flightset, passengers, alpha,beta,test_constraint, display_constraints, savefig,
                    runway_step_constraint, taxi_step_constraint, terminal_step_constraint,is_greedy):
    init_missed_pax, final_missed_pax = compute_missed_passengers(flightset, passengers)
    init_terminals_congestion, final_terminals_congestion, init_taxi_congestion, final_taxi_congestion = compute_congestion(
        airport, flightset)
    runway_bo, runway_ao = compute_throughput_runway(airport, flightset)
    delay_landing, delay_takeoff, total_landing_delay, total_takeoff_delay, nb_slots_violated = compute_delay_disruption(flightset)

    set_status_flights(flightset, airport,START_AIRPORT_DISRUPTION_TIME, END_AIRPORT_DISRUPTION_TIME)
    flightset_crop, passengers_crop, flightset_og, flightset_planned = crop_instance(airport, flightset, passengers,
                                                                           END_AIRPORT_DISRUPTION_TIME)
    nb_dep_flights = len(flightset.flights_d)
    nb_arr_flights = len(flightset.flights_a)
    nb_dep_flights_disruption = len(flightset_crop.flights_d)
    nb_arr_flights_disruption = len(flightset_crop.flights_a)
    if is_greedy:
        filename = FOLDER_RESULTS + f'summary_results_{SCENARIO}_greedy.txt'
    else:
        filename = FOLDER_RESULTS + f'summary_results_{SCENARIO}_alpha_{alpha}_beta_{beta}.txt' #_delayOBT_{DELTA_OBT*TIME_STEP//60}min.txt'
    with open(filename, 'w') as file:
        nb_stranded_pax_bo = int(sum(init_missed_pax))
        nb_stranded_pax_ao = int(sum(final_missed_pax))
        ratio = (nb_stranded_pax_bo - nb_stranded_pax_ao) /nb_stranded_pax_bo
        str_stranded_pax_bo = f'Number of stranded passengers before optim: {int(sum(init_missed_pax))}'
        str_stranded_pax_ao = f'Number of stranded passengers after optim: {int(sum(final_missed_pax))}'
        print(str_stranded_pax_bo)
        print(str_stranded_pax_ao)
        file.write(str_stranded_pax_bo + '\n')
        file.write(str_stranded_pax_ao + '\n')
        str_nb_dep_flights = f'Nb departure flights: Day= {nb_dep_flights} , during the disruption= {nb_dep_flights_disruption}'
        str_nb_arr_flights = f'Nb arrival flights: Day= {nb_arr_flights} , during the disruption= {nb_arr_flights_disruption}'
        print(str_nb_dep_flights)
        print(str_nb_arr_flights)
        file.write(str_nb_dep_flights + "\n")
        file.write(str_nb_arr_flights + "\n")
        str_stranded_pax_ratio = f'Reduction in number of stranded passengers after optim: {round(100 * ratio,2)}%'
        print(str_stranded_pax_ratio)
        file.write(str_stranded_pax_ratio + '\n')
        str_average_landing = f"average deviation for landing flights during disruption: {round(float(np.sum(list(delay_landing.values()))/nb_arr_flights_disruption), 1)}min"
        str_total_landing =f"total deviation for landing flights: {int(total_landing_delay)}min"
        str_nb_delayed_landing = f"nb of arrival flights that have been delayed: {np.sum(np.array(list(delay_landing.values())) !=0)}"
        print(str_average_landing)
        print(str_total_landing)
        print(str_nb_delayed_landing)
        file.write(str_average_landing + "\n")
        file.write(str_total_landing + "\n")
        file.write(str_nb_delayed_landing + "\n")
        str_average_takeoff =  f"average deviation for  departure flights: {round(float(np.sum(list(delay_takeoff.values()))/nb_dep_flights_disruption), 1)}min"
        str_total_takeoff =f"total deviation for departure flights: {int(total_takeoff_delay)}min"
        print(str_average_takeoff)
        print(str_total_takeoff)
        file.write(str_average_takeoff+'\n')
        file.write(str_total_takeoff+'\n')
        str_nb_delayed_takeoff = f"nb of departure flights that have been delayed: {np.sum(np.array(list(delay_takeoff.values())) !=0)}"
        print(str_nb_delayed_takeoff)
        file.write(str_nb_delayed_takeoff + "\n")
        str_slots = f"nb of departure flights that didn't respect their slot: {nb_slots_violated}"
        # str_slots = f"share of departure flights that didn't respect their slot: " \
        #             f"{int(round(100*nb_slots_violated/len(flightset.flights_d)))}%"
        print(str_slots)
        file.write(str_slots)
    if test_constraint:
        is_runway_throughput_satisfied(airport, runway_ao, is_step_constraint=runway_step_constraint)
        is_taxi_capacity_satisfied(airport, final_taxi_congestion, is_step_constraint=taxi_step_constraint)
        is_terminal_capacity_satisfied(airport, final_terminals_congestion,
                                       is_step_constraint=terminal_step_constraint)
        is_air_connecting_pax_satisfied(flightset, passengers)
        is_turn_around_constraint_satisfied(flightset, airport)
        is_slot_constraint_satisfied(flightset)
    if display_constraints:
        display_throughput_constraints(airport, runway_bo,runway_ao,
                                       is_step_constraint=runway_step_constraint,
                                       savefig=savefig)
        display_capacity_constraint(airport, init_terminals_congestion, final_terminals_congestion,
                                    init_taxi_congestion, final_taxi_congestion,
                                    is_taxi_step_constraint=taxi_step_constraint,
                                    is_terminal_step_constraint=terminal_step_constraint,
                                    savefig=savefig)

    display_slot_violation(flightset,savefig=savefig)

    fig, axes = plt.subplots(2, figsize=(8, 5))
    plt.subplots_adjust(left=0.125,
                        bottom=0.1,
                        right=0.9,
                        top=0.9,
                        wspace=0.3,
                        hspace=0.4)
    display_missed_passengers(init_missed_pax, final_missed_pax, ax=axes[0])
    # display_cumul_passengers(init_missed_pax, final_missed_pax, ax=axes[1], label=label)
    display_histogram_delay(flightset, delay_landing, delay_takeoff, ax=axes[1])

    if savefig:
        plt.savefig(FOLDER_RESULTS + f'histograms_{SCENARIO}.png',bbox_inches='tight')
    else:
        plt.show()
    return nb_stranded_pax_bo, nb_stranded_pax_ao, total_landing_delay, total_takeoff_delay, nb_slots_violated, \


def plot_scenarios():
    df=pd.DataFrame()
    df['Scenarios'] = ['s{0}'.format(i) for i in range(1,4)]
    df['missed_pax_ground_bo'] = []
    df['missed_pax_ground_ao'] = [824,308,1081,2029,1959,1413,14557,346]
    df['average_deviation']=[6.5,6.15,6.4,6.41,6.45,5.48,6.7,6.04]
    df['average_arr_deviation']=[3.15,5.88,3.72,3.11,3.73,3.46,3.57,3.76]
    df['average_dep_deviation']=[9.13,8.09,8.35,9.20,8.45,7.13,9,7.06]
    df['relative_decrease (%)'] = (1- df['missed_pax_ground_ao']/df['missed_pax_ground_bo']) *100
    print(df['relative_decrease (%)'])
    df['missed_pax_air'] = [0,0,0,0,6,0,0,0]
    fig,ax = plt.subplots(figsize=(8,4))
    x=df['Scenarios']
    y=df['missed_pax_ground_bo']
    y2=df['missed_pax_ground_ao']
    x=np.arange(len(df['Scenarios']))
    width=0.1
    ax.bar(x-width,y,color='C0',alpha=0.6,label='stranded passengers before optimization',width=2*width)
    ax.bar(x-width,y2,color='C1',alpha=0.6,label='stranded passengers after optimization',width=2*width)
    ax.set_xticks(x)
    ax.set_xticklabels(df['Scenarios'])
    ax.set_ylabel('Number of stranded \n outbound passengers',fontsize=12)
    ax2 = ax.twinx()
    ax2.bar(x+width,df['average_dep_deviation'],color='r',alpha=0.5,width=2*width,label='average departure deviation')
    ax2.bar(x+3*width,df['average_arr_deviation'],color='yellow',alpha=0.4,width=2*width, label='average arrival deviation')

    ax2.set_ylim(0,15)
    ax2.set_ylabel('Average deviation (min)',fontsize=12)
    ax.legend()
    # plt.savefig('Results/ICRAT/comparison_scenarios2.png',bbox_inches='tight')
    plt.show()





def plot_sensitivity_analysis():
    alphas = [0, 0.01, 0.1, 1, 10, 100]
    betas = [0, 0.01, 0.1, 1, 10, 100]
    res = np.zeros((len(alphas), len(betas), 5))

    with open('Results/previousScenarios/S0/sensitivity_alpha_beta_analysis.txt', 'r') as file:
        file.readline()
        liste = file.readline().split()
        nb_arr,nb_dep = int(liste[1]), int(liste[3])

        for line in file:
            # liste = line.split()
            alpha,beta,nb_stranded_pax_bo,nb_stranded_pax_ao,arr_delay,dep_delay,nb_slot_violated = [float(e) for e in line.split()]
            i,j = alphas.index(alpha), betas.index(beta)
            res[i][j] = nb_stranded_pax_bo,nb_stranded_pax_ao,arr_delay,dep_delay,nb_slot_violated
            # print(alpha,beta,nb_stranded_pax_bo,nb_stranded_pax_ao,arr_delay,dep_delay,nb_slot_violated )

    fig,ax = plt.subplots()
    for j in range(len(betas)):
        ax.plot(alphas,res[:,j,4],label = f"beta={betas[j]}")
        # ax.plot(alphas,res[:,j,3],label = f"beta={betas[j]} dep delay")

        # print('j',res[:,j,1])
    ax.set_xscale('log')
    ax.set_xlabel('alpha')
    # ax.set_ylabel('Number of stranded pax')
    ax.set_ylabel('Total slots violated')

    # ax.set_title('Evolution nb stranded_pax in function of alpha ')
    ax.legend()

    plt.savefig(FOLDER_RESULTS  + 'evolution_slots_alpha_beta.png',bbox_inches='tight')