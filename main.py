def printTab(tab):
    for row in tab:
        print(row)


def DoPrimalPivotOperation(tab, isMin):
    # tab = [
    #     # x1   x2  e1  s2 s3 rhs
    #     [-100, 0, -30, 0, 0, 90],
    #     [0, 1, -1, 0, 0, 3],
    #     [1, 0, 1, 1, 0, 4],
    #     [10, 0, 4, 0, 1, 28]
    # ]
    # for element in tab:
    #     # print(element)
    # print()
    testRow = tab[0][:-1]
    # # print(testRow)

    # largestNegativeNumber = min(testRow)
    # largestNegativeNumber = max(testRow)

    if isMin:
        largestNegativeNumber = min(num for num in testRow if num < 0 and num != 0)
    else:
        largestNegativeNumber = max(num for num in testRow if num < 0 and num != 0)

    # largestNegativeNumber = max(num for num in testRow if num < 0 and num != 0)
    # largestNegativeNumber = min(num for num in testRow if num < 0 and num != 0)
    # # print(f"\nthe largest negative number is {largestNegativeNumber}")
    # # print(tab[0])

    colIndex = tab[0].index(largestNegativeNumber)

    i = 0
    thetas = []
    for row in tab:
        if i == 0:
            i += 1
            continue

        if row[colIndex] != 0:
            thetas.append(row[-1] / row[colIndex])
        else:
            thetas.append(float('inf'))

    # minTheta = min(thetas)
    minTheta = min(num for num in thetas if num > 0)
    # print(thetas)
    # print(minTheta)

    rowIndex = thetas.index(minTheta) + 1

    # # print(f"\nthe pivot row {rowIndex} and the pivot column {colIndex}")

    operationTab = []

    divNumber = tab[rowIndex][colIndex]
    # print(rowIndex, colIndex)
    # print(divNumber)

    operationTab = [[0 for _ in row] for row in tab]

    for i in range(len(tab)):
        for j in range(len(tab[i])):
            operationTab[rowIndex][j] = tab[rowIndex][j] / divNumber
            if operationTab[rowIndex][j] == -0.0:
                operationTab[rowIndex][j] = 0.0

    # print(operationTab[rowIndex])

    # the formula: Element_New_Table((i, j)) = Element_Old_Table((i, j)) - (Element_Old_Table((i, Pivot_column)) * Element_New_Table((Pivot_Row, j)))
    for i in range(len(tab)):
        if i == rowIndex:
            continue
        for j in range(len(tab[i])):

            mathItem = tab[i][j] - \
                (tab[i][colIndex] * operationTab[rowIndex][j])
            
            # # print(f"{tab[i][j]} - ({tab[i][colIndex]} * {operationTab[rowIndex][j]}) = {mathItem}")


            operationTab[i][j] = mathItem

    return operationTab


def DoFormulationOperation(objFunc, constrants):
    excessCount = 0
    slackCount = 0

    for i in range(len(constrants)):
        if constrants[i][-1] == 1:
            excessCount += 1
        else:
            slackCount += 1

    for i in range(len(constrants)):
        for j in range(len(constrants[i])):
            if constrants[i][-1] == 1:
                constrants[i][j] = -1 * constrants[i][j]

    for i in range(len(constrants)):
        del constrants[i][-1]

    tableSizeH = len(constrants) + 1

    tableSizeW = excessCount + slackCount + 1 + len(objFunc)
    opTable = []
    for i in range(tableSizeH):
        opTable.append([])
        for j in range(tableSizeW):
            opTable[i].append(0)

    for i in range(len(objFunc)):
        opTable[0][i] = -objFunc[i]

    for i in range(len(constrants)):
        for j in range(len(constrants[i]) - 1):
            opTable[i + 1][j] = constrants[i][j]
            opTable[i + 1][-1] = constrants[i][-1]

    # added the slack and excess 1s
    for i in range(1, len(opTable)):
        for j in range(len(objFunc), len(opTable[i]) - 1):
            opTable[i][i + 1 * len(objFunc) - 1] = 1

    return opTable


