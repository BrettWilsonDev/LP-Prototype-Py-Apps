import pygame
from imgui.integrations.pygame import PygameRenderer
import imgui

import copy

import sympy as sp

import sys
import os
# python to exe keeps files in root
try:
    from dualsimplex import DualSimplex as Dual
except:
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    from dual.dualsimplex import DualSimplex as Dual


class MathPreliminaries:
    dual = Dual()

    d = sp.symbols('d')
    globalOptimalTab = []
    globalHeaderRow = []

    def __init__(self, isConsoleOutput=False):
        self.isConsoleOutput = isConsoleOutput

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

        if testNum == -1:
            return None
        else:
            return objFunc, constraints, isMin

    def scrubDelta(self, lst):
        cleaned_list = []

        for elem in lst:
            if isinstance(elem, (sp.Add, sp.Mul)):
                # Remove terms involving `d` and keep only the constant term
                termWithoutd = elem.as_independent(self.d, as_Add=True)[0]
                cleaned_list.append(termWithoutd)
            elif hasattr(elem, 'has') and elem.has(self.d):
                # If the entire element is `d`, replace with 0
                cleaned_list.append(0)
            else:
                cleaned_list.append(elem)

        return cleaned_list

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

    def doSensitivityAnalysis(self, objFunc, constraints, isMin, absRule=False, optTabLockState=False):
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

    def doGui(self):
        pygame.init()
        size = 1920 / 2, 1080 / 2

        os.system('cls' if os.name == 'nt' else 'clear')
        if self.isConsoleOutput:
            print("\nBrett's simplex prototype tool for dual simplex problems\n")

        pygame.display.set_mode(size, pygame.DOUBLEBUF |
                                pygame.OPENGL | pygame.RESIZABLE)

        pygame.display.set_caption(
            "mathematical preliminaries Simplex Prototype")

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

        changingTable = []

        matCbv = []
        matB = []
        matBNegOne = []
        matCbvNegOne = []

        absRule = False

        lockOptTab = "off"
        optTabLockState = False

        newTableaus = []

        IMPivotCols = []
        IMPivotRows = []
        IMHeaderRow = []

        pivotCol = -1
        pivotRow = -1

        solveDelta = False
        deltaSolve = "off"

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
            imgui.text(
                "you can use +d to represent the delta variable ex: 60+d")
            imgui.spacing()
            imgui.spacing()

            for i in range(len(objFunc)):
                # value = objFunc[i]
                value = str(objFunc[i])
                imgui.set_next_item_width(50)
                imgui.same_line()
                # changed, objFunc[i] = imgui.input_float(
                changed, objFunc[i] = imgui.input_text(
                    "##objFunc {}".format(i + 1), value)
                imgui.same_line()
                imgui.text(f"x{i + 1}")

                if changed:
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
                    # value = constraints[i][j]
                    value = str(constraints[i][j])
                    imgui.set_next_item_width(50)
                    imgui.same_line()
                    # changed, xValue = imgui.input_float(
                    changed, xValue = imgui.input_text(
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
                # rhsValue = constraints[i][-2]
                rhsValue = str(constraints[i][-2])
                # rhsChanged, rhs = imgui.input_float(
                rhsChanged, rhs = imgui.input_text(
                    "##RHSC{}{}".format(i, j), rhsValue)

                if rhsChanged:
                    constraints[i][-2] = rhs

            if imgui.radio_button("lock optimal tab", lockOptTab == "on"):
                lockOptTab = "on"

            imgui.same_line(0, 20)

            if imgui.radio_button("unlock optimal tab", lockOptTab == "off"):
                lockOptTab = "off"

            imgui.text("optimal tab lock: {}".format(lockOptTab))

            if imgui.radio_button("solve Delta on", deltaSolve == "on"):
                deltaSolve = "on"

            imgui.same_line(0, 20)

            if imgui.radio_button("solve Delta off", deltaSolve == "off"):
                deltaSolve = "off"

            if problemType == "Min":
                isMin = True
            else:
                isMin = False

            if absProblemType == "abs On":
                absRule = True
            else:
                absRule = False

            if lockOptTab == "on":
                optTabLockState = True
            else:
                optTabLockState = False

            if deltaSolve == "on":
                solveDelta = True
            else:
                solveDelta = False

            # solve button =======================================================
            if imgui.button("Solve"):
                try:
                    if self.testInput() is not None:
                        objFunc, constraints, isMin = self.testInput()
                    # objFunc, constraints, isMin = testInput()

                    # print(objFunc, constraints, isMin)
                    a = copy.deepcopy(objFunc)
                    b = copy.deepcopy(constraints)

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

                    changingTable, matrixCbv, matrixB, matrixBNegOne, matrixCbvNegOne, basicVarSpots = self.doSensitivityAnalysis(
                        a, b, isMin, absRule, optTabLockState)

                    matCbv = matrixCbv.tolist()
                    matB = matrixB.transpose().tolist()
                    matBNegOne = matrixBNegOne.transpose().tolist()
                    matCbvNegOne = matrixCbvNegOne.tolist()

                    # make matrix in to a 2d list
                    tMatCbv = []
                    tMatCbvNegOne = []
                    for i in range(len(matCbv)):
                        tMatCbv.append(matCbv[i][0])
                        tMatCbvNegOne.append(matCbvNegOne[i][0])
                    matCbv = tMatCbv
                    matCbvNegOne = tMatCbvNegOne

                    if solveDelta:
                        for i in range(len(changingTable)):
                            for j in range(len(changingTable[i])):
                                if isinstance(changingTable[i][j], (sp.Add, sp.Mul)):
                                    changingTable[i][j] = f"d = {
                                        round(float(sp.solve(changingTable[i][j], self.d)[0]), 6)}"

                except Exception as e:
                    print("math error:", e)

            imgui.spacing()
            imgui.spacing()
            imgui.spacing()
            imgui.spacing()

            try:
                # cbv matrix
                imgui.push_style_color(imgui.COLOR_TEXT, 1.0, 1.0, 0.0)
                imgui.text("{:>30}".format("CBv"))
                imgui.pop_style_color()
                for i in range(len(matCbv)):
                    if type(matCbv[i]).__name__ == "Float" or self.absF(matCbv[i]) == 0.0 or self.absF(matCbv[i]) == 1:
                        imgui.text("{:>15.3f}".format(float(matCbv[i])))
                    else:
                        imgui.push_style_color(imgui.COLOR_TEXT, 0.0, 1.0, 0.0)
                        imgui.text("{:>15}".format(str(matCbv[i])))
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
                for i in range(len(matB)):
                    for j in range(len(matB[i])):
                        if type(matB[i][j]).__name__ == "Float" or self.absF(matB[i][j]) == 0.0 or self.absF(matB[i][j]) == 1:
                            imgui.text("{:>15.3f}".format(float(matB[i][j])))
                        else:
                            imgui.push_style_color(
                                imgui.COLOR_TEXT, 0.0, 1.0, 0.0)
                            imgui.text("{:>15}".format(str(matB[i][j])))
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
                for i in range(len(matBNegOne)):
                    for j in range(len(matBNegOne[i])):
                        if type(matBNegOne[i][j]).__name__ == "Float" or self.absF(matBNegOne[i][j]) == 0.0 or self.absF(matBNegOne[i][j]) == 1:
                            imgui.text("{:>15.3f}".format(
                                float(matBNegOne[i][j])))
                        else:
                            imgui.push_style_color(
                                imgui.COLOR_TEXT, 0.0, 1.0, 0.0)
                            imgui.text("{:>15}".format(str(matBNegOne[i][j])))
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
                for i in range(len(matCbvNegOne)):
                    if type(matCbvNegOne[i]).__name__ == "Float" or self.absF(matCbvNegOne[i]) == 0.0 or self.absF(matCbvNegOne[i]) == 1:
                        imgui.text("{:>15.3f}".format(float(matCbvNegOne[i])))
                    else:
                        imgui.push_style_color(imgui.COLOR_TEXT, 0.0, 1.0, 0.0)
                        imgui.text("{:>15}".format(str(matCbvNegOne[i])))
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
            for i in range(len(changingTable)):
                for j in range(len(changingTable[i])):
                    if isinstance(changingTable[i][j], float) or self.absF(changingTable[i][j]) == 0.0 or self.absF(changingTable[i][j]) == 1:
                        imgui.text("{:>15.3f}".format(changingTable[i][j]))
                    else:
                        imgui.push_style_color(imgui.COLOR_TEXT, 0.0, 1.0, 0.0)
                        imgui.text("{:>15}".format(str(changingTable[i][j])))
                        imgui.pop_style_color()
                    if i < len(changingTable[i]) - 1:
                        imgui.same_line(0, 20)
                imgui.spacing()

            imgui.spacing()
            imgui.spacing()
            imgui.spacing()
            imgui.spacing()

            if optTabLockState:
                if imgui.button("Optimize again"):
                    try:
                        newTableaus, changingVars, optimalSolution, IMPivotCols, IMPivotRows, IMHeaderRow = self.dual.doDualSimplex([
                        ], [], isMin, changingTable)
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
                    for hCtr in range(len(self.globalHeaderRow)):
                        imgui.text("{:>8}".format(
                            str(self.globalHeaderRow[hCtr])))
                        imgui.same_line(0, 20)
                    imgui.spacing()
                    for j in range(len(newTableaus[i])):
                        if j == pivotRow and pivotRow != -1:
                            imgui.push_style_color(
                                imgui.COLOR_TEXT, 0.0, 1.0, 0.0)
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

            imgui.render()
            impl.render(imgui.get_draw_data())

            pygame.display.flip()


def main(isConsoleOutput=False):
    classInstance = MathPreliminaries(isConsoleOutput)
    classInstance.doGui()


if __name__ == "__main__":
    main(True)
