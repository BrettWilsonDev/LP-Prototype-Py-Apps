import copy
import math


def testInput():
    goals = [
        # <= is 0 and >= is 1
        [300, 200, 20000, 0],
        [150, 100, 11000, 1],
        [3, 1, 200, 0],
    ]

    constraints = [
    ]

    goals = [
        # <= is 0 and >= is 1
        [12, 9, 15, 125, 1],
        [5, 3, 4, 40, 2],
        [5, 7, 8, 55, 0],
    ]

    constraints = [
    ]

    goals = [
        # <= is 0 and >= is 1 and == is 2
        [40, 30, 20, 100, 0],
        [2, 4, 3, 10, 2],
        [5, 8, 4, 30, 1],
    ]

    constraints = [
    ]

    return goals, constraints


def BuildFirstPreemptiveTableau(goalConstraints, constraints):
    tabSizeH = len(constraints) + len(goalConstraints) * 2
    tabSizeW = 1 + 1 + (len(goalConstraints) * 2) + \
        len(constraints) + (len(goalConstraints[-1]) - 2)

    penlites = len(goalConstraints)

    amtOfObjVars = (len(goalConstraints[-1]) - 2)

    tab = []

    tempGoalConstraints = []
    equalPositions = []
    for i in range(len(goalConstraints)):
        if goalConstraints[i][-1] == 2:
            tempGoalConstraints.append(goalConstraints[i])
            equalPositions.append(i)
            tabSizeH += 2
            tabSizeW += 2
            penlites += 1
            
    tempGoals = copy.deepcopy(goalConstraints)

    fixedEqualGoals = []
    for lst in tempGoalConstraints:
        # Copy the 1D list twice
        listCopy1 = lst[:]
        listCopy2 = lst[:]
        
        listCopy1[-1] = 0
        listCopy2[-1] = 1
        
        fixedEqualGoals.append(listCopy1)
        fixedEqualGoals.append(listCopy2)

    for i in range(len(equalPositions)):
        del goalConstraints[equalPositions[i]]
        goalConstraints.insert(equalPositions[i], fixedEqualGoals[i+1])
        goalConstraints.insert(equalPositions[i], fixedEqualGoals[i])

    # initialize table with empty rows
    for i in range(tabSizeH):
        tab.append([])

    # initialize table with zeros
    for i in range(tabSizeH):
        for j in range(tabSizeW):
            tab[i].append(0)

    # put in lhs in the z col
    for i in range(penlites):
        tab[i][0] = 1

    # put in penlites
    gCtr = amtOfObjVars + 1
    for i in range(len(goalConstraints)):
        if goalConstraints[i][-1] == 0:
            tab[i][gCtr + 1] = -1
        elif goalConstraints[i][-1] == 1:
            tab[i][gCtr] = -1
        gCtr += 2

    # put in goal constraints
    for i in range(penlites, tabSizeH - len(constraints)):
        for j in range(1, amtOfObjVars + 1):
            tab[i][-1] = goalConstraints[i - penlites][-2]
            tab[i][j] = goalConstraints[i - penlites][j - 1]

    # put in normal constraints
    for i in range(tabSizeH - len(constraints), tabSizeH):
        for j in range(1, (len(constraints[-1]) - 2) + 1):
            tab[i][-1] = constraints[i - (tabSizeH - len(constraints))][-2]
            tab[i][j] = constraints[i - (tabSizeH - len(constraints))][j - 1]

    # put the 1 -1 for goal constraints in
    onesCtr = amtOfObjVars + 1
    for i in range(penlites, tabSizeH - len(constraints)):
        tab[i][onesCtr] = 1
        tab[i][onesCtr + 1] = -1
        onesCtr += 2

    # make new tab
    newTab = copy.deepcopy(tab)

    gCtr = len(goalConstraints)
    for i in range(penlites):
        for j in range(len(tab[i])):
            if goalConstraints[i][-1] == 0:
                newTab[i][j] = tab[i + penlites][j] - tab[i][j]
            elif goalConstraints[i][-1] == 1:
                newTab[i][j] = tab[i + penlites][j] + tab[i][j]
        gCtr += 1


    gNegCtr = 0
    for i in range(len(tempGoals)):
        if tempGoals[i][-1] == 2:
            for k in range(len(newTab)):
                del newTab[k][-(i + 3 + gNegCtr)]
                del newTab[k][-(i + 2 + gNegCtr)]

                del tab[k][-(i + 3 + gNegCtr)]
                del tab[k][-(i + 2 + gNegCtr)]

            newTab[i+1][-(i + 2 + gNegCtr)] = -1

            tab[i+1][-(i + 3 + gNegCtr)] = -1

            del newTab[-(i + 1)]
            del tab[-(i + 1)]

        gNegCtr += 1
                   
    return tab, newTab, penlites


