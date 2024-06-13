import math

import re

# import tkinter as tk**

import sys
import pygame
import OpenGL.GL as gl
from imgui.integrations.pygame import PygameRenderer
import imgui
import os
import copy

IMPivotCols = []
IMPivotRows = []
IMHeaderRow = []

def read_file(file_path):
    with open(file_path, 'r') as file:
        content = file.readlines()

    # Extract the first list
    first_list_str = content[0].strip()
    first_list = [float(num.strip())
                  for num in first_list_str.strip('[]').split(',')]

    # # Extract the list of lists
    # second_list_str = [line.strip() for line in content[2:] if line.strip()]
    # second_list = [[int(num) for num in re.findall(r'\d+', sublist)] for sublist in second_list_str]

    # Extract the list of lists, skipping lines starting with '#'
    second_list_str = [line.strip() for line in content[2:]
                       if line.strip() and not line.strip().startswith('#')]
    second_list = [[float(num) for num in re.findall(r'\d+', sublist)]
                   for sublist in second_list_str]

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

    # print(excessCount, slackCount, len(objFunc))

    # build the display header row eg x1 x2 e1 e2 s1 s2 rhs
    imCtr = 1
    for i in range(len(objFunc)):
        IMHeaderRow.append("x" + str(imCtr))
        imCtr += 1

    imCtr = 1

    if excessCount > 0:
        for i in range(excessCount):
            IMHeaderRow.append("e" + str(imCtr))
            imCtr += 1

    if slackCount > 0:
        for i in range(slackCount):
            IMHeaderRow.append("s" + str(imCtr))
            imCtr += 1

    IMHeaderRow.append("rhs")
    
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
    # for item in tab:
    #     if item == -0.0:
    #         item = 0.0

    thetaRow = []

    rhs = [row[-1] for row in tab]
    rhsNeg = [row[-1] for row in tab if row[-1] < 0]
    # minRhsNum = min(rhs)
    # print(rhsNeg)
    # minRhsNum = max(rhsNeg)
    minRhsNum = min(rhsNeg)

    # print(minRhsNum)

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

    # print(smallestPosPivotTheta)

    rowIndex = pivotRow
    colIndex = dualPivotThetas.index(smallestPosPivotTheta)
    # print(colIndex)

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

    print(f"the pivot col in Dual is {
          colIndex + 1} and the pivot row is {rowIndex + 1}")
    
    global IMPivotCols
    IMPivotCols.append(colIndex)
    global IMPivotRows
    IMPivotRows.append(rowIndex)

    return newTab, thetaRow


def DoPrimalPivotOperation(tab, isMin):
    # for item in tab:
    #     if item == -0.0:
    #         item = 0.0

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

    # todo fix the below
    if minTheta == float('inf'):
        if 0 in thetas:
            minTheta = 0
        else:
            return None, None

    # print(f"thetas: {thetas}")
    # print(f"t")
    rowIndex = thetas.index(minTheta) + 1

    # print()
    # printTab(tab)
    # print()

    # print(f"\n######################the pivot row {rowIndex} and the pivot column {colIndex}")

    operationTab = []

    divNumber = tab[rowIndex][colIndex]
    # print(divNumber)

    # if divNumber == 'inf':
    #     divNumber = 1

    if divNumber == 0:
        return None, None

    # print("div number", divNumber)

    operationTab = [[0 for _ in row] for row in tab]

    for i in range(len(tab)):
        for j in range(len(tab[i])):
            # print(f"{operationTab[rowIndex][j]} = {tab[rowIndex][j]} / {divNumber}")
            operationTab[rowIndex][j] = tab[rowIndex][j] / divNumber
            if operationTab[rowIndex][j] == -0.0:
                operationTab[rowIndex][j] = 0.0

            # if divNumber != 0:
            #     operationTab[rowIndex][j] = tab[rowIndex][j] / divNumber
            # else:
            #     operationTab[rowIndex][j] = float('inf')
            # if operationTab[rowIndex][j] == -0.0:
            #     operationTab[rowIndex][j] = 0.0

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

    print(f"the pivot col in primal is {
          colIndex + 1} and the pivot row is {rowIndex + 1}")
    
    global IMPivotCols
    IMPivotCols.append(colIndex)
    global IMPivotRows
    IMPivotRows.append(rowIndex)

    return operationTab, thetasCol


def GetInput(objFunc, constrants, isMin):
    # isMin = False
    # objFunc = []

    # 0 is <= and 1 is >= and 2 is =
    # constrants = []

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

    # objFunc, constrants = read_file('data.txt')
    # print("data in:")
    # print(f"objective function {objFunc}")
    # print()
    # print(f"constrants {constrants}")

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

    # print()
    # isMin = int(input("is Problem max or min 0 or 1: "))

    return tab, isMin, amtOfE, amtOfS, len(objFunc)


