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
        self.testInputSelected = 0 # sets the test values

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

        self.isMin = False

        # Add tree traversal specific variables
        self.bestSolution = None
        self.bestObjective = float('-inf') if not self.isMin else float('inf')
        self.nodeCounter = 0
        self.allSolutions = []  # Store all integer solutions found
        self.enablePruning = False  # NEW: Control whether to use pruning

        self.displayTableausMin = []
        self.displayTableausMax = []

        self.pivotColMin = []
        self.pivotColMax = []

        self.pivotRowMin = []
        self.pivotRowMax = []

    def testInput(self, testNum=-1):
        # isMin = False

        # if testNum == 0:
        #     objFunc = [8, 5]
        #     constraints = [[1, 1, 6, 0],
        #                    [9, 5, 45, 0],
        #                    ]

            # addedConstraints = [
            #     [1, 0, 3, 0],
            # ]


        isMin = False

        if testNum == 0:
            objFunc = [13, 8]
            constraints = [[1, 2, 10, 0],
                           [5, 2, 20, 0],
                           ]

        if testNum == 1:
            objFunc = [3, 2, 4]  # maximize 3x + 2y + 4z
            constraints = [
                [2, 1, 3, 10, 0],
                [1, 2, 1, 8, 0],
                [3, 1, 2, 15, 0],
            ]
            isMin = False

        if testNum == 2: #knap sack
            objFunc = [2, 3, 3, 5, 2, 4] 
            constraints = [
                [11, 8, 6, 14, 10, 10, 40, 0], # c1
                [1, 0, 0, 0, 0, 0, 0, 1, 0], # c2
                [0, 1, 0, 0, 0, 0, 0, 1, 0], # c3
                [0, 0, 1, 0, 0, 0, 0, 1, 0], # c4
                [0, 0, 0, 1, 0, 0, 0, 1, 0], # c5
                [0, 0, 0, 0, 1, 0, 0, 1, 0], # c6
                [0, 0, 0, 0, 0, 1, 0, 1, 0], # c7
            ]
            isMin = False

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

    # def printTableau(self, tableau, title="Tableau"):
    #     if self.isConsoleOutput:
    #         print(f"\n{title}")
    #         for i in range(len(tableau)):
    #             for j in range(len(tableau[i])):
    #                 print(f"{self.roundValue(tableau[i][j]):>8.4f}", end="  ")
    #             print()
    #         print()

    def printTableau(self, tableau, title="Tableau", row=-1, col=-1):
        headerStr = []

        for i in range(len(self.objFunc)):
            headerStr.append(f"x{i+1}")

        for i in range(len(self.objFunc), len(tableau[0]) - 1):
            headerStr.append(f"s/e{i-len(self.objFunc)+1}")

        headerStr.append("rhs")

        if self.isConsoleOutput:
            print(f"\n{title}")
            print("  ".join([f"{h:>8}" for h in headerStr]))
            for i in range(len(tableau)):
                for j in range(len(tableau[i])):
                    if row != -1 and (i == row or j == col):
                        print(f"\033[92m{self.roundValue(tableau[i][j]):>8.4f}\033[0m", end="  ")
                    else:
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

    # def testIfBasicVarIsInt(self, tabs):
    #     decisionVars = []
    #     for i in range(len(self.objFunc)):
    #         for j in range(len(tabs[-1])):
    #             val = self.roundValue(tabs[-1][j][i])
    #             if abs(val - 1.0) <= self.tolerance:
    #                 rhsVal = self.roundValue(tabs[-1][j][-1])
    #                 decisionVars.append(rhsVal)

    #     # Find the fractional variable closest to 0.5
    #     bestXSpot = -1
    #     bestRhsVal = None
    #     minDistanceToHalf = float('inf')
        
    #     for i in range(len(decisionVars)):
    #         if not self.isIntegerValue(decisionVars[i]):
    #             fractionalPart = decisionVars[i] - math.floor(decisionVars[i])
    #             distanceToHalf = abs(fractionalPart - 0.5)
                
    #             if distanceToHalf < minDistanceToHalf:
    #                 minDistanceToHalf = distanceToHalf
    #                 bestXSpot = i
    #                 bestRhsVal = decisionVars[i]

    #     if bestXSpot == -1:
    #         return None, None
    #     else:
    #         return bestXSpot, bestRhsVal

    def testIfBasicVarIsInt(self, tabs):
        decisionVars = []
        
        # Only check the ORIGINAL decision variables (not slack/surplus variables)
        for i in range(len(self.objFunc)):  # Only original decision variables
            for j in range(len(tabs[-1])):
                val = self.roundValue(tabs[-1][j][i])
                if abs(val - 1.0) <= self.tolerance:
                    rhsVal = self.roundValue(tabs[-1][j][-1])
                    decisionVars.append(rhsVal)
                    break  # Found the basic variable, move to next
            else:
                # If no basic variable found for this decision variable, it's 0
                decisionVars.append(0.0)

        # Find the fractional variable closest to 0.5 among DECISION VARIABLES ONLY
        bestXSpot = -1
        bestRhsVal = None
        minDistanceToHalf = float('inf')
        
        for i in range(len(decisionVars)):
            if not self.isIntegerValue(decisionVars[i]):
                fractionalPart = decisionVars[i] - math.floor(decisionVars[i])
                distanceToHalf = abs(fractionalPart - 0.5)
                
                if distanceToHalf < minDistanceToHalf:
                    minDistanceToHalf = distanceToHalf
                    bestXSpot = i  # This will be within range of original variables
                    bestRhsVal = decisionVars[i]

        if bestXSpot == -1:
            return None, None
        else:
            return bestXSpot, bestRhsVal

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
            # Store ALL integer solutions found
            self.allSolutions.append((solution.copy(), objVal))
            
            if self.isMin:
                if objVal < self.bestObjective:
                    self.bestObjective = objVal
                    self.bestSolution = solution
                    if self.isConsoleOutput:
                        print(
                            f"New best integer solution found: {solution} with objective {objVal}")
                    return True
                else:
                    if self.isConsoleOutput:
                        print(
                            f"Integer solution found: {solution} with objective {objVal} (not better than current best)")
            else:
                if objVal > self.bestObjective:
                    self.bestObjective = objVal
                    self.bestSolution = solution
                    if self.isConsoleOutput:
                        print(
                            f"New best integer solution found: {solution} with objective {objVal}")
                    return True
                else:
                    if self.isConsoleOutput:
                        print(
                            f"Integer solution found: {solution} with objective {objVal} (not better than current best)")
        return False

    def shouldPrune(self, tabs):
        # NEW: Only prune if pruning is enabled
        if not self.enablePruning:
            return False
            
        objVal = self.getObjectiveValue(tabs)

        if objVal is None:
            return True  # Infeasible solution

        if self.bestSolution is not None:
            if self.isMin:
                return objVal >= self.bestObjective
            else:
                return objVal <= self.bestObjective

        return False

    # def doBranchAndBound(self, initialTabs, enablePruning=False):
    #     """
    #     Performs branch and bound algorithm.
        
    #     Args:
    #         initialTabs: Initial LP relaxation tableau
    #         enablePruning: If True, uses standard pruning. If False, explores all branches.
    #     """
    #     self.enablePruning = enablePruning
        
    #     if self.isConsoleOutput:
    #         print("Starting Branch and Bound Algorithm")
    #         if enablePruning:
    #             print("Pruning: ENABLED (standard branch and bound)")
    #         else:
    #             print("Pruning: DISABLED (complete tree exploration)")
    #         print("="*50)

    #     # Round initial tableaus
    #     initialTabs = self.roundTableaus(initialTabs)

    #     # Initialize best solution tracking
    #     self.bestSolution = None
    #     self.bestObjective = float('-inf') if not self.isMin else float('inf')
    #     self.nodeCounter = 0
    #     self.allSolutions = []

    #     # Stack to store nodes to process: (tableau, depth, nodeId, constraintsAdded)
    #     nodeStack = [(initialTabs, 0, 0, [])]

    #     ctr = 0
    #     while nodeStack:

    #         ctr += 1

    #         if ctr > 20:
    #             print("something is very wrong")
    #             break

    #         currentTabs, depth, nodeId, constraintsPath = nodeStack.pop()
    #         self.nodeCounter += 1

    #         # Round current tableaus
    #         currentTabs = self.roundTableaus(currentTabs)

    #         if self.isConsoleOutput:
    #             print(f"\n--- Processing Node {nodeId} (Depth {depth}) ---")
    #             print(f"Constraints path: {constraintsPath}")

    #         # Check if current solution should be pruned (only if pruning enabled)
    #         if self.shouldPrune(currentTabs):
    #             if self.isConsoleOutput:
    #                 print(f"Node {nodeId} pruned by bound")
    #             continue

    #         # Update best solution if current is integer and better
    #         self.updateBestSolution(currentTabs)

    #         # Try to branch further
    #         newConMin, newConMax = self.makeBranch(currentTabs)

    #         if newConMin is None and newConMax is None:
    #             # Integer solution found - already handled in updateBestSolution
    #             if self.isConsoleOutput:
    #                 solution = self.getCurrentSolution(currentTabs)
    #                 objVal = self.getObjectiveValue(currentTabs)
    #                 print(
    #                     f"Node {nodeId}: Integer solution {solution} with objective {objVal}")
    #             continue

    #         # Create two child nodes
    #         childNodes = []

    #         # Process "less than or equal" branch (newConMin)
    #         try:
    #             if self.isConsoleOutput:
    #                 # print(f"\nTrying MIN branch: {newConMin}")
    #                 print(f"\nTrying MIN branch: {newConMin}", end=" ")
    #                 for i in range(len(newConMin) - 2):
    #                     if (newConMin[i] == 0 or newConMin[i] == 0.0):
    #                         continue
    #                     if newConMin[i] == 1 or newConMin[i] == 1.0:
    #                         print(f"x{i+1}", end=" ")
    #                     else:
    #                         print(f"{newConMin[i]}*x{i+1}", end=" ")
    #                 if newConMin[-1] == 0:
    #                     print(f"<=", end=" ")
    #                 else:
    #                     print(f">=", end=" ")
    #                 print(f"{newConMin[-2]}", end=" ")

    #             tempConsMin = [newConMin]
    #             displayTabMin, newTabMin = self.doAddConstraint(
    #                 tempConsMin, currentTabs[-1])

    #             newTableausMin, self.changingVars, optimalSolutionMin, IMPivotColsMin, IMPivotRowsMin, IMHeaderRowMin = self.dual.doDualSimplex(
    #                 [], [], self.isMin, displayTabMin)
                
    #             if (optimalSolutionMin == None):
    #                 # print(newTableausMin)
    #                 self.printTableau(
    #                     newTableausMin, "Infeasible tableau")
    #                 newTableausMin = []
                
    #             self.pivotColMin.append(IMPivotColsMin)
    #             self.pivotRowMin.append(IMPivotRowsMin)

    #             if optimalSolutionMin != None:
    #                 if newTableausMin and len(newTableausMin) > 0:
    #                     # Round the new tableaus
    #                     newTableausMin = self.roundTableaus(newTableausMin)
    #                     childNodes.append((newTableausMin, depth + 1, self.nodeCounter + 1,
    #                                     constraintsPath + [f"x{newConMin[:-2].index(1)+1} <= {newConMin[-2]}"]))
    #                 elif self.isConsoleOutput:
    #                     print("MIN branch infeasible")

    #             if self.isConsoleOutput and newTableausMin:
    #                 for i in range(len(newTableausMin) - 1):
    #                     self.printTableau(
    #                         newTableausMin[i], f"MIN branch Tableau {i+1}")
    #                     self.displayTableausMin.append(newTableausMin[i])
    #                 self.printTableau(
    #                     newTableausMin[-1], "MIN branch final tableau")
    #                 self.displayTableausMin.append(newTableausMin[-1])
                    
    #         except Exception as e:
    #             if self.isConsoleOutput:
    #                 print(f"MIN branch failed: {e}")

    #         # Process "greater than or equal" branch (newConMax)
    #         try:
    #             if self.isConsoleOutput:
    #                 print(f"\nTrying MAX branch: {newConMax}", end=" ")
    #                 for i in range(len(newConMax) - 2):
    #                     if (newConMax[i] == 0 or newConMax[i] == 0.0):
    #                         continue
    #                     if newConMax[i] == 1 or newConMax[i] == 1.0:
    #                         print(f"x{i+1}", end=" ")
    #                     else:
    #                         print(f"{newConMax[i]}*x{i+1}", end=" ")
    #                 if newConMax[-1] == 0:
    #                     print(f"<=", end=" ")
    #                 else:
    #                     print(f">=", end=" ")
    #                 print(f"{newConMax[-2]}", end=" ")

    #             tempConsMax = [newConMax]
    #             displayTabMax, newTabMax = self.doAddConstraint(
    #                 tempConsMax, currentTabs[-1])

    #             newTableausMax, self.changingVars, optimalSolutionMax, IMPivotColsMax, IMPivotRowsMax, IMHeaderRowMax = self.dual.doDualSimplex(
    #                 [], [], self.isMin, displayTabMax)
                
    #             if (optimalSolutionMax == None):
    #                 # print(newTableausMin)
    #                 self.printTableau(
    #                     newTableausMax, "Infeasible tableau")
    #                 newTableausMax = []

    #             if optimalSolutionMax != None:
    #                 if newTableausMax and len(newTableausMax) > 0:
    #                     # Round the new tableaus
    #                     newTableausMax = self.roundTableaus(newTableausMax)
    #                     childNodes.append((newTableausMax, depth + 1, self.nodeCounter + 2,
    #                                     constraintsPath + [f"x{newConMax[:-2].index(1)+1} >= {newConMax[-2]}"]))
    #                 elif self.isConsoleOutput:
    #                     print("MAX branch infeasible")

    #             if self.isConsoleOutput and newTableausMax:
    #                 for i in range(len(newTableausMax) - 1):
    #                     self.printTableau(
    #                         newTableausMax[i], f"MAX branch Tableau {i+1}")
    #                 self.printTableau(
    #                     newTableausMax[-1], "MAX branch final tableau")

    #         except Exception as e:
    #             if self.isConsoleOutput:
    #                 print(f"MAX branch failed: {e}")
    #                 # raise


    #         # Add child nodes to stack (reverse order for depth-first search)
    #         for child in reversed(childNodes):
    #             nodeStack.append(child)

    #     # Print final results
    #     if self.isConsoleOutput:
    #         print("\n" + "="*50)
    #         print("BRANCH AND BOUND COMPLETED")
    #         print("="*50)
    #         if self.bestSolution is not None:
    #             print(f"Best integer solution: {self.bestSolution}")
    #             print(f"Best objective value: {self.bestObjective}")
    #         else:
    #             print("No integer solution found")
    #         print(f"Total nodes processed: {self.nodeCounter}")
            
    #         # Print all integer solutions found
    #         if self.allSolutions:
    #             print(f"\nAll integer solutions found ({len(self.allSolutions)}):")
    #             for i, (sol, obj) in enumerate(self.allSolutions, 1):
    #                 print(f"  {i}. Solution: {sol}, Objective: {obj}")

    #     return self.bestSolution, self.bestObjective

    def doBranchAndBound(self, initialTabs, enablePruning=False):
        """
        Performs branch and bound algorithm with hierarchical node labeling.
        
        Args:
            initialTabs: Initial LP relaxation tableau
            enablePruning: If True, uses standard pruning. If False, explores all branches.
        """
        self.enablePruning = enablePruning
        
        if self.isConsoleOutput:
            print("Starting Branch and Bound Algorithm")
            if enablePruning:
                print("Pruning: ENABLED (standard branch and bound)")
            else:
                print("Pruning: DISABLED (complete tree exploration)")
            print("="*50)

        # Round initial tableaus
        initialTabs = self.roundTableaus(initialTabs)

        # Initialize best solution tracking
        self.bestSolution = None
        self.bestObjective = float('-inf') if not self.isMin else float('inf')
        self.nodeCounter = 0
        self.allSolutions = []

        # Stack to store nodes to process: (tableau, depth, nodeLabel, constraintsAdded, parentLabel)
        # Start with root node labeled as "0" (will be processed first)
        nodeStack = [(initialTabs, 0, "0", [], None)]
        
        # Keep track of child counters for each parent
        childCounters = {}

        ctr = 0
        while nodeStack:
            ctr += 1

            if ctr > 20:
                print("something is very wrong")
                break

            currentTabs, depth, nodeLabel, constraintsPath, parentLabel = nodeStack.pop()
            self.nodeCounter += 1

            # Round current tableaus
            currentTabs = self.roundTableaus(currentTabs)

            if self.isConsoleOutput:
                print(f"\n--- Processing Node {nodeLabel} (Depth {depth}) ---")
                if parentLabel:
                    print(f"Parent: {parentLabel}")
                print(f"Constraints path: {constraintsPath}")

            # Check if current solution should be pruned (only if pruning enabled)
            if self.shouldPrune(currentTabs):
                if self.isConsoleOutput:
                    print(f"Node {nodeLabel} pruned by bound")
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
                    print(f"Node {nodeLabel}: Integer solution {solution} with objective {objVal}")
                continue

            # Initialize child counter for this node if not exists
            if nodeLabel not in childCounters:
                childCounters[nodeLabel] = 0

            # Create two child nodes with hierarchical labels
            childNodes = []

            # Process "less than or equal" branch (newConMin) - Child 1
            try:
                childCounters[nodeLabel] += 1
                if nodeLabel == "0":  # Root node case
                    childLabel = "1"
                else:
                    childLabel = f"{nodeLabel}.{childCounters[nodeLabel]}"
                
                if self.isConsoleOutput:
                    print(f"\nTrying MIN branch (Node {childLabel}): {newConMin}", end=" ")
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

                newTableausMin, self.changingVars, optimalSolutionMin, IMPivotColsMin, IMPivotRowsMin, IMHeaderRowMin = self.dual.doDualSimplex(
                    [], [], self.isMin, displayTabMin)
                
                if (optimalSolutionMin == None):
                    self.printTableau(newTableausMin, f"Node {childLabel}: Infeasible tableau")
                    newTableausMin = []
                
                self.pivotColMin.append(IMPivotColsMin)
                self.pivotRowMin.append(IMPivotRowsMin)

                print(f"Cols: {IMPivotColsMin}")
                print(f"Rows: {IMPivotRowsMin}")

                if optimalSolutionMin != None:
                    if newTableausMin and len(newTableausMin) > 0:
                        # Round the new tableaus
                        newTableausMin = self.roundTableaus(newTableausMin)
                        constraint_desc = f"x{newConMin[:-2].index(1)+1} <= {newConMin[-2]}"
                        childNodes.append((newTableausMin, depth + 1, childLabel,
                                        constraintsPath + [constraint_desc], nodeLabel))
                    elif self.isConsoleOutput:
                        print(f"MIN branch (Node {childLabel}) infeasible")

                if self.isConsoleOutput and newTableausMin:
                    for i in range(len(newTableausMin) - 1):
                        try:
                            self.printTableau(newTableausMin[i], f"Node {childLabel} MIN branch Tableau {i+1}", IMPivotRowsMin[i], IMPivotColsMin[i])
                        except:
                            self.printTableau(newTableausMin[i], f"Node {childLabel} MIN branch Tableau {i+1}")
                        self.displayTableausMin.append(newTableausMin[i])
                    self.printTableau(newTableausMin[-1], f"Node {childLabel} MIN branch final tableau")
                    self.displayTableausMin.append(newTableausMin[-1])
                        
            except Exception as e:
                if self.isConsoleOutput:
                    print(f"MIN branch (Node {childLabel}) failed: {e}")

            # Process "greater than or equal" branch (newConMax) - Child 2
            try:
                childCounters[nodeLabel] += 1
                if nodeLabel == "0":  # Root node case
                    childLabel = "2"
                else:
                    childLabel = f"{nodeLabel}.{childCounters[nodeLabel]}"
                    
                if self.isConsoleOutput:
                    print(f"\nTrying MAX branch (Node {childLabel}): {newConMax}", end=" ")
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

                newTableausMax, self.changingVars, optimalSolutionMax, IMPivotColsMax, IMPivotRowsMax, IMHeaderRowMax = self.dual.doDualSimplex(
                    [], [], self.isMin, displayTabMax)
                
                if (optimalSolutionMax == None):
                    self.printTableau(newTableausMax, f"Node {childLabel}: Infeasible tableau")
                    newTableausMax = []

                print(f"Cols: {IMPivotColsMax}")
                print(f"Rows: {IMPivotRowsMax}")

                if optimalSolutionMax != None:
                    if newTableausMax and len(newTableausMax) > 0:
                        # Round the new tableaus
                        newTableausMax = self.roundTableaus(newTableausMax)
                        constraint_desc = f"x{newConMax[:-2].index(1)+1} >= {newConMax[-2]}"
                        childNodes.append((newTableausMax, depth + 1, childLabel,
                                        constraintsPath + [constraint_desc], nodeLabel))
                    elif self.isConsoleOutput:
                        print(f"MAX branch (Node {childLabel}) infeasible")

                if self.isConsoleOutput and newTableausMax:
                    for i in range(len(newTableausMax) - 1):
                        try:
                            self.printTableau(newTableausMax[i], f"Node {childLabel} MAX branch Tableau {i+1}", IMPivotRowsMax[i], IMPivotColsMax[i])
                        except:
                            self.printTableau(newTableausMax[i], f"Node {childLabel} MAX branch Tableau {i+1}")
                        # self.printTableau(newTableausMax[i], f"Node {childLabel} MAX branch Tableau {i+1}")
                    self.printTableau(newTableausMax[-1], f"Node {childLabel} MAX branch final tableau")

            except Exception as e:
                if self.isConsoleOutput:
                    print(f"MAX branch (Node {childLabel}) failed: {e}")

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
            
            # Print all integer solutions found
            if self.allSolutions:
                print(f"\nAll integer solutions found ({len(self.allSolutions)}):")
                for i, (sol, obj) in enumerate(self.allSolutions, 1):
                    print(f"  {i}. Solution: {sol}, Objective: {obj}")

        return self.bestSolution, self.bestObjective
    
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

                self.isMin = isMin

                try:
                    # Solve initial LP relaxation
                    self.newTableaus, self.changingVars, self.optimalSolution = self.dual.doDualSimplex(
                        a, b, isMin)
                    
                    _, _, _, IMPivotCols, IMPivotRows, _ = self.dual.doDualSimplex(
                        [], [], self.isMin, self.newTableaus[0])
                
                    print(f"pivot rows: {(IMPivotRows)}")
                    print(f"pivot columns: {(IMPivotCols)}")

                    # Round the initial tableaus
                    self.newTableaus = self.roundTableaus(self.newTableaus)

                    if self.isConsoleOutput:
                        print("Initial LP relaxation solved")
                        for i in range(len(self.newTableaus) - 1):
                            try:
                                self.printTableau(self.newTableaus[i], f"Initial Tableau {i+1}", IMPivotRows[i], IMPivotCols[i])
                            except:
                                self.printTableau(self.newTableaus[i], f"Initial Tableau {i+1}")
                        self.printTableau(self.newTableaus[-1], "Initial tableau solved")
                        solution = self.getCurrentSolution(self.newTableaus)
                        objVal = self.getObjectiveValue(self.newTableaus)
                        print(f"Initial solution: {solution}")
                        print(f"Initial objective: {objVal}")

                    # Start branch and bound
                    bestSolution, bestObjective = self.doBranchAndBound(
                        self.newTableaus, self.enablePruning)
                    
                    print(self.pivotColMin)

                except Exception as e:
                    if self.isConsoleOutput:
                        print(f"Error in dual simplex: {e}")
                        # raise
            except Exception as e:
                print("math error:", e)
                imgui.text("math error: {}".format(e))
                self.errorE = "math error: {}".format(e)
                # raise

        imgui.same_line(0, 30)
        imgui.push_style_color(imgui.COLOR_TEXT, 1.0, 0.0, 0.0)
        if imgui.button("Reset"):
            self.reset()
        imgui.pop_style_color()

        imgui.spacing()
        imgui.spacing()
        imgui.spacing()
        imgui.spacing()
        imgui.spacing()

        
        for i in range(len(self.displayTableausMin)):
            # imgui.text(f"{self.pivotColMax[i]}")
            for j in range(len(self.displayTableausMin[i])):
                # try:
                #     imgui.text(f"{self.pivotColMin[i][j]}")
                #     imgui.spacing()
                # except:
                #     pass
                for k in range(len(self.displayTableausMin[i][j])):
                    imgui.same_line()
                    imgui.text("{:>8.3f}".format(self.displayTableausMin[i][j][k]))
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
            int(1920 / 2), int(1080 / 2), "Dual Simplex Prototype", None, None)
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

    def test(self, enablePruning=False):
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
                
                _, _, _, IMPivotCols, IMPivotRows, _ = self.dual.doDualSimplex(
                        [], [], self.isMin, self.newTableaus[0])
                
                print(f"pivot rows: {(IMPivotRows)}")
                print(f"pivot columns: {(IMPivotCols)}")
                
                # Round the initial tableaus
                self.newTableaus = self.roundTableaus(self.newTableaus)

                if self.isConsoleOutput:
                    print("Initial LP relaxation solved")
                    for i in range(len(self.newTableaus) - 1):
                        try:
                            self.printTableau(self.newTableaus[i], f"Initial Tableau {i+1}", IMPivotRows[i], IMPivotCols[i])
                        except:
                            self.printTableau(self.newTableaus[i], f"Initial Tableau {i+1}")
                    self.printTableau(self.newTableaus[-1], "Initial tableau solved")
                    solution = self.getCurrentSolution(self.newTableaus)
                    objVal = self.getObjectiveValue(self.newTableaus)
                    print(f"Initial solution: {solution}")
                    print(f"Initial objective: {objVal}")

                # Start branch and bound
                bestSolution, bestObjective = self.doBranchAndBound(
                    self.newTableaus, enablePruning)

            except Exception as e:
                if self.isConsoleOutput:
                    print(f"Error in dual simplex: {e}")
                # raise

        except Exception as e:
            print("math error:", e)
            # raise


def main(isConsoleOutput=False):
    classInstance = BranchAndBound(isConsoleOutput)
    # classInstance.doGui()
    classInstance.test()


if __name__ == "__main__":
    # To run with complete tree exploration (no pruning):
    main(True)
    
    # To run with standard pruning:
    # main(True, True)