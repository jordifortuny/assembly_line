from __future__ import print_function
from ortools.sat.python import cp_model

import pandas as pd

def custom_optim_function(stations, boleans_tasks_same_station,
 num_models, num_tasks, num_stations):
    
    all_tasks = range(num_tasks)
    all_stations = range(num_stations)
    all_models = range(num_models)

    WEIGHT_SAME_TASK_AT_SAME_STATION = 1
    WEIGHT_NUM_STATIONS_USED = 1
    Q = num_tasks

    #Try to assign same tasks to same stations (TODO FINISH THIS CORRECTLY)
    for t in all_tasks:
        for s in all_stations:
        	Q = Q - WEIGHT_SAME_TASK_AT_SAME_STATION*boleans_tasks_same_station[(t,s)]

    #Minimize number of stations used
    for s in all_stations:
        for m in all_models:
            Q = Q + WEIGHT_NUM_STATIONS_USED*stations[(s,m)]

    return Q

def read_data_from_excel(file):

	dataset = pd.read_excel(file)

	num_models = int((dataset.shape[1]-2)/2)
	num_tasks = dataset.shape[0]
	num_stations = num_tasks

	all_tasks = dataset["Task_code"].to_list()

	durations = [] 
	for i in range(num_models):
		s = "m" + str(i+1) + "_task_load"
		durations.append(dataset[s].to_list())

	precedences = [] 
	for i in range(num_models):
		s = "m" + str(i+1) + "_precedessors"
		list_precedessors = dataset[s].to_list()
		new_list_precedessors = []
		for p in list_precedessors:
			if "-" in str(p):
				if p == "-":
					new_list_precedessors.append([]) 
				else:
					l = p.split("-")
					mini_list_precedessors = []
					for n in l:
						mini_list_precedessors.append(int(n))
					new_list_precedessors.append(mini_list_precedessors)
			else:
				new_list_precedessors.append([p])

		precedences.append(new_list_precedessors)

	return num_models, num_tasks, all_tasks, num_stations, durations, precedences


def main():
    
    # This program tries to find an optimal assignment of num_tasks tasks of 
    # durations (d1, d2, ..., d_num_tasks) to a maximum of num_stations stations,
    # subject to some constraints (see below).

    # Each station should not work more than a maximum time T.
    # All tasks must be performed.
    # Each task should only be performed in one station.
    # Each task may have some precedences:
    #    some tasks that need to be performed in a previous station.

    # The optimal assignment minimizes the number of stations used.
    
    num_models, num_tasks, all_tasks, num_stations, durations, precedences = read_data_from_excel("Cevikcan2.xlsx")
    T = 100000
    num_stations = 14
    dict_tasks_nodes = dict()
    for i in range(num_tasks):
    	dict_tasks_nodes[all_tasks[i]] = i

    print("Num models {}".format(num_models))
    print("Num tasks {}".format(num_tasks))
    print("Num stations {}".format(num_stations))
    
    all_stations = range(num_stations)
    all_models = range(num_models)
    
    # Creates the model.
    model = cp_model.CpModel()

    # Creates assignations variables ----------------
    # assignations[(t, s)]: task 't' is performed in station 's'.
    assignations = {}
    for t in all_tasks:
        for s in all_stations:
               for m in all_models:
                assignations[(t,s,m)] = model.NewBoolVar('assignation_t%is%im%i' % (t,s,m))

    # stations_used[s]: station 's' is being used.
    stations_used = {}
    for s in all_stations:
        for m in all_models:
            stations_used[(s,m)] = model.NewBoolVar('station_s%im%i' % (s,m))

    #Booleans tasks same station
    boleans_tasks_same_station = {}
    for t in all_tasks:
        for s in all_stations:
        	boleans_tasks_same_station[(dict_tasks_nodes[t],s)] = model.NewBoolVar('bolean_tasks_same_station_t%is%i' % (t,s))
        	model.Add(sum(assignations[(t,s,m)] for m in all_models) == num_models).OnlyEnforceIf(boleans_tasks_same_station[(dict_tasks_nodes[t],s)])
        	model.Add(sum(assignations[(t,s,m)] for m in all_models) < num_models).OnlyEnforceIf(boleans_tasks_same_station[(dict_tasks_nodes[t],s)].Not())	

    # Constraints ----------------
    # Each task should only be performed in one station and all must be performed
    for m in all_models: 
        for t in all_tasks:
            model.Add(sum(assignations[(t,s,m)] for s in all_stations) == 1)

    # To keep order in the stations used
    for m in all_models:
        for s in all_stations:
            if(s != 0):
                model.Add(stations_used[(s,m)] <= stations_used[(s-1,m)])

    # Each station should not work more than a maximum time T
    for m in all_models:
        for s in all_stations:
        	model.Add(sum(assignations[(t,s,m)]*durations[m][dict_tasks_nodes[t]] for t in all_tasks) <= T*stations_used[(s,m)])

    #Each task may have some precedences:
    for m in all_models:
        for t in all_tasks:
            for p in precedences[m][dict_tasks_nodes[t]]:
            	model.Add(sum(s*(assignations[(t,s,m)] - assignations[(p,s,m)]) for s in all_stations) >= 0)

    #Objective function
    model.Minimize(custom_optim_function(stations_used, boleans_tasks_same_station,
     num_models, num_tasks, num_stations))

    # Creates the solver and solve.
    solver = cp_model.CpSolver()

    solver.parameters.log_search_progress = True
    solver.parameters.linearization_level = 2
    solver.parameters.num_search_workers = 8
    solver.parameters.max_time_in_seconds = 1800

    solver.Solve(model)
    print(solver.ResponseStats())

    # Stores the output into a dictionary and then saves it as a pandas DataFrame
    d = dict()
    for m in all_models:
    	list_tasks_performed = []
    	for s in all_stations:
    		if solver.Value(stations_used[(s, m)]) == 0:
    			list_tasks_performed.append("")
    		else:
    			list_tasks = []
    			for t in all_tasks:
    				if solver.Value(assignations[(t,s,m)]) == 1:
    					list_tasks.append(str(t))
    				list_tasks_str = "-".join(list_tasks)
    			list_tasks_performed.append(list_tasks_str)
    	d["model " + str(m)] = list_tasks_performed 

    df = pd.DataFrame.from_dict(d)
    df.to_csv("output.csv")

    # Print Statistics.
    print()
    print('Statistics')
    print('  - Objective value = %i' % solver.ObjectiveValue())
    print('  - wall time       : %f s' % solver.WallTime())

if __name__ == '__main__':
    main()