def DoDualSimplex(objFunc, constraints, isMin):
    print()
    # isMin = False
    # isMin = True

    # thetaRows = []
    thetaCols = []
    tableaus = []

    tab, isMin, amtOfE, amtOfS, lenObj = GetInput(objFunc, constraints, isMin)
    print()

    tableaus.append(tab)

    while True:
        for items in tableaus[-1]:
            for item in items:
                if item == -0.0:
                    item = 0.0

        rhsTest = []
        for i in range(len(tableaus[-1])):
            rhsTest.append(tableaus[-1][i][-1])
        allRhsPositive = all(num >= 0 for num in rhsTest)

        if allRhsPositive:
            break

        tab, thetaRow = DoDualPivotOperation(tableaus[-1])
        # displayTableau.append(tab)
        # displayTableau[-1].append(thetaRow)
        for items in tab:
            for item in items:
                if item == -0.0:
                    item = 0.0
        tableaus.append(tab)

    objFuncTest = []
    for i in range(len(tableaus[-1][0]) - 1):
        objFuncTest.append(tableaus[-1][0][i])

    if isMin:
        allObjFuncPositive = all(num <= 0 for num in objFuncTest)
    else:
        allObjFuncPositive = all(num >= 0 for num in objFuncTest)

    if allObjFuncPositive:
        print("\nOptimal Solution Found")
        print(tableaus[-1][0][-1])
        print()
    else:
        # # print("No Optimal Solution Found")
        while True:
            # printTab(tableaus[-1])

            for items in tableaus[-1]:
                for item in items:
                    if item == -0.0:
                        item = 0.0

            if tableaus[-1] is None:
                print("\nNo Optimal Solution Found")
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

            if thetaCol is None and tab is None:
                break

            # displayTableau.append(tab)
            thetaCols.append(thetaCol.copy())
            # displayTableau[-1][-1].append(thetaCol.copy)
            tableaus.append(tab)
            # print(tableaus[-1])

        print("\nOptimal Solution Found")
        if tableaus[-1] is not None:
            print(tableaus[-1][0][-1])
            print()
        else:
            print("\nNo Optimal Solution Found")

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

        # print(tableaus)

        # flattened_data = [item for sublist in tableaus for subsublist in sublist for item in subsublist]

        # for item in flattened_data:
        #     imgui.text(f'{item:8.3f}')

    return tableaus


