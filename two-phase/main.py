import copy


def testInput():
    isMin = False

    objFunc = [100, 30]

    # # 0 is <= and 1 is >= and 2 is =
    constraints = [
        [0, 1, 3, 1],
        [1, 1, 7, 0],
        [10, 4, 40, 0],
        # [2, 3, 4, 1],
        # [5, -6, 7, 0],
        # [0, 7, -8, 1],
    ]


    # objFunc = [100, 80, 40]

    # # # # # 0 is <= and 1 is >= and 2 is =
    # constraints = [
    #     [2, 1, 1, 3, 1],
    #     [1, 1, 0, 2, 1],
    # ]

    # objFunc = [100, 30, 40]

    # # # 0 is <= and 1 is >= and 2 is =
    # constraints = [
    #     [0, 1, 3, 4, 1],
    #     [1, 1, 7, 4, 0],
    #     [10, 4, 40, 5, 0],
    # ]

    # isMin = True
    # isMin = False

    return objFunc, constraints, isMin


def FormulateFirstTab(objFunc, constraints):
    tab = []

    objFuncSize = len(objFunc)

    #           con            w    z
    tableH = len(constraints) + 1 + 1
    #          obj var    rhs  a     constraints
    tableW = objFuncSize + 1 + 0 + len(constraints)

    # print(tableH)
    # print(tableW)
    # print()

    # for i in range(tableH):
    #     tab.append([])
    #     for j in range(tableW):
    #         tab[i].append(0)

    # eCons = copy.deepcopy(constraints)
    eCons = []

    # print(eCons)

    for i in range(len(constraints)):
        if constraints[i][-1] == 1:
            eCons.append(copy.deepcopy(constraints[i]))

    # print(eCons)
    for i in range(len(eCons)):
        for j in range(len(eCons[i])):
            eCons[i][j] = eCons[i][j] * -1

    # print(eCons)

    # calculate summed w row
    summedW = []
    temp = 0
    for i in range(objFuncSize + 1):
        temp = 0
        for j in range(len(eCons)):
            temp += eCons[j][i]

        summedW.append(temp)

    print()

    # neg the w row
    for i in range(len(summedW)):
        summedW[i] = summedW[i] * -1

    # make the w row string
    wStr = ""
    for i in range(len(summedW) - 1):
        wStr += " + " + str(summedW[i]) + "x" + str(i + 1)

    for i in range(len(eCons)):
        wStr += " - e" + str(i + 1)

    print(f"w{wStr} = {summedW[-1]}\n")

    # fill the table with duds but respect amt of a cols
    for i in range(tableH):
        tab.append([])
        for j in range(tableW + len(eCons)):
            tab[i].append(0)

    # add w row
    for i in range(objFuncSize):
        tab[0][i] = summedW[i]

    tab[0][-1] = summedW[-1]

    # add z row
    for i in range(objFuncSize):
        tab[1][i] = objFunc[i] * -1

    # print(constraints)

    constraints.sort(key=lambda x: x[-1], reverse=True)

    # print(constraints)

    tempAllCons = []
    tempCons = []
    for i in range(tableH - 2):
        tempCons = []
        for j in range(tableW + len(eCons)):
            tempCons.append(0)
        tempAllCons.append(tempCons)

    aCols = []
    aCtr = objFuncSize
    for i in range(len(tempAllCons)):
        for k in range(objFuncSize):
            tempAllCons[i][k] = constraints[i][k]
            tempAllCons[i][-1] = constraints[i][-2]

        if constraints[i][-1] == 1:
            tempAllCons[i][aCtr] = 1
            tempAllCons[i][aCtr + 1] = -1
            aCols.append(aCtr)
            aCtr += 2
        else:
            tempAllCons[i][aCtr] = 1
            aCtr += 1

    # print(aCtr)

    for i in range(2, len(tab)):
        for j in range(len(tab[i])):
            tab[i][j] = tempAllCons[i - 2][j]

    for i in range(2, len(tab)):
        for j in range(objFuncSize, len(tab[i])):
            if tempAllCons[i - 2][j] == -1:
                tab[0][j] = -1

    # print(tempAllCons)

    # for i in range(len(tab)):
    #     for j in range(len(tab[i])):
    #         print("{:10.3f}".format(tab[i][j]), end=" ")
    #     print()

    return tab, aCols


def DoPivotOperationsPhase1(tab):
    largestW = max(tab[0][:-1])
    # print(largestW)

    pivotCol = tab[0][:-1].index(largestW)
    # print(pivotCol)

    thetas = []
    for i in range(2, len(tab)):
        # print(f"{tab[i][-1]} / {tab[i][pivotCol]} = {tab[i][-1] / tab[i][pivotCol]}")

        if tab[i][pivotCol] == 0:
            thetas.append(float('inf'))
        else:
            thetas.append(tab[i][-1] / tab[i][pivotCol])

    # print(thetas)
    theta = min(x for x in thetas if x > 0 and x != float('inf'))
    # print(theta)

    pivotRow = thetas.index(theta)
    pivotRow += 2
    # print(pivotRow)

    newTab = copy.deepcopy(tab)

    for i in range(len(newTab)):
        for j in range(len(newTab[i])):
            newTab[i][j] = 0

    # the div row
    divNum = tab[pivotRow][pivotCol]
    # print(divNum)

    if divNum == 0:
        print("Divide by 0 error")
        return

    for i in range(len(tab)):
        for j in range(len(tab[i])):
            newTab[pivotRow][j] = tab[pivotRow][j] / divNum
            # print(f"{newTab[pivotRow][j]} = {tab[pivotRow][j]} / {divNum}")

    # print()

    # the formula: Element_New_Table((i, j)) = Element_Old_Table((i, j)) - (Element_Old_Table((i, Pivot_column)) * Element_New_Table((Pivot_Row, j)))
    for i in range(len(tab)):
        for j in range(len(tab[i])):
            if i != pivotRow:
                newTab[i][j] = tab[i][j] - \
                    (tab[i][pivotCol] * newTab[pivotRow][j])

    isAllNegW = all(num <= 0 for num in newTab[0]) if newTab[0] else False

    # print(isAllNegW)

    # for i in range(len(newTab)):
    #     for j in range(len(newTab[i])):
    #         print("{:10.3f}".format(newTab[i][j]), end=" ")
    #     print()

    print(f"In Phase 1, The pivot row is {pivotRow + 1} and the pivot col is {pivotCol + 1}")

    return newTab, isAllNegW


