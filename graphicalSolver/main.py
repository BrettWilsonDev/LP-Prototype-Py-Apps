import copy
import math

import matplotlib.pyplot as plt

import pygame
from imgui.integrations.pygame import PygameRenderer
import imgui
import os
import sys


def testInput():
    isMin = False
    objFunc = [8, 1]
    constraints = [[1, 1, 40, 0],
                   [2, 1, 60, 0],
                   ]

    isMin = True
    objFunc = [100, 30]
    constraints = [[0, 1, 3, 1],
                   [1, 1, 7, 0],
                   [10, 4, 40, 0],
                   ]
    
    objFunc = [1200, 800]
    constraints = [[8, 4, 1600, 0],
                   [4, 4, 1000, 0],
                   [1, 0, 170, 0],
                   [0, 1, 200, 0],
                   [1, 0, 40, 1],
                   [0, 1, 25, 1],
                   [1, -1, 0, 1],
                   [1, -4, 0, 0],
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

    xBounds = (0, max(constraint[2]
               for constraint in constraints if constraint[0] != 0))
    yBounds = (0, max(constraint[2]
               for constraint in constraints if constraint[1] != 0))

    endPoints = []
    for constraint in constraints:
        endPoints.extend(getEndpoints(
            constraint[0], constraint[1], constraint[2], xBounds, yBounds))

    # Combine and filter points
    allPoints = intersectionPoints + endPoints
    allPoints.append((0, 0))
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

    print("\nlineSegments")
    for i in range(len(lineSegmentPoints)):
        try:
            print(f" (start: {lineSegmentPoints[i]} end: {lineSegmentPoints[i + 1]})")
        except:
            pass

    print("\nfeasible region")
    for i in range(len(feasiblePoints)):
        print(feasiblePoints[i], end="")
    print("\n")

    return feasiblePoints, lineSegmentPoints, intersectionPoints


def solveGraphical(objFunc, feasiblePoints, isMin=False):
    def evaluateObjective(x, y):
        # return 100 * x + 30 * y
        return objFunc[0] * x + objFunc[1] * y

    objectiveValues = [evaluateObjective(x, y) for x, y in feasiblePoints]

    if isMin:
        optimalValue = min(objectiveValues)
    else:
        optimalValue = max(objectiveValues)

    optimalPoint = feasiblePoints[objectiveValues.index(optimalValue)]

    print(f"Optimal value: {optimalValue} at {optimalPoint}")

    return optimalValue, optimalPoint


def drawGraph(feasiblePoints, lineSegmentPoints, intersectionPoints, optimalPoint=None, optimalValue=None):
    # print(lineSegmentPoints)
    fullLineSegments = []
    for i in range(0, len(lineSegmentPoints), 2):
        x1, y1 = lineSegmentPoints[i]
        try:
            x2, y2 = lineSegmentPoints[i + 1]
        except:
            x2 = 0
            y2 = 0
        fullLineSegments.append((x1, y1, x2, y2))

    segments = copy.deepcopy(fullLineSegments)

    colors = ['blue', 'orange', 'purple', 'pink', 'brown', 'gray', 'black', 'cyan',
              'magenta', 'gold', 'coral', 'turquoise', 'violet', 'tomato', 'orchid',
              'sienna', 'maroon', 'navy', 'olive', 'lime', 'teal', 'peru', 'indigo',
              'goldenrod', 'salmon']

    # set up the plot
    plt.figure(figsize=(8, 6), num=f"Optimal Value: {
               optimalValue} at point: {optimalPoint}")

    # Plotting each segment individually
    i = 1
    for segment in segments:
        xStart, yStart = segment[0], segment[1]
        xEnd, yEnd = segment[2], segment[3]

        # Plot the line segment
        plt.plot([xStart, xEnd], [yStart, yEnd], marker='o',
                 linestyle='-', color=colors[i - 1], label=f"c{i} at ({xEnd}, {yStart})")

        # Annotate the start and end points
        plt.text(xStart, yStart, f'({xStart}, {yStart})',
                 fontsize=10, va='bottom', ha='left')
        plt.text(xEnd, yEnd, f'({xEnd}, {yEnd})',
                 fontsize=10, va='bottom', ha='left')

        i += 1

    for point in feasiblePoints:
        x, y = point
        plt.text(x, y, f'({x}, {y})', fontsize=10, va='bottom', ha='left')

    # the optimal point
    if optimalPoint is not None:
        x, y = optimalPoint
        plt.scatter(x, y, color='green', marker='o', label=f"Optimal Point at {
                    optimalPoint} : {optimalValue}", s=150)

    # the intersection points
    for point in intersectionPoints:
        x, y = point
        plt.plot(x, y, color='black', marker='o')


    # the feasible region
    feasiblePoints.append(feasiblePoints[0])
    plt.fill_between(*zip(*feasiblePoints), color='red',
                     alpha=0.2, label='Feasible Region')
    
    # the origin point 0, 0
    plt.plot(0, 0, color='black', marker='o')
    plt.text(0, 0, f'({0}, {0})', fontsize=10, va='bottom', ha='left')

    plt.title('Graphical Solver')
    plt.xlabel('X1 Axis')
    plt.ylabel('X2 Axis')
    plt.grid(True)
    plt.tight_layout()

    plt.legend(loc='upper right', fontsize='small')
    plt.show()


def doGui():
    # window setup
    pygame.init()
    size = 1920 / 2, 1080 / 2

    os.system('cls' if os.name == 'nt' else 'clear')
    print("\nBrett's lp Graphical Solver Prototype\n")

    pygame.display.set_mode(size, pygame.DOUBLEBUF |
                            pygame.OPENGL | pygame.RESIZABLE)

    pygame.display.set_caption("lp Graphical Solver Prototype")

    icon = pygame.Surface((1, 1)).convert_alpha()
    icon.fill((0, 0, 0, 1))
    pygame.display.set_icon(icon)

    imgui.create_context()
    impl = PygameRenderer()

    io = imgui.get_io()
    io.display_size = size

    # var setup
    problemType = "Max"

    amtOfObjVars = 2
    objFunc = [0.0, 0.0]

    # constraints
    amtOfConstraints = 1
    constraints = [[0.0, 0.0, 0.0, 0.0]]
    signItems = ["<=", ">=", "="]
    signItemsChoices = [0]

    optimalValue = 0
    optimalPoint = (0, 0)

    while 1:
        # window handling
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

        # input ======================================================

        if imgui.radio_button("Max", problemType == "Max"):
            problemType = "Max"

        if imgui.radio_button("Min", problemType == "Min"):
            problemType = "Min"

        imgui.text("Problem is: {}".format(problemType))

        imgui.spacing()

        for i in range(len(objFunc)):
            value = objFunc[i]
            imgui.set_next_item_width(50)
            imgui.same_line()
            changed, objFunc[i] = imgui.input_float(
                "objFunc {}".format(i + 1), value)

            if changed:
                # Value has been updated
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
                value = constraints[i][j]
                imgui.set_next_item_width(50)
                imgui.same_line()
                changed, xValue = imgui.input_float(
                    "xC{}{}".format(i, j), value)
                if changed:
                    constraints[i][j] = xValue

            imgui.same_line()
            imgui.push_item_width(50)
            changed, selectedItemSign = imgui.combo(
                "comboC{}{}".format(i, j), signItemsChoices[i], signItems)
            if changed:
                signItemsChoices[i] = selectedItemSign
                constraints[i][-1] = signItemsChoices[i]

            imgui.pop_item_width()
            imgui.same_line()
            imgui.set_next_item_width(50)
            rhsValue = constraints[i][-2]
            rhsChanged, rhs = imgui.input_float(
                "RHSC{}{}".format(i, j), rhsValue)

            if rhsChanged:
                constraints[i][-2] = rhs

        if problemType == "Min":
            isMin = True
        else:
            isMin = False

        # solve button ================================================
        if imgui.button("Solve"):
            try:
                objFunc, constraints, isMin = testInput()

                feasiblePoints, lineSegmentPoints, intersectionPoints = getSortedPoints(
                    constraints)

                optimalValue, optimalPoint = solveGraphical(
                    objFunc, feasiblePoints, isMin)

                drawGraph(feasiblePoints, lineSegmentPoints,
                          intersectionPoints, optimalPoint, optimalValue)

            except Exception as e:
                print(e)
                imgui.text("Math Error")
                

        imgui.end()

        imgui.render()
        impl.render(imgui.get_draw_data())

        pygame.display.flip()


def main():
    doGui()


main()
