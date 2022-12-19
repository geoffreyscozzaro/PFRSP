


SCENARIO = 'S45'


if SCENARIO == 'S45':
    DAY = 24  # 23
    MONTH = 6  # 6
    YEAR = 2019
    MODE_DISRUPTED = 'SUBWAY'
    DELAY = 45 * 60  # 60*60 in seconds
    START_MODE_DISRUPTION_HOUR = 7  # 10
    END_MODE_DISRUPTION_HOUR = 15  # 18

if SCENARIO == 'R45':
    DAY = 24  # 23
    MONTH = 6  # 6
    YEAR = 2019
    MODE_DISRUPTED = 'ROAD'
    DELAY = 45 * 60  # 60*60 in seconds
    START_MODE_DISRUPTION_HOUR = 7  # 10
    END_MODE_DISRUPTION_HOUR = 15  # 18
elif SCENARIO == 'T45':
    DAY = 24  # 23
    MONTH = 6  # 6
    YEAR = 2019
    MODE_DISRUPTED = 'TRAIN'
    DELAY = 45 * 60  # 60*60 in seconds
    START_MODE_DISRUPTION_HOUR = 7  # 10
    END_MODE_DISRUPTION_HOUR = 15  # 18
elif SCENARIO == 'S90':
    DAY = 24  # 23
    MONTH = 6  # 6
    YEAR = 2019
    MODE_DISRUPTED = 'SUBWAY'
    DELAY = 90 * 60  # 60*60 in seconds
    START_MODE_DISRUPTION_HOUR = 7  # 10
    END_MODE_DISRUPTION_HOUR = 15  # 18
elif SCENARIO == 'R90':##2019/06/24: nb aircraft: 1447
    DAY = 24  # 23
    MONTH = 6  # 6
    YEAR = 2019
    MODE_DISRUPTED = 'ROAD'
    DELAY = 90 * 60  # 60*60 in seconds
    START_MODE_DISRUPTION_HOUR = 7  # 10
    END_MODE_DISRUPTION_HOUR = 15  # 18
elif SCENARIO == 'T90': ##2021/06/24: nb aircraft: 555
    DAY = 24  # 23
    MONTH = 6  # 6
    YEAR = 2019
    MODE_DISRUPTED = 'TRAIN'
    DELAY = 90 * 60  # 60*60 in seconds
    START_MODE_DISRUPTION_HOUR = 7  # 10
    END_MODE_DISRUPTION_HOUR = 15  # 18
elif SCENARIO == 'S45_1': ##2021/06/24: nb aircraft: 555
    DAY = 24  # 23
    MONTH = 6  # 6
    YEAR = 2019
    MODE_DISRUPTED = 'SUBWAY'
    DELAY = 45 * 60  # 60*60 in seconds
    START_MODE_DISRUPTION_HOUR = 5  # 10
    END_MODE_DISRUPTION_HOUR = 10  # 18
elif SCENARIO == 'S45_2': ##2021/06/24: nb aircraft: 555
    DAY = 24  # 23
    MONTH = 6  # 6
    YEAR = 2019
    MODE_DISRUPTED = 'SUBWAY'
    DELAY = 45 * 60  # 60*60 in seconds
    START_MODE_DISRUPTION_HOUR = 14  # 10
    END_MODE_DISRUPTION_HOUR = 21  # 18
elif SCENARIO == 'S45_3': ##2021/06/24: nb aircraft: 555
    DAY = 24  # 23
    MONTH = 6  # 6
    YEAR = 2019
    MODE_DISRUPTED = 'SUBWAY'
    DELAY = 45 * 60  # 60*60 in seconds
    START_MODE_DISRUPTION_HOUR = 5  # 10
    END_MODE_DISRUPTION_HOUR = 21  # 18



STR_MONTH = str(MONTH).zfill(2)
STR_DAY = str(DAY).zfill(2)
DATE = f'{YEAR}/{STR_MONTH}/{STR_DAY}'