def DoPivotOperations(tab, conStartRow, zRow, tabNum=1):
    oldTab = copy.deepcopy(tab)
    newTab = []

    newTab = [[0 for _ in row] for row in oldTab]

    # exclude the z col and rhs
    currentZRow = zRow
    currentZ = tab[currentZRow][:-1]
    currentZ[0] = 0

    # print(currentZ)

    # find the largest z and its index for the pivot col
    largestZ = max(currentZ)
    pivotCol = currentZ.index(largestZ)

    # find the pivot row
    useZero = False
    ratios = []
    for i in range(conStartRow, len(tab)):
        div = tab[i][pivotCol]
        if div == 0:
            ratios.append(float('inf'))
        else:
            ratios.append(tab[i][-1] / tab[i][pivotCol])

            if (tab[i][-1] / tab[i][pivotCol]) == 0 and ((tab[i][pivotCol]) == abs(tab[i][pivotCol])):
                useZero = True


    if useZero:
        positiveRatios = [ratio for ratio in ratios if ratio >= 0]
    else:
        positiveRatios = [ratio for ratio in ratios if ratio > 0]

    for i in range(len(positiveRatios)):
        if positiveRatios[i] == float('inf'):
            del positiveRatios[i]

    pivotRow = ratios.index(min(positiveRatios))
    pivotRow += conStartRow

    divNumber = tab[pivotRow][pivotCol]

    for i in range(len(tab)):
        for j in range(len(tab[i])):
            newTab[pivotRow][j] = tab[pivotRow][j] / divNumber
            if newTab[pivotRow][j] == -0.0:
                newTab[pivotRow][j] = 0.0

    # do the pivot operations
    # the formula: Element_New_Table((i, j)) = Element_Old_Table((i, j)) - (Element_Old_Table((i, Pivot_column)) * Element_New_Table((Pivot_Row, j)))
    for i in range(len(tab)):
        for j in range(len(tab[i])):
            if i == pivotRow:
                continue

            newTab[i][j] = oldTab[i][j] - \
                (oldTab[i][pivotCol] * newTab[pivotRow][j])

    newTab = [[0.0 if abs(val) < 1e-10 else val for val in sublist]
              for sublist in newTab]

    for items in newTab:
        for i, item in enumerate(items):
            if item == 0.0 and math.copysign(1, item) == -1:
                newTab[i][i] = abs(item)

    zRhs = []

    for i in range(conStartRow):
        zRhs.append(newTab[i][-1])

    # print(f"pivoting on table {tabNum}\nIn row {
    #       pivotRow + 1} and col {pivotCol + 1 - 1}\n")

    return newTab, zRhs


