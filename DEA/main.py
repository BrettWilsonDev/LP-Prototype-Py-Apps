import dualSimplex

import copy

from pulp import LpMaximize, LpProblem, LpVariable


def testInput():
    LpInputs = [
        [5, 14],
        [8, 15],
        [7, 12],
    ]

    LpOutputs = [
        [9, 4, 16],
        [5, 7, 10],
        [4, 9, 13],
    ]

    return LpInputs, LpOutputs

def buildTable(currentSelection = 0):

    # currentSelection = 0

    LpInputs, LpOutputs = testInput()

    tabWLen = len(LpInputs[-1]) + len(LpOutputs[-1])
    print(tabWLen)

    tabHLen = tabWLen + 1 + 1 + len(LpInputs)
    print(tabHLen)

    # build bottom rows
    bottomRows = []
    for i in range(len(LpInputs) + 2):
            row = [0] * (len(LpInputs) + 2)
            row[i] = 1
            bottomRows.append(row)

    # build top rows
    topRows = []
    for i in range(len(LpOutputs)):
        topRows.append(copy.deepcopy(LpOutputs[i]))

    for i in range(len(LpInputs)):
        for j in range(len(LpInputs[i])):
            topRows[i].append(copy.deepcopy(-LpInputs[i][j]))

    print(topRows)

    # build middle row
    middleRow = []
    for i in range(tabWLen):
        middleRow.append(0)

    # TODO clean up brain not braining
    currentMiddleRow = LpInputs[currentSelection]
    # print(currentMiddleRow)
    for i in range(len(currentMiddleRow)):
         del middleRow[i]
         middleRow.append(currentMiddleRow[i])

    print(middleRow) 

    # zRow
    zRow = copy.deepcopy(LpOutputs[currentSelection])

    for i in range(tabWLen - len(zRow)):
        zRow.append(0)

    print(zRow)

    print()
    table = []
    table.append(zRow)
    for i in range(len(topRows)):
        table.append(copy.deepcopy(topRows[i]))

    table.append(middleRow)

    for i in range(len(bottomRows)):
        table.append(bottomRows[i])

    print(table)
    
    # print()
    # for i in range(len(table)):
    #     for j in range(len(table[i])):
    #         # print(table[i][j], end=" ")
    #         print("{:10.3f}".format(table[i][j]), end=" ")
    #     print()

    objfunc = LpOutputs[currentSelection]

    # print(objfunc)

    constraints = []
    for i in range(len(topRows)):
        constraints.append(copy.deepcopy(topRows[i]))
        constraints[i].append(0)
        constraints[i].append(0)

    tempMiddleRow = copy.deepcopy(middleRow)
    tempMiddleRow.append(1)
    tempMiddleRow.append(0)
    constraints.append(tempMiddleRow)
    tempMiddleRow = copy.deepcopy(middleRow)
    tempMiddleRow.append(1)
    tempMiddleRow.append(1)
    constraints.append(tempMiddleRow)

    # constraints.append(middleRow)

    tempCons = []
    for i in range(len(bottomRows)):
        tempCons.append(copy.deepcopy(bottomRows[i]))
        tempCons[i].append(0.0001)
        tempCons[i].append(1)
        constraints.append(tempCons[i])

    print(constraints)
    print()

    # return table, objfunc, constraints
    return table, zRow, constraints

def SolveTable(table, objfunc, constraints):
    # print(objfunc, constraints)

    print(objfunc)
    for i in range(len(constraints)):
        print(constraints[i])

    tableaus, changingVars, optimalSolution = dualSimplex.DoDualSimplex(objfunc, constraints, 0)
    print(changingVars, optimalSolution)

    mathCons = []
    for i in range(len(constraints)):
        mathCons.append([])
        for j in range(len(constraints[i]) - 1):
            mathCons[i].append(copy.deepcopy(constraints[i][j]))

    cellRef = []
    # sum([a * b for a, b in zip(dualChangingVars, dualConstraintsLhs[i])])
    for i in range(len(mathCons)):
        # print(mathCons[i])
        tSum = sum([a * b for a, b in zip(changingVars, mathCons[i])])
        # print(tSum)

    print()
    for i in range(len(tableaus[-1])):
        for j in range(len(tableaus[-1][i])):
            print(tableaus[-1][i][j], end=" ")
        print()

def main():
    # buildTable()
    SolveTable(buildTable()[0], buildTable()[1], buildTable()[2])

main()
