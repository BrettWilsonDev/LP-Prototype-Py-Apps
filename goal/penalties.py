import copy
import math


def testInput():
    goals = [
        # <= is 0 and >= is 1 and == is 2
        # [40, 30, 20, 100, 0],
        # [2, 4, 3, 10, 2],
        # [5, 8, 4, 30, 1],
        [40, 30, 20, 100, 0],
        [2, 4, 3, 10, 2],
        [5, 8, 4, 30, 1],
        # [2, 4, 3, 10, 2],
    ]

    constraints = [
    ]

    penalties = [5, 8, 12, 15]

    orderOverride = [2, 1, 0]
    # orderOverride = [3, 1, 2, 0]
    # orderOverride = []

    # penalties = [5, 8, 12, 15, 8, 12]
    # penalties = [5, 8, 12, 8, 12, 15]
    # penalties = [5, 8, 12, 15, 8, 12,]
    # penalties = [8, 12, 8, 12]
    # penalties = [2, 4, 2, 4]

    # goals = [
    #     # <= is 0 and >= is 1 and == is 2
    #     [7, 3, 40, 1],
    #     [10, 5, 60, 1],
    #     [5, 4, 35, 1],
    # ]

    # constraints = [
    #     [100, 60, 600, 0]
    # ]

    # penalties = [200, 100, 50]

    # goals = [
    #     # <= is 0 and >= is 1 and == is 2
    #     [12, 9, 15, 125, 1],
    #     [5, 3, 4, 40, 2],
    #     [5, 7, 8, 55, 0],
    # ]

    # constraints = [
    # ]

    # penalties = [5, 4, 2, 3]

    # orderOverride = []

    return goals, constraints, penalties, orderOverride


