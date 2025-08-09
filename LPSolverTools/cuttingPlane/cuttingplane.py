import imgui
from imgui.integrations.glfw import GlfwRenderer
import glfw

import math
import copy
import sys
import os
from fractions import Fraction

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
            # isMin = True
            # objFunc = [6, 8]
            # constraints = [[3, 1, 4, 1],
            #                [1, 2, 4, 1],
            #                ]
            

            isMin = False
            objFunc = [13, 8]
            constraints = [[1, 2, 10, 0],
                           [5, 2, 20, 0],
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
        """Improved rounding with fraction conversion to avoid floating point errors"""
        try:
            # Convert to fraction first, then to float with proper rounding
            if isinstance(value, (int, float)):
                # Use fractions to get exact representation, then round
                frac = Fraction(value).limit_denominator(10000)
                rounded = round(float(frac), self.precision)
                return rounded
            return value
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

    def cleanValue(self, value, tolerance=1e-10):
        """Clean up floating point values to remove tiny errors"""
        if abs(value) < tolerance:
            return 0.0
        
        # Try to convert to a simple fraction
        frac = Fraction(value).limit_denominator(1000)
        if abs(float(frac) - value) < tolerance:
            return float(frac)
        
        return value

    def gomoryCut(self, row, verbose=False):
        if len(row) < 2:
            raise ValueError(
                "Input must have at least one coefficient and RHS.")

        # Clean the input row first
        cleanRow = [self.cleanValue(x) for x in row]
        
        # Use fractions for exact arithmetic
        coefs = [Fraction(x).limit_denominator(10000) for x in cleanRow[:-1]]
        rhs = Fraction(cleanRow[-1]).limit_denominator(10000)

        def getFractionalPart(x):
            """Get the fractional part of a number"""
            integer_part = int(x)
            fractional_part = x - integer_part
            
            # If negative, adjust the fractional part to be positive
            if fractional_part < 0:
                fractional_part += 1
                
            return fractional_part

        if verbose:
            print(f"Original row: {[float(c) for c in coefs]} | {float(rhs)}")

        # Generate the Gomory cut using exact fraction arithmetic
        fracCoefs = []
        for c in coefs:
            frac_part = getFractionalPart(c)
            fracCoefs.append(-frac_part)
        
        rhsFrac = getFractionalPart(rhs)
        negFracRhs = -rhsFrac

        # Convert back to floats and clean
        result = [self.cleanValue(float(x)) for x in fracCoefs] + [self.cleanValue(float(negFracRhs))]
        
        if verbose:
            print(f"Gomory cut coefficients: {result}")

        return result
    
    def getBasicVarSpots(self, tableaus):
        # get the spots of the basic variables
        basicVarSpots = []
        tableau = tableaus[-1]
        
        for k in range(len(tableau[0])):
            columnIndex = k
            column = [self.cleanValue(tableau[i][columnIndex]) for i in range(len(tableau))]
            
            # Check if this is a unit vector (exactly one 1, rest 0s)
            ones_count = sum(1 for x in column if abs(x - 1.0) < self.tolerance)
            zeros_count = sum(1 for x in column if abs(x) < self.tolerance)
            
            if ones_count == 1 and zeros_count == len(column) - 1:
                basicVarSpots.append(k)

        return basicVarSpots
    
    def hasFractionalSolution(self, tableau):
        """Check if the current optimal solution has fractional basic variables"""
        for i in range(1, len(tableau)):  # Skip objective row
            rhsValue = self.cleanValue(tableau[i][-1])
            
            # Check if the value is significantly different from its integer part
            integerPart = round(rhsValue)
            if abs(rhsValue - integerPart) > self.tolerance:
                return True
        
        return False

    def findMostFractionalRow(self, tableau):
        """Find the row with the most fractional RHS value for Gomory cut"""
        maxFractional = 0
        selectedRow = 1
        
        for i in range(1, len(tableau)):  # Skip objective row
            rhsValue = self.cleanValue(tableau[i][-1])
            integerPart = int(rhsValue)
            fractionalPart = rhsValue - integerPart
            
            # Normalize fractional part to [0, 1)
            if fractionalPart < 0:
                fractionalPart += 1
                
            # We want the fractional part closest to 0.5 (most fractional)
            fractionalMeasure = min(fractionalPart, 1 - fractionalPart)
            
            if fractionalMeasure > maxFractional:
                maxFractional = fractionalMeasure
                selectedRow = i
                
        return selectedRow

    def cleanTableau(self, tableau):
        """Clean the entire tableau to remove floating point errors"""
        cleanedTableau = []
        for row in tableau:
            cleanedRow = [self.cleanValue(val) for val in row]
            cleanedTableau.append(cleanedRow)
        return cleanedTableau

    def doCuttingPlane(self, workingTableau):
        currentTableau = self.cleanTableau(workingTableau)
        iteration = 1

        # Recursive cutting plane loop
        while self.hasFractionalSolution(currentTableau) and iteration <= self.maxIterations:
            print(f"\n=== CUTTING PLANE ITERATION {iteration} ===")
            
            # Clean tableau before processing
            currentTableau = self.cleanTableau(currentTableau)
            
            # Find the most fractional row for Gomory cut
            pickedRow = self.findMostFractionalRow(currentTableau)
            
            print(f"Selected row {pickedRow} for Gomory cut: {[self.roundValue(x) for x in currentTableau[pickedRow]]}")

            # Generate Gomory cut from the selected row
            tempList = currentTableau[pickedRow][len(self.objFunc):]  # Remove objective function coefficients
            newCon = self.gomoryCut(tempList, verbose=True)

            # Clean the new constraint
            newCon = [self.cleanValue(x) for x in newCon]

            # Prepare the new constraint for tableau format
            for i in range(len(self.objFunc)):
                newCon.insert(i, 0)

            newCon.insert(-1, 1)  # Add slack variable coefficient
            print(f"Generated cutting plane constraint: {[self.roundValue(x) for x in newCon]}")

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

            # Clean and update current tableau for next iteration
            currentTableau = self.cleanTableau(finalTableaus[-1])
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