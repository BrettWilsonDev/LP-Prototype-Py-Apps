import pygame
from imgui.integrations.pygame import PygameRenderer
import imgui

import sys
import os
import copy


class DualSimplex:
    def __init__(self, isConsoleOutput=False):
        self.isConsoleOutput = isConsoleOutput
        self.testInputSelected = -1

        self.IMPivotCols = []
        self.IMPivotRows = []
        self.IMHeaderRow = []

        self.problemType = "Max"

        # dual constraints
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

        self.errorE = ""

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

            isMin = True
        elif testNum == 3:
            objFunc = [10, 50, 80, 100]
            constraints = [[1, 4, 4, 8, 140, 0],
                           [1, 0, 0, 0, 50, 0],
                           [1, 0, 0, 0, 50, 1],
                           [1, 1, 1, 1, 70, 1],
                           ]
        elif testNum == 4:
            objFunc = [9, 4, 16, 0, 0, 0]
            constraints = [[9, 4, 16, -5, -14, 0, 0],
                           [5, 7, 16, -8, -15, 0, 0],
                           [4, 9, 13, -7, -12, 0, 0],
                           [0, 0, 0, 5, 14, 1, 0],
                           [0, 0, 0, 5, 14, 1, 1],
                           [1, 0, 0, 0, 0, 0.0001, 1],
                           [0, 1, 0, 0, 0, 0.0001, 1],
                           [0, 0, 1, 0, 0, 0.0001, 1],
                           [0, 0, 0, 1, 0, 0.0001, 1],
                           [0, 0, 0, 0, 1, 0.0001, 1],
                           ]

        if testNum == -1:
            return None
        else:
            return objFunc, constraints, isMin

    def doFormulationOperation(self, objFunc, constraints):
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

        # build the display header row eg x1 x2 e1 e2 s1 s2 rhs
        imCtr = 1
        for i in range(len(objFunc)):
            self.IMHeaderRow.append("x" + str(imCtr))
            imCtr += 1

        imCtr = 1

        if excessCount > 0:
            for i in range(excessCount):
                self.IMHeaderRow.append("e" + str(imCtr))
                imCtr += 1

        if slackCount > 0:
            for i in range(slackCount):
                self.IMHeaderRow.append("s" + str(imCtr))
                imCtr += 1

        self.IMHeaderRow.append("rhs")

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

    def doFormulationOperation(self, objFunc, constraints):
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

        # build the display header row eg x1 x2 e1 e2 s1 s2 rhs
        imCtr = 1
        for i in range(len(objFunc)):
            self.IMHeaderRow.append("x" + str(imCtr))
            imCtr += 1

        imCtr = 1

        if excessCount > 0:
            for i in range(excessCount):
                self.IMHeaderRow.append("e" + str(imCtr))
                imCtr += 1

        if slackCount > 0:
            for i in range(slackCount):
                self.IMHeaderRow.append("s" + str(imCtr))
                imCtr += 1

        self.IMHeaderRow.append("rhs")

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

    def doDualPivotOperation(self, tab):
        thetaRow = []

        rhs = [row[-1] for row in tab]
        rhsNeg = [row[-1] for row in tab if row[-1] < 0]

        minRhsNum = min(rhsNeg)

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

        # if zero is the only choice then pivot on it
        if all(x == 0 or x == float('inf') for x in dualPivotThetas):
            smallestPosPivotTheta = 0
        else:
            smallestPosPivotTheta = min(
                dualPivotThetas, key=lambda x: x if x > 0 else float('inf'))

        rowIndex = pivotRow
        colIndex = dualPivotThetas.index(smallestPosPivotTheta)

        oldTab = tab.copy()

        newTab = []

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

                newTab[i][j] = mathItem

        newTab[rowIndex] = pivotMathRow

        if self.isConsoleOutput:
            print(f"the pivot col in Dual is {
                colIndex + 1} and the pivot row is {rowIndex + 1}")

        self.IMPivotCols.append(colIndex)
        self.IMPivotRows.append(rowIndex)

        return newTab, thetaRow

    def doPrimalPivotOperation(self, tab, isMin):
        thetasCol = []

        testRow = tab[0][:-1]

        if isMin:
            largestNegativeNumber = min(
                num for num in testRow if num < 0 and num != 0)
        else:
            largestNegativeNumber = min(
                num for num in testRow if num < 0 and num != 0)

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

        allNegativeThetas = all(num < 0 for num in thetas)

        if allNegativeThetas:
            return None, None

        if not any(num > 0 for num in thetas if num not in {0, float('inf')}):
            if 0 in thetas:
                minTheta = 0.0
            else:
                return None, None
        else:
            minTheta = min(x for x in thetas if x > 0 and x != float('inf'))
            # minTheta = min(num for num in thetas if num > 0)

        # minTheta = min(num for num in thetas if num > 0)

        if minTheta == float('inf'):
            if 0 in thetas:
                minTheta = 0
            else:
                return None, None

        rowIndex = thetas.index(minTheta) + 1

        operationTab = []

        divNumber = tab[rowIndex][colIndex]

        if divNumber == 0:
            return None, None

        operationTab = [[0 for _ in row] for row in tab]

        for i in range(len(tab)):
            for j in range(len(tab[i])):
                operationTab[rowIndex][j] = tab[rowIndex][j] / divNumber
                if operationTab[rowIndex][j] == -0.0:
                    operationTab[rowIndex][j] = 0.0

        # the formula: Element_New_Table((i, j)) = Element_Old_Table((i, j)) - (Element_Old_Table((i, Pivot_column)) * Element_New_Table((Pivot_Row, j)))
        for i in range(len(tab)):
            if i == rowIndex:
                continue
            for j in range(len(tab[i])):

                mathItem = tab[i][j] - \
                    (tab[i][colIndex] * operationTab[rowIndex][j])

                operationTab[i][j] = mathItem

        if self.isConsoleOutput:
            print(f"the pivot col in primal is {
                colIndex + 1} and the pivot row is {rowIndex + 1}")

        self.IMPivotCols.append(colIndex)
        self.IMPivotRows.append(rowIndex)

        return operationTab, thetasCol

    def getInput(self, objFunc, constrants, isMin):
        amtOfE = 0
        amtOfS = 0
        for i in range(len(constrants)):
            if constrants[i][-1] == 1 or constrants[i][-1] == 2:
                amtOfE += 1
            else:
                amtOfS += 1

        tab = self.doFormulationOperation(objFunc, constrants)

        return tab, isMin, amtOfE, amtOfS, len(objFunc)

    def doDualSimplex(self, objFunc, constraints, isMin, tabOverride=None):
        thetaCols = []
        tableaus = []

        tab, isMin, amtOfE, amtOfS, lenObj = self.getInput(
            objFunc, constraints, isMin)

        # for use in other tools
        if tabOverride is not None:
            tab = tabOverride
            self.IMPivotCols = []
            self.IMPivotRows = []
            del self.IMHeaderRow[-1]

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

            tab, thetaRow = self.doDualPivotOperation(tableaus[-1])
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
            if self.isConsoleOutput:
                print("\nOptimal Solution Found")
                print(tableaus[-1][0][-1])
                print()
        else:
            while True:
                for items in tableaus[-1]:
                    for item in items:
                        if item == -0.0:
                            item = 0.0

                if tableaus[-1] is None:
                    if self.isConsoleOutput:
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

                tab, thetaCol = self.doPrimalPivotOperation(
                    tableaus[-1], isMin)

                if thetaCol is None and tab is None:
                    break

                thetaCols.append(thetaCol.copy())
                tableaus.append(tab)

            # final optimal check
            rhsTest = []
            for i in range(len(tableaus[-1])):
                rhsTest.append(tableaus[-1][i][-1])
            allRhsPositive = all(num >= 0 for num in rhsTest)

            if not allRhsPositive:
                tableaus.pop()
                self.IMPivotCols.pop()
                self.IMPivotRows.pop()

            if self.isConsoleOutput:
                print("\nOptimal Solution Found")
                if tableaus[-1] is not None:
                    print(tableaus[-1][0][-1])
                    print()
                else:
                    print("\nNo Optimal Solution Found")

        xVars = []
        for i in range(lenObj):
            xVars.append("x{}".format(i + 1))

        amtOfX = 0
        amtOfSlack = 0
        amtOfExcess = 0

        topRow = []

        topRowSize = lenObj + amtOfE + amtOfS

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

        if self.isConsoleOutput:
            for i in range(len(tableaus)):
                print("Tableau {}".format(i + 1))
                print(" ".join(["{:>10}".format(val) for val in topRow]))
                for j in range(len(tableaus[i])):
                    for k in range(len(tableaus[i][j])):
                        print("{:10.3f}".format(tableaus[i][j][k]), end=" ")
                    print()
                print()

        tSCVars = []
        for k in range(lenObj):
            columnIndex = k  # Index of the column you want to work with
            tCVars = []

            for i in range(len(tableaus[-1])):
                columnValue = tableaus[-1][i][columnIndex]
                # Now you can work with the value in the column
                tCVars.append(columnValue)
            if (sum(1 for num in tCVars if num != 0) == 1):
                tSCVars.append(tCVars)
            else:
                tSCVars.append(None)

        changingVars = []
        for i in range(len(tSCVars)):
            if tSCVars[i] is not None:
                changingVars.append(tableaus[-1][tSCVars[i].index(1.0)][-1])
            else:
                changingVars.append(0)

        if self.isConsoleOutput:
            print()
            print(changingVars)

        optimalSolution = tableaus[-1][0][-1]
        if self.isConsoleOutput:
            print()
            print(optimalSolution)

        if tabOverride is None:
            return tableaus, changingVars, optimalSolution
        else:
            return tableaus, changingVars, optimalSolution, self.IMPivotCols, self.IMPivotRows, self.IMHeaderRow

    def imguiUIElements(self, windowSize):
        imgui.new_frame()

        imgui.set_next_window_position(0, 0)  # Set the window position
        imgui.set_next_window_size(
            (windowSize[0]), (windowSize[1]))  # Set the window size
        imgui.begin("Tableaus Output",
                    flags=imgui.WINDOW_NO_TITLE_BAR | imgui.WINDOW_NO_RESIZE)

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
            # imgui.same_line()

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

        # solve button =======================================================================================
        if imgui.button("Solve"):
            try:
                if self.testInput(self.testInputSelected) is not None:
                    self.objFunc, self.constraints, isMin = self.testInput(
                        self.testInputSelected)

                a = copy.deepcopy(self.objFunc)
                b = copy.deepcopy(self.constraints)
                self.tableaus, self.changingVars, self.optimalSolution = self.doDualSimplex(
                    a, b, isMin)

                self.IMPivotCols.append(-1)
                self.IMPivotRows.append(-1)

                self.tRow = copy.deepcopy(self.IMPivotRows)
                self.tCol = copy.deepcopy(self.IMPivotCols)
                self.tHeader = copy.deepcopy(self.IMHeaderRow)

                self.IMHeaderRow.clear()
                self.IMPivotRows.clear()
                self.IMPivotCols.clear()

                self.errorE = ""
            except Exception as e:
                print("math error:", e)
                imgui.text("math error: {}".format(e))
                self.errorE = "math error: {}".format(e)
                raise

        imgui.spacing()
        imgui.spacing()

        imgui.text(self.errorE)

        imgui.spacing()
        imgui.spacing()
        for i in range(len(self.tableaus)):
            pivotCol = self.tCol[i]
            pivotRow = self.tRow[i]
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
                    imgui.text("z  ")
                else:
                    imgui.text("c " + str(j))
                imgui.same_line(0, 20)
                for k in range(len(self.tableaus[i][j])):
                    if k == pivotCol and pivotCol != -1:
                        imgui.push_style_color(
                            imgui.COLOR_TEXT, 0.0, 1.0, 0.0)
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

        imgui.end()

    def doGui(self):
        pygame.init()
        size = 1920 / 2, 1080 / 2

        os.system('cls' if os.name == 'nt' else 'clear')
        if self.isConsoleOutput:
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

        while 1:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    exit()

                impl.process_event(event)

            windowSize = pygame.display.get_window_size()

            self.imguiUIElements(windowSize)

            imgui.render()
            impl.render(imgui.get_draw_data())

            pygame.display.flip()


def main(isConsoleOutput=False):
    classInstance = DualSimplex(isConsoleOutput)
    classInstance.doGui()


if __name__ == "__main__":
    main(True)
