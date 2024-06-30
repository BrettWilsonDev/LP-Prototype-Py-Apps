import sympy as sp

import re

import sys
import pygame
import OpenGL.GL as gl
from imgui.integrations.pygame import PygameRenderer
import imgui
import os
import copy

import dualSimplex
import mathPrelims


def testInput():
    isMin = False

    objFunc = [60, 30, 20]
    constraints = [[8, 6, 1, 48, 0],
                   [4, 2, 1.5, 20, 0],
                   [2, 1.5, 0.5, 8, 0],
                   ]

    addedConstraints = [
        [1, 0, 0, 2, 1],
        [0, 1, 0, 2, 1],
        [0, 0, 1, 2, 1],
    ]

    # addedConstraints = [
    #     [1, 0, 0, 1, 1],
    # ]

    # # addedActivities = [15, 1, 1, 1]
    # # addedActivities = []

    # objFunc = [30, 28, 26, 30]
    # constraints = [[8, 8, 4, 4, 160, 0],
    #                [1, 0, 0, 0, 5, 0],
    #                [1, 0, 0, 0, 5, 1],
    #                [1, 1, 1, 1, 20, 1],
    #                ]

    # addedConstraints = [
    #     [1, -1, 0, 0, 0, 0],
    #     [-1, 1, 0, 0, 0, 1],
    # ]

    return objFunc, constraints, isMin, addedConstraints


def GetMathPrelims(objFunc, constraints, isMin, absRule=False):
    changingTable, matrixCbv, matrixB, matrixBNegOne, matrixCbvNegOne, basicVarSpots = mathPrelims.doSensitivityAnalysis(
        objFunc, constraints, isMin, absRule)
    return changingTable, matrixCbv, matrixB, matrixBNegOne, matrixCbvNegOne, basicVarSpots


def DoAddActivity(objFunc, constraints, isMin, activity, absRule=False):
    changingTable, matrixCbv, matrixB, matrixBNegOne, matrixCbvNegOne, basicVarSpots = GetMathPrelims(
        objFunc, constraints, isMin, absRule)

    matrixAct = sp.Matrix(activity[1:])

    c = matrixAct.transpose() * matrixCbvNegOne

    cTop = c[0, 0] - activity[0]

    b = matrixAct.transpose() * matrixBNegOne

    tdisplayCol = b.tolist()

    displayCol = []
    for i in range(len(tdisplayCol[-1])):
        displayCol.append(tdisplayCol[-1][i])

    displayCol.insert(0, cTop)

    print(displayCol)

    return displayCol, changingTable


def DoAddConstraint(objFunc, constraints, isMin, addedConstraints, absRule=False, reverseRows=False, negRuleState=False):
    changingTable, matrixCbv, matrixB, matrixBNegOne, matrixCbvNegOne, basicVarSpots = GetMathPrelims(
        objFunc, constraints, isMin=False, absRule=False)

    newTab = copy.deepcopy(changingTable)

    for k in range(len(addedConstraints)):
        for i in range(len(changingTable)):
            newTab[i].insert(-1, 0.0)

        newCon = []
        for i in range(len(changingTable[0]) + len(addedConstraints)):
            newCon.append(0.0)

        for i in range(len(addedConstraints[k]) - 2):
            newCon[i] = float(addedConstraints[k][i])

        newCon[-1] = float(addedConstraints[k][-2])

        slackSpot = ((len(newCon) - len(addedConstraints)) - 1) + k
        if addedConstraints[k][-1] == 1:
            newCon[slackSpot] = -1.0
        else:
            newCon[slackSpot] = 1.0

        newTab.append(newCon)

    print("\nunfixed tab")
    for i in range(len(newTab)):
        for j in range(len(newTab[i])):
            print(newTab[i][j], end="     ")
        print()
    print("\n\n")

    displayTab = copy.deepcopy(newTab)
    for k in range(len(addedConstraints)):
        for i in range(len(newTab[0])):
            tLst = []
            for j in range(len(newTab)):
                tLst.append(newTab[j][i])
            if i in basicVarSpots:
                if tLst[-(len(addedConstraints) - (k))] != 0:
                    testLst = []

                    for ojCtr in range(len(objFunc)):
                        testLst.append([])

                    for ntCtr in range(len(newTab)):
                        for ojCtr in range(len(objFunc)):
                            testLst[ojCtr].append(newTab[ntCtr][ojCtr])

                    colIndex = testLst.index(tLst)

                    bottomRow = ((k) + len(newTab) - len(addedConstraints))
                    for spotsCtr in range(len(newTab) - len(addedConstraints)):
                        if testLst[colIndex][spotsCtr] == 1:
                            topRow = spotsCtr
                            tempNewRow = []

                            for newTabCtr in range(len(newTab[0])):
                                if newTab[bottomRow][colIndex] == -1:
                                    if reverseRows:
                                        tempNewRow.append(
                                            newTab[topRow][newTabCtr] + newTab[topRow][newTabCtr])
                                    else:
                                        tempNewRow.append(
                                            newTab[bottomRow][newTabCtr] + newTab[topRow][newTabCtr])
                                elif newTab[bottomRow][colIndex] == 1:
                                    if reverseRows:
                                        tempNewRow.append(
                                            newTab[topRow][newTabCtr] - newTab[bottomRow][newTabCtr])
                                    else:
                                        tempNewRow.append(
                                            newTab[bottomRow][newTabCtr] - newTab[topRow][newTabCtr])
                                else:
                                    pass

                            displayTab[bottomRow] = tempNewRow

    negRows = []
    if negRuleState:
        for i in range(len(changingTable), len(displayTab)):
            for j in range(len(changingTable[-1]) - 1, len(displayTab[i]) - 1):
                if displayTab[i][j] < 0:
                    negRows.append(i)

        for i in range(len(negRows)):
            for j in range(len(displayTab[0])):
                displayTab[negRows[i]][j] = -displayTab[negRows[i]][j]

    print("fixed tab")
    for i in range(len(displayTab)):
        for j in range(len(displayTab[i])):
            print(displayTab[i][j], end="     ")
        print()

    return displayTab, newTab


