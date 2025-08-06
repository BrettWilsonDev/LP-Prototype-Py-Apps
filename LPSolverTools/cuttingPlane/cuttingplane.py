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
        self.maxIterations = 10  # Add maximum iterations to prevent infinite loops
        self.reset()

    def reset(self):
        self.dual = Dual()
        self.testInputSelected = 1

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

        if testNum == 2:
            isMin = False
            objFunc = [5, 2]
            constraints = [[3, 1, 12, 0],
                           [1, 1, 5, 0],
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
        
    def roundMatrix(self, matrix):
        if isinstance(matrix, list):
            if isinstance(matrix[0], list):
                # 2D matrix
                return [[self.roundValue(val) for val in row] for row in matrix]
            else:
                # 1D array
                return [self.roundValue(val) for val in matrix]
        else:
            return self.roundValue(matrix)

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
    
    def getBasicVarSpots(self, tableaus):
        # get the spots of the basic variables
        basicVarSpots = []
        for k in range(len(tableaus[-1][-1])):
            columnIndex = k
            tCVars = []

            for i in range(len(tableaus[-1])):
                columnValue = self.roundValue(tableaus[-1][i][columnIndex])
                tCVars.append(columnValue)

            sumVals = self.roundValue(sum(tCVars))
            if abs(sumVals - 1.0) <= self.tolerance:
                basicVarSpots.append(k)

        # get the columns of the basic variables
        basicVarCols = []
        for i in range(len(tableaus[-1][-1])):
            tLst = []
            if i in basicVarSpots:
                for j in range(len(tableaus[-1])):
                    roundedVal = self.roundValue(tableaus[-1][j][i])
                    tLst.append(roundedVal)
                basicVarCols.append(tLst)

        # sort the cbv according the basic var positions
        zippedCbv = list(zip(basicVarCols, basicVarSpots))
        sortedCbvZipped = sorted(
            zippedCbv, key=lambda x: x[0].index(1.0) if 1.0 in x[0] else (x[0].index(1) if 1 in x[0] else len(x[0])))
        if sortedCbvZipped:
            sortedBasicVars, basicVarSpots = zip(*sortedCbvZipped)
        else:
            basicVarSpots = []

        return basicVarSpots
    
    def hasFractionalSolution(self, tableau):
        """Check if the current optimal solution has fractional basic variables"""
        basicVarSpots = self.getBasicVarSpots([tableau])
        
        for i in range(1, len(tableau)):  # Skip objective row
            rhsValue = self.roundValue(tableau[i][-1])
            decimalPart = abs(rhsValue - round(rhsValue))
            
            if decimalPart > self.tolerance:
                return True
        
        return False

    def findMostFractionalRow(self, tableau):
        """Find the row with the most fractional RHS value for Gomory cut"""
        rhsDecimals = []
        for i in range(1, len(tableau)):
            decimalPart = self.roundValue(tableau[i][-1] - int(tableau[i][-1]))
            rhsDecimals.append(self.roundValue(decimalPart))

        rhsPickList = [self.roundValue(abs(dec - 0.5)) for dec in rhsDecimals]
        pickedRowIndex = rhsPickList.index(min(rhsPickList))
        
        # Convert to actual row index in tableau
        pickedRow = ((self.getBasicVarSpots([tableau])).index(pickedRowIndex)) + 1
        
        return pickedRow
    
    def doCuttingPlane(self, workingTableau):

        currentTableau = workingTableau
        iteration = 1

        # Recursive cutting plane loop
        while self.hasFractionalSolution(currentTableau) and iteration <= self.maxIterations:
            print(f"\n=== CUTTING PLANE ITERATION {iteration} ===")
            
            # Find the most fractional row for Gomory cut
            pickedRow = self.findMostFractionalRow(currentTableau)
            
            print(f"Selected row for Gomory cut: {self.roundValue(currentTableau[pickedRow])}")

            # Generate Gomory cut from the selected row
            tempList = self.roundValue(currentTableau[pickedRow])
            tempList = tempList[len(self.objFunc):]  # Remove objective function coefficients
            newCon = self.gomoryCut(tempList, verbose=True)

            for i in range(len(newCon)):
                newCon[i] = self.roundValue(newCon[i])

            # Prepare the new constraint for tableau format
            for i in range(len(self.objFunc)):
                newCon.insert(i, 0)

            newCon.insert(-1, 1)  # Add slack variable coefficient
            print(f"Generated cutting plane constraint: {newCon}")

            # Add new column for the slack variable
            print("Adding new slack variable column...")
            for i in range(len(currentTableau)):
                currentTableau[i].insert(-1, 0)

            # Add the new constraint row
            currentTableau.append(newCon)

            self.printTableau(currentTableau, title=f"Tableau with cutting plane constraint {iteration}")

            # Solve the new problem with dual simplex
            finalTableaus, self.changingVars, self.optimalSolution, self.IMPivotCols, self.IMPivotRows, self.IMHeaderRow = self.dual.doDualSimplex(
                [], [], self.isMin, currentTableau)
            
            for i in range(len(finalTableaus)):
                self.printTableau(finalTableaus[i], title=f"Iteration {iteration} - Tableau {i+1}")

            # Update current tableau for next iteration
            currentTableau = finalTableaus[-1]
            iteration += 1

        # Final results
        if not self.hasFractionalSolution(currentTableau):
            print(f"\n=== OPTIMAL INTEGER SOLUTION FOUND ===")
            print(f"Solution achieved after {iteration-1} cutting plane iterations")
        else:
            print(f"\n=== MAXIMUM ITERATIONS REACHED ===")
            print(f"Stopped after {self.maxIterations} iterations")
            
        self.printTableau(currentTableau, title="Final Optimal Tableau")

        return currentTableau

    def test(self):
        if self.testInput(self.testInputSelected) is not None:
            self.objFunc, self.constraints, self.isMin = self.testInput(
                self.testInputSelected)

        # Initial dual simplex solution
        workingTableaus, self.changingVars, self.optimalSolution = self.dual.doDualSimplex(
            self.objFunc, self.constraints, self.isMin)
        
        for i in range(len(workingTableaus)):
            self.printTableau(workingTableaus[i], title=f"Initial Tableau {i+1}")

        self.doCuttingPlane(workingTableaus[-1])


def main(isConsoleOutput=False):
    classInstance = CuttingPlane(isConsoleOutput)
    classInstance.test()


if __name__ == "__main__":
    main(True)