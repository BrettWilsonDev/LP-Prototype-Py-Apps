import copy
import math

import sys
import pygame
import OpenGL.GL as gl
from imgui.integrations.pygame import PygameRenderer
import imgui
import os

IMPivotCols = []
IMPivotRows = []
IMHeaderRow = []


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

    
    # objFunc = [5, -4, 3]

    # # # 0 is <= and 1 is >= and 2 is =
    # constraints = [
    #     [2, 1, -6, 20, 1],
    #     [2, 1, -6, 20, 0],
    #     [6, 5, 10, 76, 0],
    #     [8, -3, 6, 50, 0],
    # ]

    objFunc = [1200, 800]

    # # 0 is <= and 1 is >= and 2 is =
    constraints = [
        [8, 4, 1600, 0],
        [4, 4, 1000, 0],
        [1, 0, 170, 0],
        [0, 1, 200, 0],
        [1, 0, 40, 1],
        [0, 1, 25, 1],
        [1, -1, 0, 1],
        [1, -4, 0, 0],
    ]

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

    excessCount = 0
    slackCount = 0
    for i in range(len(constraints)):
        if constraints[i][-1] == 1:
            excessCount += 1
        else:
            slackCount += 1
            
    # build the display header row eg x1 x2 e1 e2 s1 s2 rhs
    imCtr = 1
    for i in range(len(objFunc)):
        IMHeaderRow.append("x" + str(imCtr))
        imCtr += 1

    imCtr = 1

    if excessCount > 0:
        for i in range(excessCount):
            IMHeaderRow.append("a" + str(imCtr))
            IMHeaderRow.append("e" + str(imCtr))
            imCtr += 1

    if slackCount > 0:
        for i in range(slackCount):
            IMHeaderRow.append("s" + str(imCtr))
            imCtr += 1

    IMHeaderRow.append("rhs")

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

    # constraints[2:].sort(key=lambda x: x[-1], reverse=True)
    # constraints.sort(key=lambda x: x[-1], reverse=True)

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

    global IMPivotCols
    IMPivotCols.append(pivotCol)
    global IMPivotRows
    IMPivotRows.append(pivotRow)

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

    global IMPivotCols
    IMPivotCols.append(pivotCol)
    global IMPivotRows
    IMPivotRows.append(pivotRow)

    return newTab, isAllNegZ

def DoTwoPhase(objFunc, constraints, isMin):
    # isMin = False
    tabs = []
    isAllNegW = False
    # objFunc, constraints, isMin = testInput()
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

    return tabs

def DoGui():
    pygame.init()
    size = 1920 / 2, 1080 / 2

    os.system('cls' if os.name == 'nt' else 'clear')
    print("\nBrett's simplex prototype tool for Two-Phase simplex problems\n")

    pygame.display.set_mode(size, pygame.DOUBLEBUF |
                            pygame.OPENGL | pygame.RESIZABLE)

    pygame.display.set_caption("Two-Phase Simplex Prototype")

    icon = pygame.Surface((1, 1)).convert_alpha()
    icon.fill((0, 0, 0, 1))
    pygame.display.set_icon(icon)

    imgui.create_context()
    impl = PygameRenderer()

    io = imgui.get_io()
    io.display_size = size

    # simplex specific vars
    problemType = "Max"

    # dual constraints
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
        # windowing stuff
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
        

        # simplex stuff

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
                tableaus = DoTwoPhase(a, b, isMin)

                del tableaus[-2]

                IMPivotCols.append(-1)
                IMPivotRows.append(-1)

                # IMPivotCols.append(-1)
                # IMPivotRows.append(-1)

                print(len(tableaus))

                tRow = copy.deepcopy(IMPivotRows)
                tCol = copy.deepcopy(IMPivotCols)
                tHeader = copy.deepcopy(IMHeaderRow)

                IMHeaderRow.clear()
                IMPivotRows.clear()
                IMPivotCols.clear()

            except Exception as e:
                print("math error:", e)

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
                    imgui.text("w  ")
                elif j == 1:
                    imgui.text("z  ")
                else:
                    imgui.text("c " + str(j - 1))
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
    # DoTwoPhase()
    DoGui()

main()
