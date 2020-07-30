#!/usr/bin/env python
# coding: utf-8

# In[1]:


import pandas as pd
from ortools.linear_solver import pywraplp

solver = pywraplp.Solver('aviation problem', pywraplp.Solver.CBC_MIXED_INTEGER_PROGRAMMING)
infinity = solver.infinity()
print("Running..")

# In[2]:

""" PART A - Load the Data """
file_name = 'Aviation_Data.xlsx'
flight_schedule = pd.read_excel(file_name, 'Flight schedule', header=0, index_col=0)
taxi_distances = pd.read_excel(file_name, 'Taxi distances', header=0, index_col=0)
terminal_capacity = pd.read_excel(file_name, 'Terminal capacity', header=0, index_col=0, dtype=int())

# In[3]:


flights = list(flight_schedule.index.values)
terminals = list(terminal_capacity.index.values)
runways = list(taxi_distances.index.values)


# In[4]:

set_of_time_slots = set()
for flight in flights:
    set_of_time_slots.add(flight_schedule.loc[flight, 'Arrival'])
    set_of_time_slots.add(flight_schedule.loc[flight, 'Departure'])

# In[5]:


# In[6]:
""" PART B -  create the decision variables for the arrival runway allocation,departure runway allocation ,terminal allocation """

arrival_runway_allocations = {}
for flight in flights:
    variables = {}
    for runway in runways:
        variables[runway] = solver.IntVar(0, 1, flight + runway + 'arrival_runway_allocations')
    arrival_runway_allocations[flight] = variables


""" PART G -  implement the constraints that ensure that each flight has exactly one allocated arrival runway """
for flight in flights:
    solver.Add(solver.Sum(list(arrival_runway_allocations[flight].values())) == 1)

# In[7]:

""" PART B -  create the decision variables for the arrival runway allocation,departure runway allocation ,terminal allocation """
departure_runway_allocations = {}
for flight in flights:
    variables = {}
    for runway in runways:
        variables[runway] = solver.IntVar(0, 1, flight + runway + 'departure_runway_allocations')
    departure_runway_allocations[flight] = variables

""" PART G -  implement the constraints that ensure that each flight has exactly  one allocated departure runway """
for flight in flights:
    solver.Add(solver.Sum(list(departure_runway_allocations[flight].values())) == 1)


""" PART B -  create the decision variables for the arrival runway allocation,departure runway allocation ,terminal allocation """
terminal_allocations = {}
for flight in flights:
    variables = {}
    for terminal in terminals:
        variables[terminal] = solver.IntVar(0, 1, flight + terminal + "terminal_allocations")
    terminal_allocations[flight] = variables

""" PART H -  implement the constraints the ensure that each flight is allocated to exactly one terminal  """
for flight in flights:
    solver.Add(solver.Sum(list(terminal_allocations[flight].values())) == 1)
# In[8]:


""" PART C -  create auxiliary variables for the taxi movements between runways and terminals for each flight"""


def create_taxi_movement_variables(terminals, flights, runways, text):
    taxi_movement_per_flight = {}
    for terminal in terminals:
        taxi_movement_per_flight[terminal] = {}
        for runway in runways:
            taxi_movement_per_flight[terminal][runway] = []
            for flight in flights:
                variable = solver.IntVar(0, 1, text + terminal + flight + runway)
                taxi_movement_per_flight[terminal][runway].append(variable)
    return taxi_movement_per_flight


taxi_movement_per_flight_arriving = create_taxi_movement_variables(terminals, flights, runways,
                                                                   "taxi_movement_per_flight_arriving")

taxi_movement_per_flight_departing = create_taxi_movement_variables(terminals, flights, runways,
                                                                    "taxi_movement_per_flight_departing")

""" PART D -  implement the constraints that ensure that every flight has exactly two taxi movements  """
""" PART E -  implement the constraints that ensure that the taxi movements of a flight are to and from the allocated terminal """
""" PART F -  implement the constraints that ensure that the taxi movements of a flight include the allocated arrival and departure runways """


def ensure_taxi_one_movement(taxi_movement_per_flight, terminal_allocations, runway_allocations, terminals, runways,
                             flights):
    for terminal in terminals:
        for runway in runways:
            for i, flight in zip(range(len(flights)), flights):
                variable = taxi_movement_per_flight[terminal][runway][i]
                solver.Add(variable <= terminal_allocations[flight][terminal])
                solver.Add(variable <= runway_allocations[flight][runway])
                solver.Add(variable >= terminal_allocations[flight][terminal] + runway_allocations[flight][runway] - 1)


