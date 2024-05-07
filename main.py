import math

import re

def read_file(file_path):
    with open(file_path, 'r') as file:
        content = file.readlines()

    # Extract the first list
    first_list_str = content[0].strip()
    first_list = [int(num.strip()) for num in first_list_str.strip('[]').split(',')]
    
    # # Extract the list of lists
    # second_list_str = [line.strip() for line in content[2:] if line.strip()]
    # second_list = [[int(num) for num in re.findall(r'\d+', sublist)] for sublist in second_list_str]

    # Extract the list of lists, skipping lines starting with '#'
    second_list_str = [line.strip() for line in content[2:] if line.strip() and not line.strip().startswith('#')]
    second_list = [[int(num) for num in re.findall(r'\d+', sublist)] for sublist in second_list_str]
    
    
    del second_list[0]
    del second_list[-1]

    return first_list, second_list

# def read_file(file_path):
#     with open(file_path, 'r') as file:
#         content = file.readlines()
    
#     # is_true = content[0].strip() == 0

#     first_list_str = content[1].strip()
#     first_list = [int(num.strip()) for num in first_list_str.strip('[]').split(',') if num.strip()]
    
#     # Extract the list of lists, skipping lines starting with '#'
#     second_list_str = [line.strip() for line in content[3:] if line.strip() and not line.strip().startswith('#')]
#     second_list = [[int(num) for num in re.findall(r'\d+', sublist)] for sublist in second_list_str]
    
#     del second_list[0]
#     del second_list[-1]
    
#     return first_list, second_list


# file_path = "data.txt"  # Replace "your_file.txt" with the path to your file
# first_list, second_list = read_file(file_path)

# print("First List:", first_list)
# print("Second List of Lists:", second_list)

def printTab(tab):
    if tab is None:
        return None
    for row in tab:
        print(row)


def DoFormulationOperation(objFunc, constraints):
    excessCount = 0
    slackCount = 0

    for i in range(len(constraints)):
        if constraints[i][-1] == 1:
            excessCount += 1
        else:
            slackCount += 1

    for i in range(len(constraints)):
        for j in range(len(constraints[i])):
            if constraints[i][-1] == 1:
                constraints[i][j] = -1 * constraints[i][j]

    for i in range(len(constraints)):
        del constraints[i][-1]

    tableSizeH = len(constraints) + 1

    tableSizeW = excessCount + slackCount + 1 + len(objFunc)
    opTable = []
    for i in range(tableSizeH):
        opTable.append([])
        for j in range(tableSizeW):
            opTable[i].append(0)

    for i in range(len(objFunc)):
        opTable[0][i] = -objFunc[i]

    for i in range(len(constraints)):
        for j in range(len(constraints[i]) - 1):
            opTable[i + 1][j] = constraints[i][j]
            opTable[i + 1][-1] = constraints[i][-1]

    # added the slack and excess 1s
    for i in range(1, len(opTable)):
        for j in range(len(objFunc), len(opTable[i]) - 1):
            opTable[i][i + 1 * len(objFunc) - 1] = 1

    return opTable


def DoDualPivotOperation(tab):
    thetaRow = []

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

    thetaRow = dualPivotThetas.copy()

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

    # print(f"the pivot col is {pivotColIndex} and the pivot row is {rowIndex}")

    return newTab, thetaRow


def DoPrimalPivotOperation(tab, isMin):
    thetasCol = []

    testRow = tab[0][:-1]

    if isMin:
        largestNegativeNumber = min(
            num for num in testRow if num < 0 and num != 0)
    else:
        largestNegativeNumber = min(
            num for num in testRow if num < 0 and num != 0)
        
    # print(largestNegativeNumber)

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

    thetasCol = thetas.copy()

    # print(thetas)

    # print("theatascol")
    # print(thetasCol)

    allNegativeThetas = all(num < 0 for num in thetas)

    if allNegativeThetas:
        return None

    minTheta = min(num for num in thetas if num > 0)

    rowIndex = thetas.index(minTheta) + 1

    # print()
    # printTab(tab)
    # print()

    # print(f"\nthe pivot row {rowIndex} and the pivot column {colIndex}")

    operationTab = []

    divNumber = tab[rowIndex][colIndex]

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

    print(f"the pivot col is {colIndex} and the pivot row is {rowIndex}")

    return operationTab, thetasCol


def GetInput():
    isMin = False
    objFunc = []    

    # 0 is <= and 1 is >= and 2 is =
    constrants = []

    # objFunc = [100, 30]

    # # 0 is <= and 1 is >= and 2 is =
    # constrants = [
    #     [0, 1, 3, 1],
    #     [1, 1, 7, 0],
    #     [10, 4, 40, 0]
    # ]

    # objFunc = [50, 20, 30, 80]

    # # 0 is <= and 1 is >= and 2 is =
    # constrants = [
    #     [400, 200, 150, 500, 500, 1],
    #     [3, 2, 0, 0, 6, 1],
    #     [2, 2, 4, 4, 10, 1],
    #     [2, 4, 1, 5, 8, 1],
    # ]

    # console input
    # isMin = int(input("is Problem max or min 0 or 1: "))
    # amtOfObjfuncs = int(input("amount of objective functions vars: "))
    # amtOfConstrants = int(input("amount of constrants: "))

    # for i in range(amtOfObjfuncs):
    #     objFunc.append(int(input(f"objective function x{i+1}: ")))

    # print("x-2 is what the constraint is = to")
    # print("x-1 is what the constraint sign is")
    # print("0 is <= and 1 is >= and 2 is = put it at the end")
    # for i in range(amtOfConstrants):
    #     constrants.append([])
    #     ctr = 1
    #     for j in range(amtOfObjfuncs + 2):
    #         if ctr != 0:
    #             constrants[i].append(int(input(f"constrant num {i+1} x{ctr}: ")))

    #         if ctr != amtOfObjfuncs:
    #             ctr += 1
    #         else:
    #             ctr = -2
    #     print()

    # isMin = False
    # objFunc = [100, 30]

    # # 0 is <= and 1 is >= and 2 is =
    # constrants = [
    #     [0, 1, 3, 1],
    #     [1, 1, 7, 0],
    #     [10, 4, 40, 0]
    # ]

    objFunc, constrants = read_file('data.txt')
    print("data in:")
    print(objFunc)
    print()
    print(constrants)

    amtOfE = 0
    amtOfS = 0
    for i in range(len(constrants)):
        if constrants[i][-1] == 1 or constrants[i][-1] == 2:
            amtOfE += 1
        else:
            amtOfS += 1

    tab = DoFormulationOperation(objFunc, constrants)

    # printTab(tab)
    # print(amtOfE, amtOfS)

    print()
    isMin = int(input("is Problem max or min 0 or 1: "))

    return tab, isMin, amtOfE, amtOfS, len(objFunc)


