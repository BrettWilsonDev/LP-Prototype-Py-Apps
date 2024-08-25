if __name__ == "__main__":
    import imgui
    from imgui.integrations.glfw import GlfwRenderer
    import glfw

import math
import copy
import sys
import os

import sympy as sp
try:
    from dualsimplex import DualSimplex as Dual
    from mathpreliminaries import MathPreliminaries as MathPrelims
except:
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    from dual.dualsimplex import DualSimplex as Dual
    from mathPrelim.mathpreliminaries import MathPreliminaries as MathPrelims


class AddingActsCons:
    def __init__(self, isConsoleOutput=False):
        self.isConsoleOutput = isConsoleOutput

        self.reset()
    
    def reset(self):
        self.dual = Dual()
        self.mathPrelim = MathPrelims()
        self.testInputSelected = -1

        # simplex specific vars
        self.problemType = "Max"
        self.absProblemType = "abs Off"

        # dual constraints
        self.amtOfObjVars = 2
        self.objFunc = [0.0, 0.0]

        self.constraints = [[0.0, 0.0, 0.0, 0.0]]
        self.signItems = ["<=", ">="]
        self.signItemsChoices = [0]

        self.amtOfConstraints = 1

        self.activity = [0.0, 0.0]

        self.absRule = False

        self.problemChoice = "activity"

        self.problemState = True

        self.actDisplayCol = []

        self.amtOfAddingConstraints = 1

        self.addingConstraints = []

        self.addingSignItemsChoices = [0]

        self.fixedTab = []
        self.unfixedTab = []

        self.changingTable = []

        self.IMPivotCols = []
        self.IMPivotRows = []
        self.IMHeaderRow = []

        self.pivotCol = -1
        self.pivotRow = -1

        self.newTableaus = []

        self.reverseRowsState = False
        self.rowsReversed = "off"

        self.negRuleState = False
        self.negRule = "off"

    def testInput(self, testNum=-1):
        isMin = False

        if testNum == 0:
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

        elif testNum == 1:
            objFunc = [30, 28, 26, 30]
            constraints = [[8, 8, 4, 4, 160, 0],
                           [1, 0, 0, 0, 5, 0],
                           [1, 0, 0, 0, 5, 1],
                           [1, 1, 1, 1, 20, 1],
                           ]

            addedConstraints = [
                [1, -1, 0, 0, 0, 0],
                [-1, 1, 0, 0, 0, 1],
            ]

        if testNum == -1:
            return None
        else:
            return objFunc, constraints, isMin, addedConstraints

    def getMathPrelims(self, objFunc, constraints, isMin, absRule=False):
        changingTable, matrixCbv, matrixB, matrixBNegOne, matrixCbvNegOne, basicVarSpots = self.mathPrelim.doPreliminaries(
            objFunc, constraints, isMin, absRule)
        return changingTable, matrixCbv, matrixB, matrixBNegOne, matrixCbvNegOne, basicVarSpots

    def doAddActivity(self, objFunc, constraints, isMin, activity, absRule=False):
        changingTable, matrixCbv, matrixB, matrixBNegOne, matrixCbvNegOne, basicVarSpots = self.getMathPrelims(
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

        if self.isConsoleOutput:
            print(displayCol)

        return displayCol, changingTable

    def doAddConstraint(self, objFunc, constraints, isMin, addedConstraints, absRule=False, reverseRows=False, negRuleState=False):
        changingTable, matrixCbv, matrixB, matrixBNegOne, matrixCbvNegOne, basicVarSpots = self.getMathPrelims(
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

        if self.isConsoleOutput:
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

        if self.isConsoleOutput:
            print("fixed tab")
            for i in range(len(displayTab)):
                for j in range(len(displayTab[i])):
                    print(displayTab[i][j], end="     ")
                print()

        return displayTab, newTab

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

        if imgui.radio_button("abs on", self.absProblemType == "abs On"):
            self.absProblemType = "abs On"

        if imgui.radio_button("abs off", self.absProblemType == "abs Off"):
            self.absProblemType = "abs Off"

        imgui.text("absolute rule is: {}".format(self.absProblemType))

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
                pass

        if imgui.button("Constraint +"):
            self.amtOfConstraints += 1
            self.constraints.append([0.0] * self.amtOfObjVars)
            self.constraints[-1].append(0.0)  # add sign spot
            self.constraints[-1].append(0.0)  # add rhs spot
            self.signItemsChoices.append(0)

            self.activity.append(0.0)

        imgui.same_line()

        if imgui.button("Constraint -"):
            if self.amtOfConstraints != 1:
                self.amtOfConstraints += -1
                self.constraints.pop()
                self.signItemsChoices.pop()

                self.activity.pop()

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

        if imgui.radio_button("adding activity", self.problemChoice == "activity"):
            self.problemChoice = "activity"

        imgui.same_line(0, 20)

        if imgui.radio_button("adding constraints", self.problemChoice == "constraints"):
            self.problemChoice = "constraints"

        imgui.text("the current problem is adding {}".format(
            self.problemChoice))

        if self.problemType == "Min":
            isMin = True
        else:
            isMin = False

        if self.absProblemType == "abs On":
            self.absRule = True
        else:
            self.absRule = False

        if self.problemChoice == "activity":
            self.problemState = True
        else:
            self.problemState = False

        if self.problemState:
            try:
                imgui.new_line()
                for i in range(len(self.constraints) + 1):
                    value = (self.activity[i])
                    imgui.set_next_item_width(50)
                    imgui.same_line()
                    imgui.new_line()
                    changed, self.activity[i] = imgui.input_float(
                        "##activity {}".format(i + 1), value)
                    if i == 0:
                        imgui.same_line()
                        imgui.text("x")
                    else:
                        imgui.same_line()
                        imgui.text("c{}".format(i))
            except:
                pass
        else:
            if imgui.button("New Constraint +"):
                self.amtOfAddingConstraints += 1
                self.addingConstraints.append([0.0] * self.amtOfObjVars)
                self.addingConstraints[-1].append(0.0)  # add sign spot
                self.addingConstraints[-1].append(0.0)  # add rhs spot
                self.addingSignItemsChoices.append(0)

            imgui.same_line()

            if imgui.button("New Constraint -"):
                if self.amtOfAddingConstraints != 1:
                    self.amtOfAddingConstraints += -1
                    self.addingConstraints.pop()
                    self.addingSignItemsChoices.pop()

            for i in range(self.amtOfAddingConstraints):
                imgui.spacing()
                if len(self.addingConstraints) <= i:
                    self.addingConstraints.append(
                        [0.0] * (self.amtOfObjVars + 2))

                for j in range(self.amtOfObjVars):
                    value = (self.addingConstraints[i][j])
                    imgui.set_next_item_width(50)
                    imgui.same_line()
                    changed, xValue = imgui.input_float(
                        "##axC{}{}".format(i, j), value)
                    imgui.same_line()
                    imgui.text(f"x{j + 1}")
                    if changed:
                        self.addingConstraints[i][j] = xValue

                imgui.same_line()
                imgui.push_item_width(50)
                changed, self.selectedItemSign = imgui.combo(
                    "##acomboC{}{}".format(i, j), self.addingSignItemsChoices[i], self.signItems)
                if changed:
                    self.addingSignItemsChoices[i] = self.selectedItemSign
                    self.addingConstraints[i][-1] = self.addingSignItemsChoices[i]

                imgui.pop_item_width()
                imgui.same_line()
                imgui.set_next_item_width(50)
                rhsValue = (self.addingConstraints[i][-2])
                rhsChanged, rhs = imgui.input_float(
                    "##aRHSC{}{}".format(i, j), rhsValue)

                if rhsChanged:
                    self.addingConstraints[i][-2] = rhs

            if imgui.radio_button("reverse rows on", self.rowsReversed == "on"):
                self.rowsReversed = "on"

            imgui.same_line(0, 20)

            if imgui.radio_button("reverse rows off", self.rowsReversed == "off"):
                self.rowsReversed = "off"

            imgui.text("reversing of rows is: {}".format(self.rowsReversed))

            if self.rowsReversed == "on":
                self.reverseRowsState = True
            else:
                self.reverseRowsState = False

            if imgui.radio_button("keep slack basic on", self.negRule == "on"):
                self.negRule = "on"

            imgui.same_line(0, 20)

            if imgui.radio_button("keep slack basic off", self.negRule == "off"):
                self.negRule = "off"

            imgui.text("keep slack basic is: {}".format(self.negRule))

            if self.negRule == "on":
                self.negRuleState = True
            else:
                self.negRuleState = False

        imgui.spacing()
        imgui.spacing()
        # the solve button =================================================
        if imgui.button("Solve"):
            try:
                if self.testInput(self.testInputSelected) is not None:
                    self.objFunc, self.constraints, isMin, self.addingConstraints = self.testInput(
                        self.testInputSelected)

                a = copy.deepcopy(self.objFunc)
                b = copy.deepcopy(self.constraints)

                if self.problemState:
                    c = copy.deepcopy(self.activity)
                    self.actDisplayCol, self.changingTable = self.doAddActivity(
                        a, b, isMin, c, self.absRule)
                else:
                    e = copy.deepcopy(self.addingConstraints)
                    self.addedConstraints = self.addingConstraints
                    if self.isConsoleOutput:
                        print(self.addingConstraints)
                    self.fixedTab, self.unfixedTab = self.doAddConstraint(
                        a, b, isMin, e, self.absRule, self.reverseRowsState, self.negRuleState)

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

        if self.problemState:
            for i in range(len(self.actDisplayCol)):
                if i == 0:
                    imgui.text("Activity    ")
                else:
                    imgui.text("Constraint {}".format(i))
                imgui.same_line()
                imgui.text("{:>15.3f}".format(float(self.actDisplayCol[i])))
                imgui.new_line()
        else:
            imgui.text("unfixed Tab:")
            for i in range(len(self.unfixedTab)):
                for j in range(len(self.unfixedTab[i])):
                    if i >= (len(self.unfixedTab) - len(self.addedConstraints)):
                        imgui.push_style_color(
                            imgui.COLOR_TEXT, 1.0, 1.0, 0.0)
                    imgui.text("{:>9.3f}".format(float(self.unfixedTab[i][j])))
                    if i >= (len(self.unfixedTab) - len(self.addedConstraints)):
                        imgui.pop_style_color()
                    imgui.same_line(0, 20)
                imgui.new_line()

            imgui.spacing()
            imgui.spacing()
            imgui.spacing()

            imgui.text("fixed Tab:")
            for i in range(len(self.fixedTab)):
                for j in range(len(self.fixedTab[i])):
                    if i >= (len(self.unfixedTab) - len(self.addedConstraints)):
                        imgui.push_style_color(
                            imgui.COLOR_TEXT, 1.0, 1.0, 0.0)
                    imgui.text("{:>9.3f}".format(float(self.fixedTab[i][j])))
                    if i >= (len(self.unfixedTab) - len(self.addedConstraints)):
                        imgui.pop_style_color()
                    imgui.same_line(0, 20)
                imgui.new_line()

        imgui.spacing()
        imgui.spacing()
        imgui.spacing()
        imgui.spacing()

        if imgui.button("Optimize again"):
            if self.problemState:
                tab = copy.deepcopy(self.changingTable)

                for i in range(len(tab)):
                    tab[i].insert(len(self.objFunc),
                                  float(self.actDisplayCol[i]))
                    if self.isConsoleOutput:
                        print(float(self.actDisplayCol[i]))

                if self.isConsoleOutput:
                    print()
                    for i in range(len(tab)):
                        for j in range(len(tab[i])):
                            print(tab[i][j], end=" ")
                        print()

                try:
                    self.newTableaus, self.changingVars, self.optimalSolution, self.IMPivotCols, self.IMPivotRows, self.IMHeaderRow = self.dual.doDualSimplex([
                    ], [], isMin, tab)

                    print("len")
                    print(len(self.changingTable))

                    self.IMHeaderRow.clear()

                    for i in range(len(self.newTableaus[-1][-1])):
                        if i < (len(self.objFunc) + 1):
                            self.IMHeaderRow.append(f"x{i+1}")
                        elif i == (len(self.newTableaus[-1][-1]) - 1):
                            self.IMHeaderRow.append(f"rhs")
                        else:
                            self.IMHeaderRow.append(f"h{i+1}")

                    if self.isConsoleOutput:
                        print()
                        for i in range(len(self.newTableaus[-1])):
                            for j in range(len(self.newTableaus[-1][i])):
                                print(
                                    float(self.newTableaus[-1][i][j]), end=" ")
                            print()

                except Exception as e:
                    print("math error in Optimize again:", e)
            else:
                if self.isConsoleOutput:
                    print()
                    for i in range(len(self.fixedTab)):
                        for j in range(len(self.fixedTab[i])):
                            print(float(self.fixedTab[i][j]), end=" ")
                        print()

                tab = copy.deepcopy(self.fixedTab)

                try:
                    self.newTableaus, self.changingVars, self.optimalSolution, self.IMPivotCols, self.IMPivotRows, self.IMHeaderRow = self.dual.doDualSimplex([
                    ], [], isMin, tab)

                    self.IMHeaderRow.clear()

                    for i in range(len(self.newTableaus[-1][-1])):
                        if i <= (len(self.objFunc) - 1):
                            self.IMHeaderRow.append(f"x{i+1}")
                        elif i == (len(self.newTableaus[-1][-1]) - 1):
                            self.IMHeaderRow.append(f"rhs")
                        else:
                            self.IMHeaderRow.append(f"h{i+1}")

                except Exception as e:
                    print("math error in Optimize again:", e)

        imgui.spacing()
        imgui.spacing()
        imgui.spacing()
        imgui.spacing()

        for i in range(len(self.newTableaus)):
            if i < len(self.IMPivotCols):
                pivotCol = self.IMPivotCols[i]
                pivotRow = self.IMPivotRows[i]
            else:
                pivotCol = -1
                pivotRow = -1
            imgui.text("Tableau {}".format(i + 1))
            imgui.text("t-" + str(i + 1))
            imgui.same_line(0, 20)
            for hCtr in range(len(self.IMHeaderRow)):
                imgui.text("{:>8}".format(str(self.IMHeaderRow[hCtr])))
                imgui.same_line(0, 20)
            imgui.spacing()
            for j in range(len(self.newTableaus[i])):
                if j == pivotRow and pivotRow != -1:
                    imgui.push_style_color(imgui.COLOR_TEXT, 0.0, 1.0, 0.0)
                if j == 0:
                    imgui.text("z  ")
                else:
                    imgui.text("c " + str(j))
                imgui.same_line(0, 20)
                for k in range(len(self.newTableaus[i][j])):
                    if k == pivotCol and pivotCol != -1:
                        imgui.push_style_color(
                            imgui.COLOR_TEXT, 0.0, 1.0, 0.0)
                    imgui.text("{:>8.3f}".format(self.newTableaus[i][j][k]))
                    if k < len(self.newTableaus[i][j]) - 1:
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

        imgui.end_child()
        imgui.end()

    def doGui(self):
        if not glfw.init():
            print("Could not initialize OpenGL context")
            return

        window = glfw.create_window(
            int(1920 / 2), int(1080 / 2), "Adding activities/constraints Simplex Prototype", None, None)
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
    classInstance = AddingActsCons(isConsoleOutput)
    classInstance.doGui()


if __name__ == "__main__":
    main(True)