ensure_taxi_one_movement(taxi_movement_per_flight_arriving, terminal_allocations, arrival_runway_allocations, terminals,
                         runways, flights)

ensure_taxi_one_movement(taxi_movement_per_flight_departing, terminal_allocations, departure_runway_allocations,
                         terminals, runways, flights)

# In[9]:

# create and set a variable fr departure time of each flight
per_flight_departure_time = {}
for flight in flights:
    variables = {}
    for time in set_of_time_slots:
        t_str = str(time)
        variables[str(time)] = solver.IntVar(0, 1, flight + t_str + 'per_flight_departure_time')
        if flight_schedule.loc[flight, 'Departure'] == time:
            solver.Add(variables[t_str] == 1)
        else:
            solver.Add(variables[t_str] == 0)
    per_flight_departure_time[flight] = variables

# In[10]:

# create and set a variable fr arrival time of each flight
per_flight_arrival_times = {}
for flight in flights:
    variables = {}
    for time in set_of_time_slots:
        t_str = str(time)
        variables[str(time)] = solver.IntVar(0, 1, flight + t_str + 'per_flight_arrival_times')
        if flight_schedule.loc[flight, 'Arrival'] == time:
            solver.Add(variables[t_str] == 1)
        else:
            solver.Add(variables[t_str] == 0)
    per_flight_arrival_times[flight] = variables

# create and set a variable fr all time slots a flight will be at the airport
times_when_flight_using_airport = {}
for flight in flights:
    variables = {}
    for time in set_of_time_slots:
        t_str = str(time)
        variables[t_str] = solver.IntVar(0, 1, flight + t_str + 'times_when_flight_using_airport')
        if flight_schedule.loc[flight, 'Departure'] > time >= flight_schedule.loc[flight, 'Arrival']:
            solver.Add(variables[t_str] == 1)
        else:
            solver.Add(variables[t_str] == 0)
    times_when_flight_using_airport[flight] = variables

# In[13]:

""" PART J  - implement the constraints that ensure that the terminal capacities are not exceeded  """
num_of_flights_per_term_per_time = {}
for terminal in terminals:
    for time in set_of_time_slots:
        time = str(time)
        num_of_flights_per_term_per_time[(terminal, time)] = []
        for flight in flights:
            variable = solver.IntVar(0, 1, flight + terminal + time + "num_of_flights_per_term_per_time")
            solver.Add(variable >= terminal_allocations[flight][terminal] + times_when_flight_using_airport[flight][time] - 1)
            solver.Add(variable <= terminal_allocations[flight][terminal])
            solver.Add(variable <= times_when_flight_using_airport[flight][time])
            num_of_flights_per_term_per_time[(terminal, time)].append(variable)
        capacity = terminal_capacity.loc[terminal, "Gates"]
        solver.Add(solver.Sum(num_of_flights_per_term_per_time[(terminal, time)]) <= capacity)



# In[14]:

""" PART I  - implement the constraints that ensure that no runway is used by more than one flight during each timeslot """
#At a given time  a flight cannot share the same runway when arriving or departing with another flight
for flight in flights:
    rest_flights = list(flights)
    rest_flights.remove(flight)
    for rest_flight in rest_flights:
        for runway in runways:
            for time in set_of_time_slots:
                time = str(time)
                solver.Add(
                    solver.Sum([per_flight_arrival_times[flight][time], per_flight_arrival_times[rest_flight][time], arrival_runway_allocations[flight][runway], arrival_runway_allocations[rest_flight][runway]                  
                                ]) <= 3)
                solver.Add(
                    solver.Sum([per_flight_arrival_times[flight][time], per_flight_departure_time[rest_flight][time], arrival_runway_allocations[flight][runway], departure_runway_allocations[rest_flight][runway]
                                ]) <= 3)
                solver.Add(
                    solver.Sum([per_flight_departure_time[rest_flight][time], per_flight_arrival_times[flight][time], departure_runway_allocations[rest_flight][runway], arrival_runway_allocations[flight][runway] 
                                ]) <= 3)

                solver.Add(
                    solver.Sum([per_flight_departure_time[flight][time], per_flight_departure_time[rest_flight][time], departure_runway_allocations[flight][runway], departure_runway_allocations[rest_flight][runway]
                                ]) <= 3)


