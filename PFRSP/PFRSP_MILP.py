import time

import matplotlib.pyplot as plt
from gurobipy import *
from pre_processing import *
from post_processing import *
from PFRSP_heuristic import *
import pulp


def milp_pfrsp(airport, flightset0, passengers0, alpha, beta, t_start, t_end):
    print('Creation of the model started...')
    modele = Model('PFRSP')
    ########################### DATA ###############################
    flightset, passengers, flightset_og, flightset_planned = crop_instance(airport, flightset0, passengers0, t_end)

    occ_ogp_terms, occ_ogp_tn, occ_ogp_runways = compute_occupancies_ogp(airport, flightset_og, flightset_planned,
                                                                         t_start, t_end)

    indices_a = flightset.flights_a.keys()
    flights_a = flightset.flights_a
    indices_d = flightset.flights_d.keys()
    flights_d = flightset.flights_d

    print('id departure flights: ', indices_d)
    print('id arrival flights: ', indices_a)

    print(f'number of departing flights: {len(indices_d)},  number of arriving flights:{len(indices_a)}')

    indices_ad = flightset0.id_flights_ad  # vols ayant contrainte de turn around, meme id pour vol arrivee et depart

    print("id flights having turn around constraint:  ",
          indices_ad)  ### probleme il faut prendre en compte decision predecesseir
    ids_cf = [(key[0], key[1]) for key in passengers0.air_connected_pax_table]
    transfer_times = {}
    for c in passengers0.air_connected_pax_table.values():
        transfer_times[(c.id_dep_flight, c.id_arr_flight)] = c.min_connection_time

    K = [k.terminal_number for k in airport.terminals]

    g = passengers.ground_pax_connected_table

    id_runway_d, id_runway_a = [], []
    runways = {}
    for r in airport.runways:
        if r.type == 0:
            id_runway_a.append(r.id)
        if r.type == 1:
            id_runway_d.append(r.id)
        runways[r.id] = r

    T = [i for i in range(t_start, t_end)]
    # T_RUNWAYS = [i for i in range(t_start - (RUNWAY_WINDOW_DURATION-1),t_end-(RUNWAY_WINDOW_DURATION-1))] # for arrival runways

    taxi_durations_in = airport.taxi_in_duration  # attention ! sur les index et non les id
    taxi_durations_out = airport.taxi_out_duration  # attention ! sur les index et non les id

    T_A = {}  # dictionnary associating for each arriving flight f a subset of time when f can land
    T_D = {}  # dictionnary associating for each departing flight f a subset of time when f can departs from the gate
    for key, flight in flights_a.items():
        T_A[key] = [i for i in range(flight.landing_time - DELTA_L_MIN, flight.landing_time + DELTA_L_MAX + 1)]
    for key, flight in flights_d.items():
        T_D[key] = [i for i in range(round(flight.obt), round(flight.obt) + DELTA_OBT + 1)]

    A_t = {}  # dictionnary associating for each time t a subset of arriving flights that can land at t
    D_t = {}  # dictionnary associating for each time t a subset of departing flights that can depart from the gate at t
    A_kt = {}  # dictionnary associating for each terminal k and time t a subset of potential departing flight f assigned to k
    D_kt = {}  # dictionnary associating for each terminal k and time t a subset of potential arriving flight f assigned to k
    # T_extended = [i for i in range(t_start-int(np.min(airport.taxi_in_duration)),t_end)] # pour compter vol on going qui ont atterit avant t_start dans capacity
    for t in T:
        list_flights_ak = [[] for _ in range(NB_TERMINALS)]  # flight list associated by terminal that can land at t
        list_flights_dk = [[] for _ in
                           range(NB_TERMINALS)]  # flight list associated by terminal that can have an obt equal to t
        for id in indices_a:
            if t in T_A[id]:
                terminal = flightset.flights_a[id].terminal
                list_flights_ak[terminal].append(id)
        for id in indices_d:
            if t in T_D[id]:
                terminal = flightset.flights_d[id].terminal
                list_flights_dk[terminal].append(id)
        for term, list_term in enumerate(list_flights_ak):
            A_kt[(term, t)] = list_flights_ak[term]
        for term, list_term in enumerate(list_flights_dk):
            D_kt[(term, t)] = list_flights_dk[term]
        list_flights_a = []
        list_flights_d = []
        for list in list_flights_ak:
            list_flights_a += list
        for list in list_flights_dk:
            list_flights_d += list
        A_t[t] = list_flights_a
        D_t[t] = list_flights_d

    ###################### Decision variables ##############################
    x_l = modele.addVars([(f, t, r) for f in indices_a for t in T_A[f] for r in id_runway_a], vtype=GRB.BINARY,
                         name='x_l')  # arriving time
    x_out = modele.addVars([(f, t, r) for f in indices_d for t in T_D[f] for r in id_runway_d], vtype=GRB.BINARY,
                           name='x_out')  # departing time

    o_t = modele.addVars([(k, t) for k in K for t in T], vtype=GRB.INTEGER, lb=0, name='o_t')  # occupancy terminal
    o_tn = modele.addVars([t for t in T], vtype=GRB.INTEGER, lb=0, name='o_tn')  # occupancy terminal

    # phi_d = modele.addVars([(r, t) for r in id_runway_d for t in T], lb= -1000, vtype=GRB.INTEGER,
    #                        name='phi_dep')  # throughput runway
    # phi_a = modele.addVars([(r, t) for r in id_runway_a for t in T], lb=0, vtype=GRB.INTEGER,
    #                        name='phi_arr')  # throughput runway
    t_l = modele.addVars(indices_a, vtype=GRB.INTEGER, name='t_l')  # actual landing block time
    t_in = modele.addVars(indices_a, vtype=GRB.INTEGER, name='t_in')  # actual in block time
    t_out = modele.addVars(indices_d, vtype=GRB.INTEGER, name='t_out')  # actual off block time
    t_to = modele.addVars(indices_d, vtype=GRB.INTEGER, name='t_to')  # actual take off time
    dt_l = modele.addVars(indices_a, vtype=GRB.INTEGER, name='dt_l')  # deviation landing time
    dt_to = modele.addVars(indices_d, vtype=GRB.INTEGER, name='dt_to')  # deviation take off
    y = modele.addVars(indices_d, vtype=GRB.BINARY, name='y')  # slot deviation
    #################### Constraints #####################
    #### Landing time and runway assignment + Landing time (deviation) computation ####

    for f in indices_a:
        modele.addConstr(quicksum([x_l[f, t, r] for t in T_A[f] for r in id_runway_a]) == 1,
                         f"contrainte arrival time and runway assignment flight {f}")
        modele.addConstr(quicksum([t * x_l[f, t, r] for t in T_A[f] for r in id_runway_a]) == t_l[f],
                         f"landing time computation flight {f}")
        modele.addConstr(quicksum(
            [(t + taxi_durations_in[r][flights_a[f].terminal]) * x_l[f, t, r] for t in T_A[f] for r in id_runway_a]) ==
                         t_in[f], f"in block time computation flight {f}")
        modele.addConstr(dt_l[f] >= t_l[f] - flights_a[f].landing_time, f"positive deviation arrival time flight {f}")
        modele.addConstr(dt_l[f] >= flights_a[f].landing_time - t_l[f], f"negative deviation arrival time flight {f}")
        # modele.addConstr(x_l[f,flights_a[f].landing_time,flights_a[f].runway]==1,f"init flight{f}")

    #### OBT and runway assignment + OBT computation  ####
    M_slot = DELTA_OBT + np.max(np.array(taxi_durations_out))
    for f in indices_d:
        modele.addConstr(quicksum([x_out[f, t, r] for t in T_D[f] for r in id_runway_d]) == 1,
                         f"contrainte departure time and runway assignment {f}")
        modele.addConstr(quicksum([t * x_out[f, t, r] for t in T_D[f] for r in id_runway_d]) == t_out[f],
                         f"off block time computation {f}")
        modele.addConstr(quicksum(
            [(t + taxi_durations_out[flights_d[f].terminal][r]) * x_out[f, t, r] for t in T_D[f] for r in
             id_runway_d]) == t_to[f], f"off block time computation flight {f}")
        # modele.addConstr(quicksum([(t+taxi_durations_out[flights_d[f].terminal][r])*x_out[f,t,r] for t in T_D[f] for r in id_runway_d]) == t_to[f] , f"take off time computation flight {f}")
        # modele.addConstr(t_to[f]<=T_MAX, f"take off on the same day {f}")
        # modele.addConstr(x_out[f,flights_d[f].obt,flights_d[f].runway]==1,f"init flight{f}")
        # taxi_time_f = taxi_durations_out[flights_d[f].terminal][flights_d[f].runway]
        modele.addConstr(y[f] >= (t_to[f] - flights_d[f].takeoff - DELTA_SLOT) / M_slot, f" y assignment {f}")
        if flights_d[f].priority:
            modele.addConstr(y[f] == 0, f"slot respect constraint")
        modele.addConstr(dt_to[f] >= t_to[f] - flights_d[f].takeoff, f"positive deviation arrival time flight {f}")
        modele.addConstr(dt_to[f] >= flights_d[f].takeoff - t_to[f], f"negative deviation arrival time flight {f}")

    ####Turn around constraint ####

    for f in indices_ad:
        arr_flight = flightset0.flights_a[f]
        dep_flight = flightset0.flights_d[f]
        # if f == 134:
        #     print(arr_flight,dep_flight)
        if (arr_flight.status == 1) and (dep_flight.status == 1):
            modele.addConstr(t_out[f] - t_in[f] >= MIN_TURNAROUND_TIME, f"contrainte turn around flight {f}")
        elif dep_flight.status == 1:  # vol actif
            ibt = arr_flight.ibt
            modele.addConstr(t_out[f] - ibt >= MIN_TURNAROUND_TIME, f"contrainte turn around flight {f}")
        elif (arr_flight.status == 1) and dep_flight.priority:  ##active arr flight connected to planned flight
            obt = dep_flight.obt
            modele.addConstr(obt + DELTA_SLOT - t_in[f] >= MIN_TURNAROUND_TIME, f"contrainte turn around flight {f}")

    #### Connecting flight constraint ####

    for (f1, f2) in ids_cf:
        arr_flight = flightset0.flights_a[f2]
        dep_flight = flightset0.flights_d[f1]
        if (arr_flight.status == 1) and (dep_flight.status == 1):
            modele.addConstr(t_out[f1] - t_in[f2] >= transfer_times[(f1, f2)],
                             f"contrainte connecting flights {f1, f2}")
        elif dep_flight.status == 1:  # on going/completed arrival flight connected to active one
            ibt = arr_flight.final_ibt
            modele.addConstr(t_out[f1] - ibt >= transfer_times[(f1, f2)], f"contrainte connecting flights {f1, f2}")
        elif (arr_flight.status == 1) and dep_flight.priority:  ##active arr flight connected to planned flight
            obt = dep_flight.obt
            modele.addConstr(obt + DELTA_SLOT - t_in[f2] >= transfer_times[(f1, f2)],
                             f"contrainte connecting flights {f1, f2}")

    occupancy = []
    capacity = []
    print('°°°°°°°°°°°°°°°°°°°°°°°°')
    # print(occupancy)
    # print(capacity)
    # for k in K:
    #     occupancy.append(airport.terminals[k].initial_occupancy + occ_ogp_terms[k][T[0]])
    #     capacity.append(airport.terminals[k].capacity)
    #     # print(occ_ogp_terms[k])
    #
    # occupancies = np.zeros((len(K),len(T)))
    # actual_occupancies = np.zeros((len(K),len(T)))
    #### Terminal capacity constraint ####
    for k in K:
        modele.addConstr(o_t[k, t_start] == airport.terminals[k].initial_occupancy + occ_ogp_terms[k][t_start],
                         f"(terminal capacity computation) {k, t_start}")
        # occupancies[k][0] = airport.terminals[k].initial_occupancy + occ_og_terms[k][t_start]
        # actual_occupancies[k][0] = airport.terminals[k].initial_occupancy + occ_og_terms[k][t_start]
        # print("***********", occ_og_terms[k])
        for i, t in enumerate(T[:-1]):
            flights_in = []
            flights_out = [x_out[f, t, r] for r in id_runway_d for f in D_kt[(k, t)]]
            for r in id_runway_a:
                taxi_time_in = taxi_durations_in[r][k]
                tbis = t - taxi_time_in
                if tbis >= t_start:
                    flights_in += [x_l[f, tbis, r] for f in A_kt[(k, tbis)]]
            modele.addConstr(
                o_t[k, T[i + 1]] == o_t[k, t] + quicksum(flights_in) - quicksum(flights_out) + occ_ogp_terms[k][
                    T[i + 1]], f"(terminal capacity computation) {k, T[i + 1]}")
            # modele.addConstr(o_t[k,T[i+1]] >= o_t[k,t] + quicksum(flights_in) - quicksum(flights_out) + occ_og_terms[k][T[i+1]],f"(terminal upper capacity computation) {k,T[i+1]}")
            # delta_flight_d = 0
            # delta_flight_a = 0
            # actual_delta_flight_d = 0
            # actual_delta_flight_a = 0
            # for flight in flights_d.values():
            #     if flight.terminal == k and flight.obt == t:
            #         delta_flight_d +=1
            # for flight in flights_a.values():
            #     if flight.terminal == k:
            #         ibt  = flight.ibt
            #         if ibt == t:
            #             delta_flight_a +=1
            # for flight in flightset0.flights_d.values():
            #     if flight.terminal == k and flight.obt == t:
            #         actual_delta_flight_d +=1
            # for flight in flightset0.flights_a.values():
            #     if flight.terminal == k:
            #         ibt  = flight.ibt
            #         if ibt == t:
            #             actual_delta_flight_a +=1
            # occupancies[k][i+1] = occupancies[k][i] + occ_og_terms[k][T[i+1]] - delta_flight_d +delta_flight_a
            # actual_occupancies[k][i+1] = actual_occupancies[k][i] - actual_delta_flight_d  + actual_delta_flight_a
            if TERMINAL_STEP_CONSTRAINT:
                modele.addConstr(o_t[k, t] <= airport.terminals[k].capacities[int(t // CAPACITY_WINDOW)],
                                 f'terminal {k} at time {t} occupancy constraint')
            else:
                modele.addConstr(o_t[k, t] <= airport.terminals[k].capacity,
                                 f'terminal {k} at time {t} occupancy constraint')

    # X = T
    # fig, axes = plt.subplots(len(K))
    # for k in K:
    # axes[k].plot(X,occupancies[k],color='C0')
    # axes[k].plot(X,actual_occupancies[k],color='C1',linestyle='--')
    # print(airport.terminals[k].capacity)
    # print(occupancies[k])
    # axes[k].axhline(airport.terminals[k].capacity,xmin=0, xmax=1,color='r')
    # axes[k].set_xlabel(f'Terminal {k}')
    # plt.show()

    #### Taxi Network capacity constraint ####

    modele.addConstr(o_tn[t_start] == occ_ogp_tn[t_start], 'initial taxi network capacity')
    for i, t in enumerate(T[:-1]):
        landing_flights, in_block_flights = [], []
        for r in id_runway_a:
            for f in A_t[t]:
                landing_flights.append(x_l[f, t, r])
            for k in K:
                taxi_time_in = taxi_durations_in[r][k]  ### car indices runway commence à 1, à améliorer...
                t_bis = int(t - taxi_time_in)
                if t_bis >= t_start:
                    for f in A_kt[(k, t_bis)]:
                        in_block_flights.append(x_l[f, t_bis, r])
        off_block_flights, take_off_flights = [], []
        for r in id_runway_d:
            for f in D_t[t]:
                off_block_flights.append(x_out[f, t, r])
            for k in K:
                taxi_time_out = taxi_durations_out[k][r]  ### car indices runway commence à 1, à améliorer...
                t_bis = int(t - taxi_time_out)
                if t_bis >= t_start:
                    for f in D_kt[(k, t_bis)]:
                        take_off_flights.append(x_out[f, t_bis, r])
        modele.addConstr(o_tn[T[i + 1]] == o_tn[t] + quicksum(landing_flights) - quicksum(in_block_flights)
                         + quicksum(off_block_flights) - quicksum(take_off_flights) + occ_ogp_tn[T[i + 1]],
                         f"(taxi network capacity computation) {T[i + 1]}")
        # modele.addConstr(o_tn[t] <= airport.taxi.capacity, f'taxi network capacity at time {t} constraint')
        modele.addConstr(o_tn[t] <= airport.taxi.capacities[int(t // CAPACITY_WINDOW)],
                         f'taxi network capacity at time {t} constraint')

    for t in T:
        for r in id_runway_a:
            # modele.addConstr(quicksum([x_l[f, t, r] for f in A_t[t]]) + occ_ogp_runways[r][t] <= runways[r].capacity,
            #                  f'throughput capacity constraint runway {r} at time {t}')
            modele.addConstr(quicksum([x_l[f, t, r] for f in A_t[t]]) + occ_ogp_runways[r][t] <= runways[r].capacities[
                int(t // CAPACITY_WINDOW)],
                             f'throughput capacity constraint runway {r} at time {t}')
        for r in id_runway_d:
            phi = []
            for k in K:
                taxi_time_out = taxi_durations_out[k][r]
                # print(taxi_time_out)
                t_bis = int(t - taxi_time_out)
                if t_bis >= t_start:
                    phi += [x_out[f, t_bis, r] for f in D_kt[(k, t_bis)]]
            # modele.addConstr(quicksum(phi) + occ_ogp_runways[r][t] <= runways[r].capacity, f'throughput capacity constraint departure runway {r} at time {t}')
            modele.addConstr(quicksum(phi) + occ_ogp_runways[r][t] <= runways[r].capacities[int(t // CAPACITY_WINDOW)],
                             f'throughput capacity constraint runway {r} at time {t}')
    ####verif if og computed well: ###
    # X = np.arange(max(0,t_start-WINDOW_SHIFT),t_end)
    # print(X)
    # throughputs = np.zeros((len(id_runway_a),len(X)))
    # actual_throughputs = np.zeros((len(id_runway_a),len(X)))
    # for t in X:
    #     for r in id_runway_a:
    #         delta_flight_a = 0
    #         actual_delta_flight_a = 0
    #         for flight in flights_a.values():
    #             if flight.final_runway == r:
    #                 landing_time = flight.final_landing_time
    #                 if landing_time == t:
    #                     delta_flight_a += 1
    #         for flight in flightset0.flights_a.values():
    #             if flight.final_runway == r:
    #                 landing_time = flight.final_landing_time
    #                 if landing_time == t:
    #                     actual_delta_flight_a += 1
    #         if t >= t_start and t < t_end:
    #             throughputs[r][t-max(0,t_start-WINDOW_SHIFT)] = occ_ogp_runways[r][t] + delta_flight_a
    #         else:
    #             throughputs[r][t-max(0,t_start-WINDOW_SHIFT)] = 0
    #         actual_throughputs[r][t-max(0,t_start-WINDOW_SHIFT)] = actual_delta_flight_a

    # if t_start >= 234 and t_start<241:
    #     fig, axes = plt.subplots(len(id_runway_a))
    #     for r in id_runway_a:
    #         axes[r].plot(X,throughputs[r],color='C0')
    #         axes[r].plot(X,actual_throughputs[r],color='C1',linestyle='--')
    #         axes[r].axhline(8,xmin=0, xmax=1,color='r')
    #         axes[r].set_xlabel(f'runway {r}')
    #     plt.show()

    ####################### objective function ###############################
    criteria1 = quicksum(
        [x_out[f, t, r] * g[f][j] for f in indices_d for j, t in enumerate(T_D[f]) for r in id_runway_d])
    # criteria2 = quicksum([t_out[f]-flights_d[f].obt for f in indices_d])+\
    #             quicksum([dt_l[f] for f in indices_a])
    criteria2 = quicksum([dt_to[f] for f in indices_d]) + \
                quicksum([dt_l[f] for f in indices_a])
    criteria3 = quicksum([y[f] for f in indices_d])
    modele.setObjective(criteria1 + alpha * criteria2 + beta * criteria3,
                        GRB.MINIMIZE)  # t : indices a prendre en fonction pushback et non t absolu

    print('Model successfully created')
    # modele.write("PFRSP.mps")
    # var, problem = pulp.LpProblem.fromMPS('PFRSP.mps')
    # solver_list = pulp.listSolvers(onlyAvailable=True)
    # print(solver_list)
    # start_pulp = time.time()
    # solution_status = problem.solve(pulp.GLPK_CMD())
    # modele = read('PFRSP.mps')
    # modele.optimize()
    # print(f"Computation time GLPK: {round(time.time() - start_pulp,2)}s")
    # print("------->",pulp.LpStatus[solution_status])

    start_gurobi = time.time()
    # modele = read('PFRSP.mps')
    modele.optimize()
    print(f"Computation time Gurobi: {round(time.time() - start_gurobi, 2)}s")
    solution_status = 'optimal'
    try:
        # if 1 == 1:
        cpt = 0
        for v in modele.getVars():
            if (v.varName.startswith('x_l')) and (np.round(v.x) == 1):
                # print(v.x)
                [id_f, landing_time, rwy_in] = [int(e) for e in v.varName[4:-1].split(',')]
                flights_a[id_f].final_landing_time = landing_time
                flights_a[id_f].final_ibt = int(landing_time + taxi_durations_in[rwy_in][flights_a[id_f].terminal])
                flights_a[id_f].final_runway = rwy_in
            elif (v.varName.startswith('x_out')) and (np.round(v.x) == 1):
                [id_f, obt, rwy_out] = [int(e) for e in v.varName[6:-1].split(',')]
                flights_d[id_f].final_obt = obt
                flights_d[id_f].final_runway = rwy_out
                flights_d[id_f].final_takeoff = int(obt + taxi_durations_out[flights_d[id_f].terminal][rwy_out])
    except:
        modele.computeIIS()
        modele.write("model.ilp")
        solution_status = 'infeasible'
    # print('**************', solution_status)
    return flights_a, flights_d, solution_status


def solve_time_windows_milp(airport, flightset, passengers, alpha, beta, greedy):
    t_start = START_AIRPORT_DISRUPTION_TIME
    t_end = t_start + WINDOW_DURATION
    solution_status = 'optimal'
    if greedy:
        list_tabu_dep_flights = []
        dico_tabu_arr_flights = initialized_tabu_arr_flights(flightset, passengers)  # per pushback step
    while (t_start + WINDOW_SHIFT < T_MAX and solution_status == 'optimal'):
        set_status_flights(flightset, airport, t_start, t_end)
        compute_terminals_occupancy(flightset, airport)
        print(
            f"********************Run problem between {t_start * TIME_STEP // 60}min and {t_end * TIME_STEP // 60}min************************")
        # start_time = time.time()
        if greedy:
            flights_a, flights_d, list_tabu_dep_flights, dico_tabu_arr_flights = run_greedy(airport, flightset,
                                                                                             passengers, t_start, t_end,
                                                                                             list_tabu_dep_flights,
                                                                                             dico_tabu_arr_flights)
        else:
            flights_a, flights_d, solution_status = milp_pfrsp(airport, flightset, passengers, alpha, beta, t_start,
                                                               t_end)
        # end_time = time.time()
        # print(f'Computation time between {t_start * TIME_STEP // 60}min and {t_end * TIME_STEP // 60}:  {np.round(end_time-start_time,3)}s')
        flightset = update_flightset(flightset, flights_a, flights_d)
        t_start += WINDOW_SHIFT
        t_end += WINDOW_SHIFT
    # for flight in flightset.flights_d.values():
    #     if flight.status == 0:
    #         print(flight.id, "-------------- still planned")
    # for flight in flightset.flights_a.values():
    #     if flight.status == 0:
    #         print(flight.id, "-------------- still planned")
    if (greedy == False) and (solution_status == 'optimal'):
        print('************ OPTIMIZATION RUN FOR THE FULL DAY ************')
    return flightset

