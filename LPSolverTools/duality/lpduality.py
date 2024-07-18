import pygame
from imgui.integrations.pygame import PygameRenderer
import imgui

import copy

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from dual.dualsimplex import DualSimplex as Dual
from mathPrelim.mathpreliminaries import MathPreliminaries as MathPrelims


class LPDuality:
    dual = Dual()

    isConsoleOutput = False

    def __init__(self, isConsoleOutput=False):
        self.isConsoleOutput = isConsoleOutput

    def testInput(self, testNum=-1):
        isMin = False
        if testNum == 0:
            objFunc = [100, 30]

            constraints = [[0, 1, 3, 1], [1, 1, 7, 0], [10, 4, 40, 0]]
        elif testNum == 1:
            objFunc = [60, 30, 20]

            constraints = [[8, 6, 1, 48, 0], [
                4, 2, 1.5, 20, 0], [2, 1.5, 0.5, 8, 0]]
        elif testNum == 2:
            objFunc = [48, 20, 8]

            constraints = [[8, 4, 2, 60, 1],
                           [6, 2, 1.5, 30, 1],
                           [1, 1.5, 0.5, 20, 1]]
        elif testNum == 3:
            objFunc = [10, 50, 80, 100]
            constraints = [[1, 4, 4, 8, 140, 0],
                           [1, 0, 0, 0, 50, 0],
                           [1, 0, 0, 0, 50, 1],
                           [1, 1, 1, 1, 70, 1],
                           ]

        if testNum == -1:
            return None
        else:
            return objFunc, constraints, isMin

    def transposeMat(self, matrix):
        return [list(row) for row in zip(*matrix)]

    def doDuality(self, objFunc, constraints, isMin):
        if self.isConsoleOutput:
            print(f"\nobjective function: {objFunc}")

        a = copy.deepcopy(objFunc)
        b = copy.deepcopy(constraints)
        tableaus, changingVars, optimalSolution = self.dual.doDualSimplex(
            a, b, isMin)

        if self.isConsoleOutput:
            print(f"\noptimal solution: {optimalSolution}")

            print(f"\nchanging vars: {changingVars}")

        constraintsLhs = copy.deepcopy(constraints)

        for i in range(len(constraintsLhs)):
            del constraintsLhs[i][-1]
            del constraintsLhs[i][-1]

        cellRef = []

        for i in range(len(constraintsLhs)):
            tSum = sum(
                [a * b for a, b in zip(changingVars, constraintsLhs[i])])
            # print(tSum)
            if self.isConsoleOutput:
                print(f"Cell Ref: {tSum}")
            cellRef.append(tSum)

        if self.isConsoleOutput:
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

        if self.isConsoleOutput:
            print(f"\ndual objective function: {dualObjFunc}")

        dualConstraints = self.transposeMat(constraintsLhs)

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
        tableaus, dualChangingVars, dualOptimalSolution = self.dual.doDualSimplex(
            a, b, isMin)

        if self.isConsoleOutput:
            print(f"\noptimal solution: {dualOptimalSolution}")

            print(f"\nchanging vars: {dualChangingVars}")

        dualConstraintsLhs = copy.deepcopy(dualConstraints)

        for i in range(len(dualConstraintsLhs)):
            del dualConstraintsLhs[i][-1]
            del dualConstraintsLhs[i][-1]

        dualCellRef = []

        for i in range(len(dualConstraintsLhs)):
            tSum = sum(
                [a * b for a, b in zip(dualChangingVars, dualConstraintsLhs[i])])
            if self.isConsoleOutput:
                print(f"Cell Ref: {tSum}")
            dualCellRef.append(tSum)

        if self.isConsoleOutput:
            print()
            for i in range(len(dualConstraintsLhs)):
                for j in range(len(dualConstraintsLhs[0])):
                    print(dualConstraintsLhs[i][j], end=" ")
                print()

        return objFunc, optimalSolution, changingVars, constraintsLhs, cellRef, dualObjFunc, dualOptimalSolution, dualChangingVars, dualConstraintsLhs, dualCellRef

    def doGui(self):
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
                    "##objFunc {}".format(i + 1), value)
                imgui.same_line()
                imgui.text(f"x{i + 1}")

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
                        "##xC{}{}".format(i, j), value)
                    imgui.same_line()
                    imgui.text(f"x{j + 1}")
                    if changed:
                        constraints[i][j] = xValue

                imgui.same_line()
                imgui.push_item_width(50)
                changed, selectedItemSign = imgui.combo(
                    "##comboC{}{}".format(i, j), signItemsChoices[i], signItems)
                if changed:
                    signItemsChoices[i] = selectedItemSign
                    constraints[i][-1] = signItemsChoices[i]

                imgui.pop_item_width()
                imgui.same_line()
                imgui.set_next_item_width(50)
                rhsValue = constraints[i][-2]
                rhsChanged, rhs = imgui.input_float(
                    "##RHSC{}{}".format(i, j), rhsValue)

                if rhsChanged:
                    constraints[i][-2] = rhs

            if problemType == "Min":
                isMin = True
            else:
                isMin = False

            # solve button ==================================================
            if imgui.button("Solve"):
                try:
                    if self.testInput() is not None:
                        objFunc, constraints, isMin = self.testInput()

                    headerString.clear()
                    dualHeaderString.clear()

                    a = copy.deepcopy(objFunc)
                    b = copy.deepcopy(constraints)
                    objFunc, optimalSolution, changingVars, constraintsLhs, cellRef, dualObjFunc, dualOptimalSolution, dualChangingVars, dualConstraintsLhs, dualCellRef = self.doDuality(
                        a, b, isMin)

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
                            imgui.push_style_color(
                                imgui.COLOR_TEXT, 1.0, 0.0, 1.0)
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
                # dual ==============================================
                imgui.text(
                    "  ______________________________________________________________________________________")
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
                            imgui.push_style_color(
                                imgui.COLOR_TEXT, 0.0, 1.0, 1.0)
                        if isinstance(dualDisplayCons[i][j], float):
                            imgui.text("{:>8.3f}".format(
                                dualDisplayCons[i][j]))
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

            imgui.render()
            impl.render(imgui.get_draw_data())

            pygame.display.flip()


def main(isConsoleOutput=False):
    classInstance = LPDuality(isConsoleOutput)
    classInstance.doGui()


if __name__ == "__main__":
    main(True)
