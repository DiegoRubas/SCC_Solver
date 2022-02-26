import os

import pandas as pd
from pulp import LpProblem, LpMaximize, LpBinary, LpVariable, GLPK

MISSIONS = ["Cordeel", "Dynafin", "Pfizer", "Yakima Chief", "Waterland"]
NO_STUDENTS_PER_MISSION = 6

df = pd.read_excel(r'/Users/nikorubas/Documents/GitHub/SCC_Solver/data/data.xlsx')
df = df.sort_values('Score', ascending=False)

no_students = df.shape[0]
no_missions = len(MISSIONS)

preferences = []
for i, row in df.iterrows():
    student_preference = [0 for j in range(5)]
    if row['1st choice'] in MISSIONS:
        student_preference[MISSIONS.index(row['1st choice'])] = 4
    if row['2nd choice'] in MISSIONS:
        student_preference[MISSIONS.index(row['2nd choice'])] = 2
    if row['3rd choice'] in MISSIONS:
        student_preference[MISSIONS.index(row['3rd choice'])] = 1
    preferences.append(student_preference)

scores = []
for i, row in df.iterrows():
    scores.append(row['Score'])

# ------------------- MEET GLPK ----------------------

# Problem
problem = LpProblem("SCC_Solver", sense=LpMaximize)

# Variables
x_ij = [
    [LpVariable("x_{}_{}".format(i, j), cat=LpBinary)
     for j in range(no_missions)]
    for i in range(no_students)
]

# Constraints

# 1 : Number of students for mission j is not bigger than the max number of students allowed for mission j
for j in range(no_missions):
    no_students_for_mission_j = 0
    for i in range(no_students):
        no_students_for_mission_j += x_ij[i][j]

    problem += (no_students_for_mission_j == NO_STUDENTS_PER_MISSION, "MaxStudents_{}".format(j))

# 2 A student is given exactly 1 slot
for i in range(no_students):
    n_missions_for_student_i = 0
    for j in range(no_missions):
        n_missions_for_student_i += x_ij[i][j]

    problem += (n_missions_for_student_i <= 1, "OneSlot_{}".format(i))

# Economic function

cost = 0
for i in range(no_students):
    for j in range(no_missions):
        # cost += x_ij[i][j]*preferences[i][j]
        # cost += x_ij[i][j]*scores[i]
        cost += x_ij[i][j]*preferences[i][j]*scores[i]

problem += cost, 'Objective Function'

solution = problem.solve(solver=GLPK(keepFiles=True, timeLimit=30))

## Problem solution analysis
# matching of student ID and location in the array

result = df.copy()
result.drop(inplace=True, columns=['Score', 'University', 'Gender', 'Year', 'Degree', 'Exchange'])

i = 0
for idx, row in result.iterrows():
    for choice in ['1st choice', '2nd choice', '3rd choice']:
        if row[choice] not in MISSIONS or x_ij[i][MISSIONS.index(row[choice])].varValue == 0:
            result.loc[idx, choice] = 'X'
    i += 1

student_mission_dict = dict()
mission_teams = dict()
for m in MISSIONS:
    mission_teams[m] = []
for i in range(no_students):
    for j in range(no_missions):
        if x_ij[i][j].varValue == 1:
            student_mission_dict[df.iloc[i]['Candidate Name']] = MISSIONS[j]
            mission_teams[MISSIONS[j]].append(df.iloc[i]['Candidate Name'])


student_mission_df = pd.DataFrame({
    "Student": student_mission_dict.keys(),
    "Mission": student_mission_dict.values()
})

mission_teams_df = pd.DataFrame({
    "Mission": mission_teams.keys(),
    "Students": mission_teams.values()
})

student_mission_df.to_csv("../out/Student_mission.csv", index=False)
mission_teams_df.to_csv("../out/Mission_teams.csv", index=False)
result.to_csv("../out/Result.csv", index=False)
