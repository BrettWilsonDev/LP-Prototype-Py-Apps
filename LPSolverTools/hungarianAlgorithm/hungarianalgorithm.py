import numpy as np
import copy

class HungarianAlgorithm:
    def __init__(self, valMatrix, maximize=False, blankValue=None):
        self.originalMatrix = np.array(valMatrix, dtype=float)
        self.maximize = maximize
        self.blankValue = blankValue

        if blankValue is not None:
            if maximize:
                self.originalMatrix[self.originalMatrix == blankValue] = -np.inf
            else:
                self.originalMatrix[self.originalMatrix == blankValue] = np.inf

        if maximize:
            self.matrix = -self.originalMatrix.copy()
            self.matrix[self.originalMatrix == -np.inf] = np.inf
        else:
            self.matrix = copy.deepcopy(self.originalMatrix)

        self.nRows, self.nCols = self.matrix.shape
        self.stepCount = 0
        self.dummyAdded = False

    def printMatrix(self, matrix, title="Matrix"):
        print(f"\n{title}:")
        print("-" * 50)
        for i, row in enumerate(matrix):
            rowStr = []
            for j, val in enumerate(row):
                if val == np.inf:
                    rowStr.append("   ∞  ")
                elif val == -np.inf:
                    rowStr.append("  -∞  ")
                else:
                    rowStr.append(f"{val:6.1f}")
            print(f"Row {i}: [{', '.join(rowStr)}]")
        print()

    def step1AddDummy(self):
        self.stepCount += 1
        print(f"STEP {self.stepCount}: Add dummy row/column if needed")
        print("=" * 60)

        if self.nRows != self.nCols:
            maxDim = max(self.nRows, self.nCols)
            finiteValues = self.matrix[self.matrix != np.inf]

            if len(finiteValues) > 0:
                highval = np.min(finiteValues) if self.maximize else np.max(finiteValues)
            else:
                highval = 1000

            newMatrix = np.full((maxDim, maxDim), highval)

            if self.nRows < self.nCols:
                newMatrix[:self.nRows, :] = self.matrix
                print(f"Added {maxDim - self.nRows} dummy row(s) with val {highval}")
                self.dummyAdded = True
            else:
                newMatrix[:, :self.nCols] = self.matrix
                print(f"Added {maxDim - self.nCols} dummy column(s) with val {highval}")
                self.dummyAdded = True

            self.matrix = newMatrix
            self.nRows, self.nCols = maxDim, maxDim
        else:
            print("Matrix is already square - no dummy needed")

        self.printMatrix(self.matrix, "Matrix after Step 1")

    def step2RowReduction(self):
        self.stepCount += 1
        print(f"STEP {self.stepCount}: Row reduction")
        print("=" * 60)

        for i in range(self.nRows):
            finiteValues = self.matrix[i, :][self.matrix[i, :] != np.inf]
            if len(finiteValues) > 0:
                minVal = np.min(finiteValues)
                print(f"Row {i}: minimum value = {minVal}")
                mask = self.matrix[i, :] != np.inf
                self.matrix[i, mask] -= minVal
            else:
                print(f"Row {i}: all values are infinite - no reduction needed")

        self.printMatrix(self.matrix, "Matrix after row reduction")

    def step3ColumnReduction(self):
        self.stepCount += 1
        print(f"STEP {self.stepCount}: Column reduction")
        print("=" * 60)

        for j in range(self.nCols):
            finiteValues = self.matrix[:, j][self.matrix[:, j] != np.inf]
            if len(finiteValues) > 0:
                minVal = np.min(finiteValues)
                print(f"Column {j}: minimum value = {minVal}")
                mask = self.matrix[:, j] != np.inf
                self.matrix[mask, j] -= minVal
            else:
                print(f"Column {j}: all values are infinite - no reduction needed")

        self.printMatrix(self.matrix, "Matrix after column reduction")

    def findMinimumLines(self):
        zeros = (self.matrix == 0) & (self.matrix != np.inf)
        markedRows = set()
        markedCols = set()

        assignments = self.findAssignment(zeros)
        assignedRows = set()
        assignedCols = set()

        for row, col in assignments:
            if row is not None and col is not None:
                assignedRows.add(row)
                assignedCols.add(col)

        for i in range(self.nRows):
            if i not in assignedRows:
                markedRows.add(i)

        changed = True
        while changed:
            changed = False
            for row in list(markedRows):
                for col in range(self.nCols):
                    if zeros[row, col] and col not in markedCols:
                        markedCols.add(col)
                        changed = True

            for row, col in assignments:
                if col in markedCols and row not in markedRows:
                    markedRows.add(row)
                    changed = True

        lineRows = set(range(self.nRows)) - markedRows
        lineCols = markedCols

        return lineRows, lineCols

    def findAssignment(self, zerosMatrix):
        assignments = []
        usedRows = set()
        usedCols = set()

        for i in range(self.nRows):
            for j in range(self.nCols):
                if zerosMatrix[i, j] and i not in usedRows and j not in usedCols:
                    assignments.append((i, j))
                    usedRows.add(i)
                    usedCols.add(j)
                    break

        return assignments

    def step4CheckOptimality(self):
        self.stepCount += 1
        print(f"STEP {self.stepCount}: Check optimality")
        print("=" * 60)

        lineRows, lineCols = self.findMinimumLines()
        numLines = len(lineRows) + len(lineCols)

        print(f"Lines covering all zeros:")
        print(f"Row lines: {sorted(lineRows)}")
        print(f"Column lines: {sorted(lineCols)}")
        print(f"Total lines: {numLines}")
        print(f"Matrix size: {self.nRows}")

        if numLines == self.nRows:
            print("✓ Number of lines equals matrix size - OPTIMAL!")
            return True, lineRows, lineCols
        else:
            print("✗ Number of lines ≠ matrix size - NOT OPTIMAL")
            return False, lineRows, lineCols

    def step5ImproveSolution(self, lineRows, lineCols):
        self.stepCount += 1
        print(f"STEP {self.stepCount}: Improve solution")
        print("=" * 60)

        covered = np.zeros((self.nRows, self.nCols), dtype=bool)

        for i in lineRows:
            covered[i, :] = True
        for j in lineCols:
            covered[:, j] = True

        uncoveredValues = [
            self.matrix[i, j]
            for i in range(self.nRows)
            for j in range(self.nCols)
            if not covered[i, j] and self.matrix[i, j] != np.inf
        ]

        if not uncoveredValues:
            print("No uncovered finite values found - algorithm may not converge")
            return

        a = min(uncoveredValues)
        print(f"Step 5a: Smallest uncovered value a = {a}")
        print("Step 5b: Subtract a from uncovered elements")
        print("Step 5c: Add a to doubly covered elements")

        for i in range(self.nRows):
            for j in range(self.nCols):
                if self.matrix[i, j] != np.inf:
                    rowCovered = i in lineRows
                    colCovered = j in lineCols

                    if not rowCovered and not colCovered:
                        self.matrix[i, j] -= a
                    elif rowCovered and colCovered:
                        self.matrix[i, j] += a

        self.printMatrix(self.matrix, "Matrix after improvement")

    def step6FindAssignment(self):
        self.stepCount += 1
        print(f"STEP {self.stepCount}: Find optimal assignment")
        print("=" * 60)

        zeros = (self.matrix == 0) & (self.matrix != np.inf)
        assignment = self.findOptimalAssignment(zeros)

        print("Optimal assignment (row, col):")
        totalval = 0
        validAssignments = []

        for i, (row, col) in enumerate(assignment):
            if (row < self.originalMatrix.shape[0] and 
                col < self.originalMatrix.shape[1] and
                self.originalMatrix[row, col] != self.blankValue):

                val = self.originalMatrix[row, col]
                totalval += val
                validAssignments.append((row, col))

                if self.blankValue is not None and val == self.blankValue:
                    print(f"  Assignment {i+1}: Row {row} → Column {col} (FORBIDDEN - blank slot!)")
                else:
                    print(f"  Assignment {i+1}: Row {row} → Column {col} (val: {val})")
            else:
                print(f"  Assignment {i+1}: Row {row} → Column {col} (dummy assignment - ignored)")

        problemType = "maximization" if self.maximize else "minimization"
        print(f"\nTotal optimal val ({problemType}): {totalval}")

        return validAssignments, totalval

    def findOptimalAssignment(self, zerosMatrix):
        assignment = []
        tempZeros = zerosMatrix.copy()

        while True:
            assigned = False

            for i in range(self.nRows):
                zeroCols = [j for j in range(self.nCols) if tempZeros[i, j]]
                if len(zeroCols) == 1:
                    j = zeroCols[0]
                    assignment.append((i, j))
                    tempZeros[i, :] = False
                    tempZeros[:, j] = False
                    assigned = True
                    break

            if assigned:
                continue

            for j in range(self.nCols):
                zeroRows = [i for i in range(self.nRows) if tempZeros[i, j]]
                if len(zeroRows) == 1:
                    i = zeroRows[0]
                    assignment.append((i, j))
                    tempZeros[i, :] = False
                    tempZeros[:, j] = False
                    assigned = True
                    break

            if not assigned:
                found = False
                for i in range(self.nRows):
                    for j in range(self.nCols):
                        if tempZeros[i, j]:
                            assignment.append((i, j))
                            tempZeros[i, :] = False
                            tempZeros[:, j] = False
                            found = True
                            break
                    if found:
                        break

                if not found:
                    break

        return assignment

    def solve(self):
        problemType = "MAXIMIZATION" if self.maximize else "MINIMIZATION"
        print(f"HUNGARIAN ALGORITHM - {problemType} PROBLEM - STEP BY STEP SOLUTION")
        print("=" * 70)
        self.printMatrix(self.originalMatrix, "Original val Matrix")

        if self.maximize:
            print("Converting maximization to minimization problem...")
            self.printMatrix(self.matrix, "Converted Matrix (for minimization)")

        self.step1AddDummy()
        self.step2RowReduction()
        self.step3ColumnReduction()

        maxIterations = 10
        iteration = 0

        while iteration < maxIterations:
            optimal, lineRows, lineCols = self.step4CheckOptimality()

            if optimal:
                break
            else:
                self.step5ImproveSolution(lineRows, lineCols)
                iteration += 1

        if iteration >= maxIterations:
            print(f"WARNING: Maximum iterations ({maxIterations}) reached!")

        assignment, totalval = self.step6FindAssignment()
        return assignment, totalval



