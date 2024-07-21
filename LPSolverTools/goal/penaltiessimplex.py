import copy
import math

import pygame
from imgui.integrations.pygame import PygameRenderer
import imgui
import os
import sys


class PenaltiesSimplex:

    def __init__(self, isConsoleOutput=False):
        self.isConsoleOutput = isConsoleOutput
        self.testInputSelected = -1

        self.GuiHeaderRow = []
        self.GuiPivotCols = []
        self.GuiPivotRows = []

        # goal constraints
        self.amtOfObjVars = 2

        # goal constraints
        self.amtOfGoalConstraints = 1
        self.goalConstraints = [[0.0, 0.0, 0.0, 0.0]]
        self.signItems = ["<=", ">=", "="]
        self.signItemsChoices = [0]

        # goal constraints
        self.amtOfConstraints = 0
        self.constraints = []
        self.signItemsChoicesC = [0]

        self.tableaus = []

        self.goals = ["goal 1"]
        self.goalOrder = [0]

        self.toggle = False

        self.pivotCol = -1
        self.pivotRow = -1
        self.tCol = -1
        self.tRow = -1

        self.goalMetStrings = []

        self.opTable = -1

        self.extraGoalCtr = 0

        self.penalties = [0.0]
        self.penaltiesTotals = []

    def testInput(self, testNum=-1):
        if testNum == 0:
            goals = [
                # <= is 0 and >= is 1 and == is 2
                [40, 30, 20, 100, 0],
                [2, 4, 3, 10, 2],
                [5, 8, 4, 30, 1],

            ]

            constraints = [
            ]

            penalties = [5, 8, 12, 15]

            orderOverride = [2, 1, 0]
        elif testNum == 1:
            goals = [
                # <= is 0 and >= is 1 and == is 2
                [12, 9, 15, 125, 1],
                [5, 3, 4, 40, 2],
                [5, 7, 8, 55, 0],

            ]

            constraints = [
            ]

            penalties = [5, 2, 4, 3]

            orderOverride = [0, 1, 2]
        if testNum == -1:
            return None
        else:
            return goals, constraints, penalties, orderOverride

    def buildFirstpenaltiesVarTableau(self, goalConstraints, constraints, penaltiesVar, orderOverride=[]):
        oldTab = []
        newTab = []
        conStart = 0

        # hight = (goals + goalConstraints) = goals * 2 + constraints
        tabSizeH = (len(goalConstraints) * 2) + len(constraints)

        # width = z + rhs + x + (g+,-) * 2 + slack
        tabSizeW = 1 + 1 + \
            (len(goalConstraints[-1]) - 2) + \
            (len(goalConstraints) * 2) + len(constraints)

        amtOfObjVars = (len(goalConstraints[-1]) - 2)
        amtOfGoals = len(goalConstraints)

        # build Gui header row
        self.GuiHeaderRow.append("z")

        for i in range(amtOfObjVars):
            self.GuiHeaderRow.append("x" + str(i + 1))

        for i in range(amtOfGoals):
            self.GuiHeaderRow.append("g" + str(i + 1) + "-")
            self.GuiHeaderRow.append("g" + str(i + 1) + "+")

        for i in range(len(constraints)):
            self.GuiHeaderRow.append("c" + str(i + 1))

        self.GuiHeaderRow.append("Rhs")

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

        # put in penaltiesVar spots
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

        # put in penaltiesVar values or leave as -1
        if len(penaltiesVar) != 0:
            for i in range(len(oldTab)):
                for j in range(len(oldTab[i])):
                    if oldTab[i][j] == -1:
                        oldTab[i][j] = -penaltiesVar[i]

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
                        (topRows[i][j] - (bottomRows[i][j] * penaltiesVar[i]))
                elif goalConstraints[i][-1] == 1:
                    newTab[i][j] = (
                        topRows[i][j] + (bottomRows[i][j] * penaltiesVar[i]))

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

        conStart = amtOfGoals
        return oldTab, newTab, conStart

    def doPivotOperations(self, tab, conStartRow, zRow, tabNum=1):
        oldTab = copy.deepcopy(tab)
        newTab = []

        newTab = [[0 for _ in row] for row in oldTab]

        # exclude the z col and rhs
        currentZRow = zRow
        currentZ = tab[currentZRow][:-1]
        currentZ[0] = 0

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

        self.GuiPivotRows.append(pivotRow)
        self.GuiPivotCols.append(pivotCol)

        return newTab, zRhs

    def doPenalties(self, goals, constraints, penalties, orderOverride=[]):
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
            seen.add(expandedOrder[i])

        firstTab, FormulatedTab, conStartRow = self.buildFirstpenaltiesVarTableau(
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

            # get the rhs from basic cols
            for i in range(len(basicVarLst)):
                if basicVarLst[i] is not None:
                    sign = signLst[i]
                    for j in range(len(basicVarLst[i])):
                        if basicVarLst[i][j] == 1.0:
                            if sign == 1:
                                goalRhs[j] = (
                                    tableaus[-1][j + conStartRow][-1])
                            elif sign == -1:
                                goalRhs[j] = (-tableaus[-1]
                                              [j + conStartRow][-1])

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
                if goalRhs[i] == None:
                    metGoals[i] = True
                    if goals[i][-1] != 2:
                        goalMetString.append(f"{i + 1} met: exactly")
                    continue

                # check if goal is met based on constraints conditions
                if goals[i][-1] == 0:
                    if (goalRhs[i] + goals[i][-2]) <= goals[i][-2]:
                        if goalRhs[i] > 0:
                            goalMetString.append(
                                f"{i + 1} met: over by {abs(goalRhs[i])}")
                        else:
                            goalMetString.append(
                                f"{i + 1} met: under by {abs(goalRhs[i])}")
                        metGoals[i] = True
                    else:
                        if goalRhs[i] > 0:
                            goalMetString.append(
                                f"{i + 1} not met: over by {abs(goalRhs[i])}")
                        else:
                            goalMetString.append(
                                f"{i + 1} not met: under by {abs(goalRhs[i])}")
                        metGoals[i] = False
                elif goals[i][-1] == 1:
                    if (goalRhs[i] + goals[i][-2]) >= goals[i][-2]:
                        if goalRhs[i] > 0:
                            goalMetString.append(
                                f"{i + 1} met: over by {abs(goalRhs[i])}")
                        else:
                            goalMetString.append(
                                f"{i + 1} met: under by {abs(goalRhs[i])}")
                        metGoals[i] = True
                    else:
                        if goalRhs[i] > 0:
                            goalMetString.append(
                                f"{i + 1} not met: over by {abs(goalRhs[i])}")
                        else:
                            goalMetString.append(
                                f"{i + 1} not met: under by {abs(goalRhs[i])}")
                        metGoals[i] = False
                elif goals[i][-1] == 2:
                    if (goalRhs[i] == goals[i][-2]):
                        metGoals[i] = True
                    else:
                        metGoals[i] = False

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

            # penalties specific used to get the total penalties for each tableau
            tempPenaltiesTotal = 0
            for i in range(len(metGoals)):
                if not metGoals[i]:
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

                    if not ((metGoals[i]) and (metGoals[i+1])):
                        if not metGoals[i]:

                            if goalRhs[i] > 0:
                                goalMetString.append(
                                    f"{i + 1} not met: over by {abs(goalRhs[i])}")
                            else:
                                goalMetString.append(
                                    f"{i + 1} not met: under by {abs(goalRhs[i])}")
                        elif not metGoals[i+1]:
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

            metGoals = copy.deepcopy(tempMetGoals)

            try:
                newTab, zRhs = self.doPivotOperations(
                    tableaus[-1], conStartRow, currentZRow, 1)
                tableaus.append(newTab)
            except Exception as e:
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
        if self.isConsoleOutput:
            print(penaltiesTotals)

        if self.isConsoleOutput:
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

        if self.isConsoleOutput:
            print(f"Penalty: {penaltiesTotals[opTable]}")
            for l in range(len(goalMetStrings[opTable])):
                print(f"Goal {l+1} {goalMetStrings[opTable][l]}")
            print("Tableau {}".format(opTable + 1))
            for j in range(len(tableaus[opTable])):
                for k in range(len(tableaus[opTable][j])):
                    print("{:10.3f}".format(tableaus[opTable][j][k]), end=" ")
                print()
            print()

        return tableaus, goalMetStrings, opTable, penaltiesTotals

    def spaceGui(self, amt):
        for i in range(amt):
            imgui.spacing()

    def imguiUIElements(self, windowSize):
        imgui.new_frame()

        imgui.set_next_window_position(0, 0)  # Set the window position
        imgui.set_next_window_size(
            (windowSize[0]), (windowSize[1]))  # Set the window size
        imgui.begin("Tableaus Output",
                    flags=imgui.WINDOW_NO_TITLE_BAR | imgui.WINDOW_NO_RESIZE)

        # input

        # obj vars ===========================================
        if imgui.button("decision variables +"):
            self.amtOfObjVars += 1
            for i in range(len(self.goalConstraints)):
                self.goalConstraints[i].append(0.0)

        imgui.same_line()

        if imgui.button("decision variables -"):
            if self.amtOfObjVars != 2:
                self.amtOfObjVars += -1
                for i in range(len(self.goalConstraints)):
                    self.goalConstraints[i].pop()

        self.spaceGui(3)

        # goal constraints ===========================================
        if imgui.button("GoalConstraint +"):
            self.amtOfGoalConstraints += 1
            # goalConstraints.append([0.0, 0.0])
            self.goalConstraints.append([0.0] * self.amtOfObjVars)
            self.goalConstraints[-1].append(0.0)  # add sign spot
            self.goalConstraints[-1].append(0.0)  # add rhs spot
            self.signItemsChoices.append(0)
            self.goals.append(f"Goal {len(self.goals) + 1}")
            self.goalOrder.append(len(self.goals) - 1)
            self.penalties.append(0.0)

        imgui.same_line()

        if imgui.button("GoalConstraint -"):
            if self.amtOfGoalConstraints != 1:
                self.amtOfGoalConstraints += -1
                self.goalConstraints.pop()
                self.signItemsChoices.pop()
                self.goals.pop()
                self.goalOrder.pop()
                self.penalties.pop()

        # spaceGui(3)

        imgui.spacing()
        for i in range(self.amtOfGoalConstraints):
            imgui.spacing()
            if len(self.goalConstraints) <= i:
                # Fill with default values if needed
                self.goalConstraints.append([0.0] * (self.amtOfObjVars + 2))

            for j in range(self.amtOfObjVars):
                value = self.goalConstraints[i][j]
                imgui.set_next_item_width(50)
                imgui.same_line()
                changed, xValue = imgui.input_float(
                    "##x{}{}".format(i, j), value)
                imgui.same_line()
                imgui.text(f"x{j + 1}")
                if changed:
                    self.goalConstraints[i][j] = xValue

            imgui.same_line()
            imgui.push_item_width(50)
            changed, self.selectedItemSign = imgui.combo(
                "##combo{}{}".format(i, j), self.signItemsChoices[i], self.signItems)
            if changed:
                self.signItemsChoices[i] = self.selectedItemSign
                self.goalConstraints[i][-1] = self.signItemsChoices[i]
                # for i in range(len(goalConstraints)):
                if self.goalConstraints[i][-1] == 2:
                    self.penalties.append(0.0)
                else:
                    if len(self.penalties) > len(self.goalConstraints):
                        self.penalties.pop()

            imgui.pop_item_width()
            imgui.same_line()
            imgui.set_next_item_width(50)
            rhsValue = self.goalConstraints[i][-2]
            rhsChanged, rhs = imgui.input_float(
                "##RHS{}{}".format(i, j), rhsValue)

            if rhsChanged:
                self.goalConstraints[i][-2] = rhs

        self.spaceGui(6)

        # normal constraints ===========================================
        if len(self.constraints) == 0:
            pass

        if imgui.button("Constraint +"):
            self.amtOfConstraints += 1
            # goalConstraints.append([0.0, 0.0])
            self.constraints.append([0.0] * self.amtOfObjVars)
            self.constraints[-1].append(0.0)  # add sign spot
            self.constraints[-1].append(0.0)  # add rhs spot
            self.signItemsChoicesC.append(0)

        imgui.same_line()

        if len(self.constraints) != 0:
            if imgui.button("Constraint -"):
                if self.amtOfConstraints != 0:
                    self.amtOfConstraints += -1
                    self.constraints.pop()
                    self.signItemsChoicesC.pop()

            # spaceGui(6)
            for i in range(self.amtOfConstraints):
                imgui.spacing()
                if len(self.constraints) <= i:
                    # Fill with default values if needed
                    self.constraints.append([0.0] * (self.amtOfObjVars + 2))

                for j in range(self.amtOfObjVars):
                    value = self.constraints[i][j]
                    imgui.set_next_item_width(50)
                    imgui.same_line()
                    changed, xValue = imgui.input_float(
                        "##xC{}{}".format(i, j), value)
                    imgui.same_line()
                    imgui.text(f"x{j + 1}")
                    if changed:
                        self.constraints[i][j] = xValue

                imgui.same_line()
                imgui.push_item_width(50)
                changed, self.selectedItemSignC = imgui.combo(
                    "##comboC{}{}".format(i, j), self.signItemsChoicesC[i], self.signItems)
                if changed:
                    self.signItemsChoicesC[i] = self.selectedItemSignC
                    self.constraints[i][-1] = self.signItemsChoicesC[i]

                imgui.pop_item_width()
                imgui.same_line()
                imgui.set_next_item_width(50)
                rhsValue = self.constraints[i][-2]
                rhsChanged, rhs = imgui.input_float(
                    "##RHSC{}{}".format(i, j), rhsValue)

                if rhsChanged:
                    self.constraints[i][-2] = rhs

        self.spaceGui(6)

        imgui.text("Penalties:")
        self.spaceGui(2)
        for i in range(len(self.penalties)):
            value = self.penalties[i]
            imgui.text(f"penalty {i + 1}")
            imgui.set_next_item_width(50)
            imgui.same_line()
            changed, self.penalties[i] = imgui.input_float(
                "##penalty {}".format(i + 1), value)
            imgui.same_line()

            if changed:
                # Value has been updated
                pass

        self.spaceGui(6)

        if imgui.button("Show Goal Order" if not self.toggle else "Hide Goal Order"):
            # Toggle the boolean variable
            self.toggle = not self.toggle

        if self.toggle:
            self.spaceGui(3)
            for i in range(len(self.goals)):
                imgui.text(self.goals[i])

                imgui.same_line()
                if imgui.button(f"Up##{i}") and i > 0:
                    self.goals[i], self.goals[i -
                                              1] = self.goals[i - 1], self.goals[i]
                    self.goalOrder[i], self.goalOrder[i -
                                                      1] = self.goalOrder[i - 1], self.goalOrder[i]

                imgui.same_line()
                if imgui.button(f"Down##{i}") and i < len(self.goals) - 1:
                    self.goals[i], self.goals[i +
                                              1] = self.goals[i + 1], self.goals[i]
                    self.goalOrder[i], self.goalOrder[i +
                                                      1] = self.goalOrder[i + 1], self.goalOrder[i]

        self.spaceGui(6)
        # solve button =============================================================================================
        if imgui.button("Solve"):
            try:
                if self.testInput(self.testInputSelected) is not None:
                    self.goalConstraints, self.constraints, self.penalties, self.goalOrder = self.testInput(
                        self.testInputSelected)

                orderCopy = copy.deepcopy(self.goalOrder)
                if self.goalOrder == sorted(self.goalOrder):
                    orderCopy = []

                self.GuiPivotCols.append(-1)
                self.GuiPivotRows.append(-1)
                self.tableaus, self.goalMetStrings, self.opTable, self.penaltiesTotals = self.doPenalties(
                    self.goalConstraints, self.constraints, self.penalties, orderCopy)

                self.GuiPivotCols.append(-1)
                self.GuiPivotRows.append(-1)

                self.tRow = copy.deepcopy(self.GuiPivotRows)
                self.tCol = copy.deepcopy(self.GuiPivotCols)
                self.tHeader = copy.deepcopy(self.GuiHeaderRow)

                self.GuiHeaderRow.clear()
                self.GuiPivotRows.clear()
                self.GuiPivotCols.clear()

                for i in range(len(self.goalConstraints)):
                    if self.goalConstraints[i][-1] == 2:
                        self.extraGoalCtr += 1

                for i in range(len(self.tableaus) - len(self.tRow)):
                    self.tRow.append(-1)
                    self.tCol.append(-1)

            except Exception as e:
                print(e)
                imgui.text("Math Error")
                raise

        try:
            imgui.spacing()
            imgui.spacing()
            for i in range(len(self.tableaus)):
                pivotCol = self.tCol[i]
                pivotRow = self.tRow[i]
                if i == 0:
                    imgui.text("Setup Tableau")
                elif i == self.opTable:
                    imgui.push_style_color(imgui.COLOR_TEXT, 0.0, 1.0, 1.0)
                    imgui.text(f"Optimal Tableau {self.opTable}")
                    imgui.pop_style_color()
                else:
                    imgui.text("Tableau {}".format(i))
                if self.penaltiesTotals[i] != float('inf'):
                    imgui.text(f"Penalties: {self.penaltiesTotals[i]}")
                for metString in range(len(self.goalMetStrings[i])):
                    if self.goalMetStrings[i][metString] != " ":
                        imgui.text(
                            f"Goal {metString + 1} {self.goalMetStrings[i][metString]}")
                    # imgui.text(goalMetStrings[i])
                imgui.text("t-" + str(i))
                imgui.same_line(0, 20)
                for hCtr in range(len(self.tHeader)):
                    imgui.text("{:>8}".format(str(self.tHeader[hCtr])))
                    imgui.same_line(0, 20)
                imgui.spacing()
                for j in range(len(self.tableaus[i])):
                    if j == pivotRow and pivotRow != -1:
                        imgui.push_style_color(imgui.COLOR_TEXT, 0.0, 1.0, 0.0)
                    if j < (len(self.goalConstraints) + self.extraGoalCtr):
                        imgui.text("z " + str(j + 1))
                    else:
                        imgui.text(
                            "c " + str(j - (len(self.goalConstraints) + self.extraGoalCtr) + 1))
                    imgui.same_line(0, 20)
                    for k in range(len(self.tableaus[i][j])):
                        if k == pivotCol and pivotCol != -1:
                            imgui.push_style_color(
                                imgui.COLOR_TEXT, 0.0, 1.0, 0.0)
                        imgui.text("{:>8.3f}".format(self.tableaus[i][j][k]))
                        if k < len(self.tableaus[i][j]) - 1:
                            imgui.same_line(0, 20)
                        if k == pivotCol and pivotCol != -1:
                            imgui.pop_style_color()
                    if j == pivotRow and pivotRow != -1:
                        imgui.pop_style_color()
                    imgui.spacing()
                imgui.spacing()
                imgui.spacing()
                imgui.spacing()
                imgui.spacing()
            imgui.spacing()

        except Exception as e:
            imgui.text("Could Not display next tableau")
            raise

        imgui.end()

    def doGui(self):
        # window setup
        pygame.init()
        size = 1920 / 2, 1080 / 2

        os.system('cls' if os.name == 'nt' else 'clear')
        if self.isConsoleOutput:
            print(
                "\nBrett's simplex prototype tool for goal Preemptive simplex problems\n")

        pygame.display.set_mode(size, pygame.DOUBLEBUF |
                                pygame.OPENGL | pygame.RESIZABLE)

        pygame.display.set_caption("Goal Preemptive Simplex Prototype")

        icon = pygame.Surface((1, 1)).convert_alpha()
        icon.fill((0, 0, 0, 1))
        pygame.display.set_icon(icon)

        imgui.create_context()
        impl = PygameRenderer()

        io = imgui.get_io()
        io.display_size = size

        # var setup

        while 1:
            # window handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    sys.exit()

                impl.process_event(event)

            windowSize = pygame.display.get_window_size()

            self.imguiUIElements(windowSize)

            imgui.render()
            impl.render(imgui.get_draw_data())

            pygame.display.flip()


def main(isConsoleOutput=False):
    classInstance = PenaltiesSimplex(isConsoleOutput)
    classInstance.doGui()


if __name__ == "__main__":
    main(True)