def BuildFirstPenlitesTableau(goalConstraints, constraints, penlites, orderOverride=[]):
    oldTab = []
    newTab = []
    conStart = 0

    # print(penlites, goalConstraints, constraints)

    # hight = (goals + goalConstraints) = goals * 2 + constraints
    tabSizeH = (len(goalConstraints) * 2) + len(constraints)

    # width = z + rhs + x + (g+,-) * 2 + slack
    tabSizeW = 1 + 1 + \
        (len(goalConstraints[-1]) - 2) + \
        (len(goalConstraints) * 2) + len(constraints)

    amtOfObjVars = (len(goalConstraints[-1]) - 2)
    amtOfGoals = len(goalConstraints)

    # fix the equalities constraints sizes
    for i in range(len(goalConstraints)):
        if goalConstraints[i][-1] == 2:
            tabSizeH += 1
            amtOfGoals += 1

    # initialize table with empty rows
    for i in range(tabSizeH):
        oldTab.append([])

    # initialize table with zeros
    for i in range(tabSizeH):
        for j in range(tabSizeW):
            oldTab[i].append(0)

    # put in lhs in the z col
    for i in range(amtOfGoals):
        oldTab[i][0] = 1

    # TODO keep an eye on the placement of the penalties for goal 2+ 2-
    # put in penlites spots
    gCtr = amtOfObjVars + 1
    ExtraCtr = 0
    for i in range(len(goalConstraints)):
        if goalConstraints[i][-1] == 0:
            oldTab[i + ExtraCtr][gCtr + 1] = -1
        elif goalConstraints[i][-1] == 1:
            oldTab[i + ExtraCtr][gCtr] = -1
        elif goalConstraints[i][-1] == 2:
            oldTab[i + ExtraCtr][gCtr] = -1
            oldTab[i + 1 + ExtraCtr][gCtr + 1] = -1
            ExtraCtr += 1
        gCtr += 2

    # put in penlites values or leave as -1
    if len(penlites) != 0:
        for i in range(len(oldTab)):
            for j in range(len(oldTab[i])):
                if oldTab[i][j] == -1:
                    oldTab[i][j] = -penlites[i]

    # put in the slacks
    for i in range(len(constraints)):
        if constraints[i][-1] == 0:
            oldTab[tabSizeH - i - 1][-(i+2)] = 1
        elif constraints[i][-1] == 1:
            oldTab[tabSizeH - i - 1][-(i+2)] = -1

    # put the 1 -1 for goal constraints in
    onesCtr = amtOfObjVars + 1
    for i in range(amtOfGoals, tabSizeH - len(constraints)):
        oldTab[i][onesCtr] = 1
        oldTab[i][onesCtr + 1] = -1
        onesCtr += 2

    # put in goal constraints
    for i in range(len(goalConstraints)):
        for j in range(amtOfObjVars):
            oldTab[i + amtOfGoals][j + 1] = goalConstraints[i][j]  # lhs
            oldTab[i + amtOfGoals][-1] = goalConstraints[i][-2]  # rhs

    # put in constraints
    for i in range(len(constraints)):
        for j in range(amtOfObjVars):
            oldTab[i + amtOfGoals +
                   len(goalConstraints)][j + 1] = constraints[i][j]  # lhs
            oldTab[i + amtOfGoals +
                   len(goalConstraints)][-1] = constraints[i][-2]  # rhs

    # for j in range(len(oldTab)):
    #     for k in range(len(oldTab[j])):
    #         print("{:10.3f}".format(oldTab[j][k]), end=" ")
    #     print()
    # print()

    # first tab done move on to second tab
    newTab = copy.deepcopy(oldTab)

    # rows at the top of the old table are the goals
    topRows = []
    for i in range(amtOfGoals):
        topRows.append([])
        for j in range(len(oldTab[i])):
            topRows[i].append(oldTab[i][j])

    # rows at the bottom of the old table are the goal constraints
    bottomRows = []
    for i in range(len(goalConstraints)):
        bottomRows.append([])
        for j in range(len(oldTab[i])):
            bottomRows[i].append(oldTab[i + amtOfGoals][j])

    # fix the equalities issues by duplicating the goal constraint rows that belong to the equalities
    tempBottomRows = []
    for i in range(len(goalConstraints)):
        if goalConstraints[i][-1] == 2:
            listCopy = bottomRows[i][:]

            tempBottomRows.append(listCopy)
            tempBottomRows.append(listCopy)
        else:
            tempBottomRows.append(bottomRows[i])

    bottomRows = tempBottomRows

    backUpGoals = copy.deepcopy(goalConstraints)
    # fix the equalities issues by duplicating the goal constraint rows that belong to the equalities
    tempGoals = []
    for goal in goalConstraints:
        if goal[-1] == 2:
            listCopy1 = goal[:]
            listCopy2 = goal[:]

            listCopy1[-1] = 0
            listCopy2[-1] = 1

            tempGoals.append(listCopy2)
            tempGoals.append(listCopy1)
        else:
            tempGoals.append(goal)

    goalConstraints = tempGoals

    # keep in mind this is penalties initial tab calculations

    # calculate the new table goal rows
    for i in range(len(goalConstraints)):
        for j in range(len(newTab[i])):
            if goalConstraints[i][-1] == 0:
                newTab[i][j] = -1 * \
                    (topRows[i][j] - (bottomRows[i][j] * penlites[i]))
            elif goalConstraints[i][-1] == 1:
                newTab[i][j] = (
                    topRows[i][j] + (bottomRows[i][j] * penlites[i]))

    # fix the order of the equalities
    equalCtr = 0
    for i in range(len(backUpGoals)):
        if backUpGoals[i][-1] == 2:
            tempRow = newTab[i + equalCtr]
            newTab[i + equalCtr] = newTab[i + 1 + equalCtr]
            newTab[i + 1 + equalCtr] = tempRow

            equalCtr += 1

    # reorder the goals according to user input
    if orderOverride != []:
        tempNewTab = []
        for i in range(len(orderOverride)):
            tempRow = newTab[orderOverride[i]]
            tempNewTab.append(tempRow)

        for i in range(len(tempNewTab)):
            newTab[i] = tempNewTab[i]

    # print()
    # for j in range(len(newTab)):
    #     for k in range(len(newTab[j])):
    #         print("{:10.3f}".format(newTab[j][k]), end=" ")
    #     print()
    # print()

    conStart = amtOfGoals
    return oldTab, newTab, conStart


def DoPivotOperations(tab, conStartRow, zRow, tabNum=1):
    # print(zRow)
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

    # print(positiveRatios)
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
        #   pivotRow + 1} and col {pivotCol + 1}\n")

    return newTab, zRhs