def DoGui():
    pygame.init()
    size = 1920 / 2, 1080 / 2

    os.system('cls' if os.name == 'nt' else 'clear')

    pygame.display.set_mode(size, pygame.DOUBLEBUF |
                            pygame.OPENGL | pygame.RESIZABLE)

    pygame.display.set_caption(
        "adding activities/constraints Simplex Prototype")

    icon = pygame.Surface((1, 1)).convert_alpha()
    icon.fill((0, 0, 0, 1))
    pygame.display.set_icon(icon)

    imgui.create_context()
    impl = PygameRenderer()

    io = imgui.get_io()
    io.display_size = size

    # simplex specific vars

    problemType = "Max"
    absProblemType = "abs Off"

    # dual constraints
    amtOfObjVars = 2
    objFunc = [0.0, 0.0]

    constraints = [[0.0, 0.0, 0.0, 0.0]]
    signItems = ["<=", ">="]
    signItemsChoices = [0]

    amtOfConstraints = 1

    activity = [0.0, 0.0]

    absRule = False

    problemChoice = "activity"

    problemState = True

    actDisplayCol = []

    amtOfAddingConstraints = 1

    addingConstraints = []

    addingSignItemsChoices = [0]

    fixedTab = []
    unfixedTab = []

    changingTable = []

    IMPivotCols = []
    IMPivotRows = []
    IMHeaderRow = []

    pivotCol = -1
    pivotRow = -1

    newTableaus = []

    reverseRowsState = False
    rowsReversed = "off"

    negRuleState = False
    negRule = "off"

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

        if imgui.radio_button("abs on", absProblemType == "abs On"):
            absProblemType = "abs On"

        if imgui.radio_button("abs off", absProblemType == "abs Off"):
            absProblemType = "abs Off"

        imgui.text("absolute rule is: {}".format(absProblemType))

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
                pass

        if imgui.button("Constraint +"):
            amtOfConstraints += 1
            constraints.append([0.0] * amtOfObjVars)
            constraints[-1].append(0.0)  # add sign spot
            constraints[-1].append(0.0)  # add rhs spot
            signItemsChoices.append(0)

            activity.append(0.0)

        imgui.same_line()

        if imgui.button("Constraint -"):
            if amtOfConstraints != 1:
                amtOfConstraints += -1
                constraints.pop()
                signItemsChoices.pop()

                activity.pop()

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

        if imgui.radio_button("adding activity", problemChoice == "activity"):
            problemChoice = "activity"

        imgui.same_line(0, 20)

        if imgui.radio_button("adding constraints", problemChoice == "constraints"):
            problemChoice = "constraints"

        imgui.text("the current problem is adding {}".format(problemChoice))

        if problemType == "Min":
            isMin = True
        else:
            isMin = False

        if absProblemType == "abs On":
            absRule = True
        else:
            absRule = False

        if problemChoice == "activity":
            problemState = True
        else:
            problemState = False

        if problemState:
            imgui.new_line()
            for i in range(len(constraints) + 1):
                value = (activity[i])
                imgui.set_next_item_width(50)
                imgui.same_line()
                imgui.new_line()
                changed, activity[i] = imgui.input_float(
                    "activity {}".format(i + 1), value)
                if i == 0:
                    imgui.same_line()
                    imgui.text("x")
                else:
                    imgui.same_line()
                    imgui.text("c{}".format(i))
        else:
            if imgui.button("aConstraint +"):
                amtOfAddingConstraints += 1
                addingConstraints.append([0.0] * amtOfObjVars)
                addingConstraints[-1].append(0.0)  # add sign spot
                addingConstraints[-1].append(0.0)  # add rhs spot
                addingSignItemsChoices.append(0)

            imgui.same_line()

            if imgui.button("aConstraint -"):
                if amtOfAddingConstraints != 1:
                    amtOfAddingConstraints += -1
                    addingConstraints.pop()
                    addingSignItemsChoices.pop()

            for i in range(amtOfAddingConstraints):
                imgui.spacing()
                if len(addingConstraints) <= i:
                    addingConstraints.append([0.0] * (amtOfObjVars + 2))

                for j in range(amtOfObjVars):
                    value = (addingConstraints[i][j])
                    imgui.set_next_item_width(50)
                    imgui.same_line()
                    changed, xValue = imgui.input_float(
                        "axC{}{}".format(i, j), value)
                    if changed:
                        addingConstraints[i][j] = xValue

                imgui.same_line()
                imgui.push_item_width(50)
                changed, selectedItemSign = imgui.combo(
                    "acomboC{}{}".format(i, j), addingSignItemsChoices[i], signItems)
                if changed:
                    addingSignItemsChoices[i] = selectedItemSign
                    addingConstraints[i][-1] = addingSignItemsChoices[i]

                imgui.pop_item_width()
                imgui.same_line()
                imgui.set_next_item_width(50)
                rhsValue = (addingConstraints[i][-2])
                rhsChanged, rhs = imgui.input_float(
                    "aRHSC{}{}".format(i, j), rhsValue)

                if rhsChanged:
                    addingConstraints[i][-2] = rhs

            if imgui.radio_button("reverse rows on", rowsReversed == "on"):
                rowsReversed = "on"

            imgui.same_line(0, 20)

            if imgui.radio_button("reverse rows off", rowsReversed == "off"):
                rowsReversed = "off"

            imgui.text("reversing of rows is: {}".format(rowsReversed))

            if rowsReversed == "on":
                reverseRowsState = True
            else:
                reverseRowsState = False

            if imgui.radio_button("keep slack basic on", negRule == "on"):
                negRule = "on"

            imgui.same_line(0, 20)

            if imgui.radio_button("keep slack basic off", negRule == "off"):
                negRule = "off"

            imgui.text("keep slack basic is: {}".format(negRule))

            if negRule == "on":
                negRuleState = True
            else:
                negRuleState = False

        imgui.spacing()
        imgui.spacing()
        # the solve button =================================================
        if imgui.button("Solve"):
            try:
                # objFunc, constraints, isMin, addingConstraints = testInput()

                a = copy.deepcopy(objFunc)
                b = copy.deepcopy(constraints)

                if problemState:
                    c = copy.deepcopy(activity)
                    actDisplayCol, changingTable = DoAddActivity(
                        a, b, isMin, c, absRule)
                else:
                    e = copy.deepcopy(addingConstraints)
                    addedConstraints = addingConstraints
                    print(addingConstraints)
                    fixedTab, unfixedTab = DoAddConstraint(
                        a, b, isMin, e, absRule, reverseRowsState, negRuleState)

            except Exception as e:
                print("math error:", e)

        imgui.spacing()
        imgui.spacing()
        imgui.spacing()
        imgui.spacing()

        if problemState:
            for i in range(len(actDisplayCol)):
                if i == 0:
                    imgui.text("Activity    ")
                else:
                    imgui.text("Constraint {}".format(i))
                imgui.same_line()
                imgui.text("{:>15.3f}".format(float(actDisplayCol[i])))
                imgui.new_line()
        else:
            imgui.text("unfixed Tab:")
            for i in range(len(unfixedTab)):
                for j in range(len(unfixedTab[i])):
                    if i >= (len(unfixedTab) - len(addedConstraints)):
                        imgui.push_style_color(imgui.COLOR_TEXT, 1.0, 1.0, 0.0)
                    imgui.text("{:>9.3f}".format(float(unfixedTab[i][j])))
                    if i >= (len(unfixedTab) - len(addedConstraints)):
                        imgui.pop_style_color()
                    imgui.same_line(0, 20)
                imgui.new_line()

            imgui.spacing()
            imgui.spacing()
            imgui.spacing()

            imgui.text("fixed Tab:")
            for i in range(len(fixedTab)):
                for j in range(len(fixedTab[i])):
                    if i >= (len(unfixedTab) - len(addedConstraints)):
                        imgui.push_style_color(imgui.COLOR_TEXT, 1.0, 1.0, 0.0)
                    imgui.text("{:>9.3f}".format(float(fixedTab[i][j])))
                    if i >= (len(unfixedTab) - len(addedConstraints)):
                        imgui.pop_style_color()
                    imgui.same_line(0, 20)
                imgui.new_line()

        imgui.spacing()
        imgui.spacing()
        imgui.spacing()
        imgui.spacing()

        if imgui.button("Optimize again"):
            if problemState:
                tab = copy.deepcopy(changingTable)

                for i in range(len(tab)):
                    tab[i].insert(len(objFunc), float(actDisplayCol[i]))
                    print(float(actDisplayCol[i]))

                print()
                for i in range(len(tab)):
                    for j in range(len(tab[i])):
                        print(tab[i][j], end=" ")
                    print()

                try:
                    newTableaus, changingVars, optimalSolution, IMPivotCols, IMPivotRows, IMHeaderRow = dualSimplex.DoDualSimplex([
                    ], [], isMin, tab)

                    IMHeaderRow.clear()

                    for i in range(len(newTableaus[-1][-1])):
                        if i < (len(objFunc) + 1):
                            IMHeaderRow.append(f"x{i+1}")
                        elif i == (len(newTableaus[-1][-1]) - 1):
                            IMHeaderRow.append(f"rhs")
                        else:
                            IMHeaderRow.append(f"h{i+1}")

                    print()
                    for i in range(len(newTableaus[-1])):
                        for j in range(len(newTableaus[-1][i])):
                            print(float(newTableaus[-1][i][j]), end=" ")
                        print()

                except Exception as e:
                    print("math error in Optimize again:", e)
            else:
                print()
                for i in range(len(fixedTab)):
                    for j in range(len(fixedTab[i])):
                        print(float(fixedTab[i][j]), end=" ")
                    print()

                tab = copy.deepcopy(fixedTab)

                try:
                    newTableaus, changingVars, optimalSolution, IMPivotCols, IMPivotRows, IMHeaderRow = dualSimplex.DoDualSimplex([
                    ], [], isMin, tab)

                    IMHeaderRow.clear()

                    for i in range(len(newTableaus[-1][-1])):
                        if i <= (len(objFunc) - 1):
                            IMHeaderRow.append(f"x{i+1}")
                        elif i == (len(newTableaus[-1][-1]) - 1):
                            IMHeaderRow.append(f"rhs")
                        else:
                            IMHeaderRow.append(f"h{i+1}")

                except Exception as e:
                    print("math error in Optimize again:", e)

        imgui.spacing()
        imgui.spacing()
        imgui.spacing()
        imgui.spacing()

        for i in range(len(newTableaus)):
            if i < len(IMPivotCols):
                pivotCol = IMPivotCols[i]
                pivotRow = IMPivotRows[i]
            else:
                pivotCol = -1
                pivotRow = -1
            imgui.text("Tableau {}".format(i + 1))
            imgui.text("t-" + str(i + 1))
            imgui.same_line(0, 20)
            for hCtr in range(len(IMHeaderRow)):
                imgui.text("{:>8}".format(str(IMHeaderRow[hCtr])))
                imgui.same_line(0, 20)
            imgui.spacing()
            for j in range(len(newTableaus[i])):
                if j == pivotRow and pivotRow != -1:
                    imgui.push_style_color(imgui.COLOR_TEXT, 0.0, 1.0, 0.0)
                if j == 0:
                    imgui.text("z  ")
                else:
                    imgui.text("c " + str(j))
                imgui.same_line(0, 20)
                for k in range(len(newTableaus[i][j])):
                    if k == pivotCol and pivotCol != -1:
                        imgui.push_style_color(
                            imgui.COLOR_TEXT, 0.0, 1.0, 0.0)
                    imgui.text("{:>8.3f}".format(newTableaus[i][j][k]))
                    if k < len(newTableaus[i][j]) - 1:
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


main()