# Example usage and test cases
if __name__ == "__main__":
    # print("EXAMPLE 1: Basic Minimization Problem")
    # print("=" * 80)
    
    # val_matrix1 = [
    #     [10, 19, 8, 15],
    #     [10, 18, 7, 17],
    #     [13, 16, 9, 14],
    #     [12, 19, 8, 18],
    #     [14, 17, 10, 19],
    # ]
    
    # hungarian1 = HungarianAlgorithm(val_matrix1, maximize=False)
    # assignment1, val1 = hungarian1.solve()
    
    # print("\n" + "="*80)
    # print("EXAMPLE 2: Maximization Problem")
    # print("="*80)
    
    # # Profit matrix (we want to maximize)
    # profit_matrix = [
    #     [90, 75, 75, 80],
    #     [35, 85, 55, 65],
    #     [125, 95, 90, 105],
    #     [45, 110, 95, 115]
    # ]
    
    # hungarian2 = HungarianAlgorithm(profit_matrix, maximize=True)
    # assignment2, val2 = hungarian2.solve()
    
    # print("\n" + "="*80)
    # print("EXAMPLE 3: Problem with Blank Slots (Forbidden Assignments)")
    # print("="*80)
    
    # # val matrix with some forbidden assignments (represented by np.inf)
    # val_matrix_with_blanks = [
    #     [10, np.inf, 8, 15],
    #     [10, 18, np.inf, 17],
    #     [13, 16, 9, np.inf],
    #     [np.inf, 19, 8, 18]
    # ]
    
    # hungarian3 = HungarianAlgorithm(val_matrix_with_blanks, maximize=False, blank_value=np.inf)
    # assignment3, val3 = hungarian3.solve()
    
    # print("\n" + "="*80)
    # print("EXAMPLE 4: Maximization with Blank Slots")
    # print("="*80)
    
    # # Profit matrix with forbidden assignments (use a specific value like -999)
    # FORBIDDEN = -999
    # profit_matrix_with_blanks = [
    #     [90, FORBIDDEN, 75, 80],
    #     [35, 85, FORBIDDEN, 65],
    #     [125, 95, 90, FORBIDDEN],
    #     [FORBIDDEN, 110, 95, 115]
    # ]
    
    # hungarian4 = HungarianAlgorithm(profit_matrix_with_blanks, maximize=True, blank_value=FORBIDDEN)
    # assignment4, val4 = hungarian4.solve()

    # Profit matrix with forbidden assignments (use a specific value like -999)
    b = -999
    profit_matrix_with_blanks = [
        [22, 18, 30, 18],
        [18, b, 27, 22],
        [26, 20, 28, 28],
        [16, 22, b, 14],
        [21, b, 25, 28],
    ]
    
    hungarian4 = HungarianAlgorithm(profit_matrix_with_blanks, maximize=False, blankValue=b)
    assignment4, val4 = hungarian4.solve()

    # print("EXAMPLE 1: Basic Minimization Problem")
    # print("=" * 80)
    
    # val_matrix1 = [
    #     [1, 2, 4],
    #     [5, 3, 4],
    #     [5, 4, 8],
    # ]
    
    # hungarian1 = HungarianAlgorithm(val_matrix1, maximize=False)
    # assignment1, val1 = hungarian1.solve()


    # print("EXAMPLE 1: Basic Minimization Problem")
    # print("=" * 80)
    
    # val_matrix1 = [
    #     [10, 19, 8, 15],
    #     [10, 18, 7, 17],
    #     [13, 16, 9, 14],
    #     [12, 19, 8, 18],
    #     [14, 17, 10, 19],
    # ]
    
    # hungarian1 = HungarianAlgorithm(val_matrix1, maximize=False)
    # assignment1, val1 = hungarian1.solve()