def DoPivotOperationsPhase2(tab, isMin):

    if isMin:
        largestZ = max(tab[1][:-1])
    else:
        largestZ = min(tab[1][:-1])
    # print(largestW)

    pivotCol = tab[1][:-1].index(largestZ)
    # print(pivotCol)

    thetas = []
    for i in range(2, len(tab)):
        # print(f"{tab[i][-1]} / {tab[i][pivotCol]} = {tab[i][-1] / tab[i][pivotCol]}")

        if tab[i][pivotCol] == 0:
            thetas.append(float('inf'))
        else:
            thetas.append(tab[i][-1] / tab[i][pivotCol])

    # print(thetas)
    theta = min(x for x in thetas if x > 0 and x != float('inf'))
    # print(theta)

    pivotRow = thetas.index(theta)
    pivotRow += 2
    # print(pivotRow)

    newTab = copy.deepcopy(tab)

    for i in range(len(newTab)):
        for j in range(len(newTab[i])):
            newTab[i][j] = 0

    # the div row
    divNum = tab[pivotRow][pivotCol]

    if divNum == 0:
        print("Divide by 0 error")
        return

    for i in range(len(tab)):
        for j in range(len(tab[i])):
            newTab[pivotRow][j] = tab[pivotRow][j] / divNum

    # the formula: Element_New_Table((i, j)) = Element_Old_Table((i, j)) - (Element_Old_Table((i, Pivot_column)) * Element_New_Table((Pivot_Row, j)))
    for i in range(len(tab)):
        for j in range(len(tab[i])):
            if i != pivotRow:
                newTab[i][j] = tab[i][j] - \
                    (tab[i][pivotCol] * newTab[pivotRow][j])

    if isMin:
        isAllNegZ = all(num <= 0 for num in newTab[1][:-1])
    else:
        isAllNegZ = all(num >= 0 for num in newTab[1][:-1])

    # print(isAllNegZ)


    # for i in range(len(newTab)):
    #     for j in range(len(newTab[i])):
    #         print("{:10.3f}".format(newTab[i][j]), end=" ")
    #     print()

    print(f"In Phase 2, The pivot row is {pivotRow + 1} and the pivot col is {pivotCol + 1}")

    return newTab, isAllNegZ


def main():
    isMin = False
    tabs = []
    isAllNegW = False
    objFunc, constraints, isMin = testInput()
    tab, aCols = FormulateFirstTab(objFunc, constraints)
    tabs.append(tab)

    isAllNegW = all(num <= 0 for num in tabs[-1][0]) if tabs[-1][0] else False

    # print()
    # tab, isAllNegW = DoPivotOperationsPhase1(tabs[-1])
    # tabs.append(tab)

    # tab, isAllNegW = DoPivotOperationsPhase1(tabs[-1])
    # tabs.append(tab)

    # print(tabs[-1])

    phase1Ctr = 0
    while not isAllNegW:
        tab, isAllNegW = DoPivotOperationsPhase1(tabs[-1])
        tabs.append(tab)

        phase1Ctr += 1
        if isAllNegW or phase1Ctr > 50:
            break


    # print(phase1Ctr)

    tabPhaseNum = phase1Ctr + 1

    newTab = copy.deepcopy(tabs[-1])
    # for i in range(len(newTab)):
    #     for j in range(len(newTab[i])):

    for k in range(len(aCols)):
        for i in range(len(newTab)):
            # print(newTab[i][aCols[k]])
            newTab[i][aCols[k]] = 0

    # del tabs[-1]
    # del newTab[0]
    tabs.append(newTab)

    if not isMin:
        AllPosZ = all(num >= 0 for num in tabs[-1][1][:-1])
        # print(AllPosZ)
    else:
        AllPosZ = all(num <= 0 for num in tabs[-1][1][:-1])
        # print(AllPosZ)

    phase2Ctr = 0
    while not AllPosZ:
        tab, AllPosZ = DoPivotOperationsPhase2(tabs[-1], isMin)
        tabs.append(tab)

        if AllPosZ or phase2Ctr > 25:
            break

        phase2Ctr += 1

    print("\nNote there is a extra table before phase 2 to show all\n")

    currentPhase = 1
    for i in range(len(tabs)):
        if i == tabPhaseNum:
            currentPhase = 2
        
        print("Phase {}".format(currentPhase))
        print("Tableau {}".format(i + 1))
        # print(" ".join(["{:>10}".format(val) for val in topRow]))
        for j in range(len(tabs[i])):
            for k in range(len(tabs[i][j])):
                print("{:10.3f}".format(tabs[i][j][k]), end=" ")
            print()
        print()
main()
