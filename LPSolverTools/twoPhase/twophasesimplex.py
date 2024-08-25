if __name__ == "__main__":
    import imgui
    from imgui.integrations.glfw import GlfwRenderer
    import glfw

import math
import copy
import sys
import os


class TwoPhaseSimplex:

    def __init__(self, isConsoleOutput=False):
        self.isConsoleOutput = isConsoleOutput

        self.reset()

    def reset(self):
        self.testInputSelected = -1

        self.IMPivotCols = []
        self.IMPivotRows = []
        self.IMHeaderRow = []
        self.IMPhaseType = []

        self.problemType = "Max"

        self.amtOfObjVars = 2
        self.objFunc = [0.0, 0.0]

        self.constraints = [[0.0, 0.0, 0.0, 0.0]]
        self.signItems = ["<=", ">="]
        self.signItemsChoices = [0]

        self.amtOfConstraints = 1

        self.tableaus = []

        self.pivotCol = -1
        self.pivotRow = -1
        self.tCol = -1
        self.tRow = -1
        self.tHeader = []

    def testInput(self, testNum=-1):
        isMin = False

        if testNum == 0:
            objFunc = [100, 30]

            # # 0 is <= and 1 is >= and 2 is =
            constraints = [
                [0, 1, 3, 1],
                [1, 1, 7, 0],
                [10, 4, 40, 0],
            ]
        elif testNum == 1:
            objFunc = [10, 50, 80, 100]
            constraints = [[1, 4, 4, 8, 140, 0],
                           [1, 0, 0, 0, 50, 0],
                           [1, 0, 0, 0, 50, 1],
                           [1, 1, 1, 1, 70, 1],
                           ]
        elif testNum == 2:
            objFunc = [48, 20, 8]

            constraints = [[8, 4, 2, 60, 1],
                           [6, 2, 1.5, 30, 1],
                           [1, 1.5, 0.5, 20, 1]]
            isMin = True

        if testNum == -1:
            return None
        else:
            return objFunc, constraints, isMin

    def formulateFirstTab1(self, objFunc, constraints):
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
            self.IMHeaderRow.append("x" + str(imCtr))
            imCtr += 1

        imCtr = 1

        if excessCount > 0:
            for i in range(excessCount):
                self.IMHeaderRow.append("a" + str(imCtr))
                self.IMHeaderRow.append("e" + str(imCtr))
                imCtr += 1

        if slackCount > 0:
            for i in range(slackCount):
                self.IMHeaderRow.append("s" + str(imCtr))
                imCtr += 1

        self.IMHeaderRow.append("rhs")

        eCons = []

        for i in range(len(constraints)):
            if constraints[i][-1] == 1:
                eCons.append(copy.deepcopy(constraints[i]))

        for i in range(len(eCons)):
            for j in range(len(eCons[i])):
                eCons[i][j] = eCons[i][j] * -1

        # calculate summed w row
        summedW = []
        temp = 0
        for i in range(objFuncSize + 1):
            temp = 0
            for j in range(len(eCons)):
                temp += eCons[j][i]

            summedW.append(temp)

        if self.isConsoleOutput:
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

        if self.isConsoleOutput:
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

        for i in range(2, len(tab)):
            for j in range(len(tab[i])):
                tab[i][j] = tempAllCons[i - 2][j]

        for i in range(2, len(tab)):
            for j in range(objFuncSize, len(tab[i])):
                if tempAllCons[i - 2][j] == -1:
                    tab[0][j] = -1

        return tab, aCols

    def doPivotOperationsPhase1(self, tab):
        largestW = max(tab[0][:-1])

        pivotCol = tab[0][:-1].index(largestW)

        thetas = []
        for i in range(2, len(tab)):
            if tab[i][pivotCol] == 0:
                thetas.append(float('inf'))
            else:
                thetas.append(tab[i][-1] / tab[i][pivotCol])

        theta = min(x for x in thetas if x > 0 and x != float('inf'))

        pivotRow = thetas.index(theta)
        pivotRow += 2

        newTab = copy.deepcopy(tab)

        for i in range(len(newTab)):
            for j in range(len(newTab[i])):
                newTab[i][j] = 0

        # the div row
        divNum = tab[pivotRow][pivotCol]

        if divNum == 0:
            if self.isConsoleOutput:
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

        for i in range(len(newTab[0])):
            # if newTab[0][i] > 0 and abs(newTab[0][i]) < 1e-16:
            if abs(newTab[0][i]) < 1e-12:
                newTab[0][i] = 0.0

        isAllNegW = all(num <= 0 for num in newTab[0]) if newTab[0] else False

        if self.isConsoleOutput:
            print(f"In Phase 1, The pivot row is {pivotRow + 1} and the pivot col is {pivotCol + 1}")

        self.IMPivotCols.append(pivotCol)
        self.IMPivotRows.append(pivotRow)

        return newTab, isAllNegW

    def doPivotOperationsPhase2(self, tab, isMin):
        if isMin:
            largestZ = max(tab[1][:-1])
        else:
            largestZ = min(tab[1][:-1])

        pivotCol = tab[1][:-1].index(largestZ)

        thetas = []
        for i in range(2, len(tab)):
            if tab[i][pivotCol] == 0:
                thetas.append(float('inf'))
            else:
                thetas.append(tab[i][-1] / tab[i][pivotCol])

        allNegativeThetas = all(num < 0 for num in thetas)

        if allNegativeThetas:
            return None, None

        for i in range(len(thetas)):
            if abs(thetas[i]) < 1e-12:
                thetas[i] = 0.0

        if not any(num > 0 for num in thetas if num not in {0, float('inf')}):
            if 0 in thetas:
                theta = 0.0
            else:
                return None, None
        else:
            theta = min(x for x in thetas if x > 0 and x != float('inf'))

        pivotRow = thetas.index(theta)
        pivotRow += 2

        newTab = copy.deepcopy(tab)

        for i in range(len(newTab)):
            for j in range(len(newTab[i])):
                newTab[i][j] = 0

        # the div row
        divNum = tab[pivotRow][pivotCol]

        if divNum == 0:
            if self.isConsoleOutput:
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

        if self.isConsoleOutput:
            print(f"In Phase 2, The pivot row is {pivotRow + 1} and the pivot col is {pivotCol + 1}")

        self.IMPivotCols.append(pivotCol)
        self.IMPivotRows.append(pivotRow)

        return newTab, isAllNegZ

    def doTwoPhase(self, objFunc, constraints, isMin):
        tabs = []
        isAllNegW = False
        tab, aCols = self.formulateFirstTab1(objFunc, constraints)
        tabs.append(tab)

        isAllNegW = all(
            num <= 0 for num in tabs[-1][0]) if tabs[-1][0] else False
        phase1Ctr = 0
        while not isAllNegW:
            tab, isAllNegW = self.doPivotOperationsPhase1(tabs[-1])
            if isAllNegW is None and tab is None:
                break

            tabs.append(tab)

            phase1Ctr += 1
            self.IMPhaseType.append(0)
            if isAllNegW or phase1Ctr > 10:
                break

        tabPhaseNum = phase1Ctr + 1

        newTab = copy.deepcopy(tabs[-1])

        for k in range(len(aCols)):
            for i in range(len(newTab)):
                newTab[i][aCols[k]] = 0.0

        tabs.append(newTab)

        if not isMin:
            AllPosZ = all(num >= 0 for num in tabs[-1][1][:-1])
        else:
            AllPosZ = all(num <= 0 for num in tabs[-1][1][:-1])

        indexOfDupe = tabs.index(tabs[-1])

        phase2Ctr = 0
        while not AllPosZ:
            self.prevZ = tabs[-1][1][-1]
            tab, AllPosZ = self.doPivotOperationsPhase2(tabs[-1], isMin)

            if AllPosZ is None and tab is None:
                break

            tabs.append(tab)

            if AllPosZ or phase2Ctr > 100:
                break

            phase2Ctr += 1
            self.IMPhaseType.append(2)

        del tabs[indexOfDupe]

        # final optimal check
        isAllNegW = all(
            num <= 0 for num in tabs[-1][0]) if tabs[-1][0] else False
        if not isAllNegW:
            tabs.pop()
            self.IMPivotCols.pop()
            self.IMPivotRows.pop()

        self.IMPhaseType.append(2)
        currentPhase = 1
        for i in range(len(tabs)):
            if i == tabPhaseNum:
                currentPhase = 2

            if self.isConsoleOutput:
                print("Phase {}".format(currentPhase))
                print("Tableau {}".format(i + 1))
                for j in range(len(tabs[i])):
                    for k in range(len(tabs[i][j])):
                        print("{:10.3f}".format(tabs[i][j][k]), end=" ")
                    print()
                print()

        return tabs

    def imguiUIElements(self, windowSize, windowPosX = 0, windowPosY = 0):
        imgui.set_next_window_position(windowPosX, windowPosY)  # Set the window position
        imgui.set_next_window_size(
            (windowSize[0]), (windowSize[1]))  # Set the window size
        imgui.begin("Tableaus Output",
                    flags=imgui.WINDOW_NO_TITLE_BAR | imgui.WINDOW_NO_RESIZE | imgui.WINDOW_ALWAYS_HORIZONTAL_SCROLLBAR)
        imgui.begin_child("Scrollable Child", width=0, height=0,
            border=True, flags=imgui.WINDOW_ALWAYS_HORIZONTAL_SCROLLBAR)

        # simplex stuff

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
            if amtOfObjVars != 2:
                amtOfObjVars += -1
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
                self.constraints.append([0.0] * (amtOfObjVars + 2))

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

        # solve button ============================================================
        if imgui.button("Solve"):
            try:
                # objFunc, constraints, isMin = testInput()
                if self.testInput(self.testInputSelected) is not None:
                    self.objFunc, self.constraints, isMin = self.testInput(
                        self.testInputSelected)

                a = copy.deepcopy(self.objFunc)
                b = copy.deepcopy(self.constraints)
                self.tableaus = self.doTwoPhase(a, b, isMin)

                # del tableaus[-2]

                self.IMPivotCols.append(-1)
                self.IMPivotRows.append(-1)

                self.IMPhaseType.append(0)
                self.IMPhaseType.append(0)

                self.tRow = copy.deepcopy(self.IMPivotRows)
                self.tCol = copy.deepcopy(self.IMPivotCols)
                self.tHeader = copy.deepcopy(self.IMHeaderRow)
                self.tPhase = copy.deepcopy(self.IMPhaseType)
                self.tPhase[-1] = 2
                self.tPhase[-2] = 2

                self.IMHeaderRow.clear()
                self.IMPivotRows.clear()
                self.IMPivotCols.clear()
                self.IMPhaseType.clear()

                self.tCol.append(-1)
                self.tRow.append(-1)

            except Exception as e:
                print("math error:", e)
                
        imgui.same_line(0, 30)
        imgui.push_style_color(imgui.COLOR_TEXT, 1.0, 0.0, 0.0)
        if imgui.button("Reset"):
            self.reset()
        imgui.pop_style_color()


        imgui.spacing()
        imgui.spacing()
        for i in range(len(self.tableaus)):
            pivotCol = self.tCol[i]
            pivotRow = self.tRow[i]
            if self.tPhase[i] == 0:
                imgui.text("Phase 1")
            else:
                imgui.text("Phase 2")
            imgui.text("Tableau {}".format(i + 1))
            imgui.text("t-" + str(i + 1))
            imgui.same_line(0, 20)
            for hCtr in range(len(self.tHeader)):
                imgui.text("{:>8}".format(str(self.tHeader[hCtr])))
                imgui.same_line(0, 20)
            imgui.spacing()
            for j in range(len(self.tableaus[i])):
                if j == pivotRow and pivotRow != -1:
                    imgui.push_style_color(imgui.COLOR_TEXT, 0.0, 1.0, 0.0)
                if j == 0:
                    imgui.text("w  ")
                elif j == 1:
                    imgui.text("z  ")
                else:
                    imgui.text("c " + str(j - 1))
                imgui.same_line(0, 20)
                for k in range(len(self.tableaus[i][j])):
                    if k == pivotCol and pivotCol != -1:
                        imgui.push_style_color(imgui.COLOR_TEXT, 0.0, 1.0, 0.0)
                    imgui.text("{:>8.3f}".format(self.tableaus[i][j][k]))
                    if k < len(self.tableaus[i][j]) - 1:
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

        imgui.end_child()
        imgui.end()

    def doGui(self):
        if not glfw.init():
            print("Could not initialize OpenGL context")
            return

        window = glfw.create_window(
            int(1920 / 2), int(1080 / 2), "Two-Phase Simplex Prototype", None, None)
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
    classInstance = TwoPhaseSimplex(isConsoleOutput)
    classInstance.doGui()


if __name__ == "__main__":
    main(True)
