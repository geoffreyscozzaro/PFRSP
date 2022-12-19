import PFRSP_MILP
from constants import *
from pre_processing import *
import time
from post_processing import *


def main(airport, flightset, passengers, alpha, beta, greedy=False, read_sol=False, savefig=False, filename=''):
    start = time.time()
    if read_sol:
        flights_a, flights_d = read_solution(filename)
        flightset.flights_a = flights_a
        flightset.flights_d = flights_d
        flightset_milp = flightset
    else:
        flightset_milp = PFRSP_MILP.solve_time_windows_milp(airport, flightset, passengers, alpha, beta, greedy)
        write_solution(flightset_milp, label='')
    computational_time = time.time() - start
    print(f" Computational time: {round(computational_time, 2)}s")
    tot_stranded_pax_bo, tot_stranded_pax_ao, tot_deviation_dep_flights, tot_deviation_arr_flights, tot_slots_violated = post_processing(
        airport, flightset_milp, passengers, alpha, beta, test_constraint=True,
        terminal_step_constraint=TERMINAL_STEP_CONSTRAINT, display_constraints=True,
        taxi_step_constraint=TAXI_STEP_CONSTRAINT, runway_step_constraint=RUNWAY_STEP_CONSTRAINT,
        savefig=savefig, is_greedy=greedy)
    print("####", tot_stranded_pax_bo, tot_stranded_pax_ao, tot_deviation_arr_flights, tot_deviation_dep_flights,
          tot_slots_violated)

    return tot_stranded_pax_bo, tot_stranded_pax_ao, tot_deviation_arr_flights, tot_deviation_dep_flights, tot_slots_violated


airport, flightset, passengers = read_instance()
alpha,beta = ALPHA,BETA
main(airport,flightset,passengers, alpha,beta,read_sol=False, greedy= False, savefig=True) #, filename=FOLDER_RESULTS + f'flightset_results_{SCENARIO}_pushback_{DELTA_OBT*TIME_STEP//60}min.txt')





