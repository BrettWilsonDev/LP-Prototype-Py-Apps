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

    return penalties, goals, constraints

def BuildFirstPenlitesTableau(penlites, goalConstraints, constraints):
    oldTab = []
    newTab = []
    conStart = 0


    # print(penlites)
    # print(goalConstraints)
    # print(constraints)

    # hight = (goals + goalConstraints) = goals * 2 + constraints
    tabSizeH = (len(goalConstraints) * 2) + len(constraints)

    # width = z + rhs + x + (g+,-) * 2 + slack
    tabSizeW = 1 + 1 + (len(goalConstraints[-1]) - 2) + (len(goalConstraints) * 2) + len(constraints)

    amtOfObjVars = (len(goalConstraints[-1]) - 2)
    amtOfGoals = len(goalConstraints)
    
    # fix the equalities constraints sizes
    for i in range(len(goalConstraints)):
        if goalConstraints[i][-1] == 2:
            tabSizeH += 1
            amtOfGoals += 1

    # print(tabSizeH)
    # print(tabSizeW)



    # print(amtOfObjVars)
    # print(amtOfGoals)

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
            oldTab[i + amtOfGoals][j + 1] = goalConstraints[i][j] # lhs
            oldTab[i + amtOfGoals][-1] = goalConstraints[i][-2] # rhs

    # put in constraints
    for i in range(len(constraints)):
        for j in range(amtOfObjVars):
            oldTab[i + amtOfGoals + len(goalConstraints)][j + 1] = constraints[i][j] # lhs
            oldTab[i + amtOfGoals + len(goalConstraints)][-1] = constraints[i][-2] # rhs


    for j in range(len(oldTab)):
        for k in range(len(oldTab[j])):
            print("{:10.3f}".format(oldTab[j][k]), end=" ")
        print()
    print()


    # first tab done move on to second tab
    newTab = copy.deepcopy(oldTab)


    # rows at the top of the old table are the goals
    topRows = []
    for i in range(amtOfGoals):
        topRows.append([])
        for j in range(len(oldTab[i])):
            topRows[i].append(oldTab[i][j])

    # print(topRows)

    # rows at the bottom of the old table are the goal constraints
    bottomRows = []
    for i in range(len(goalConstraints)):
        bottomRows.append([])
        for j in range(len(oldTab[i])):
            bottomRows[i].append(oldTab[i + amtOfGoals][j])

    # print(bottomRows)

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
    # backUpGoals = []
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
                newTab[i][j] = -1 * (topRows[i][j] - (bottomRows[i][j] * penlites[i]))
            elif goalConstraints[i][-1] == 1:
                newTab[i][j] = (topRows[i][j] + (bottomRows[i][j] * penlites[i]))

    print(backUpGoals)

    # fix the order of the equalities
    equalCtr = 0
    for i in range(len(backUpGoals)):
        if backUpGoals[i][-1] == 2:
            tempRow = newTab[i + equalCtr]
            newTab[i + equalCtr] = newTab[i + 1 + equalCtr]
            newTab[i + 1 + equalCtr] = tempRow

            equalCtr += 1

            
    print()
    for j in range(len(newTab)):
        for k in range(len(newTab[j])):
            print("{:10.3f}".format(newTab[j][k]), end=" ")
        print()
    print()

    conStart = amtOfGoals
    return oldTab, newTab, conStart

def main():
    penlites, goalConstraints, constraints = testInput()
    BuildFirstPenlitesTableau(penlites, goalConstraints, constraints)



main()