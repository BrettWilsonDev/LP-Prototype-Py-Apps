if __name__ == "__main__":
    import imgui
    from imgui.integrations.glfw import GlfwRenderer
    import glfw

import math
import copy
import sys
import os
try:
    from dualsimplex import DualSimplex as Dual
except:
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    from dual.dualsimplex import DualSimplex as Dual


class LPDuality:

    def __init__(self, isConsoleOutput=False):
        self.isConsoleOutput = isConsoleOutput

        self.reset()

    def reset(self):
        self.dual = Dual()
        self.testInputSelected = 0

        # simplex specific vars
        self.problemType = "Max"

        self.objFunc = []
        self.optimalSolution = 0
        self.changingVars = []
        self.constraintsLhs = []
        self.cellRef = []
        self.dualObjFunc = []
        self.dualOptimalSolution = 0
        self.dualChangingVars = []
        self.dualConstraints = []
        self.dualConstraintsLhs = []
        self.dualCellRef = []

        # dual constraints
        self.amtOfObjVars = 2
        self.objFunc = [0.0, 0.0]

        self.constraints = [[0.0, 0.0, 0.0, 0.0]]
        self.signItems = ["<=", ">="]
        self.signItemsChoices = [0]

        self.amtOfConstraints = 1

        self.headerString = []
        self.dualHeaderString = []

        self.tObjFunc = []
        self.tDualObjFunc = []

        self.errorE = ""

        self.strMin = ""
        self.strDualMin = ""

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

        # fix slack and excess mix
        slackCtr = 0
        excessCtr = 0
        for i in range(len(constraints)):
            if constraints[i][-1] == 1:
                excessCtr += 1
            else:
                slackCtr += 1

        if slackCtr != len(constraints) and excessCtr != len(constraints):
            for i in range(len(constraints)):
                if constraints[i][-1] == 1:
                    constraints[i][-1] = 0
                    for j in range(len(constraints[i]) - 1):
                        constraints[i][j] = -constraints[i][j]
                        print(constraints[i][j], end=" ")

        self.dualConstraints = copy.deepcopy(constraints)

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
        
        for i in range(len(dualObjFunc)):
            if dualObjFunc[i] < 0:
                for j in range(len(dualConstraints)):
                    dualConstraints[j][i] = -dualConstraints[j][i]

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
                    try:
                        print(dualConstraintsLhs[i][j], end=" ")
                    except:
                        pass
                print()

        return objFunc, optimalSolution, changingVars, constraintsLhs, cellRef, dualObjFunc, dualOptimalSolution, dualChangingVars, dualConstraintsLhs, dualCellRef

    def imguiUIElements(self, windowSize, windowPosX = 0, windowPosY = 0):
        imgui.set_next_window_position(windowPosX, windowPosY)  # Set the window position
        imgui.set_next_window_size(
            (windowSize[0]), (windowSize[1]))  # Set the window size
        imgui.begin("Tableaus Output",
                    flags=imgui.WINDOW_NO_TITLE_BAR | imgui.WINDOW_NO_RESIZE | imgui.WINDOW_ALWAYS_HORIZONTAL_SCROLLBAR)
        imgui.begin_child("Scrollable Child", width=0, height=0,
            border=True, flags=imgui.WINDOW_ALWAYS_HORIZONTAL_SCROLLBAR)

        if imgui.radio_button("Max", self.problemType == "Max"):
            self.problemType = "Max"

        if imgui.radio_button("Min", self.problemType == "Min"):
            self.problemType = "Min"

        imgui.text("Problem is: {}".format(self.problemType))

        # obj vars ===========================================
        if imgui.button("decision variables +"):
            self.amtOfObjVars += 1
            for i in range(len(self.constraints)):
                self.constraints[i].append(0.0)
            self.objFunc.append(0.0)

        imgui.same_line()

        if imgui.button("decision variables -"):
            if self.amtOfObjVars != 2:
                self.amtOfObjVars += -1
                for i in range(len(self.constraints)):
                    self.constraints[i].pop()
                self.objFunc.pop()

        imgui.spacing()

        for i in range(len(self.objFunc)):
            value = self.objFunc[i]
            imgui.set_next_item_width(50)
            imgui.same_line()
            changed, self.objFunc[i] = imgui.input_float(
                "##objFunc {}".format(i + 1), value)
            imgui.same_line()
            imgui.text(f"x{i + 1}")

            if changed:
                # Value has been updated
                pass

        if imgui.button("Constraint +"):
            self.amtOfConstraints += 1
            self.constraints.append([0.0] * self.amtOfObjVars)
            self.constraints[-1].append(0.0)  # add sign spot
            self.constraints[-1].append(0.0)  # add rhs spot
            self.signItemsChoices.append(0)

        imgui.same_line()

        if imgui.button("Constraint -"):
            if self.amtOfConstraints != 1:
                self.amtOfConstraints += -1
                self.constraints.pop()
                self.signItemsChoices.pop()

        # spaceGui(6)
        for i in range(self.amtOfConstraints):
            imgui.spacing()
            if len(self.constraints) <= i:
                # Fill with default values if needed
                self.constraints.append([0.0] * (self.amtOfObjVars + 2))

            for j in range(self.amtOfObjVars):
                value = self.constraints[i][j]
                imgui.set_next_item_width(50)
                imgui.same_line()
                changed, xValue = imgui.input_float(
                    "##xC{}{}".format(i, j), value)
                imgui.same_line()
                imgui.text(f"x{j + 1}")
                if changed:
                    self.constraints[i][j] = xValue

            imgui.same_line()
            imgui.push_item_width(50)
            changed, self.selectedItemSign = imgui.combo(
                "##comboC{}{}".format(i, j), self.signItemsChoices[i], self.signItems)
            if changed:
                self.signItemsChoices[i] = self.selectedItemSign
                self.constraints[i][-1] = self.signItemsChoices[i]

            imgui.pop_item_width()
            imgui.same_line()
            imgui.set_next_item_width(50)
            rhsValue = self.constraints[i][-2]
            rhsChanged, rhs = imgui.input_float(
                "##RHSC{}{}".format(i, j), rhsValue)

            if rhsChanged:
                self.constraints[i][-2] = rhs

        if self.problemType == "Min":
            isMin = True
        else:
            isMin = False

        # solve button ==================================================
        if imgui.button("Solve"):
            try:
                if self.testInput(self.testInputSelected) is not None:
                    self.objFunc, self.constraints, isMin = self.testInput(
                        self.testInputSelected)

                self.headerString.clear()
                self.dualHeaderString.clear()

                a = copy.deepcopy(self.objFunc)
                b = copy.deepcopy(self.constraints)
                self.objFunc, self.optimalSolution, self.changingVars, self.constraintsLhs, self.cellRef, self.dualObjFunc, self.dualOptimalSolution, self.dualChangingVars, self.dualConstraintsLhs, self.dualCellRef = self.doDuality(
                    a, b, isMin)

                # for display reasons
                self.tObjFunc = copy.deepcopy(self.objFunc)
                self.tDualObjFunc = copy.deepcopy(self.dualObjFunc)
                self.tObjFunc.append(self.optimalSolution)
                self.tDualObjFunc.append(self.dualOptimalSolution)

                dualMin = not isMin

                if isMin:
                    self.strMin = "max"
                else:
                    self.strMin = "min"

                if dualMin:
                    self.strDualMin = "max"
                else:
                    self.strDualMin = "min"

                self.headerString.append("Primal")
                self.dualHeaderString.append("Dual")

                for i in range(len(self.objFunc)):
                    self.headerString.append("x{}".format(i + 1))

                for i in range(len(self.dualObjFunc)):
                    self.dualHeaderString.append("y{}".format(i + 1))

                self.headerString.append("Ref")
                self.headerString.append("Sign")
                self.headerString.append("Rhs")
                self.headerString.append("Slack")

                self.dualHeaderString.append("Ref")
                self.dualHeaderString.append("Sign")
                self.dualHeaderString.append("Rhs")
                self.dualHeaderString.append("Slack")

                self.errorE = ""
            except Exception as e:
                print("math error:", e)
                imgui.text("math error: {}".format(e))
                self.errorE = "math error: {}".format(e)

        imgui.same_line(0, 30)
        imgui.push_style_color(imgui.COLOR_TEXT, 1.0, 0.0, 0.0)
        if imgui.button("Reset"):
            self.reset()
        imgui.pop_style_color()

        imgui.spacing()
        imgui.text(self.errorE)

        imgui.spacing()
        imgui.spacing()

        try:
            for i in range(len(self.headerString)):
                imgui.text("{:>8}".format(self.headerString[i]))
                imgui.same_line(0, 20)

            imgui.spacing()

            # display the objective function
            imgui.text("{:>8}".format(f"{self.strDualMin} z"))
            imgui.same_line(0, 20)
            for i in range(len(self.tObjFunc)):
                if i != len(self.tObjFunc) - 1:
                    imgui.push_style_color(imgui.COLOR_TEXT, 0.0, 1.0, 1.0)
                else:
                    imgui.push_style_color(imgui.COLOR_TEXT, 0.0, 1.0, 0.0)
                imgui.text("{:>8.3f}".format(self.tObjFunc[i]))
                # if i != len(objFunc) - 1:
                imgui.pop_style_color()
                imgui.same_line(0, 20)

            imgui.spacing()

            displayCons = copy.deepcopy(self.constraintsLhs)

            # build display cons
            for i in range(len(self.constraintsLhs)):
                displayCons[i].append(self.cellRef[i])
                if self.constraints[i][-1] == 0:
                    displayCons[i].append("<=")
                else:
                    displayCons[i].append(">=")
                displayCons[i].append(self.constraints[i][-2])

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
            for i in range(len(self.changingVars)):
                imgui.push_style_color(imgui.COLOR_TEXT, 1.0, 1.0, 0.0)
                imgui.text("{:>8.3f}".format(self.changingVars[i]))
                imgui.pop_style_color()
                imgui.same_line(0, 20)

            imgui.spacing()
            imgui.spacing()
            imgui.spacing()
            # dual ==============================================
            imgui.separator()
            imgui.separator()
            imgui.spacing()
            imgui.spacing()
            imgui.spacing()

            for i in range(len(self.dualHeaderString)):
                imgui.text("{:>8}".format(self.dualHeaderString[i]))
                imgui.same_line(0, 20)

            imgui.spacing()

            # display the objective function
            imgui.text("{:>8}".format(f"{self.strMin} z"))
            imgui.same_line(0, 20)
            for i in range(len(self.tDualObjFunc)):
                if i != len(self.tDualObjFunc) - 1:
                    imgui.push_style_color(imgui.COLOR_TEXT, 1.0, 0.0, 1.0)
                else:
                    imgui.push_style_color(imgui.COLOR_TEXT, 0.0, 1.0, 0.0)
                imgui.text("{:>8.3f}".format(self.tDualObjFunc[i]))
                # if i != len(objFunc) - 1:
                imgui.pop_style_color()
                imgui.same_line(0, 20)

            imgui.spacing()

            dualDisplayCons = copy.deepcopy(self.dualConstraintsLhs)

            # build display cons
            for i in range(len(self.dualConstraintsLhs)):
                dualDisplayCons[i].append(self.dualCellRef[i])
                if self.dualConstraints[i][-1] == 0:
                    dualDisplayCons[i].append(">=")
                else:
                    dualDisplayCons[i].append("<=")
                dualDisplayCons[i].append(self.objFunc[i])

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
            for i in range(len(self.dualChangingVars)):
                imgui.push_style_color(imgui.COLOR_TEXT, 1.0, 1.0, 0.0)
                imgui.text("{:>8.3f}".format(self.dualChangingVars[i]))
                imgui.pop_style_color()
                imgui.same_line(0, 20)

        except Exception as e:
            pass

        imgui.end_child()
        imgui.end()

    def doGui(self):
        if not glfw.init():
            print("Could not initialize OpenGL context")
            return

        window = glfw.create_window(
            int(1920 / 2), int(1080 / 2), "Duality Prototype", None, None)
        if not window:
            glfw.terminate()
            return

        # Make the window's context current
        glfw.make_context_current(window)

        # Initialize ImGui
        imgui.create_context()
        impl = GlfwRenderer(window)

        while not glfw.window_should_close(window):
            glfw.poll_events()
            impl.process_inputs()

            imgui.new_frame()
            self.imguiUIElements(glfw.get_window_size(window))

            # Rendering
            imgui.render()
            impl.render(imgui.get_draw_data())
            glfw.swap_buffers(window)

        # Cleanup
        impl.shutdown()
        glfw.terminate()


def main(isConsoleOutput=False):
    classInstance = LPDuality(isConsoleOutput)
    classInstance.doGui()


if __name__ == "__main__":
    main(True)