def DoPenalties(goals, constraints, penalties, orderOverride=[]):
    a = copy.deepcopy(goals)
    b = copy.deepcopy(constraints)
    c = copy.deepcopy(penalties)
    originalGoals = copy.deepcopy(goals)
    tableaus = []

    expandedOrder = copy.deepcopy(orderOverride)

    # account for the equalities
    if orderOverride != []:
        # order goals according to the override order
        overrideGoals = []
        for i in range(len(originalGoals)):
            overrideGoals.append(originalGoals[orderOverride[i]])

        expandedOrder = copy.deepcopy(orderOverride)
        for i in orderOverride:
            if overrideGoals[i][-1] == 2:
                expandedOrder.insert(i + 1, orderOverride[i] + 1)

    # fix the order from dupes made due to equalities
    seen = set()
    for i in range(len(expandedOrder)):
        if expandedOrder[i] in seen or expandedOrder[i] in expandedOrder[i+1:]:
            expandedOrder[i] += 1
            # print(expandedOrder[i+1:])
        seen.add(expandedOrder[i])

    # print(expandedOrder)

    firstTab, FormulatedTab, conStartRow = BuildFirstPenlitesTableau(
        a, b, c, expandedOrder)
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

    goalMetStrings = []

    penaltiesTotals = []

    ctr = 0
    while ctr != 100 and isLoopRunning:
        basicVarLst = []
        for k in range(lenObj + 1, (len(tableaus[-1][-1]) - 1) - len(constraints)):
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

        # print(basicVarLst)

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

        EqualitySigns = []
        EqualitySigns = []
        # handle the equalities by duplicating goals 1 positive and 1 negative according to the pos neg oder ex: col g2+ g2-
        for i in range(len(originalGoals)):
            if originalGoals[i][-1] == 2:
                if goalRhs[i] is not None:
                    if goalRhs[i] > 0:
                        EqualitySigns.append(i)
                        EqualitySigns.append(-(i+1))
                    else:
                        EqualitySigns.append(-i)
                        EqualitySigns.append(i+1)
                    goalRhs.insert(i, abs(goalRhs[i]))
                    goalRhs[i + 1] = -abs(goalRhs[i + 1])
                    # goalRhs.insert(i, -goalRhs[i])
                else:
                    goalRhs.insert(i, goalRhs[i])
                goalRhs.pop()

        goalMetString = []

        # check if goal is met based on constraints conditions
        for i in range(len(goalRhs)):
            # I hope dearly that this mathematical algorithm acquaints for both non-basic columns being optimal.
            if goalRhs[i] == None:
                metGoals[i] = True
                if goals[i][-1] != 2:
                    # print(f"Goal {i + 1} met by {goalRhs[i]}")
                    goalMetString.append(f"{i + 1} met: exactly")
                continue

            # TODO display the met state in gui
            # check if goal is met based on constraints conditions
            if goals[i][-1] == 0:
                if (goalRhs[i] + goals[i][-2]) <= goals[i][-2]:
                    # print("Goal {} met".format(i + 1))
                    # print(f"Goal {i + 1} met by {goalRhs[i]}")
                    if goalRhs[i] > 0:
                        goalMetString.append(
                            f"{i + 1} met: over by {abs(goalRhs[i])}")
                    else:
                        goalMetString.append(
                            f"{i + 1} met: under by {abs(goalRhs[i])}")
                    metGoals[i] = True
                else:
                    # print(f"Goal {i + 1} not met by {goalRhs[i]}")
                    # print(f"Goal {i + 1} not met by {goalRhs[i]}")
                    if goalRhs[i] > 0:
                        goalMetString.append(
                            f"{i + 1} not met: over by {abs(goalRhs[i])}")
                    else:
                        goalMetString.append(
                            f"{i + 1} not met: under by {abs(goalRhs[i])}")
                    metGoals[i] = False
            elif goals[i][-1] == 1:
                if (goalRhs[i] + goals[i][-2]) >= goals[i][-2]:
                    # print(f"Goal {i + 1} met by {goalRhs[i]}")
                    if goalRhs[i] > 0:
                        goalMetString.append(
                            f"{i + 1} met: over by {abs(goalRhs[i])}")
                    else:
                        goalMetString.append(
                            f"{i + 1} met: under by {abs(goalRhs[i])}")
                    metGoals[i] = True
                else:
                    # print(f"Goal {i + 1} not met by {goalRhs[i]}")
                    if goalRhs[i] > 0:
                        goalMetString.append(
                            f"{i + 1} not met: over by {abs(goalRhs[i])}")
                    else:
                        goalMetString.append(
                            f"{i + 1} not met: under by {abs(goalRhs[i])}")
                    metGoals[i] = False
            elif goals[i][-1] == 2:
                # TODO display the met state in gui but not from here from below for equalities
                if (goalRhs[i] == goals[i][-2]):
                    # print(f"Goal {i + 1} met by {goalRhs[i]}")
                    metGoals[i] = True
                else:
                    # print(f"Goal {i + 1} not met by {goalRhs[i]}")
                    metGoals[i] = False

        # print(metGoals)

        zRhsBackUp = copy.deepcopy(zRhs)
        if expandedOrder != []:
            tempZRhs = []

            for i in range(len(zRhs)):
                tempZRhs.append(zRhs[expandedOrder[i]])

            zRhs = copy.deepcopy(tempZRhs)

        # 0 in top rhs means goal met regardless of bottom rhs
        for i in range(len(zRhs)):
            if zRhs[i] == 0.0:
                metGoals[i] = True

        zRhs = copy.deepcopy(zRhsBackUp)

        if expandedOrder != []:
            tempMet = []
            for i in range(len(metGoals)):
                tempMet.append(metGoals[expandedOrder[i]])

            metGoals = tempMet

        # for the equality if z- is the basic var then z+ is false vice versa
        if EqualitySigns != []:
            for i in range(len(EqualitySigns)):
                if EqualitySigns[i] < 0:
                    metGoals[abs(EqualitySigns[i])] = True
                else:
                    metGoals[EqualitySigns[i]] = False

        # print(metGoals)
        # penalties specific used to get the total penalties for each tableau
        tempPenaltiesTotal = 0
        for i in range(len(metGoals)):
            if not metGoals[i]:
                # print(zRhs[i])
                tempPenaltiesTotal += abs(zRhs[i])

        penaltiesTotals.append(tempPenaltiesTotal)

        # swap to the row of the current goal being worked on
        for i in range(len(metGoals)):
            if metGoals[i] == False:
                currentZRow = i
                break

        tempMetGoals = copy.deepcopy(metGoals)
        for i in range(len(originalGoals)):
            if originalGoals[i][-1] == 2:

                # TODO display the met state in gui
                if not ((metGoals[i]) and (metGoals[i+1])):
                    if not metGoals[i]:
                        # print(f"Goal {i + 1} not met by {goalRhs[i]}")
                        if goalRhs[i] > 0:
                            goalMetString.append(
                                f"{i + 1} not met: over by {abs(goalRhs[i])}")
                        else:
                            goalMetString.append(
                                f"{i + 1} not met: under by {abs(goalRhs[i])}")
                    elif not metGoals[i+1]:
                        # print(f"Goal {i + 1} not met by {goalRhs[i + 1]}")
                        if goalRhs[i+1] > 0:
                            goalMetString.append(
                                f"{i + 1} not met: over by {abs(goalRhs[i+1])}")
                        else:
                            goalMetString.append(
                                f"{i + 1} not met: under by {abs(goalRhs[i+1])}")
                        pass
                    metGoals[i] = False
                    metGoals[i+1] = False
                else:
                    # print(f"Goal {i + 1} met by exactly")
                    goalMetString.append(f"{i + 1} met: exactly")
                    metGoals[i] = True
                    metGoals[i+1] = True

        goalMetStrings.append(goalMetString)

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

        # print(metGoals)

        metGoals = copy.deepcopy(tempMetGoals)

        # print(metGoals)

        try:
            newTab, zRhs = DoPivotOperations(
                tableaus[-1], conStartRow, currentZRow, 1)
            tableaus.append(newTab)
        except Exception as e:
            # print("Exception: {}".format(e))
            # table before is most likely optimal
            goalMetStrings.append("0")
            penaltiesTotals.append(float('inf'))
            break

        ctr += 1

    sortedGoalMetStrings = [sorted(sublist, key=lambda item: int(
        item.split()[0])) for sublist in goalMetStrings]

    for i in range(len(sortedGoalMetStrings)):
        for j in range(len(sortedGoalMetStrings[i])):
            sortedGoalMetStrings[i][j] = ' '.join(
                sortedGoalMetStrings[i][j].split()[1:])

    goalMetStrings = sortedGoalMetStrings

    penaltiesTotals.insert(0, float('inf'))
    goalMetStrings.insert(0, " ")
    print(penaltiesTotals)

    for i in range(len(tableaus)):
        try:
            print(f"Penalty: {penaltiesTotals[i]}")
            for l in range(len(goalMetStrings[i])):
                print(f"Goal {l+1} {goalMetStrings[i][l]}")
        except Exception as e:
            pass
        print("Tableau {}".format(i + 1))
        for j in range(len(tableaus[i])):
            for k in range(len(tableaus[i][j])):
                print("{:10.3f}".format(tableaus[i][j][k]), end=" ")
            print()
        print()

    print("\noptimal Tableau:\n")

    opTable = penaltiesTotals.index(min(penaltiesTotals))
    print(f"Penalty: {penaltiesTotals[opTable]}")
    for l in range(len(goalMetStrings[opTable])):
        print(f"Goal {l+1} {goalMetStrings[opTable][l]}")
    print("Tableau {}".format(opTable + 1))
    for j in range(len(tableaus[opTable])):
        for k in range(len(tableaus[opTable][j])):
            print("{:10.3f}".format(tableaus[opTable][j][k]), end=" ")
        print()
    print()


def main():
    goals, constraints, penalties, orderOverride = testInput()

    DoPenalties(goals, constraints, penalties, orderOverride)


main()
