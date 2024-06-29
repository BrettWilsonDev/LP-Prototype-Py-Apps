import dualSimplex

import math

import re

import sys
import pygame
import OpenGL.GL as gl
from imgui.integrations.pygame import PygameRenderer
import imgui
import os
import copy

def transposeMat(matrix):
    return [list(row) for row in zip(*matrix)]

def doGui():
    objFunc = []
    optimalSolution = 0
    changingVars = []
    constraintsLhs = []
    cellRef = []
    dualObjFunc = []
    dualOptimalSolution = 0
    dualChangingVars = []
    dualConstraintsLhs = []
    dualCellRef = []

    pygame.init()
    size = 1920 / 2, 1080 / 2

    os.system('cls' if os.name == 'nt' else 'clear')

    pygame.display.set_mode(size, pygame.DOUBLEBUF |
                            pygame.OPENGL | pygame.RESIZABLE)

    pygame.display.set_caption("duality Prototype")

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

    headerString = []
    dualHeaderString = []

    tObjFunc = []
    tDualObjFunc = []

    errorE = ""

    strMin = ""
    strDualMin = ""

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
            try:
                headerString.clear()
                dualHeaderString.clear()

                a = copy.deepcopy(objFunc)
                b = copy.deepcopy(constraints)
                objFunc, optimalSolution, changingVars, constraintsLhs, cellRef, dualObjFunc, dualOptimalSolution, dualChangingVars, dualConstraintsLhs, dualCellRef = doDuality(a, b, isMin)

                # for display reasons
                tObjFunc = copy.deepcopy(objFunc)
                tDualObjFunc = copy.deepcopy(dualObjFunc)
                tObjFunc.append(optimalSolution)
                tDualObjFunc.append(dualOptimalSolution)

                dualMin = not isMin

                if isMin:
                    strMin = "max"
                else:
                    strMin = "min"

                if dualMin:
                    strDualMin = "max"
                else:
                    strDualMin = "min"

                headerString.append("Primal")
                dualHeaderString.append("Dual")

                for i in range(len(objFunc)):
                    headerString.append("x{}".format(i + 1))

                for i in range(len(dualObjFunc)):
                    dualHeaderString.append("y{}".format(i + 1))


                headerString.append("Ref")
                headerString.append("Sign")
                headerString.append("Rhs")
                headerString.append("Slack")

                dualHeaderString.append("Ref")
                dualHeaderString.append("Sign")
                dualHeaderString.append("Rhs")
                dualHeaderString.append("Slack")


                # print(f"header {headerString}")
                errorE = ""
            except Exception as e:
                print("math error:", e)
                imgui.text("math error: {}".format(e))
                errorE = "math error: {}".format(e)

        imgui.spacing()
        imgui.text(errorE)
                
        imgui.spacing()
        imgui.spacing()

        try:
            for i in range(len(headerString)):
                imgui.text("{:>8}".format(headerString[i]))
                imgui.same_line(0, 20)

            imgui.spacing()
            
            # display the objective function
            imgui.text("{:>8}".format(f"{strDualMin} z"))
            imgui.same_line(0, 20)
            for i in range(len(tObjFunc)):
                if i != len(tObjFunc) - 1:
                    imgui.push_style_color(imgui.COLOR_TEXT, 0.0, 1.0, 1.0)
                else:
                    imgui.push_style_color(imgui.COLOR_TEXT, 0.0, 1.0, 0.0)
                imgui.text("{:>8.3f}".format(tObjFunc[i]))
                # if i != len(objFunc) - 1:
                imgui.pop_style_color()
                imgui.same_line(0, 20)

            imgui.spacing()   

            displayCons = copy.deepcopy(constraintsLhs)     

            # build display cons
            for i in range(len(constraintsLhs)):
                displayCons[i].append(cellRef[i])
                if constraints[i][-1] == 0:
                    displayCons[i].append("<=")
                else:
                    displayCons[i].append(">=")
                displayCons[i].append(constraints[i][-2])

                tSlack = displayCons[i][-1] - displayCons[i][-3]
                displayCons[i].append(tSlack)

            # display the constraints
            for i in range(len(displayCons)):
                imgui.text("{:>8}".format("c{}".format(i + 1)))
                imgui.same_line(0, 20)
                for j in range(len(displayCons[i])):
                    if j == len(displayCons[i]) - 2:
                        imgui.push_style_color(imgui.COLOR_TEXT, 1.0, 0.0, 1.0)             
                    if isinstance(displayCons[i][j], float):   
                        imgui.text("{:>8.3f}".format(displayCons[i][j]))
                    else:
                        imgui.text("{:>8}".format(displayCons[i][j]))
                    if j == len(displayCons[i]) - 2:
                        imgui.pop_style_color()
                    if j < len(displayCons[i]) - 1:
                        imgui.same_line(0, 20)

            imgui.spacing()
            imgui.spacing()
            imgui.spacing()

            imgui.text("{:>8}".format("opt"))
            imgui.same_line(0, 20)
            for i in range(len(changingVars)):
                imgui.push_style_color(imgui.COLOR_TEXT, 1.0, 1.0, 0.0)
                imgui.text("{:>8.3f}".format(changingVars[i]))
                imgui.pop_style_color()
                imgui.same_line(0, 20)


            imgui.spacing()
            imgui.spacing()
            imgui.spacing()
            imgui.text("  ______________________________________________________________________________________") # dual ==============================================
            imgui.spacing()
            imgui.spacing()
            imgui.spacing()

            for i in range(len(dualHeaderString)):
                imgui.text("{:>8}".format(dualHeaderString[i]))
                imgui.same_line(0, 20)

            imgui.spacing()
            
            # display the objective function
            imgui.text("{:>8}".format(f"{strMin} z"))
            imgui.same_line(0, 20)
            for i in range(len(tDualObjFunc)):
                if i != len(tDualObjFunc) - 1:
                    imgui.push_style_color(imgui.COLOR_TEXT, 1.0, 0.0, 1.0)
                else:
                    imgui.push_style_color(imgui.COLOR_TEXT, 0.0, 1.0, 0.0)
                imgui.text("{:>8.3f}".format(tDualObjFunc[i]))
                # if i != len(objFunc) - 1:
                imgui.pop_style_color()
                imgui.same_line(0, 20)

            imgui.spacing()   

            dualDisplayCons = copy.deepcopy(dualConstraintsLhs)     

            # build display cons
            for i in range(len(dualConstraintsLhs)):
                dualDisplayCons[i].append(dualCellRef[i])
                if constraints[i][-1] == 0:
                    dualDisplayCons[i].append(">=")
                else:
                    dualDisplayCons[i].append("<=")
                dualDisplayCons[i].append(objFunc[i])

                tSlack = dualDisplayCons[i][-1] - dualDisplayCons[i][-3]
                dualDisplayCons[i].append(tSlack)

            # display the constraints
            for i in range(len(dualDisplayCons)):
                imgui.text("{:>8}".format("c{}".format(i + 1)))
                imgui.same_line(0, 20)
                for j in range(len(dualDisplayCons[i])):
                    if j == len(dualDisplayCons[i]) - 2:
                        imgui.push_style_color(imgui.COLOR_TEXT, 0.0, 1.0, 1.0)
                    if isinstance(dualDisplayCons[i][j], float):   
                        imgui.text("{:>8.3f}".format(dualDisplayCons[i][j]))
                    else:
                        imgui.text("{:>8}".format(dualDisplayCons[i][j]))
                    if j == len(dualDisplayCons[i]) - 2:
                        imgui.pop_style_color()
                    if j < len(dualDisplayCons[i]) - 1:
                        imgui.same_line(0, 20)

            imgui.spacing()
            imgui.spacing()
            imgui.spacing()

            imgui.text("{:>8}".format("opt"))
            imgui.same_line(0, 20)
            for i in range(len(dualChangingVars)):
                imgui.push_style_color(imgui.COLOR_TEXT, 1.0, 1.0, 0.0)
                imgui.text("{:>8.3f}".format(dualChangingVars[i]))
                imgui.pop_style_color()
                imgui.same_line(0, 20)

        except Exception as e:
            pass

        imgui.end()

        # gl stuff
        gl.glClearColor(0, 0, 0, 1)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        imgui.render()
        impl.render(imgui.get_draw_data())

        pygame.display.flip()