def DoGui():
    pygame.init()
    size = 1920 / 2, 1080 / 2

    os.system('cls' if os.name == 'nt' else 'clear')
    print("\nBrett's simplex prototype tool for dual simplex problems\n")

    pygame.display.set_mode(size, pygame.DOUBLEBUF |
                            pygame.OPENGL | pygame.RESIZABLE)

    pygame.display.set_caption("dual Simplex Prototype")

    icon = pygame.Surface((1, 1)).convert_alpha()
    icon.fill((0, 0, 0, 1))
    pygame.display.set_icon(icon)

    imgui.create_context()
    impl = PygameRenderer()

    io = imgui.get_io()
    io.display_size = size

    problemType = "Max"

    # constraints = []

    # goal constraints
    amtOfObjVars = 2
    objFunc = [0.0, 0.0]

    constraints = [[0.0, 0.0, 0.0, 0.0]]
    signItems = ["<=", ">="]
    signItemsChoices = [0]

    amtOfConstraints = 1

    tableaus = []

    pivotCol = -1
    pivotRow = -1
    tCol = -1
    tRow = -1
    tHeader = []

    global IMPivotCols
    global IMPivotRows
    global IMHeaderRow


    while 1:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()

            impl.process_event(event)

        imgui.new_frame()

        window_size = pygame.display.get_window_size()

        imgui.set_next_window_position(0, 0)  # Set the window position
        imgui.set_next_window_size(
            (window_size[0]), (window_size[1]))  # Set the window size
        imgui.begin("Tableaus Output",
                    flags=imgui.WINDOW_NO_TITLE_BAR | imgui.WINDOW_NO_RESIZE)

        if imgui.radio_button("Max", problemType == "Max"):
            problemType = "Max"

        if imgui.radio_button("Min", problemType == "Min"):
            problemType = "Min"

        imgui.text("Problem is: {}".format(problemType))

        # obj vars ===========================================
        if imgui.button("decision variables +"):
            amtOfObjVars += 1
            for i in range(len(constraints)):
                constraints[i].append(0.0)
            objFunc.append(0.0)

        imgui.same_line()

        if imgui.button("decision variables -"):
            if amtOfObjVars != 2:
                amtOfObjVars += -1
                for i in range(len(constraints)):
                    constraints[i].pop()
                objFunc.pop()

        imgui.spacing()

        for i in range(len(objFunc)):
            value = objFunc[i]
            imgui.set_next_item_width(50)
            imgui.same_line()
            changed, objFunc[i] = imgui.input_float(
                "objFunc {}".format(i + 1), value)

            if changed:
                # Value has been updated
                pass

        if imgui.button("Constraint +"):
            amtOfConstraints += 1
            constraints.append([0.0] * amtOfObjVars)
            constraints[-1].append(0.0)  # add sign spot
            constraints[-1].append(0.0)  # add rhs spot
            signItemsChoices.append(0)

        imgui.same_line()

        if imgui.button("Constraint -"):
            if amtOfConstraints != 1:
                amtOfConstraints += -1
                constraints.pop()
                signItemsChoices.pop()

        # spaceGui(6)
        for i in range(amtOfConstraints):
            imgui.spacing()
            if len(constraints) <= i:
                # Fill with default values if needed
                constraints.append([0.0] * (amtOfObjVars + 2))

            for j in range(amtOfObjVars):
                value = constraints[i][j]
                imgui.set_next_item_width(50)
                imgui.same_line()
                changed, xValue = imgui.input_float(
                    "xC{}{}".format(i, j), value)
                if changed:
                    constraints[i][j] = xValue

            imgui.same_line()
            imgui.push_item_width(50)
            changed, selectedItemSign = imgui.combo(
                "comboC{}{}".format(i, j), signItemsChoices[i], signItems)
            if changed:
                signItemsChoices[i] = selectedItemSign
                constraints[i][-1] = signItemsChoices[i]

            imgui.pop_item_width()
            imgui.same_line()
            imgui.set_next_item_width(50)
            rhsValue = constraints[i][-2]
            rhsChanged, rhs = imgui.input_float(
                "RHSC{}{}".format(i, j), rhsValue)

            if rhsChanged:
                constraints[i][-2] = rhs

        if problemType == "Min":
            isMin = True
        else:
            isMin = False

        if imgui.button("Solve"):
            print(objFunc, constraints, isMin)
            try:
                a = copy.deepcopy(objFunc)
                b = copy.deepcopy(constraints)
                tableaus = DoDualSimplex(a, b, isMin)
                # constraints = [[0.0, 0.0, 0.0, 0.0]]
                # amtOfObjVars = 2
                # objFunc = [0.0, 0.0]
                # print(len(tableaus))
                # print(len(IMPivotCols))
                # print(len(IMPivotRows))
                # print(IMPivotRows)

                IMPivotCols.append(-1)
                IMPivotRows.append(-1)

                # print(IMHeaderRow[-1])
                # print(len(IMHeaderRow))
                # print()
                # print(len(tableaus))
                # print(len(tableaus[-1]))
                # print(len(tableaus[-1][-1]))


                tRow = copy.deepcopy(IMPivotRows)
                tCol = copy.deepcopy(IMPivotCols)
                tHeader = copy.deepcopy(IMHeaderRow)

                IMHeaderRow.clear()
                IMPivotRows.clear()
                IMPivotCols.clear()


                # for item in flattened_data:
                #     imgui.text(f'{item:8.3f}')
                text = "solved"
            except Exception as e:
                print("math error:", e)


        # for i in range(len(tableaus)):
        #     for j in range(len(tableaus[i])):
        #         for k in range(len(tableaus[i][j])):
        #             imgui.text("{:>8.3f}".format(tableaus[i][j][k]))
        #             if k < len(tableaus[i][j]) - 1:
        #                 imgui.same_line(0, 20)
        #         imgui.spacing()
        #     imgui.spacing()

        # pivotCol = 2
        # pivotRow = 1

        imgui.spacing()
        imgui.spacing()
        for i in range(len(tableaus)):
            pivotCol = tCol[i]
            pivotRow = tRow[i]
            imgui.text("Tableau {}".format(i + 1))
            imgui.text("t-" + str(i + 1))
            imgui.same_line(0, 20)
            for hCtr in range(len(tHeader)):
                imgui.text("{:>8}".format(str(tHeader[hCtr])))
                imgui.same_line(0, 20)
            imgui.spacing()
            for j in range(len(tableaus[i])):
                if j == pivotRow and pivotRow != -1:
                    imgui.push_style_color(imgui.COLOR_TEXT, 0.0, 1.0, 0.0)
                if j == 0:
                    imgui.text("z  ")
                else:
                    imgui.text("c " + str(j))
                imgui.same_line(0, 20)
                for k in range(len(tableaus[i][j])):
                    if k == pivotCol and pivotCol != -1:
                        imgui.push_style_color(imgui.COLOR_TEXT, 0.0, 1.0, 0.0)
                    imgui.text("{:>8.3f}".format(tableaus[i][j][k]))
                    if k < len(tableaus[i][j]) - 1:
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

        imgui.end()

        # gl stuff
        gl.glClearColor(0, 0, 0, 1)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        imgui.render()
        impl.render(imgui.get_draw_data())

        pygame.display.flip()

def main():

    DoGui()
    # while True:
    #     DoDualSimplex()
    #     print()
    #     goAgin = input("To exit press 1 or Press enter to continue: ")
    #     if goAgin.lower() == "continue":
    #         continue
    #     elif goAgin == "1":
    #         break
main()
