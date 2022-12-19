# PFRSP
This project proposes an approach  to reschedule flights at a tactical level when an airport access mode disruption occurs.
More details on the problem can be found in https://hal-enac.archives-ouvertes.fr/hal-03701665/document.
This work is also part of the SESAR project called TRANSIT (https://www.transit-h2020.eu/)

Assuming an information sharing between ground and air transportation stakeholders, passengers arrival time forecast at the gate could be frequently updated.
Then based on these new forecast, we propose to reschedule flights to minimize the number of stranded passengers while considering airside constraints into account. 
Two methods are proposed:

-A Mixed-Integer Linear Programming model solved through Gurobi solver (PFRSP_MILP.py)

-An Heuristic approach based on a simple decision procedure that could be followed by an airport operator (PFRSP_heuristic.py)


The different data set are based on an historical day of operations at Paris-CDG airport.
Several disruptive scenarios are proposed in the folder 'Data':
R/S/T: letter qualifying the disrupted mode (Road, Subway and Train respectively)
45/90: quantify the severity of the disruption with the highest passenger delay (45min and 90min respectively). 
S45_1/_2/_3: Disruption on the subway with a maximum passenger delay of 45min tested on different hours of the day (5am-10am, 2pm-9pm, 5am-9pm respectively)
All the characteristics of these scenarios are summarized in the file 'constantes.py'._

The user should run 'main.py'. The choice of the algorithm (heuristic or milp) is done in main.py. The parameters of the model and the selection of the scenario can be modified in the 'constants.py' file.
