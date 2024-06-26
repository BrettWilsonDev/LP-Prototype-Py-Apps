import sympy as sp
import copy

import dualSimplex

d = sp.symbols('d')


def testInput():
    objFunc = [60, 30, 20]
    constraints = [[8, 6, 1, 48, 0],
                   [4, 2+d, 1.5, 20, 0],
                   [2, 1.5, 0.5, 8, 0],
                   ]

    # objFunc = [100, 30]
    # constraints = [[0, 1, 3, 1],
    #                [1, 1, 7, 0],
    #                [10, 4, 40, 0],
    #                ]

    isMin = False
    return objFunc, constraints, isMin


def scrubDelta(lst):
    cleaned_list = []

    for elem in lst:
        if isinstance(elem, (sp.Add, sp.Mul)):
            # Remove terms involving `d` and keep only the constant term
            term_without_d = elem.as_independent(d, as_Add=True)[0]
            cleaned_list.append(term_without_d)
        elif hasattr(elem, 'has') and elem.has(d):
            # If the entire element is `d`, replace with 0
            cleaned_list.append(0)
        else:
            cleaned_list.append(elem)

    return cleaned_list


def main():
    # get list spots for later use =========================

    objFunc, constraints, isMin = testInput()

    # make temporary copies of objFunc and constraints
    tObjFunc = copy.deepcopy(objFunc)
    tObjFunc = scrubDelta(tObjFunc)

    tConstraints = copy.deepcopy(constraints)
    for i in range(len(constraints)):
        tConstraints[i] = scrubDelta(tConstraints[i])

    # tableaus, changingVars, optimalSolution = dualSimplex.DoDualSimplex(objFunc, constraints, isMin)
    tableaus, changingVars, optimalSolution = dualSimplex.DoDualSimplex(
        tObjFunc, tConstraints, isMin)

    # keep delta in the table
    deltaTab = copy.deepcopy(tableaus[0])
    deltaTab = dualSimplex.DoFormulationOperation(objFunc, constraints)

    print(deltaTab)

    # get the spots of the basic variables
    basicVarSpots = []
    for k in range(len(tableaus[-1])):
        columnIndex = k
        tCVars = []

        for i in range(len(tableaus[-1])):
            columnValue = tableaus[-1][i][columnIndex]
            tCVars.append(columnValue)
        if (sum(1 for num in tCVars if num != 0) == 1):
            basicVarSpots.append(k)

    # get the columns of the basic variables
    basicVarCols = []
    for i in range(len(tableaus[-1])):
        tLst = []
        for j in range(len(tableaus[-1][i])):
            if j in basicVarSpots:
                tLst.append(tableaus[-1][i][j])
        basicVarCols.append(tLst)

    # remove dud col
    del basicVarCols[0]

    # sort the cbv according the basic var positions
    zippedCbv = list(zip(basicVarCols, basicVarSpots))
    sortedCbvZipped = sorted(
        zippedCbv, key=lambda x: x[0].index(1) if 1 in x[0] else len(x[0]))
    sortedBasicVars, basicVarSpots = zip(*sortedCbvZipped)
    # print(sortedBasicVars)

    # populate matrixes ========================================================

    tableaus[0] = copy.deepcopy(deltaTab)

    cbv = []
    for i in range(len(basicVarSpots)):
        cbv.append(copy.deepcopy(-tableaus[0][0][basicVarSpots[i]]))

    # print(cbv)

    matB = []
    for i in range(len(basicVarSpots)):
        tLst = []
        for j in range(1, len(tableaus[0])):
            # print(tableaus[0][j][basicVarSpots[i]], end=" ")
            tLst.append(tableaus[0][j][basicVarSpots[i]])
        matB.append(tLst)

    matrixCbv = sp.Matrix(cbv)

    print(matrixCbv)

    matrixB = sp.Matrix(matB)

    print(matrixB)

    matrixBNegOne = matrixB.inv()

    print(matrixBNegOne)

    matrixCbvNegOne = matrixBNegOne * matrixCbv

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
        changingZRow.append(matNegValue - -deltaTab[0][j])

    # get the rhs optimal value
    tRhsCol = []
    for i in range(1, len(deltaTab)):
        tRhsCol.append(deltaTab[i][-1])

    tRhsOptimal = (sp.Matrix(tRhsCol).transpose() * matrixCbvNegOne)
    changingOptmal = (tRhsOptimal[0, 0])

    print(changingOptmal)

    print(changingZRow)

    print()

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

    for i in range(len(changingBv)):
        print(changingBv[i])

    changingTable = copy.deepcopy(tableaus[-1])

    changingZRow.append(changingOptmal)

    changingTable[0] = changingZRow

    transposeChangingB = sp.Matrix(changingBv).transpose().tolist()

    print()
    for i in range(len(transposeChangingB)):
        print(transposeChangingB[i])

    for i in range(len(changingTable) - 1):
        for j in range(len(changingTable[i])):
            changingTable[i + 1][j] = transposeChangingB[i][j]
            # print(changingTable[i][j])

    print()
    for i in range(len(changingTable)):
        for j in range(len(changingTable[0])):
            print(changingTable[i][j], end=" ")
        print()

main()
