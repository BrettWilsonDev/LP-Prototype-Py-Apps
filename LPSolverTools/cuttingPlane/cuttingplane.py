import imgui
from imgui.integrations.glfw import GlfwRenderer
import glfw

import math
import copy
import sys
import os

from decimal import Decimal, getcontext, ROUND_HALF_UP

try:
    from dualsimplex import DualSimplex as Dual
except:
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    from dual.dualsimplex import DualSimplex as Dual


class CuttingPlane():
    def __init__(self, isConsoleOutput=False):
        self.isConsoleOutput = isConsoleOutput
        self.precision = 4  
        self.tolerance = 1e-6 
        self.reset()

    def reset(self):
        self.dual = Dual()
        self.testInputSelected = 0

        self.isMin = False

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

    def testInput(self, testNum=-1):

        if testNum == 0:
            isMin = True
            objFunc = [6, 8]
            constraints = [[3, 1, 4, 1],
                           [1, 2, 4, 1],
                           ]
            
        if testNum == 1:
            isMin = False
            objFunc = [8, 5]
            constraints = [[1, 1, 6, 0],
                           [9, 5, 45, 0],
                           ]

        if testNum == -1:
            return None, None, None
        else:
            return objFunc, constraints, isMin

    def printTableau(self, tableau, title="Tableau"):
        if self.isConsoleOutput:
            print(f"\n{title}")
            for i in range(len(tableau)):
                for j in range(len(tableau[i])):
                    print(f"{self.roundValue(tableau[i][j]):>8.4f}", end="  ")
                print()
            print()

    def roundValue(self, value):
        try:
            return round(float(value), self.precision)
        except (ValueError, TypeError):
            return value

    def gomoryCut(self, row, verbose=False):
        if len(row) < 2:
            raise ValueError(
                "Input must have at least one coefficient and RHS.")

        getcontext().prec = 12
        getcontext().rounding = ROUND_HALF_UP
        def toDecimal(x): return Decimal(str(x)).quantize(Decimal("0.0000001"))

        coefs = [toDecimal(x) for x in row[:-1]]
        rhs = toDecimal(row[-1])

        def getFraction(x):
            f = x - x.to_integral_value(rounding=ROUND_HALF_UP)
            if f < 0:
                f += 1
            return f

        if verbose:
            # Step 1: Original row
            terms = " + ".join([f"{c:.4f}e{i+1}".replace(".", ",")
                               for i, c in enumerate(coefs)])
            print(f"Xn + {terms} = {rhs:.4f}".replace(".", ","))

            # Step 2: Integer + fractional decomposition
            intParts = [c.to_integral_value(
                rounding=ROUND_HALF_UP) for c in coefs]
            fracParts = [getFraction(c) for c in coefs]
            expanded = []
            for i in range(len(coefs)):
                expanded.append(f"{intParts[i]}e{i+1}")
                if fracParts[i] != 0:
                    expanded.append(
                        f"+ {fracParts[i]:.4f}e{i+1}".replace(".", ","))
            rhsInt = rhs.to_integral_value(rounding=ROUND_HALF_UP)
            rhsFrac = getFraction(rhs)
            rhsExpr = f"{rhsInt} + {rhsFrac:.4f}".replace(".", ",")
            print(f"Xn + " + " + ".join(expanded) + f" = {rhsExpr}")

            # Step 3: Move int terms to RHS and flip signs
            negFracTerms = [
                f"- {f:.4f}e{i+1}".replace(".", ",") for i, f in enumerate(fracParts) if f != 0]
            print(
                f"Xn + 0e1 -1e2 - 1 = {' '.join(negFracTerms)} + {rhsFrac:.4f}".replace(".", ","))

            # Step 4: Inequality form with constant on left
            gomoryLhs = " ".join(negFracTerms) + \
                f" + {rhsFrac:.4f}".replace(".", ",")
            print(f"{gomoryLhs} <= 0")

            # Step 5: Final Gomory cut
            print(f"{' '.join(negFracTerms)} <= -{rhsFrac:.4f}".replace(".", ","))

        # Actual computation
        fracCoefs = [-getFraction(c) for c in coefs]
        fracRhs = getFraction(rhs)
        negFracRhs = -fracRhs

        result = [float(x) for x in fracCoefs] + [float(negFracRhs)]

        return result

    def test(self):
        if self.testInput(self.testInputSelected) is not None:
            self.objFunc, self.constraints, self.isMin = self.testInput(
                self.testInputSelected)

        # self.gomoryCut([-1.25, 0.25, 3.75], verbose=True)
        # self.gomoryCut([0.2, -0.6, 1.6], verbose=True)

        workingTableaus, self.changingVars, self.optimalSolution = self.dual.doDualSimplex(
            self.objFunc, self.constraints, self.isMin)

        for i in range(len(workingTableaus)):
            self.printTableau(workingTableaus[i], title=f"Tableau {i+1}")

        rhsDecimals = []
        for i in range(1, len(workingTableaus[-1])):
            decimalPart = workingTableaus[-1][i][-1] - int(workingTableaus[-1][i][-1])
            rhsDecimals.append(self.roundValue(decimalPart))

        rhsPickList = []
        for i in range(len(rhsDecimals)):
            rhsPickList.append(self.roundValue((rhsDecimals[i] * 100) - 0.5))

        if (self.isMin):
            pickedRow = rhsPickList.index(min(rhsPickList)) + 1
        else:
            pickedRow = rhsPickList.index(max(rhsPickList)) + 1

        # for i in range(1, len(newTableaus[-1])):
        print(self.roundValue(workingTableaus[-1][pickedRow]))

        tempList = self.roundValue(workingTableaus[-1][pickedRow])
        tempList = tempList[len(self.objFunc):]
        newCon = self.gomoryCut(tempList, verbose=True)

        for i in range(len(newCon)):
            newCon[i] = self.roundValue(newCon[i])

        # self.doAddConstraint([newCon], newTableaus[-1])

        for i in range(len(self.objFunc)):
            newCon.insert(i, 0)

        print(newCon)

        workingTableaus[-1].append(newCon)

        self.printTableau(
            workingTableaus[-1], title=f"Tableau with new cutting plane constraint")

        finalTableaus, self.changingVars, self.optimalSolution, self.IMPivotCols, self.IMPivotRows, self.IMHeaderRow = self.dual.doDualSimplex(
            [], [], self.isMin, workingTableaus[-1])
        
        for i in range(len(finalTableaus)):
            self.printTableau(finalTableaus[i], title=f"Tableau {i+1}")


def main(isConsoleOutput=False):
    classInstance = CuttingPlane(isConsoleOutput)
    classInstance.test()


if __name__ == "__main__":
    main(True)