def DoDualPivotOperation(tab):
    rhs = [row[-1] for row in tab]
    minRhsNum = min(rhs)

    pivotRow = rhs.index(minRhsNum)

    negPivotCols = []
    for i in range(len(tab[pivotRow]) - 1):
        if tab[pivotRow][i] < 0:
            negPivotCols.append(i)
        else:
            negPivotCols.append(float('inf'))

    dualPivotThetas = []
    for i in range(len(negPivotCols)):
        if negPivotCols[i] != float('inf'):

            pivotColIndex = negPivotCols[i]

            dualPivotThetas.append(
                abs(tab[0][pivotColIndex] / tab[pivotRow][pivotColIndex]))
        else:
            dualPivotThetas.append(float('inf'))

    smallestPosPivotTheta = min(dualPivotThetas)

    rowIndex = pivotRow
    colIndex = dualPivotThetas.index(smallestPosPivotTheta)

    oldTab = tab.copy()

    newTab = []

    # # print(rowIndex, colIndex)
    divNumber = tab[rowIndex][colIndex]

    newTab = [[0 for _ in row] for row in oldTab]

    pivotMathRow = []


    for i in range(len(oldTab)):
        for j in range(len(oldTab[i])):
            newTab[rowIndex][j] = oldTab[rowIndex][j] / divNumber

            if newTab[rowIndex][j] == -0.0:
                newTab[rowIndex][j] = 0.0

    pivotMathRow = newTab[rowIndex]

    # the formula: Element_New_Table((i, j)) = Element_Old_Table((i, j)) - (Element_Old_Table((i, Pivot_column)) * Element_New_Table((Pivot_Row, j)))
    for i in range(len(oldTab)):
        for j in range(len(oldTab[i])):
            if i == rowIndex:
                continue

            mathItem = oldTab[i][j] - \
                (oldTab[i][colIndex] * newTab[rowIndex][j])

            # # print(f"{newTab[i][j]} - ({oldTab[i][colIndex]} * {newTab[rowIndex][j]}) = {mathItem}")

            newTab[i][j] = mathItem

    newTab[rowIndex] = pivotMathRow

    return newTab

def GetInput():
    objFunc = [100, 30]

    # 0 is <= and 1 is >= and 2 is =
    constrants = [
        [0, 1, 3, 1],
        [1, 1, 7, 0],
        [10, 4, 40, 0]
    ]

    # objFunc = [50, 20, 30, 80]

    # # 0 is <= and 1 is >= and 2 is =
    # constrants = [
    #     [400, 200, 150, 500, 500, 1],
    #     [3, 2, 0, 0, 6, 1],
    #     [2, 2, 4, 4, 10, 1],
    #     [2, 4, 1, 5, 8, 1],
    # ]

    tab = DoFormulationOperation(objFunc, constrants)

    return tab


def DoDualSimplex():
    isMin = False
    tableaus = []

    tab = GetInput()

    tableaus.append(tab) 

    while True:
            rhsTest = []
            for i in range(len(tableaus[-1])):
                rhsTest.append(tableaus[-1][i][-1])
            allRhsPositive = all(num >= 0 for num in rhsTest)

            if allRhsPositive:
                break

            tab = DoDualPivotOperation(tableaus[-1])
            tableaus.append(tab)
            # print()
            # # printTab(tab)

    objFuncTest = []
    for i in range(len(tableaus[-1][0]) - 1):
        objFuncTest.append(tableaus[-1][0][i])

    # print()
    # print(objFuncTest)

    if isMin:
        allObjFuncPositive = all(num <= 0 for num in objFuncTest)
    else:
        allObjFuncPositive = all(num >= 0 for num in objFuncTest)

    if allObjFuncPositive:
        print("Optimal Solution Found")
        print(tableaus[-1][0][-1])
    else:
        # # print("No Optimal Solution Found")
        while True:
            objFuncTest = []
            for i in range(len(tableaus[-1][0]) - 1):
                objFuncTest.append(tableaus[-1][0][i])
            if isMin:
                allObjFuncPositive = all(num <= 0 for num in objFuncTest)
            else:
                allObjFuncPositive = all(num >= 0 for num in objFuncTest)

            if allObjFuncPositive:
                break

            tab = DoPrimalPivotOperation(tableaus[-1], isMin)
            tableaus.append(tab)
            # print()
            # printTab(tab)
        print("Optimal Solution Found")
        print(tableaus[-1][0][-1])

    for item in tableaus:
        printTab(item)
        print()

    # printTab(tableaus[-1])

    

def main():
    DoDualSimplex()
    # DoFormulationOperation()
    # tab = DoDualPivotOperation(DoFormulationOperation())
    # DoPrimalPivotOperation(tab)


    # TODO add contiues cheack for optimal and add graphical prettyness x1 x2 and add input
main()
