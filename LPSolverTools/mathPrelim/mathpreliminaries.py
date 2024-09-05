if __name__ == "__main__":
    import imgui
    from imgui.integrations.glfw import GlfwRenderer
    import glfw

import math
import copy
import sys
import os

import sympy as sp

# python to exe keeps files in root
try:
    from dualsimplex import DualSimplex as Dual
except:
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    from dual.dualsimplex import DualSimplex as Dual


class MathPreliminaries:

    def __init__(self, isConsoleOutput=False):
        self.isConsoleOutput = isConsoleOutput

        self.reset()

    def reset(self):
        self.testInputSelected = -1

        self.dual = Dual()

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

        self.matCbv = []
        self.matB = []
        self.matBNegOne = []
        self.matCbvNegOne = []

        self.absRule = False

        self.lockOptTab = "off"
        self.optTabLockState = False

        self.newTableaus = []

        self.IMPivotCols = []
        self.IMPivotRows = []
        self.IMHeaderRow = []

        self.pivotCol = -1
        self.pivotRow = -1

        self.solveDelta = False
        self.deltaSolve = "off"

        self.isAllDeltaCRow = False
        self.isSingleDeltaCRow = False
        self.isSingleDeltaARow = False
        self.singleCIndex = -1
        self.singleAIndex = -1
        self.isDeltaZCol = False
        self.isAllDeltaRows = False
        self.isFormulaDeltaChanged = False

        self.currentDeltaSelection = "dStore0"

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

    def scrubDelta(self, lst):
        cleanedList = []

        for elem in lst:
            if isinstance(elem, (sp.Add, sp.Mul)):
                # Remove terms involving `d` and keep only the constant term
                termWithoutd = elem.as_independent(self.d, as_Add=True)[0]
                cleanedList.append(termWithoutd)
            elif hasattr(elem, 'has') and elem.has(self.d):
                # If the entire element is `d`, replace with 0
                cleanedList.append(0)
            else:
                cleanedList.append(elem)

        return cleanedList

    def doFormulationOperation(self, objFunc, constraints, absRule=False):
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

        # strange abs rule
        if absRule:
            for i in range(len(opTable[0])):
                if not isinstance(opTable[0][i], (sp.Add, sp.Mul, sp.Abs)):
                    opTable[0][i] = abs(opTable[0][i])
                else:
                    var = (sp.Abs(opTable[0][i]))
                    var = str(var)
                    var = var.replace("Abs(", "").replace(")", "")
                    var = sp.sympify(var)
                    opTable[0][i] = var

            for i in range(len(opTable)):
                for j in range(len(objFunc)):
                    if not isinstance(opTable[i][j], (sp.Add, sp.Mul, sp.Abs)):
                        opTable[i][j] = abs(opTable[i][j])
                    else:
                        var = (sp.Abs(opTable[i][j]))
                        var = str(var)
                        var = var.replace("Abs(", "").replace(")", "")
                        var = sp.sympify(var)
                        opTable[i][j] = var

            for i in range(len(opTable)):
                opTable[i][-1] = abs(opTable[i][-1])
                if not isinstance(opTable[i][-1], (sp.Add, sp.Mul, sp.Abs)):
                    opTable[i][-1] = abs(opTable[i][-1])
                else:
                    var = (sp.Abs(opTable[i][-1]))
                    var = str(var)
                    var = var.replace("Abs(", "").replace(")", "")
                    var = sp.sympify(var)
                    opTable[i][-1] = var

            for i in range(len(opTable)):
                for j in range(tableSizeW - excessCount - 1, len(opTable[i]) - 1):
                    if opTable[i][j] != 0:
                        opTable[i][j] = -opTable[i][j]

        # build the header row
        self.globalHeaderRow = []

        for i in range(len(objFunc)):
            self.globalHeaderRow.append("x" + str(i + 1))

        for i in range(excessCount):
            self.globalHeaderRow.append("e" + str(i + 1))

        for i in range(slackCount):
            self.globalHeaderRow.append("s" + str(i + 1))

        self.globalHeaderRow.append("rhs")

        if self.isConsoleOutput:
            print(self.globalHeaderRow)

        return opTable

    def doPreliminaries(self, objFunc, constraints, isMin, absRule=False, optTabLockState=False):
        # get list spots for later use =========================

        # objFunc, constraints, isMin = testInput()

        # make temporary copies of objFunc and constraints
        tObjFunc = copy.deepcopy(objFunc)
        tObjFunc = self.scrubDelta(tObjFunc)

        tConstraints = copy.deepcopy(constraints)
        for i in range(len(constraints)):
            tConstraints[i] = self.scrubDelta(tConstraints[i])

        if not optTabLockState:
            tableaus, changingVars, optimalSolution = self.dual.doDualSimplex(
                tObjFunc, tConstraints, isMin)
            self.globalOptimalTab = copy.deepcopy(tableaus)
        else:
            tableaus = self.globalOptimalTab

        # keep delta in the table
        deltaTab = copy.deepcopy(tableaus[0])
        deltaTab = self.doFormulationOperation(objFunc, constraints, absRule)

        # get the spots of the basic variables
        basicVarSpots = []
        for k in range(len(tableaus[-1][-1])):
            columnIndex = k
            tCVars = []

            for i in range(len(tableaus[-1])):
                columnValue = tableaus[-1][i][columnIndex]
                tCVars.append(columnValue)

            if (sum(tCVars) == 1):
                basicVarSpots.append(k)

        # get the columns of the basic variables
        basicVarCols = []
        for i in range(len(tableaus[-1][-1])):
            tLst = []
            if i in basicVarSpots:
                for j in range(len(tableaus[-1])):
                    tLst.append(tableaus[-1][j][i])
                basicVarCols.append(tLst)

        # sort the cbv according the basic var positions
        zippedCbv = list(zip(basicVarCols, basicVarSpots))
        sortedCbvZipped = sorted(
            zippedCbv, key=lambda x: x[0].index(1) if 1 in x[0] else len(x[0]))
        sortedBasicVars, basicVarSpots = zip(*sortedCbvZipped)

        # populate matrixes ========================================================

        tableaus[0] = copy.deepcopy(deltaTab)

        cbv = []
        for i in range(len(basicVarSpots)):
            # cbv.append(copy.deepcopy(-tableaus[0][0][basicVarSpots[i]]))
            # cbv.append(copy.deepcopy(tableaus[0][0][basicVarSpots[i]]))

            if absRule:
                cbv.append(copy.deepcopy(tableaus[0][0][basicVarSpots[i]]))
            else:
                cbv.append(copy.deepcopy(-tableaus[0][0][basicVarSpots[i]]))

        if self.isConsoleOutput:
            print(basicVarSpots)

        matB = []
        for i in range(len(basicVarSpots)):
            tLst = []
            for j in range(1, len(tableaus[0])):
                # print(tableaus[0][j][basicVarSpots[i]], end=" ")
                tLst.append(tableaus[0][j][basicVarSpots[i]])
            matB.append(tLst)

        matrixCbv = sp.Matrix(cbv)

        matrixB = sp.Matrix(matB)

        matrixBNegOne = matrixB.inv()

        matrixCbvNegOne = matrixBNegOne * matrixCbv
        if self.isConsoleOutput:
            print("cbv")
            print(matrixCbv)

            print("B")
            print(matrixB)

            print("B^-1")
            print(matrixBNegOne)

            print("cbvB^-1")
            print(matrixCbvNegOne)
            print()

        # get the z values of the new changing table should be the same of the optimal table
        changingZRow = []
        for j in range(len(deltaTab[-1]) - 1):
            tLst = []
            for i in range(1, len(deltaTab)):
                tLst.append(deltaTab[i][j])
            mmultCbvNegOneBCol = sp.Matrix(tLst).transpose() * matrixCbvNegOne
            matNegValue = (mmultCbvNegOneBCol[0, 0])
            # changingZRow.append(matNegValue - -deltaTab[0][j])
            if absRule:
                changingZRow.append(matNegValue - deltaTab[0][j])
            else:
                changingZRow.append(matNegValue - -deltaTab[0][j])

        # get the rhs optimal value
        tRhsCol = []
        for i in range(1, len(deltaTab)):
            tRhsCol.append(deltaTab[i][-1])

        tRhsOptimal = (sp.Matrix(tRhsCol).transpose() * matrixCbvNegOne)
        changingOptmal = (tRhsOptimal[0, 0])

        # get the b values of the new changing table
        tChangingBv = []
        for j in range(len(deltaTab[-1])):
            tLst = []
            for i in range(1, len(deltaTab)):
                tLst.append(deltaTab[i][j])
            tMatrix = (sp.Matrix(tLst).transpose() * matrixBNegOne)
            tChangingBv.append(tMatrix.tolist())

        # convert to 2d list
        changingBv = []
        for sublist1 in tChangingBv:
            for sublist2 in sublist1:
                changingBv.append(sublist2)

        changingTable = copy.deepcopy(tableaus[-1])

        changingZRow.append(changingOptmal)

        changingTable[0] = changingZRow

        transposeChangingB = sp.Matrix(changingBv).transpose().tolist()

        for i in range(len(changingTable) - 1):
            for j in range(len(changingTable[i])):
                changingTable[i + 1][j] = transposeChangingB[i][j]

        for i in range(len(changingTable)):
            for j in range(len(changingTable[i])):
                value = changingTable[i][j]
                try:
                    value = float(value)
                    changingTable[i][j] = float(value)
                except (TypeError, ValueError):
                    pass

        if self.isConsoleOutput:
            print("\ninitial table\n")
            for i in range(len(tableaus[0])):
                for j in range(len(tableaus[0][i])):
                    print("{:15}".format(str(tableaus[0][i][j])), end=" ")
                print()

            print("\noptimal table\n")
            for i in range(len(tableaus[-1])):
                for j in range(len(tableaus[-1][i])):
                    print("{:15}".format(str(tableaus[-1][i][j])), end=" ")
                print()

            print("\noptimal changing table\n")
            for i in range(len(changingTable)):
                for j in range(len(changingTable[i])):
                    print("{:15}".format(str(changingTable[i][j])), end=" ")
                print()

        return changingTable, matrixCbv, matrixB, matrixBNegOne, matrixCbvNegOne, basicVarSpots

    def absF(self, val):
        try:
            return abs(val)
        except TypeError:
            return float("inf")

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
        imgui.text(
            "Use + to mark the item for delta analysis O is the current selection.")
        imgui.spacing()
        # imgui.spacing()
        imgui.text(
            "For no selection select:")

        imgui.same_line()
        imgui.push_id("##deltaButtonStore {}{}".format(0, 1))
        if self.currentDeltaSelection == f"dStore0":
            deltaSelectText = "O"
        else:
            deltaSelectText = "+"
        if imgui.button(f"{deltaSelectText}"):
            self.currentDeltaSelection = f"dStore0"
        imgui.pop_id()
        imgui.spacing()
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

            if rhsChanged:
                self.constraints[i][-2] = rhs

        if imgui.radio_button("lock optimal tab", self.lockOptTab == "on"):
            self.lockOptTab = "on"

        imgui.same_line(0, 20)

        if imgui.radio_button("unlock optimal tab", self.lockOptTab == "off"):
            self.lockOptTab = "off"

        imgui.text("optimal tab lock: {}".format(self.lockOptTab))

        if imgui.radio_button("solve Delta on", self.deltaSolve == "on"):
            self.deltaSolve = "on"

        imgui.same_line(0, 20)

        if imgui.radio_button("solve Delta off", self.deltaSolve == "off"):
            self.deltaSolve = "off"

        if self.problemType == "Min":
            isMin = True
        else:
            isMin = False

        if self.absProblemType == "abs On":
            absRule = True
        else:
            absRule = False

        if self.lockOptTab == "on":
            optTabLockState = True
        else:
            optTabLockState = False

        if self.deltaSolve == "on":
            self.solveDelta = True
        else:
            self.solveDelta = False

        if optTabLockState:
            self.isFormulaDeltaChanged = False

        # solve button ===============================================================================================
        if imgui.button("Solve"):
            try:
                if self.testInput(self.testInputSelected) is not None:
                    self.objFunc, self.constraints, isMin = self.testInput(
                        self.testInputSelected)
                    
                bkupObjFunc = copy.deepcopy(self.objFunc)
                bkupConstraints = copy.deepcopy(self.constraints)

                if self.currentDeltaSelection != "dStore0":
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

                # print(objFunc, constraints, isMin)
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

                self.changingTable, matrixCbv, matrixB, matrixBNegOne, matrixCbvNegOne, basicVarSpots = self.doPreliminaries(
                    a, b, isMin, absRule, optTabLockState)

                self.matCbv = matrixCbv.tolist()
                self.matB = matrixB.transpose().tolist()
                self.matBNegOne = matrixBNegOne.transpose().tolist()
                self.matCbvNegOne = matrixCbvNegOne.tolist()

                # make matrix in to a 2d list
                tMatCbv = []
                tMatCbvNegOne = []
                for i in range(len(self.matCbv)):
                    tMatCbv.append(self.matCbv[i][0])
                    tMatCbvNegOne.append(self.matCbvNegOne[i][0])
                self.matCbv = tMatCbv
                self.matCbvNegOne = tMatCbvNegOne

                if self.solveDelta:
                    for i in range(len(self.matCbv)):
                        if isinstance(self.matCbv[i], (sp.Add, sp.Mul)):
                            self.matCbv[i] = f"d = {round(float(sp.solve(self.matCbv[i], self.d)[0]), 6)}"

                    for i in range(len(self.matCbvNegOne)):
                            if isinstance(self.matCbvNegOne[i], (sp.Add, sp.Mul)):
                                self.matCbvNegOne[i] = f"d = {round(float(sp.solve(self.matCbvNegOne[i], self.d)[0]), 6)}"
                                

                    for i in range(len(self.changingTable)):
                        for j in range(len(self.changingTable[i])):
                            if isinstance(self.changingTable[i][j], (sp.Add, sp.Mul)):
                                self.changingTable[i][j] = f"d = {round(float(sp.solve(self.changingTable[i][j], self.d)[0]), 6)}"
                    
                self.isAllDeltaCRow = False
                self.isSingleDeltaCRow = False
                self.isSingleDeltaARow = False
                self.isDeltaZCol = False
                self.isAllDeltaRows = False
                self.isFormulaDeltaChanged = False

                for i in range(len(self.changingTable)):
                    for j in range(len(self.changingTable[i])):
                        if isinstance(self.changingTable[i][j], (sp.Add, sp.Mul)):
                            self.isFormulaDeltaChanged = True

                if self.isFormulaDeltaChanged:
                    print("\nMathematical Preliminary formulas that will be influenced")

                    for i in range(len(self.matB)):
                        for j in range(len(self.matB[i])):
                            if isinstance(self.matB[i][j], (sp.Add, sp.Mul)):
                                self.isAllDeltaRows = True

                    if self.isAllDeltaRows:
                        print("All formulas are influenced")

                    # print(self.matCbvNegOne)
                    if not self.isAllDeltaRows:
                        for i in range(len(self.matCbvNegOne)):
                            if isinstance(self.matCbvNegOne[i], (sp.Add, sp.Mul)):
                                self.isAllDeltaCRow = True

                        if self.isAllDeltaCRow:
                            print(f"CBVB^-1")
                            print(f"Z* = CBVB^-1.b")
                            for i in range(len(self.changingTable[-1]) - 1):
                                if i < len(self.objFunc):
                                    print(
                                        f"C{i+1}* = (CBVB^-1.A{i+1}) - C{i+1}")
                                else:
                                    print(f"S{i - len(self.objFunc) + 1}* = (CBVB^-1.A{i+1}) - C{i+1}")

                        if not self.isAllDeltaCRow:
                            for i in range(1, len(self.changingTable)):
                                for j in range(len(self.changingTable[i]) - 1):
                                    if isinstance(self.changingTable[0][j], (sp.Add, sp.Mul)):
                                        self.isSingleDeltaCRow = True
                                        self.singleCIndex = j+1
                                    if isinstance(self.changingTable[i][j], (sp.Add, sp.Mul)):
                                        self.isSingleDeltaARow = True
                                        self.singleAIndex = j+1

                        if self.isSingleDeltaCRow:
                            print(
                                f"C{self.singleCIndex}* = (CBVB^-1.A{self.singleCIndex}) - C{self.singleCIndex}")
                        if self.isSingleDeltaARow:
                            print(
                                f"A{self.singleAIndex}* = B^-1.A{self.singleAIndex}")

                        for i in range(1, len(self.changingTable) - 1):
                            print(self.changingTable[i][-1])
                            if isinstance(self.changingTable[i][-1], (sp.Add, sp.Mul)):
                                self.isDeltaZCol = True

                        if self.isDeltaZCol:
                            print("Z* = CBVB^-1.b")
                            print("b* = B^-1.b")

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

        try:
            # cbv matrix
            imgui.push_style_color(imgui.COLOR_TEXT, 1.0, 1.0, 0.0)
            imgui.text("{:>30}".format("CBv"))
            imgui.pop_style_color()
            for i in range(len(self.matCbv)):
                if type(self.matCbv[i]).__name__ == "Float" or self.absF(self.matCbv[i]) == 0.0 or self.absF(self.matCbv[i]) == 1:
                    imgui.text("{:>15.3f}".format(float(self.matCbv[i])))
                else:
                    imgui.push_style_color(imgui.COLOR_TEXT, 0.0, 1.0, 0.0)
                    imgui.text("{:>15}".format(str(self.matCbv[i])))
                    imgui.pop_style_color()
                imgui.same_line(0, 20)

            imgui.spacing()
            imgui.spacing()
            imgui.spacing()
            imgui.spacing()

            # b matrix
            imgui.push_style_color(imgui.COLOR_TEXT, 1.0, 1.0, 0.0)
            imgui.text("{:>29}".format("B"))
            imgui.pop_style_color()
            for i in range(len(self.matB)):
                for j in range(len(self.matB[i])):
                    if type(self.matB[i][j]).__name__ == "Float" or self.absF(self.matB[i][j]) == 0.0 or self.absF(self.matB[i][j]) == 1:
                        imgui.text("{:>15.3f}".format(float(self.matB[i][j])))
                    else:
                        imgui.push_style_color(
                            imgui.COLOR_TEXT, 0.0, 1.0, 0.0)
                        imgui.text("{:>15}".format(str(self.matB[i][j])))
                        imgui.pop_style_color()
                    imgui.same_line(0, 20)
                imgui.spacing()

            imgui.spacing()
            imgui.spacing()
            imgui.spacing()
            imgui.spacing()

            # b^-1 matrix
            imgui.push_style_color(imgui.COLOR_TEXT, 1.0, 1.0, 0.0)
            imgui.text("{:>31}".format("B^-1"))
            imgui.pop_style_color()
            for i in range(len(self.matBNegOne)):
                for j in range(len(self.matBNegOne[i])):
                    if type(self.matBNegOne[i][j]).__name__ == "Float" or self.absF(self.matBNegOne[i][j]) == 0.0 or self.absF(self.matBNegOne[i][j]) == 1:
                        imgui.text("{:>15.3f}".format(
                            float(self.matBNegOne[i][j])))
                    else:
                        imgui.push_style_color(
                            imgui.COLOR_TEXT, 0.0, 1.0, 0.0)
                        imgui.text("{:>15}".format(str(self.matBNegOne[i][j])))
                        imgui.pop_style_color()
                    imgui.same_line(0, 20)
                imgui.spacing()

            imgui.spacing()
            imgui.spacing()
            imgui.spacing()
            imgui.spacing()

            # cbv^-1 matrix
            imgui.push_style_color(imgui.COLOR_TEXT, 1.0, 1.0, 0.0)
            imgui.text("{:>35}".format("CbvB^-1 or q"))
            imgui.pop_style_color()
            for i in range(len(self.matCbvNegOne)):
                if type(self.matCbvNegOne[i]).__name__ == "Float" or self.absF(self.matCbvNegOne[i]) == 0.0 or self.absF(self.matCbvNegOne[i]) == 1:
                    imgui.text("{:>15.3f}".format(float(self.matCbvNegOne[i])))
                else:
                    imgui.push_style_color(imgui.COLOR_TEXT, 0.0, 1.0, 0.0)
                    imgui.text("{:>15}".format(str(self.matCbvNegOne[i])))
                    imgui.pop_style_color()
                imgui.same_line(0, 20)

        except Exception as e:
            print("error:", e)

        imgui.spacing()
        imgui.spacing()
        imgui.spacing()
        imgui.spacing()

        imgui.push_style_color(imgui.COLOR_TEXT, 1.0, 1.0, 0.0)
        imgui.text("{:>40}".format("changing Optimal Table"))
        imgui.pop_style_color()
        for hCtr in range(len(self.globalHeaderRow)):
            imgui.text("{:>15}".format(str(self.globalHeaderRow[hCtr])))
            imgui.same_line(0, 20)
        imgui.spacing()
        for i in range(len(self.changingTable)):
            for j in range(len(self.changingTable[i])):
                if isinstance(self.changingTable[i][j], float) or self.absF(self.changingTable[i][j]) == 0.0 or self.absF(self.changingTable[i][j]) == 1:
                    try:
                        imgui.text("{:>15.3f}".format(self.changingTable[i][j]))
                    except:
                        pass
                else:
                    imgui.push_style_color(imgui.COLOR_TEXT, 0.0, 1.0, 0.0)
                    imgui.text("{:>15}".format(str(self.changingTable[i][j])))
                    imgui.pop_style_color()
                if i < len(self.changingTable[i]) - 1:
                    imgui.same_line(0, 20)
            imgui.spacing()

        imgui.spacing()
        imgui.spacing()
        imgui.spacing()
        imgui.spacing()

        if optTabLockState:
            if imgui.button("Optimize again"):
                try:
                    self.newTableaus, changingVars, optimalSolution, self.IMPivotCols, self.IMPivotRows, self.IMHeaderRow = self.dual.doDualSimplex([
                    ], [], isMin, self.changingTable)
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
                for hCtr in range(len(self.globalHeaderRow)):
                    imgui.text("{:>8}".format(
                        str(self.globalHeaderRow[hCtr])))
                    imgui.same_line(0, 20)
                imgui.spacing()
                for j in range(len(self.newTableaus[i])):
                    if j == pivotRow and pivotRow != -1:
                        imgui.push_style_color(
                            imgui.COLOR_TEXT, 0.0, 1.0, 0.0)
                    if j == 0:
                        imgui.text("z  ")
                    else:
                        imgui.text("c " + str(j))
                    imgui.same_line(0, 20)
                    for k in range(len(self.newTableaus[i][j])):
                        if k == pivotCol and pivotCol != -1:
                            imgui.push_style_color(
                                imgui.COLOR_TEXT, 0.0, 1.0, 0.0)
                        imgui.text("{:>8.3f}".format(
                            self.newTableaus[i][j][k]))
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

        if self.isFormulaDeltaChanged:
            imgui.text(f"{' ':<10}{'Mathematical Preliminary formulas that will be influenced':<40}")
            imgui.spacing()
            imgui.spacing()

            if self.isAllDeltaRows:
                imgui.text(f"{' ':<15}{'All formulas are influenced':<40}")

            if self.isAllDeltaCRow:
                imgui.text(f"{' ':<15}{'CBVB^-1':<40}")
                imgui.text(f"{' ':<15}{'Z* = CBVB^-1.b':<40}")
                for i in range(len(self.changingTable[-1]) - 1):
                    if i < len(self.objFunc):
                        imgui.text(f"{' ':<15}{f'C{i+1}* = (CBVB^-1.A{i+1}) - C{i+1}':<40}")
                    else:
                        imgui.text(f"{' ':<15}{f'S{i - len(self.objFunc) + 1}* = (CBVB^-1.A{i+1}) - C{i+1}':<40}")

            if self.isSingleDeltaCRow:
                imgui.text(f"{' ':<15}{f'C{self.singleCIndex}* = (CBVB^-1.A{self.singleCIndex}) - C{self.singleCIndex}':<40}")
            if self.isSingleDeltaARow:
                imgui.text(f"{' ':<15}{f'A{self.singleAIndex}* = B^-1.A{self.singleAIndex}':<40}")

            if self.isDeltaZCol:
                imgui.text(f"{' ':<15}{'Z* = CBVB^-1.b':<40}")
                imgui.text(f"{' ':<15}{'b* = B^-1.b':<40}")

        imgui.end_child()
        imgui.end()

    def doGui(self):
        if not glfw.init():
            print("Could not initialize OpenGL context")
            return

        window = glfw.create_window(
            int(1920 / 2), int(1080 / 2), "Mathematical Preliminaries Simplex Prototype", None, None)
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
    classInstance = MathPreliminaries(isConsoleOutput)
    classInstance.doGui()


if __name__ == "__main__":
    main(True)
