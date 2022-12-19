# PFRSP
This project proposes an approach  to reschedule flights at a tactical level when an airport access mode disruption occurs.
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
All the characteristics of these scenarios are summarized in the file 'constantes.py'.

