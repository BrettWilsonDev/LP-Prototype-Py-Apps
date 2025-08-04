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
    # from mathpreliminaries import MathPreliminaries as MathPrelims
except:
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    from dual.dualsimplex import DualSimplex as Dual
    # from mathPrelim.mathpreliminaries import MathPreliminaries as MathPrelims

class BranchAndBound:
    def __init__(self, isConsoleOutput=False):
        self.isConsoleOutput = isConsoleOutput
        self.precision = 4  # Number of decimal places for rounding
        self.tolerance = 1e-6  # Tolerance for integer checks
        self.reset()

    def reset(self):
        self.dual = Dual()
        # self.mathPrelim = MathPrelims()
        self.testInputSelected = 0

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

        self.isMin = False

        # Add tree traversal specific variables
        self.bestSolution = None
        self.bestObjective = float('-inf') if not self.isMin else float('inf')
        self.nodeCounter = 0

    def testInput(self, testNum=-1):
        isMin = False

        if testNum == 0:
            objFunc = [8, 5]
            constraints = [[1, 1, 6, 0],
                           [9, 5, 45, 0],
                           ]

            # addedConstraints = [
            #     [1, 0, 3, 0],
            # ]

        if testNum == -1:
            return None
        else:
            return objFunc, constraints, isMin

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

    def roundTableaus(self, tableaus):
        if not tableaus:
            return tableaus

        roundedTableaus = []
        for tableau in tableaus:
            roundedTableau = self.roundMatrix(tableau)
            roundedTableaus.append(roundedTableau)
        return roundedTableaus

    def isIntegerValue(self, value):
        roundedVal = self.roundValue(value)
        return abs(roundedVal - round(roundedVal)) <= self.tolerance

    def printTableau(self, tableau, title="Tableau"):
        if self.isConsoleOutput:
            print(f"\n{title}")
            for i in range(len(tableau)):
                for j in range(len(tableau[i])):
                    print(f"{self.roundValue(tableau[i][j]):>8.4f}", end="  ")
                print()
            print()

    # def getMathPrelims(self, objFunc, constraints, isMin, absRule=False):
    #     changingTable, matrixCbv, matrixB, matrixBNegOne, matrixCbvNegOne, basicVarSpots = self.mathPrelim.doPreliminaries(
    #         objFunc, constraints, isMin, absRule)
    #     # Round the results
    #     changingTable = self.roundMatrix(changingTable)
    #     return changingTable, matrixCbv, matrixB, matrixBNegOne, matrixCbvNegOne, basicVarSpots

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

    def doAddConstraint(self, addedConstraints, overRideTab=None):
        if overRideTab is not None:
            changingTable = copy.deepcopy(overRideTab)
            # Round the input table
            changingTable = self.roundMatrix(changingTable)
            tempTabs = []
            tempTabs.append(changingTable)
            basicVarSpots = self.getBasicVarSpots(tempTabs)
        else:
            print("needs an input table")
            return

        newTab = copy.deepcopy(changingTable)

        # Add new constraint rows to the tableau
        for k in range(len(addedConstraints)):
            # Add a column for each new constraint's slack/surplus variable
            for i in range(len(changingTable)):
                newTab[i].insert(-1, 0.0)

            # Create the new constraint row
            newCon = []
            for i in range(len(changingTable[0]) + len(addedConstraints)):
                newCon.append(0.0)

            # Fill in the coefficients for the constraint
            for i in range(len(addedConstraints[k]) - 2):
                newCon[i] = self.roundValue(addedConstraints[k][i])

            # Set the RHS value
            newCon[-1] = self.roundValue(addedConstraints[k][-2])

            # Add slack or surplus variable
            slackSpot = ((len(newCon) - len(addedConstraints)) - 1) + k
            if addedConstraints[k][-1] == 1:  # >= constraint
                newCon[slackSpot] = -1.0  # surplus variable
            else:  # <= constraint
                newCon[slackSpot] = 1.0   # slack variable

            newTab.append(newCon)

        # Round the new tableau
        newTab = self.roundMatrix(newTab)
        self.printTableau(newTab, "unfixed tab")

        displayTab = copy.deepcopy(newTab)

        # Fix tableau to maintain basic feasible solution
        for k in range(len(addedConstraints)):
            constraintRowIndex = len(newTab) - len(addedConstraints) + k

            # Check each basic variable column
            for colIndex in basicVarSpots:
                # Get the coefficient in the new constraint row for this basic variable
                coefficientInNewRow = self.roundValue(
                    displayTab[constraintRowIndex][colIndex])

                if abs(coefficientInNewRow) > self.tolerance:
                    # Find the row where this basic variable has coefficient 1
                    pivotRow = None
                    for rowIndex in range(len(displayTab) - len(addedConstraints)):
                        if abs(self.roundValue(displayTab[rowIndex][colIndex]) - 1.0) <= self.tolerance:
                            pivotRow = rowIndex
                            break

                    if pivotRow is not None:
                        # Auto-detect if we need to reverse the row operation based on constraint type
                        constraintType = addedConstraints[k][-1]
                        autoReverse = (constraintType == 1)

                        # Perform row operation to eliminate the coefficient
                        for col in range(len(displayTab[0])):
                            pivotVal = self.roundValue(
                                displayTab[pivotRow][col])
                            constraintVal = self.roundValue(
                                displayTab[constraintRowIndex][col])

                            if autoReverse:
                                newVal = pivotVal - coefficientInNewRow * constraintVal
                            else:
                                newVal = constraintVal - coefficientInNewRow * pivotVal

                            displayTab[constraintRowIndex][col] = self.roundValue(
                                newVal)

        # Round the final tableau
        displayTab = self.roundMatrix(displayTab)
        self.printTableau(displayTab, "fixed tab")

        return displayTab, newTab

    def testIfBasicVarIsInt(self, tabs):
        decisionVars = []
        for i in range(len(self.objFunc)):
            for j in range(len(tabs[-1])):
                val = self.roundValue(tabs[-1][j][i])
                if abs(val - 1.0) <= self.tolerance:
                    rhsVal = self.roundValue(tabs[-1][j][-1])
                    decisionVars.append(rhsVal)

        xSpot = -1
        rhsVal = None
        for i in range(len(decisionVars)):
            if not self.isIntegerValue(decisionVars[i]):
                rhsVal = decisionVars[i]
                xSpot = i
                break

        if xSpot == -1:
            return None, None
        else:
            return xSpot, rhsVal

    def makeBranch(self, tabs):
        xSpot, rhsVal = self.testIfBasicVarIsInt(tabs)

        if xSpot == None and rhsVal == None:
            return None, None

        if self.isConsoleOutput:
            print(f"Branching on x{xSpot+1} = {self.roundValue(rhsVal)}")

        maxInt = math.ceil(rhsVal)
        minInt = math.floor(rhsVal)

        # Create constraint for x <= floor(value)
        newConMin = []
        for i in range(len(self.objFunc)):
            if i != xSpot:
                newConMin.append(0)
            else:
                newConMin.append(1)
        newConMin.append(minInt)
        newConMin.append(0)  # <= constraint

        # Create constraint for x >= ceil(value)
        newConMax = []
        for i in range(len(self.objFunc)):
            if i != xSpot:
                newConMax.append(0)
            else:
                newConMax.append(1)
        newConMax.append(maxInt)
        newConMax.append(1)  # >= constraint

        return newConMin, newConMax

    def getObjectiveValue(self, tabs):
        if not tabs or len(tabs) == 0:
            return None
        # Last element of first row in final tableau
        return self.roundValue(tabs[-1][0][-1])

    def getCurrentSolution(self, tabs):
        solution = [0.0] * len(self.objFunc)

        for i in range(len(self.objFunc)):
            for j in range(len(tabs[-1])):
                val = self.roundValue(tabs[-1][j][i])
                if abs(val - 1.0) <= self.tolerance:
                    solution[i] = self.roundValue(tabs[-1][j][-1])
                    break

        return solution

    def isIntegerSolution(self, solution):
        for val in solution:
            if not self.isIntegerValue(val):
                return False
        return True

    def updateBestSolution(self, tabs):
        objVal = self.getObjectiveValue(tabs)
        solution = self.getCurrentSolution(tabs)

        if objVal is None:
            return False

        if self.isIntegerSolution(solution):
            if self.isMin:
                if objVal < self.bestObjective:
                    self.bestObjective = objVal
                    self.bestSolution = solution
                    if self.isConsoleOutput:
                        print(
                            f"New best integer solution found: {solution} with objective {objVal}")
                    return True
            else:
                if objVal > self.bestObjective:
                    self.bestObjective = objVal
                    self.bestSolution = solution
                    if self.isConsoleOutput:
                        print(
                            f"New best integer solution found: {solution} with objective {objVal}")
                    return True
        return False

    def shouldPrune(self, tabs):
        objVal = self.getObjectiveValue(tabs)

        if objVal is None:
            return True  # Infeasible solution

        if self.bestSolution is not None:
            if self.isMin:
                return objVal >= self.bestObjective
            else:
                return objVal <= self.bestObjective

        return False

    def doBranchAndBound(self, initialTabs):
        if self.isConsoleOutput:
            print("Starting Branch and Bound Algorithm")
            print("="*50)

        # Round initial tableaus
        initialTabs = self.roundTableaus(initialTabs)

        # Initialize best solution tracking
        self.bestSolution = None
        self.bestObjective = float('-inf') if not self.isMin else float('inf')
        self.nodeCounter = 0

        # Stack to store nodes to process: (tableau, depth, nodeId, constraintsAdded)
        nodeStack = [(initialTabs, 0, 0, [])]

        while nodeStack:
            currentTabs, depth, nodeId, constraintsPath = nodeStack.pop()
            self.nodeCounter += 1

            # Round current tableaus
            currentTabs = self.roundTableaus(currentTabs)

            if self.isConsoleOutput:
                print(f"\n--- Processing Node {nodeId} (Depth {depth}) ---")
                print(f"Constraints path: {constraintsPath}")

            # Check if current solution should be pruned
            if self.shouldPrune(currentTabs):
                if self.isConsoleOutput:
                    print(f"Node {nodeId} pruned by bound")
                continue

            # Update best solution if current is integer and better
            self.updateBestSolution(currentTabs)

            # Try to branch further
            newConMin, newConMax = self.makeBranch(currentTabs)

            if newConMin is None and newConMax is None:
                # Integer solution found - already handled in updateBestSolution
                if self.isConsoleOutput:
                    solution = self.getCurrentSolution(currentTabs)
                    objVal = self.getObjectiveValue(currentTabs)
                    print(
                        f"Node {nodeId}: Integer solution {solution} with objective {objVal}")
                continue

            # Create two child nodes
            childNodes = []

            # Process "less than or equal" branch (newConMin)
            try:
                if self.isConsoleOutput:
                    # print(f"\nTrying MIN branch: {newConMin}")
                    print(f"\nTrying MIN branch: {newConMin}", end=" ")
                    for i in range(len(newConMin) - 2):
                        if (newConMin[i] == 0 or newConMin[i] == 0.0):
                            continue
                        if newConMin[i] == 1 or newConMin[i] == 1.0:
                            print(f"x{i+1}", end=" ")
                        else:
                            print(f"{newConMin[i]}*x{i+1}", end=" ")
                    if newConMin[-1] == 0:
                        print(f"<=", end=" ")
                    else:
                        print(f">=", end=" ")
                    print(f"{newConMin[-2]}", end=" ")

                tempConsMin = [newConMin]
                displayTabMin, newTabMin = self.doAddConstraint(
                    tempConsMin, currentTabs[-1])

                newTableausMin, self.changingVars, self.optimalSolution, self.IMPivotCols, self.IMPivotRows, self.IMHeaderRow = self.dual.doDualSimplex(
                    [], [], self.isMin, displayTabMin)

                if newTableausMin and len(newTableausMin) > 0:
                    # Round the new tableaus
                    newTableausMin = self.roundTableaus(newTableausMin)
                    childNodes.append((newTableausMin, depth + 1, self.nodeCounter + 1,
                                      constraintsPath + [f"x{newConMin[:-2].index(1)+1} <= {newConMin[-2]}"]))
                elif self.isConsoleOutput:
                    print("MIN branch infeasible")

                if self.isConsoleOutput and newTableausMin:
                    self.printTableau(
                        newTableausMin[-1], "MIN branch final tableau")

            except Exception as e:
                if self.isConsoleOutput:
                    print(f"MIN branch failed: {e}")

            # Process "greater than or equal" branch (newConMax)
            try:
                if self.isConsoleOutput:
                    print(f"\nTrying MAX branch: {newConMax}", end=" ")
                    for i in range(len(newConMax) - 2):
                        if (newConMax[i] == 0 or newConMax[i] == 0.0):
                            continue
                        if newConMax[i] == 1 or newConMax[i] == 1.0:
                            print(f"x{i+1}", end=" ")
                        else:
                            print(f"{newConMax[i]}*x{i+1}", end=" ")
                    if newConMax[-1] == 0:
                        print(f"<=", end=" ")
                    else:
                        print(f">=", end=" ")
                    print(f"{newConMax[-2]}", end=" ")

                tempConsMax = [newConMax]
                displayTabMax, newTabMax = self.doAddConstraint(
                    tempConsMax, currentTabs[-1])

                newTableausMax, self.changingVars, self.optimalSolution, self.IMPivotCols, self.IMPivotRows, self.IMHeaderRow = self.dual.doDualSimplex(
                    [], [], self.isMin, displayTabMax)

                if newTableausMax and len(newTableausMax) > 0:
                    # Round the new tableaus
                    newTableausMax = self.roundTableaus(newTableausMax)
                    childNodes.append((newTableausMax, depth + 1, self.nodeCounter + 2,
                                      constraintsPath + [f"x{newConMax[:-2].index(1)+1} >= {newConMax[-2]}"]))
                elif self.isConsoleOutput:
                    print("MAX branch infeasible")

                if self.isConsoleOutput and newTableausMax:
                    self.printTableau(
                        newTableausMax[-1], "MAX branch final tableau")

            except Exception as e:
                if self.isConsoleOutput:
                    print(f"MAX branch failed: {e}")

            # Add child nodes to stack (reverse order for depth-first search)
            for child in reversed(childNodes):
                nodeStack.append(child)

        # Print final results
        if self.isConsoleOutput:
            print("\n" + "="*50)
            print("BRANCH AND BOUND COMPLETED")
            print("="*50)
            if self.bestSolution is not None:
                print(f"Best integer solution: {self.bestSolution}")
                print(f"Best objective value: {self.bestObjective}")
            else:
                print("No integer solution found")
            print(f"Total nodes processed: {self.nodeCounter}")

        return self.bestSolution, self.bestObjective

    def test(self):
        try:
            if self.testInput(self.testInputSelected) is not None:
                self.objFunc, self.constraints, isMin = self.testInput(
                    self.testInputSelected)

            a = copy.deepcopy(self.objFunc)
            b = copy.deepcopy(self.constraints)

            self.isMin = isMin

            try:
                # Solve initial LP relaxation
                self.newTableaus, self.changingVars, self.optimalSolution = self.dual.doDualSimplex(
                    a, b, isMin)

                # Round the initial tableaus
                self.newTableaus = self.roundTableaus(self.newTableaus)

                if self.isConsoleOutput:
                    print("Initial LP relaxation solved")
                    solution = self.getCurrentSolution(self.newTableaus)
                    objVal = self.getObjectiveValue(self.newTableaus)
                    print(f"Initial solution: {solution}")
                    print(f"Initial objective: {objVal}")

                # Start branch and bound
                bestSolution, bestObjective = self.doBranchAndBound(
                    self.newTableaus)

            except Exception as e:
                if self.isConsoleOutput:
                    print(f"Error in dual simplex: {e}")
                raise

        except Exception as e:
            print("math error:", e)
            raise


def main(isConsoleOutput=False):
    classInstance = BranchAndBound(isConsoleOutput)
    classInstance.test()


if __name__ == "__main__":
    main(True)
