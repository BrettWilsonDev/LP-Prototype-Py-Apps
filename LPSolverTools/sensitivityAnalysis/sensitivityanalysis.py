# import imgui
# from imgui.integrations.glfw import GlfwRenderer
# import glfw

import copy
import sys
import os

import sympy as sp
try:
    from mathpreliminaries import MathPreliminaries as MathPrelims
except:
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    from mathPrelim.mathpreliminaries import MathPreliminaries as MathPrelims


class SensitivityAnalysis:

    def __init__(self, isConsoleOutput=False):
        self.isConsoleOutput = isConsoleOutput

        self.reset()

    def reset(self):
        self.testInputSelected = -1

        self.mathPrelim = MathPrelims()

        self.d = sp.symbols('d')
        self.globalOptimalTab = []
        self.globalHeaderRow = []

        self.problemType = "Max"
        self.absProblemType = "abs Off"

        self.amtOfObjVars = 2
        self.objFunc = [0.0, 0.0]

        self.constraints = [[0.0, 0.0, 0.0, 0.0]]
        self.signItems = ["<=", ">="]
        self.signItemsChoices = [0]

        self.amtOfConstraints = 1

        self.changingTable = []

        self.posDelta = float("inf")
        self.negDelta = float("inf")

        self.posRange = float("inf")
        self.negRange = float("inf")

        self.termPos = "?"
        self.currentDeltaSelection = "o0"

    def testInput(self, testNum=-1):
        isMin = False
        if testNum == 0:
            objFunc = [60, 30, 20]
            constraints = [[8, 6, 1, 48, 0],
                           [4, 2, 1.5, 20, 0],
                           [2, 1.5, 0.5, 8, 0],
                           ]
        elif testNum == 1:
            objFunc = [100, 30]
            constraints = [[0, 1, 3, 1],
                           [1, 1, 7, 0],
                           [10, 4, 40, 0],
                           ]
        elif testNum == 2:
            objFunc = [30, 28, 26, 30]
            constraints = [[8, 8, 4, 4, 160, 0],
                           [1, 0, 0, 0, 5, 0],
                           [1, 0, 0, 0, 5, 1],
                           [1, 1, 1, 1, 20, 1],
                           ]
        elif testNum == 3:
            objFunc = [10, 50, 80, 100]
            constraints = [[1, 4, 4, 8, 140, 0],
                           [1, 0, 0, 0, 50, 0],
                           [1, 0, 0, 0, 50, 1],
                           [1, 1, 1, 1, 70, 1],
                           ]
        elif testNum == 4:
            objFunc = [3, 2]
            constraints = [[2, 1, 100, 0],
                           [1, 1, 80, 0],
                           [1, 0, 40, 0],
                           ]
        elif testNum == 5:
            objFunc = [120, 80]
            constraints = [[8, 4, 160, 0],
                           [4, 4, 100, 0],
                           [1, 0, 17, 0],
                           [1, 0, 5, 1],
                           [0, 1, 17, 0],
                           [0, 1, 2, 1],
                           [1, -1, 0, 1],
                           [1, -4, 0, 0],
                           ]

        if testNum == -1:
            return None
        else:
            return objFunc, constraints, isMin

    def doSensitivityAnalysis(self, objfunc, constraints, isMin, absRule=False, optTabLockState=False):
        # get the changing table with deltas in it
        a = copy.deepcopy(objfunc)
        b = copy.deepcopy(constraints)
        self.changingTable, matrixCbv, matrixB, matrixBNegOne, matrixCbvNegOne, basicVarSpots = self.mathPrelim.doPreliminaries(
            a, b, isMin, absRule, optTabLockState)

        termWithoutdelta = None

        # get delta type
        objFuncHasDelta = False
        for i in range(len(objfunc)):
            if isinstance(objfunc[i], (sp.Add, sp.Mul)):
                self.termPos = f"c{i+1}"
                termWithoutdelta = objfunc[i].as_independent(
                    self.d, as_Add=True)[0]
                objFuncHasDelta = True
        rhsHasDelta = False
        for i in range(len(constraints)):
            if isinstance(constraints[i][-2], (sp.Add, sp.Mul)):
                self.termPos = f"b{i+1}"
                termWithoutdelta = constraints[i][-2].as_independent(self.d, as_Add=True)[
                    0]
                rhsHasDelta = True
        constraintsHasDelta = False
        for i in range(len(constraints)):
            for j in range(len(constraints[i]) - 2):
                if isinstance(constraints[i][j], (sp.Add, sp.Mul)):
                    self.termPos = f"c{i+1}"
                    termWithoutdelta = constraints[i][j].as_independent(self.d, as_Add=True)[
                        0]
                    constraintsHasDelta = True

        # solve the delta equations
        deltasList = []
        if objFuncHasDelta:
            for i in range(len(self.changingTable[0]) - 1):
                if isinstance(self.changingTable[0][i], (sp.Add, sp.Mul)):
                    deltasList.append(
                        float(sp.solve(self.changingTable[0][i], self.d)[0]))
        if rhsHasDelta:
            deltasList = []
            for i in range(len(self.changingTable)):
                if isinstance(self.changingTable[i][-1], (sp.Add, sp.Mul)):
                    deltasList.append(
                        float(sp.solve(self.changingTable[i][-1], self.d)[0]))
        conStraintDeltaCol = -1
        if constraintsHasDelta:
            for i in range(len(self.changingTable)):
                for j in range(len(self.changingTable[i]) - 1):
                    if isinstance(self.changingTable[i][j], (sp.Add, sp.Mul)):
                        # deltasList.append(float(sp.solve(self.changingTable[i][j], self.d)[0]))
                        conStraintDeltaCol = j

        # if constraintsHasDelta:
        #     for i in range(len(self.changingTable)):
        #         for j in range(len(self.changingTable[i]) - 1):
        #             if isinstance(self.changingTable[i][j], (sp.Add, sp.Mul)):
        #                 deltasList.append(float(sp.solve(self.changingTable[i][j], self.d)[0]))

        # rules of how to choose form multiple deltas
        # smallest delta impact for rhs 20 -20 60 -40 we would pick 20 and -20
        # from b being the constraint rhs
        #    b1    delta = 60
        #    b2    delta = 20.0
        #    b3    delta = 20.0
        #    b4    delta = -40.0

        if constraintsHasDelta:
            if isinstance(self.changingTable[0][conStraintDeltaCol], (sp.Add, sp.Mul)):
                try:
                    deltasList.append(
                        float(sp.solve(self.changingTable[0][conStraintDeltaCol], self.d)[0]))
                except:
                    self.termPos = "unsolvable"
            else:
                self.negDelta = float('inf')
                self.posDelta = float('inf')
                self.termPos = self.changingTable[0][conStraintDeltaCol]

        # extract the delta
        if not len(deltasList) == 0:
            if len(deltasList) == 1:
                if deltasList[0] < 0:
                    self.posDelta = float('inf')
                    self.negDelta = deltasList[0]
                elif deltasList[0] > 0:
                    self.posDelta = deltasList[0]
                    self.negDelta = float('inf')
            else:
                if (all(x < 0 for x in deltasList)):
                    self.posDelta = float('inf')
                    self.negDelta = min(
                        filter(lambda x: x < 0, deltasList), key=lambda x: abs(x))
                elif (all(x > 0 for x in deltasList)):
                    self.posDelta = min(
                        filter(lambda x: x > 0, deltasList), key=lambda x: abs(x))
                    self.negDelta = float('inf')
                else:
                    self.posDelta = min(
                        filter(lambda x: x > 0, deltasList), key=lambda x: abs(x))
                    self.negDelta = min(
                        filter(lambda x: x < 0, deltasList), key=lambda x: abs(x))

        # get the range
        self.posRange = float(termWithoutdelta) + float(self.posDelta)
        self.negRange = float(termWithoutdelta) + float(self.negDelta)

        if self.isConsoleOutput:
            print(self.negRange, f" <= {self.termPos} <= ", self.posRange)
            print(self.negDelta, " <= d <= ", self.posDelta)

    def imguiUIElements(self, windowSize, windowPosX=0, windowPosY=0):
        imgui.set_next_window_position(
            windowPosX, windowPosY)  # Set the window position
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
        imgui.text(
            "Use + to mark the item for analysis O is the current selection")
        imgui.spacing()
        imgui.spacing()

        for i in range(len(self.objFunc)):
            value = (self.objFunc[i])
            imgui.same_line()
            imgui.push_id("##deltaButtonO {}".format(i + 1))
            if self.currentDeltaSelection == f"o{i}":
                deltaSelectText = "O"
            else:
                deltaSelectText = "+"
            if imgui.button(f"{deltaSelectText}"):
                self.currentDeltaSelection = f"o{i}"
            imgui.pop_id()
            imgui.set_next_item_width(50)
            imgui.same_line()
            changed, self.objFunc[i] = imgui.input_float(
                "##objFunc {}".format(i + 1), value)
            imgui.same_line()
            imgui.text(f"x{i + 1}")

            if changed:
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
                value = (self.constraints[i][j])
                imgui.same_line()
                imgui.push_id("##deltaButtonC {}{}".format(i + 1, j + 1))
                if self.currentDeltaSelection == f"c{i}{j}":
                    deltaSelectText = "O"
                else:
                    deltaSelectText = "+"
                if imgui.button(f"{deltaSelectText}"):
                    self.currentDeltaSelection = f"c{i}{j}"
                imgui.pop_id()
                imgui.same_line()
                imgui.set_next_item_width(50)
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
            imgui.push_id("##deltaButtonRhs {}{}".format(i + 1, j + 1))
            if self.currentDeltaSelection == f"cRhs{i}{j}":
                deltaSelectText = "O"
            else:
                deltaSelectText = "+"
            if imgui.button(f"{deltaSelectText}"):
                self.currentDeltaSelection = f"cRhs{i}{j}"
            imgui.pop_id()
            imgui.same_line()
            imgui.set_next_item_width(50)
            rhsValue = (self.constraints[i][-2])
            rhsChanged, rhs = imgui.input_float(
                "##RHSC{}{}".format(i, j), rhsValue)

            if rhsChanged:
                self.constraints[i][-2] = rhs

        if self.problemType == "Min":
            isMin = True
        else:
            isMin = False

        # solve button =========================================================
        if imgui.button("Solve"):
            try:
                if self.testInput(self.testInputSelected) is not None:
                    self.objFunc, self.constraints, isMin = self.testInput(
                        self.testInputSelected)

                bkupObjFunc = copy.deepcopy(self.objFunc)
                bkupConstraints = copy.deepcopy(self.constraints)

                for i in range(len(self.objFunc)):
                    if self.currentDeltaSelection == f"o{i}":
                        self.objFunc[i] = sp.Add(
                            float(self.objFunc[i]), self.d)

                for i in range(len(self.constraints)):
                    for j in range(len(self.constraints[i])):
                        if self.currentDeltaSelection == f"c{i}{j}":
                            self.constraints[i][j] = sp.Add(
                                float(self.constraints[i][j]), self.d)

                for i in range(len(self.constraints)):
                    if self.currentDeltaSelection == f"cRhs{i}{len(self.objFunc) - 1}":
                        self.constraints[i][-2] = sp.Add(
                            float(self.constraints[i][-2]), self.d)

                a = copy.deepcopy(self.objFunc)
                b = copy.deepcopy(self.constraints)

                self.objFunc = copy.deepcopy(bkupObjFunc)
                self.constraints = copy.deepcopy(bkupConstraints)

                # convert obj func to numbers
                for i in range(len(a)):
                    try:
                        a[i] = float(a[i])
                    except Exception as e:
                        pass

                # obj func to expressions
                for i in range(len(a)):
                    try:
                        a[i] = sp.parse_expr(a[i])
                    except Exception as e:
                        pass

                # convert constraints to numbers
                for i in range(len(b)):
                    for j in range(len(b[i])):
                        try:
                            b[i][j] = float(b[i][j])
                        except Exception as e:
                            pass

                # convert constraints to expressions
                for i in range(len(b)):
                    for j in range(len(b[i])):
                        try:
                            b[i][j] = sp.parse_expr(b[i][j])
                        except Exception as e:
                            pass

                self.doSensitivityAnalysis(a, b, isMin, False, False)
            except Exception as e:
                print("math error:", e)

        imgui.same_line(0, 30)
        imgui.push_style_color(imgui.COLOR_TEXT, 1.0, 0.0, 0.0)
        if imgui.button("Reset"):
            self.reset()
        imgui.pop_style_color()

        imgui.spacing()
        imgui.spacing()
        imgui.spacing()
        imgui.spacing()
        imgui.text("Sensitivity Analysis:")
        imgui.spacing()
        imgui.text(f"   {self.negRange} <= {self.termPos} <= {self.posRange}")
        imgui.spacing()
        imgui.text("Delta Range:")
        imgui.spacing()
        imgui.text(f"   {self.negDelta} <= d <= {self.posDelta}")

        imgui.end_child()
        imgui.end()

    def doGui(self):
        if not glfw.init():
            print("Could not initialize OpenGL context")
            return

        window = glfw.create_window(
            int(1920 / 2), int(1080 / 2), "Sensitivity Analysis Prototype", None, None)
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
    classInstance = SensitivityAnalysis(isConsoleOutput)
    classInstance.doGui()


if __name__ == "__main__":
    main(True)