NB_FLIGHTS = 726
# NB_SLOTS = 56
NB_DEP_RUNWAYS = 2
NB_ARR_RUNWAYS = 2
NB_RUNWAYS = NB_ARR_RUNWAYS + NB_DEP_RUNWAYS

NB_TERMINALS = 9
TIME_STEP = 60*5 #in SECONDS
T_MIN = (0*60*60) //TIME_STEP# in TIME_STEPS
T_MAX = (24*60*60) // TIME_STEP # in TIME_STEPS
# import numpy as np
# print(len(np.arange(0, T_MAX + 60*60//TIME_STEP, 60*60//TIME_STEP)))
WINDOW_DURATION = (2*60*60)//TIME_STEP # in TIME_STEPS

WINDOW_SHIFT = (30*60)//TIME_STEP # fonctionne avec 15

MIN_TURNAROUND_TIME = (30*60)//TIME_STEP# in TIME_STEPS

CAPACITY_WINDOW = (60*60)//TIME_STEP #window duration to set max  capacity, hourly capacity if =60

# RUNWAY_WINDOW_DURATION = 10 # duration time window to compute maximum runway throughput in TIME STEPS


DELTA_SLOT = (10*60)//TIME_STEP # push back max to respect slot in TIME_STEPS
DELTA_OBT = (20*60)//TIME_STEP # push back max in TIME_STEPS
DELTA_L_MIN = (5*60)//TIME_STEP #deviation landing min in TIME_STEPS
DELTA_L_MAX = (15*60)//TIME_STEP #deviation landing max in TIME_STEPS




# pourcentage_pax = 0.9
# ALPHA = 0.9 # parameter objective function, =1 if only minimizing nb missed connection and 0 if only minimizing planning deviation
# ALPHA = 9 *(1/pourcentage_pax) / (1+9*(1/pourcentage_pax))

ALPHA = 0.0001 #0.1 #parameter deviation time
BETA = 0.9# 1 # #parameter non respect slot


### Constantes ###
NM_TO_METER = 1852.0
KT_TO_MS = 1852.0 / 3600.0
SPEED_RUNWAY_THRESHOLD = [110 * KT_TO_MS, 130 * KT_TO_MS, 150 * KT_TO_MS]  #in function of wtCat





# MIN_PROCESS_TIME = 40

ACCESS_TIME = (2 *60*60)//TIME_STEP #in hour, used to simulate inertia between start disruption access mode and impact on departure flights




START_MODE_DISRUPTION_TIME = (START_MODE_DISRUPTION_HOUR*60*60) // TIME_STEP #11 in hour
END_MODE_DISRUPTION_TIME = (END_MODE_DISRUPTION_HOUR*60*60) // TIME_STEP #15 in hour

START_AIRPORT_DISRUPTION_TIME = START_MODE_DISRUPTION_TIME + ACCESS_TIME #in hour
END_AIRPORT_DISRUPTION_TIME = END_MODE_DISRUPTION_TIME + ACCESS_TIME #in hour



ACCESS_TIME = 120 #min param utile pour savoir qui a ete impacte par perturbation: ex: RER bloque 10h à 12h alors pax qui en  situation nominal prevus en porte a entre 10h+ACCESS TIME et 14h+ACCESS_TIME seront retardes
#params generate  arrival flow CDG

# TERMINAL_INITIAL_OCCUPANCY = [9,59,46]
# TERMINAL_INITIAL_OCCUPANCY #computed during preprocessing
FOLDER_RESULTS = f'Results/{SCENARIO}/comparisonMethods/'
# FOLDER_RESULTS = f'Results/madrid/'

TAXI_STEP_CONSTRAINT = True

RUNWAY_STEP_CONSTRAINT= True

TERMINAL_STEP_CONSTRAINT = True


# IS_REDUCED_CAPACITY = True
# RESOURCE_TYPE = 'taxi' #terminal 'taxi'
# RESOURCE_IDX ='' # '26L' '26R' '27L'
# REDUCTION_PERCENT= 0.15


# import numpy as np
# arr = np.array([6,4,5,0,0,2])
#
# print(np.sum(arr !=0))