# In[16]:

""" Calculate total taxi movemnt for arrivals and departures """
def calculate_taxi_movement(taxi_movement_per_flight, text, terminals, runways):
    total_taxi_movement = {}
    for terminal in terminals:
        total_taxi_movement[terminal] = {}
        for runway in runways:
            total_taxi_movement[terminal][runway] = solver.IntVar(0, infinity, terminal + runway + text)
            solver.Add(total_taxi_movement[terminal][runway] == solver.Sum(taxi_movement_per_flight[terminal][runway]))
    return total_taxi_movement


total_taxi_movement_arriving = calculate_taxi_movement(taxi_movement_per_flight_arriving, "total_taxi_movement_arriving", terminals,
                                                     runways)
total_taxi_movement_departing = calculate_taxi_movement(taxi_movement_per_flight_departing, "total_taxi_movement_departing",
                                                      terminals, runways)

# In[19]:
""" PART K - implement the objective function and solve linear program and determine the optimal total taxi distances for all flights """

distance = solver.Objective()
for flight in flights:
    for terminal in terminals:
        for runway in runways:
            distance.SetCoefficient(total_taxi_movement_arriving[terminal][runway],
                                    int(taxi_distances.loc[runway, terminal]))
            distance.SetCoefficient(total_taxi_movement_departing[terminal][runway],
                                    int(taxi_distances.loc[runway, terminal]))
print("Running...")
status = solver.Solve()

def part_K(runways, terminals, total_taxi_movement_arriving,
                         total_taxi_movement_departing):
    print("K")
    total_taxi_distance = 0
    for terminal in terminals:
        for runway in runways:
            total_taxi_distance += total_taxi_movement_arriving[terminal][runway].solution_value()
            total_taxi_distance += total_taxi_movement_departing[terminal][runway].solution_value()
    print("  Total Taxi Distance:", total_taxi_distance)



# In[20]:

""" PART L : Determine the arrival runway allocation ,the departure runway allocatio, and the terminal allocation for each flight. 
             Also determine the taxi distance for each flight """
def part_L(arrival_runway_allocations, departure_runway_allocations, terminal_allocations,flights, runways, terminals):
    taxi_dist = {}
    for f in flights:
        taxi_dist[f]={}
        
        for r in runways:
            if (arrival_runway_allocations[f][r].solution_value() == 1):
                taxi_dist[f]["Arrival"]=r
            if (departure_runway_allocations[f][r].solution_value() == 1):
                taxi_dist[f]["Departure"]=r
                
        for term in terminals:
            if terminal_allocations[f][term].solution_value() == 1:
                taxi_dist[f]["terminal"]=term
    
    
    for f, dic in taxi_dist.items():
        print("  ", f)
        print("     Arival Runway:", taxi_dist[f]["Arrival"],"     Departure Runway:", taxi_dist[f]["Departure"],"     Allocated Terminal:", taxi_dist[f]["terminal"],"     Total taxi Dist:", taxi_distances.loc[taxi_dist[f]["Arrival"],taxi_dist[f]["terminal"]] + taxi_distances.loc[taxi_dist[f]["Departure"],taxi_dist[f]["terminal"]])
       
        

# In[21]:

""" PART M : Determine for each time of the day how many gates are occupied at each terminal"""

def part_M(set_of_time_slots, terminals, num_of_flights_per_term_per_time):
                         
    print("M")
    
    for terminal in terminals:
        print("- ", terminal)
        for t in set_of_time_slots:
            total_fligts_using_terminal = 0
            for variable in num_of_flights_per_term_per_time[(terminal, str(t))]:
                total_fligts_using_terminal += variable.solution_value()
            print("     Time Slot:", str(t), "Gates Occupied:", int(total_fligts_using_terminal))
    


# In[22]:


if status == 0:
    
    print("Status: ",status,":SUccess")
    part_L(arrival_runway_allocations, departure_runway_allocations, terminal_allocations,flights, runways, terminals)
    part_M(set_of_time_slots, terminals, num_of_flights_per_term_per_time)
    part_K(runways, terminals, total_taxi_movement_arriving, total_taxi_movement_departing)
                        
else:  
    print("Status: ",status)
    print("Failed to find a optimal solution")

# In[ ]:
