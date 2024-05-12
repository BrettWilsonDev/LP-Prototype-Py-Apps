import copy
import math


def GetInput():
    penlites = [200, 100, 50]

    # 0 is <= and 1 is >= and 2 is =
    goalConstraints = [
        [7, 3, 40, 1],
        [10, 5, 60, 1],
        [5, 4, 35, 1],
    ]

    # 0 is <= and 1 is >= and 2 is =
    constraints = [
        [100, 60, 600, 0],
    ]

    # lengthOfObj = len(goalConstraints[-1]) - 2

    # print(len(constraints))

    penlites = []

    # 0 is <= and 1 is >= and 2 is =
    goalConstraints = [
        [400, 300, 250, 28000, 0],
        [60, 50, 40, 5000, 1],
        [20, 35, 20, 3000, 1],
        [20, 15, 40, 1000, 1],
    ]

    # 0 is <= and 1 is >= and 2 is =
    constraints = [
        # [100, 60, 600, 0],
    ]

    return penlites, goalConstraints, constraints


def BuildFirstPenlitesTableau(penlites, goalConstraints, constraints):
    tabSizeH = len(constraints) + len(goalConstraints) + len(penlites)

    #          z  + rhs   +    x and x    +              penlites g- g+    +     slack
    tabSizeW = 1 + 1 + \
        (len(goalConstraints[-1]) - 2) + (len(penlites) * 2) + len(constraints)

    # print(tabSizeW)
    # print(tabSizeH)
    amtOfObjVars = (len(goalConstraints[-1]) - 2)
    # print(amtOfObjVars)
    # print()

    tab = []

    # initialize table with empty rows
    for i in range(tabSizeH):
        tab.append([])

    # initialize table with zeros
    for i in range(tabSizeH):
        for j in range(tabSizeW):
            tab[i].append(0)

    # put in lhs in the z col
    for i in range(len(penlites)):
        tab[i][0] = 1

    # put in penlites
    gCtr = amtOfObjVars + 1
    for i in range(len(penlites)):
        tab[i][gCtr] = -1 * penlites[i]
        gCtr += 2

    # put in goal constraints
    for i in range(len(penlites), tabSizeH - len(constraints)):
        for j in range(1, amtOfObjVars + 1):
            tab[i][-1] = goalConstraints[i - len(penlites)][-2]
            tab[i][j] = goalConstraints[i - len(penlites)][j - 1]

    # put in normal constraints
    for i in range(tabSizeH - len(constraints), tabSizeH):
        for j in range(1, (len(constraints[-1]) - 2) + 1):
            tab[i][-1] = constraints[i - (tabSizeH - len(constraints))][-2]
            tab[i][j] = constraints[i - (tabSizeH - len(constraints))][j - 1]

    # put the 1 -1 for goal constraints in
    onesCtr = amtOfObjVars + 1
    for i in range(len(penlites), tabSizeH - len(constraints)):
        tab[i][onesCtr] = 1
        tab[i][onesCtr + 1] = -1
        onesCtr += 2

    # put the 1 for normal constraints in the slack spots
    posOfSlack = (((len(penlites) * 2) + amtOfObjVars))
    onesCtr = 1
    for i in range(tabSizeH - len(constraints), tabSizeH):
        # print(posOfSlack)
        tab[i][posOfSlack + onesCtr] = 1
        onesCtr += 1

    # for i in range(tabSizeH):
    #     for j in range(tabSizeW):
    #         print(tab[i][j], end=" ")
    #     print()

    # print the table input
    # for i in range(tabSizeH):
    #     for j in range(tabSizeW):
    #         print("{:10.3f}".format(tab[i][j]), end=" ")
    #     print()
    # print()

    # new calualted tab
    # newTab = tab.copy()
    newTab = copy.deepcopy(tab)

    # calculate the new table goal rows
    gCtr = len(goalConstraints)
    for i in range(len(penlites)):
        for j in range(len(tab[i])):
            newTab[i][j] = tab[i][j] + (tab[gCtr][j] * penlites[i])
        gCtr += 1

    # for i in range(tabSizeH):
    #     for j in range(tabSizeW):
    #         print("{:10.3f}".format(tab[i][j]), end=" ")
    #     print()
    # print()

    conStart = len(penlites)

    return tab, newTab, conStart


def DoPivotOperations(tab, conStart, zRow, tabNum=1):
    # newTab = copy.deepcopy(tab)
    oldTab = copy.deepcopy(tab)
    newTab = []

    newTab = [[0 for _ in row] for row in oldTab]

    currentZRow = zRow
    currentZ = tab[currentZRow][:-1]
    # currentZ = currentZ[1:]
    currentZ[0] = 0

    # print(currentZ)

    # find the largest z and its index for the pivot col
    largestZ = max(currentZ)
    pivotCol = currentZ.index(largestZ)
    # print(f"pivot col is {pivotCol}")
    # print(largestZ)

    # find the pivot row
    useZero = False
    ratios = []
    for i in range(conStart, len(tab)):
            div = tab[i][pivotCol]
            if div == 0:
                ratios.append(float('inf'))
            else:
                ratios.append(tab[i][-1] / tab[i][pivotCol])

                if (tab[i][-1] / tab[i][pivotCol]) == 0 and ((tab[i][pivotCol]) == abs(tab[i][pivotCol])):
                    # print("use the damm zero to pivot")
                    useZero = True

    # print(ratios)

    if useZero:
        positiveRatios = [ratio for ratio in ratios if ratio >= 0]
    else:
        positiveRatios = [ratio for ratio in ratios if ratio > 0]

    pivotRow = ratios.index(min(positiveRatios))
    pivotRow += conStart
    # print(f"pivot row is {pivotRow}")

    divNumber = tab[pivotRow][pivotCol]
    # print(divNumber)

    # newTab = [[0 for _ in row] for row in oldTab]

    # do the pivot division operations
    for i in range(len(tab)):
        for j in range(len(tab[i])):
            newTab[i][j] = oldTab[i][j] / divNumber

    # print()
    # do the pivot operations
    # the formula: Element_New_Table((i, j)) = Element_Old_Table((i, j)) - (Element_Old_Table((i, Pivot_column)) * Element_New_Table((Pivot_Row, j)))
    for i in range(len(tab)):
        for j in range(len(tab[i])):
            if i == pivotRow:
                continue

            # print(f"{oldTab[i][j]} - ({oldTab[i][pivotCol]} * {newTab[pivotRow][j]}) = {oldTab[i][j] - (newTab[i][pivotCol] * oldTab[pivotRow][j])}")

            newTab[i][j] = oldTab[i][j] - \
                (oldTab[i][pivotCol] * newTab[pivotRow][j])
        # print()

    # print()
    # for i in range(len(newTab)):
    #     for j in range(len(newTab[i])):
    #         print("{:10.3f}".format(newTab[i][j]), end=" ")
    #     print()

    newTab = [[0.0 if abs(val) < 1e-10 else val for val in sublist]
                          for sublist in newTab]

    for items in newTab:
        for i, item in enumerate(items):
            if item == 0.0 and math.copysign(1, item) == -1:
                newTab[i][i] = abs(item)

    # zRowIsMet = False
    # if newTab[zRow][-1] == 0.0:
    #     zRowIsMet = True
    # else:
    #     zRowIsMet = False
    zRhs = []

    for i in range(conStart):
        zRhs.append(newTab[i][-1])
        # print(newTab[i][-1])

    print(f"pivoting on table {tabNum}\nIn row {pivotRow + 1} and col {pivotCol + 1}\n")

    return newTab, zRhs

def DoPenlites():
    zRow = 0

    penlites, goalConstraints, constraints = GetInput()

    tableaus = []

    metRhs = []

    fistTab, secondTab, conStart = BuildFirstPenlitesTableau(
        penlites, goalConstraints, constraints)
    tableaus.append(fistTab)
    tableaus.append(secondTab)

    # for i in range(conStart):
    #     metRhs.append(False)

    tabNum = 1
    loopFlag = True
    while loopFlag:
        tab, zRhs = DoPivotOperations(tableaus[-1], conStart, zRow, tabNum)
        tableaus.append(tab)
        tabNum += 1

        if zRhs[zRow] == 0.0:
            metRhs.append(True)
            # metRhs[zRow] = True
            zRow += 1

        for i in range(len(metRhs)):
            if zRhs[i] == 0.0:
                metRhs[i] = True
            else:
                metRhs[i] = False

        for i in range(len(metRhs)):
            if i < zRow and metRhs[i] == False:
                loopFlag = False

    if loopFlag == False:
        print(f"Tableau {tabNum} may be the optimal tableau\n")

    for i in range(len(tableaus)):
        print("Tableau {}".format(i + 1))
        for j in range(len(tableaus[i])):
            for k in range(len(tableaus[i][j])):
                print("{:10.3f}".format(tableaus[i][j][k]), end=" ")
            print()
        print()


def BuildFirstPreemptiveTableau(goalConstraints, constraints):
    tabSizeH = len(constraints) + len(goalConstraints) * 2
    tabSizeW = 1 + 1 + (len(goalConstraints) * 2) + \
                        len(constraints) + (len(goalConstraints[-1]) - 2)

    penlites = len(goalConstraints)

    amtOfObjVars = (len(goalConstraints[-1]) - 2)
    # print(amtOfObjVars)

    # print(tabSizeW)
    # print(tabSizeH)

    tab = []

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

    # print(goalConstraints)

    # # put in penlites
    gCtr = amtOfObjVars + 1
    for i in range(len(goalConstraints)):
        if goalConstraints[i][-1] == 0:
            tab[i][gCtr + 1] = -1
        else:
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

    # for i in range(tabSizeH):
    #     for j in range(tabSizeW):
    #         print("{:10.3f}".format(tab[i][j]), end=" ")
    #     print()
    # print()

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

    # print()
    # for i in range(tabSizeH):
    #     for j in range(tabSizeW):
    #         print("{:10.3f}".format(newTab[i][j]), end=" ")
    #     print()
    # print()

    return tab, newTab, penlites


def DoPreemptive():
    zRow = 0

    tableaus = []

    metRhs = []

    penlites, goalConstraints, constraints = GetInput()
    firstTab, secondTab, conStart = BuildFirstPreemptiveTableau(
        goalConstraints, constraints)
    tableaus.append(firstTab)
    tableaus.append(secondTab)

    # for i in range(conStart):
    #     metRhs.append(False)


    # tab, zRhs = DoPivotOperations(tableaus[-1], conStart, zRow, 1)

    # for i in range(len(zRhs)):
    #     if goalConstraints[i][-1] == 0:
    #         if zRhs[i] <= goalConstraints[i][-2]:
    #             print(zRhs[i])

    # tabNum = 1
    # loopFlag = True
    # while loopFlag:
    #     tab, zRhs = DoPivotOperations(tableaus[-1], conStart, zRow, tabNum)
    #     tableaus.append(tab)
    #     tabNum += 1

    #     if goalConstraints[zRow][-1] == 0:
    #         if zRhs[zRow] <= goalConstraints[zRow][-2]:
    #             print(zRhs[zRow])
    #             print("met")
    #             zRow += 1
    #         else:
    #             print(zRhs[zRow])
    #             print("not met")

        # for i in range(len(zRhs)):
        #     if goalConstraints[i][-1] == 0:
        #         if zRhs[i] <= goalConstraints[i][-2]:
        #             # metRhs[zRow] = True
        #             metRhs.append(True)
        #             zRow += 1
        #         elif zRhs[i] > goalConstraints[i][-2]:
        #             metRhs[i] = False
        #     else:
        #         if zRhs[zRow] == 0.0:
        #             # metRhs[zRow] = True
        #             metRhs.append(True)
        #             zRow += 1

        #         for i in range(len(metRhs)):
        #             if zRhs[i] == 0.0:
        #                 metRhs[i] = True
        #             else:
        #                 metRhs[i] = False

        # if zRhs[zRow] == 0.0:
        #     metRhs.append(True)
        #     # metRhs[zRow] = True
        #     zRow += 1

        # for i in range(len(metRhs)):
        #     if zRhs[i] == 0.0:
        #         metRhs[i] = True
        #     else:
        #         metRhs[i] = False

        # for i in range(len(metRhs)):
        #     if i < zRow and metRhs[i] == False:
        #         loopFlag = False
                
        # if tabNum == 5:
        #     loopFlag = False

    # tabNum = 1
    # tab, zRhs = DoPivotOperations(tableaus[-1], conStart, zRow, tabNum)
    # tableaus.append(tab)
    # tabNum += 1

    # tab, zRhs = DoPivotOperations(tableaus[-1], conStart, 1, tabNum)
    # tableaus.append(tab)
    # tabNum += 1

    # tab, zRhs = DoPivotOperations(tableaus[-1], conStart, 1, tabNum)
    # tableaus.append(tab)
    # tabNum += 1

    # tab, zRhs = DoPivotOperations(tableaus[-1], conStart, 1, tabNum)
    # tableaus.append(tab)
    # tabNum += 1

    # tab, zRhs = DoPivotOperations(tableaus[-1], conStart, 1, tabNum)
    # tableaus.append(tab)
    # tabNum += 1

    tabNum = 1
    loopFlag = True
    while loopFlag:
        tab, zRhs = DoPivotOperations(tableaus[-1], conStart, zRow, tabNum)
        tableaus.append(tab)
        tabNum += 1

        if goalConstraints[zRow][-1] == 0:
            if zRhs[zRow] <= goalConstraints[zRow][-2]:
                # print(zRhs[zRow])
                # print("met")
                zRow += 1
        else:
            if zRhs[zRow] == 0.0:
                metRhs.append(True)
                # metRhs[zRow] = True
                zRow += 1

        for i in range(len(metRhs)):
            if goalConstraints[i][-1] == 0:
                if zRhs[i] <= goalConstraints[i][-2]:
                    metRhs[i] = True
                elif zRhs[i] > goalConstraints[i][-2]:
                    metRhs[i] = False

        for i in range(len(metRhs)):
            if zRhs[i] == 0.0:
                metRhs[i] = True
            else:
                metRhs[i] = False

        for i in range(len(metRhs)):
            if i < zRow and metRhs[i] == False:
                loopFlag = False

    if loopFlag == False:
        print(f"Tableau {tabNum} may be the optimal tableau\n")

    for i in range(len(tableaus)):
        print("Tableau {}".format(i + 1))
        for j in range(len(tableaus[i])):
            for k in range(len(tableaus[i][j])):
                print("{:10.3f}".format(tableaus[i][j][k]), end=" ")
            print()
        print()

def main():
    # DoPenlites()
    DoPreemptive()

main()