def DoPreemptive(goals, constraints):
    a = copy.deepcopy(goals)
    b = copy.deepcopy(constraints)
    originalGoals = copy.deepcopy(goals)
    tableaus = []
    firstTab, FormulatedTab, conStartRow = BuildFirstPreemptiveTableau(
        a, b)
    tableaus.append(firstTab)
    tableaus.append(FormulatedTab)

    tempGoalLst = []
    for goal in goals:
        tempGoalLst.append(goal)
        if goal[-1] == 2:
            tempGoalLst.append(goal)

    goals = tempGoalLst

    zRhs = []
    currentZRow = 0

    for i in range(conStartRow):
        zRhs.append(tableaus[-1][i][-1])

    lenObj = len(goals[-1]) - 2

    # sign list to compare to and initial met goal state
    # the order of signs for example g- g+ TODO add option to swap the two
    metGoals = []
    signLst = []
    for i in range(len(goals)):
        signLst.append(-1)
        signLst.append(1)
        metGoals.append(False)

    metGoals[0] = True

    highestTrueIndex = -1
    currentTrueIndex = -1

    isLoopRunning = True

    ctr = 0
    while ctr != 100 and isLoopRunning:
        basicVarLst = []
        for k in range(lenObj + 1, len(tableaus[-1][-1]) - 1):
            columnIndex = k
            tempLst = []

            for i in range(conStartRow, len(tableaus[-1])):
                columnValue = tableaus[-1][i][columnIndex]
                tempLst.append(columnValue)
            if (sum(tempLst) == 1):
                basicVarLst.append(tempLst)
            else:
                basicVarLst.append(None)

        goalRhs = []
        for i in range(len(goals)):
            goalRhs.append(None)


        # get the rhs from basic cols
        for i in range(len(basicVarLst)):
            if basicVarLst[i] is not None:
                sign = signLst[i]
                for j in range(len(basicVarLst[i])):
                    if basicVarLst[i][j] == 1.0:
                        if sign == 1:
                            goalRhs[j] = (tableaus[-1][j + conStartRow][-1])
                        elif sign == -1:
                            goalRhs[j] = (-tableaus[-1][j + conStartRow][-1])

        sortedLst = []

        # sort according to where goals are
        sortCtr = 0
        for k in range(0, len(basicVarLst), 2):
            if k + 1 < len(basicVarLst):
                if basicVarLst[k] is None and basicVarLst[k + 1] is None:
                    sortedLst.append(None)
                else:
                    if basicVarLst[k] is not None:
                        sortedLst.append(basicVarLst[k])
                    if basicVarLst[k + 1] is not None:
                        sortedLst.append(basicVarLst[k + 1])
            sortCtr += 1

    
        tempLst = []
        for i in range(len(goalRhs)):
            tempLst.append(None)

        for i in range(len(sortedLst)):
            if sortedLst[i] is not None:
                for j in range(len(sortedLst[i])):
                    if sortedLst[i][j] == 1:
                        tempLst[i] = goalRhs[j]

        goalRhs = tempLst

        for i in range(len(goalRhs)):
            if goalRhs[i] == -0.0:
                goalRhs[i] = 0.0

        for i in range(len(originalGoals)):
            if originalGoals[i][-1] == 2:
                # print(goalRhs[i])
                if goalRhs[i] is not None:
                    goalRhs.insert(i, -goalRhs[i])
                else:
                    goalRhs.insert(i, goalRhs[i])
                goalRhs.pop()       
                
        for i in range(len(goalRhs)):
            # I hope dearly that this mathematical algorithm acquaints for both non-basic columns being optimal.
            if goalRhs[i] == None:
                metGoals[i] = True
                continue
                
            # TODO display the met state in gui
            # check if goal is met based on constraints conditions
            if goals[i][-1] == 0:
                if (goalRhs[i] + goals[i][-2]) <= goals[i][-2]:
                    # print("Goal {} met".format(i + 1))
                    metGoals[i] = True
                else:
                    # print("Goal {} not met".format(i + 1))
                    metGoals[i] = False
            elif goals[i][-1] == 1:
                if (goalRhs[i] + goals[i][-2]) >= goals[i][-2]:
                    # print("Goal {} met".format(i + 1))
                    metGoals[i] = True
                else:
                    # print("Goal {} not met".format(i + 1))
                    metGoals[i] = False
            elif goals[i][-1] == 2:
                # TODO display the met state in gui but not from here from below for equalities
                if (goalRhs[i] == goals[i][-2]):
                    # print("Goal {} met".format(i + 1))
                    metGoals[i] = True
                else:
                    # print("Goal {} not met".format(i + 1))
                    metGoals[i] = False

        
        # 0 in top rhs means goal met regardless of bottom rhs
        for i in range(len(zRhs)):
            if zRhs[i] == 0.0:
                metGoals[i] = True

        for i in range(len(metGoals)):
            if metGoals[i] == False:
                currentZRow = i
                break
        
        tempMetGoals = copy.deepcopy(metGoals)
        for i in range(len(originalGoals)):
            if originalGoals[i][-1] == 2:
                
                # TODO display the met state in gui
                if not ((metGoals[i]) and (metGoals[i+1])):
                    # print("Goal {} not met".format(i + 1))
                    metGoals[i] = False
                    metGoals[i+1] = False
                else:
                    # print("Goal {} met".format(i + 1))
                    metGoals[i] = True
                    metGoals[i+1] = True  

        for i in range(len(metGoals)):
            if not metGoals[i]:
                currentTrueIndex = i
                break

        if currentTrueIndex > highestTrueIndex:
            highestTrueIndex = currentTrueIndex
        else:
            if highestTrueIndex > currentTrueIndex:
                break

        if all(metGoals):
            isLoopRunning = False

        metGoals = copy.deepcopy(tempMetGoals)

        newTab, zRhs = DoPivotOperations(tableaus[-1], conStartRow, currentZRow, 1)
        tableaus.append(newTab)

        print()

        ctr += 1

    for i in range(len(tableaus)):
        print("Tableau {}".format(i + 1))
        for j in range(len(tableaus[i])):
            for k in range(len(tableaus[i][j])):
                print("{:10.3f}".format(tableaus[i][j][k]), end=" ")
            print()
        print()


def main():
    goals, constraints = testInput()

    DoPreemptive(goals, constraints)

main()