def DoDualSimplex():
    isMin = False
    # isMin = True

    # thetaRows = []
    thetaCols = []
    tableaus = []

    tab, isMin, amtOfE, amtOfS, lenObj = GetInput()

    tableaus.append(tab)
    displayTableau = []

    while True:
        rhsTest = []
        for i in range(len(tableaus[-1])):
            rhsTest.append(tableaus[-1][i][-1])
        allRhsPositive = all(num >= 0 for num in rhsTest)

        if allRhsPositive:
            break

        tab, thetaRow = DoDualPivotOperation(tableaus[-1])
        # displayTableau.append(tab)
        # displayTableau[-1].append(thetaRow)
        tableaus.append(tab)

    objFuncTest = []
    for i in range(len(tableaus[-1][0]) - 1):
        objFuncTest.append(tableaus[-1][0][i])

    if isMin:
        allObjFuncPositive = all(num <= 0 for num in objFuncTest)
    else:
        allObjFuncPositive = all(num >= 0 for num in objFuncTest)

    if allObjFuncPositive:
        print("Optimal Solution Found")
        print(tableaus[-1][0][-1])
        print()
    else:
        # # print("No Optimal Solution Found")
        while True:
            # printTab(tableaus[-1])

            if tableaus[-1] is None:
                print("No Optimal Solution Found")
                break

            objFuncTest = []
            for i in range(len(tableaus[-1][0]) - 1):
                objFuncTest.append(tableaus[-1][0][i])
            if isMin:
                allObjFuncPositive = all(num <= 0 for num in objFuncTest)
            else:
                allObjFuncPositive = all(num >= 0 for num in objFuncTest)

            if allObjFuncPositive:
                break

            tab, thetaCol = DoPrimalPivotOperation(tableaus[-1], isMin)
            
            # displayTableau.append(tab)
            thetaCols.append(thetaCol.copy())
            # displayTableau[-1][-1].append(thetaCol.copy)
            tableaus.append(tab)
            # print(tableaus[-1])

        print("Optimal Solution Found")
        if tableaus[-1] is not None:
            print(tableaus[-1][0][-1])
            print()
        else:
            print("No Optimal Solution Found")

    # for i in range(len(tableaus)):
    #     for j in range(len(tableaus[i])):
    #         tableaus[i][j].append(thetaCols[i][j])
            # print(tableaus[i][j][-1], end=" ")

                # if math.isnan(tableaus[i][j][k]):
                #     continue

    # for item in tableaus:
    #     printTab(item)
    #     print()

    xVars = []
    for i in range(lenObj):
        xVars.append("x{}".format(i + 1))

    amtOfX = 0
    amtOfSlack = 0
    amtOfExcess = 0

    topRow = []

    topRowSize = lenObj + amtOfE + amtOfS    

    # for i in range(topRowSize):
    #     if amtOfX < lenObj:
    #         topRow.append(xVars[amtOfX])
    #         amtOfX += 1

    #     if amtOfSlack < amtOfE:
    #         topRow.append("e{}".format(amtOfExcess + 1))
    #         amtOfSlack += 1

    #     if amtOfExcess < amtOfS:
    #         topRow.append("s{}".format(amtOfSlack + 1))
    #         amtOfExcess += 1

    for i in range(lenObj):
        if amtOfX < lenObj:
            topRow.append(xVars[amtOfX])
            amtOfX += 1
    
    for i in range(amtOfE):
        if amtOfSlack < amtOfE:
            topRow.append("e{}".format(amtOfExcess + 1))
            amtOfExcess += 1

    for i in range(amtOfS):
      if amtOfExcess < amtOfS:
            topRow.append("s{}".format(amtOfSlack + 1))
            amtOfSlack += 1

    topRow.append("Rhs")

    for i in range(len(tableaus)):
        print("Tableau {}".format(i + 1))
        print(" ".join(["{:>10}".format(val) for val in topRow]))
        for j in range(len(tableaus[i])):
            for k in range(len(tableaus[i][j])):
                print("{:10.3f}".format(tableaus[i][j][k]), end=" ")
            print()
        print()

def main():
    while True:
        DoDualSimplex()
        goAgin = input("exit press 1: ")
        if goAgin.lower() == "continue":
            continue
        elif goAgin == "1":
            break
        else:
            print("Invalid input. Please enter 1 to exit or 'continue' to continue.")
main()
