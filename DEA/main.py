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

def buildTable(LpInputs, LpOutputs, currentSelection = 0):
    tabWLen = len(LpInputs[-1]) + len(LpOutputs[-1])

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

    # build middle row
    middleRow = []
    for i in range(tabWLen):
        middleRow.append(0)

    currentMiddleRow = LpInputs[currentSelection]
    for i in range(len(currentMiddleRow)):
         del middleRow[i]
         middleRow.append(currentMiddleRow[i])

    zRow = copy.deepcopy(LpOutputs[currentSelection])

    for i in range(tabWLen - len(zRow)):
        zRow.append(0)

    table = []
    table.append(zRow)
    for i in range(len(topRows)):
        table.append(copy.deepcopy(topRows[i]))

    table.append(middleRow)

    for i in range(len(bottomRows)):
        table.append(bottomRows[i])


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

    conRow = LpInputs[currentSelection]
    
    return table, zRow, constraints, conRow

def SolveTable(table, objfunc, constraints, conRow):
    tableaus, changingVars, optimalSolution = dualSimplex.DoDualSimplex(objfunc, constraints, 0)
    print(changingVars, optimalSolution)

    mathCons = []
    for i in range(len(constraints)):
        mathCons.append([])
        for j in range(len(constraints[i]) - 1):
            mathCons[i].append(copy.deepcopy(constraints[i][j]))

    # get the cell ref for display purposes
    cellRef = []
    cellRef.append(optimalSolution)
    for i in range(len(mathCons)):
        tSum = sum([a * b for a, b in zip(changingVars, mathCons[i])])
        cellRef.append(tSum)

    # get the len of the outputs
    objFuncLen = 0  
    for i in range(len(objfunc)):
        if objfunc[i] != 0:
            objFuncLen += 1

    # get the outputs multiplied by the changing vars
    outputRange = []
    for i in range(objFuncLen):
        outputRange.append(objfunc[i] * changingVars[i])

    # get the inputs multiplied by the changing vars
    inputRange = []
    for i in range(len(objfunc) - objFuncLen):
        inputRange.append(conRow[i] * changingVars[i + objFuncLen])

    # get the totals
    outputTotal = sum(outputRange)
    inputTotal = sum(inputRange)

    return outputTotal, inputTotal, outputRange, inputRange, cellRef, changingVars

def DoDEA():
    LpInputs, LpOutputs = testInput()

    tables = []
    allRangesO = []
    allRangesI = []
    allOutputTotals = []
    allInputTotals = []

    for i in range(len(LpInputs)):
        table, objfunc, constraints, conRow = buildTable(LpInputs, LpOutputs, i)
        outputTotal, inputTotal, outputRange, inputRange, cellRef, changingVars = SolveTable(table, objfunc, constraints, conRow)

        allRangesO.append(outputRange)
        allRangesI.append(inputRange)

        allOutputTotals.append(outputTotal)
        allInputTotals.append(inputTotal)

        # add the cell ref to the table
        for j in range(len(cellRef) - 1):
            table[j].append(cellRef[j])

        # add the sign
        for j in range(len(LpOutputs) + 1):
            table[j].append(0)
        table[len(LpOutputs) + 1].append(2)
        for j in range((len(LpInputs[-1]) + len(LpOutputs[-1]))):
            table[j + len(LpOutputs) + 2].append(1)

        # add the rhs
        for j in range(len(LpOutputs) + 1):
            table[j].append(0)
        table[len(LpOutputs) + 1].append(1)
        for j in range((len(LpInputs[-1]) + len(LpOutputs[-1]))):
            table[j + len(LpOutputs) + 2].append(0.0001)

        tables.append(table)

    # build header
    header = []
    for i in range(len(LpOutputs[-1])):
        header.append("o" + str(i + 1))
    for i in range(len(LpInputs[-1])):
        header.append("i" + str(i + 1))
    header.append("ref")
    header.append("sign")
    header.append("rhs")


    for i in range(len(tables)):
        for cvCtr in range(len(changingVars)):
            print("{:10.4f}".format(changingVars[cvCtr]), end=" ")
        print()
        for hctr in range(len(header)):
            print("    {:6}".format(header[hctr]), end=" ")
        print()
        for j in range(len(tables[i])):
            for k in range(len(tables[i][j])):
                if k == (len(LpOutputs[-1]) + len(LpInputs[-1]) + 1):
                    if tables[i][j][k] == 0:
                        print("{:10}".format("    <="), end=" ")
                    elif tables[i][j][k] == 1:
                        print("{:10}".format("    >="), end=" ")
                    else:
                        print("{:10}".format("     ="), end=" ")
                else:
                    print("{:10.4f}".format(tables[i][j][k]), end=" ")
            print()

        print("\nranges:")
        print()
        for j in range(len(LpOutputs[-1])):
            print("  {:8}".format("o" + str(j + 1)), end=" ")

        print()
        for j in range(len(LpOutputs[-1])):
            print("{:10.6f}".format(allRangesO[i][j]), end=" ")
        print(f"  Output total: {allOutputTotals[i]}", end=" ")

        print("\n")
        for j in range(len(LpInputs[-1])):
            print("  {:8}".format("i" + str(j + 1)), end=" ")

        print()
        for j in range(len(LpInputs[-1])):
            print("{:10.6f}".format(allRangesI[i][j]), end=" ")
        print(f"   Input total: {allInputTotals[i]}", end=" ")
                
        print(f"\n\nTotals:\n\n{allOutputTotals[i]}\ndivided by\n{allInputTotals[i]}\n\n= {allOutputTotals[i] / allInputTotals[i]}")
        print()

def main():
    DoDEA()

main()