def doDuality(objFunc, constraints, isMin):
    print(f"\nobjective function: {objFunc}")

    a = copy.deepcopy(objFunc)
    b = copy.deepcopy(constraints)
    tableaus, changingVars, optimalSolution = dualSimplex.DoDualSimplex(a, b, isMin)

    print(f"\noptimal solution: {optimalSolution}")

    print(f"\nchanging vars: {changingVars}")

    constraintsLhs = copy.deepcopy(constraints)

    for i in range(len(constraintsLhs)):
        del constraintsLhs[i][-1]
        del constraintsLhs[i][-1]


    cellRef = []

    for i in range(len(constraintsLhs)):
        tSum = sum([a * b for a, b in zip(changingVars, constraintsLhs[i])])
        # print(tSum)
        print(f"Cell Ref: {tSum}")
        cellRef.append(tSum)

    print()
    for i in range(len(constraintsLhs)):
        for j in range(len(constraintsLhs[0])):
            print(constraintsLhs[i][j], end=" ")
        print()

    print()

    # duality

    dualObjFunc = []
    for i in range(len(constraintsLhs)):
        dualObjFunc.append(constraints[i][-2])

    print(f"\ndual objective function: {dualObjFunc}")

    dualConstraints = transposeMat(constraintsLhs)

    for i in range(len(dualConstraints)):
        dualConstraints[i].append(objFunc[i])


    for i in range(len(constraints)):
        if i >= len(dualConstraints):
            break
        if constraints[i][-1] == 1:
            dualConstraints[i].append(0)
        else:
            dualConstraints[i].append(1)

    isMin = not isMin

    a = []
    b = []
    a = copy.deepcopy(dualObjFunc)
    b = copy.deepcopy(dualConstraints)
    tableaus, dualChangingVars, dualOptimalSolution = dualSimplex.DoDualSimplex(a, b, isMin)

    print(f"\noptimal solution: {dualOptimalSolution}")

    print(f"\nchanging vars: {dualChangingVars}")

    dualConstraintsLhs = copy.deepcopy(dualConstraints)

    for i in range(len(dualConstraintsLhs)):
        del dualConstraintsLhs[i][-1]
        del dualConstraintsLhs[i][-1]

    dualCellRef = []

    for i in range(len(dualConstraintsLhs)):
        tSum = sum([a * b for a, b in zip(dualChangingVars, dualConstraintsLhs[i])])
        print(f"Cell Ref: {tSum}")
        dualCellRef.append(tSum)

    print()
    for i in range(len(dualConstraintsLhs)):
        for j in range(len(dualConstraintsLhs[0])):
            print(dualConstraintsLhs[i][j], end=" ")
        print()

    return objFunc, optimalSolution, changingVars, constraintsLhs, cellRef, dualObjFunc, dualOptimalSolution, dualChangingVars, dualConstraintsLhs, dualCellRef


def main():
    doGui()

main()