import copy
import math

import sympy as sp

x, y = sp.symbols('x y')

def TestInput():


    isMin = False
    objFunc = [8, 1]
    constraints = [[1, 1, 40, 0],
                   [2, 1, 60, 0],
                   ]
    
    return objFunc, constraints, isMin


def findIntersection(a1, b1, c1, a2, b2, c2):
    # Function to find intersection points of two lines
    determinant = a1 * b2 - a2 * b1
    if determinant == 0:
        return None  # Lines are parallel
    else:
        x = (c1 * b2 - c2 * b1) / determinant
        y = (a1 * c2 - a2 * c1) / determinant
        return (x, y)

def getEndpoints(a, b, c, xBounds, yBounds):
    # Function to get endpoints of the line segment within the bounds
    points = []
    if b != 0:
        y1 = (c - a * xBounds[0]) / b
        y2 = (c - a * xBounds[1]) / b
        if yBounds[0] <= y1 <= yBounds[1]:
            points.append((xBounds[0], y1))
        if yBounds[0] <= y2 <= yBounds[1]:
            points.append((xBounds[1], y2))
    if a != 0:
        x1 = (c - b * yBounds[0]) / a
        x2 = (c - b * yBounds[1]) / a
        if xBounds[0] <= x1 <= xBounds[1]:
            points.append((x1, yBounds[0]))
        if xBounds[0] <= x2 <= xBounds[1]:
            points.append((x2, yBounds[1]))
    return points

def getSortedPoints(constraints):
    # function to get feasible points and line segment points and intersection points
    intersectionPoints = []
    numConstraints = len(constraints)
    
    # Find all intersection points
    for i in range(numConstraints):
        for j in range(i + 1, numConstraints):
            point = findIntersection(constraints[i][0], constraints[i][1], constraints[i][2],
                                      constraints[j][0], constraints[j][1], constraints[j][2])
            if point is not None:
                intersectionPoints.append(point)

    xBounds = (0, max(constraint[2] for constraint in constraints if constraint[0] != 0))
    yBounds = (0, max(constraint[2] for constraint in constraints if constraint[1] != 0))

    endPoints = []
    for constraint in constraints:
        endPoints.extend(getEndpoints(constraint[0], constraint[1], constraint[2], xBounds, yBounds))

    # Combine and filter points
    allPoints = intersectionPoints + endPoints
    feasiblePoints = []
    for point in allPoints:
        x, y = point
        if all((a * x + b * y <= c if eq == 0 else a * x + b * y >= c if eq == 1 else a * x + b * y == c) 
               for a, b, c, eq in constraints) and x >= 0 and y >= 0:
            feasiblePoints.append((x, y))

    # Remove duplicates and sort
    feasiblePoints = list(set(feasiblePoints))
    feasiblePoints.sort(key=lambda p: (p[0], p[1]))

    # remove duplicates from end points
    formattedEndPoints = [(float(x), float(y)) for x, y in endPoints]
    lineSegmentPoints = []
    for point in formattedEndPoints:
        if point not in lineSegmentPoints:
            lineSegmentPoints.append(point)

    return feasiblePoints, lineSegmentPoints, intersectionPoints

def SolveGraphical(objFunc, feasiblePoints, isMin = False):
    def evaluateObjective(x, y):
        # return 100 * x + 30 * y
        return objFunc[0] * x + objFunc[1] * y
    
    objectiveValues = [evaluateObjective(x, y) for x, y in feasiblePoints]

    if isMin:
        optimalValue = min(objectiveValues)
    else:
        optimalValue = max(objectiveValues)

    optimalPoint = feasiblePoints[objectiveValues.index(optimalValue)]

    return optimalValue, optimalPoint

def main():

    objFunc, constraints, isMin = TestInput()

    feasiblePoints, lineSegmentPoints, intersectionPoints = getSortedPoints(constraints)

    optimalValue, optimalPoint = SolveGraphical(objFunc, feasiblePoints, isMin)
    print(optimalValue, optimalPoint)
main()