import imgui
from imgui.integrations.glfw import GlfwRenderer
import glfw

import copy
import sys
import os
import matplotlib.pyplot as plt

class GraphicalSolver:
    def __init__(self, isConsoleOutput=False):
        self.isConsoleOutput = isConsoleOutput

        self.reset()

    def reset(self):
        self.testInputSelected = -1

        # var setup
        self.problemType = "Max"

        self.amtOfObjVars = 2
        self.objFunc = [0.0, 0.0]

        # constraints
        self.amtOfConstraints = 1
        self.constraints = [[0.0, 0.0, 0.0, 0.0]]
        self.signItems = ["<=", ">=", "="]
        self.signItemsChoices = [0]

        self.optimalValue = 0
        self.optimalPoint = (0, 0)

    def testInput(self, testNum=-1):
        if testNum == 0:
            isMin = False
            objFunc = [8, 1]
            constraints = [[1, 1, 40, 0],
                           [2, 1, 60, 0],
                           ]
        elif testNum == 1:
            isMin = False
            objFunc = [100, 30]
            constraints = [[0, 1, 3, 1],
                           [1, 1, 7, 0],
                           [10, 4, 40, 0],
                           ]
        elif testNum == 2:
            isMin = False
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

        if testNum == -1:
            return None
        else:
            return objFunc, constraints, isMin

    def findIntersection(self, a1, b1, c1, a2, b2, c2):
        # Function to find intersection points of two lines
        determinant = a1 * b2 - a2 * b1
        if determinant == 0:
            return None  # Lines are parallel
        else:
            x = (c1 * b2 - c2 * b1) / determinant
            y = (a1 * c2 - a2 * c1) / determinant
            return (x, y)

    def getEndpoints(self, a, b, c, xBounds, yBounds):
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

    def getSortedPoints(self, constraints):
        # function to get feasible points and line segment points and intersection points
        intersectionPoints = []
        numConstraints = len(constraints)

        # Find all intersection points
        for i in range(numConstraints):
            for j in range(i + 1, numConstraints):
                point = self.findIntersection(constraints[i][0], constraints[i][1], constraints[i][2],
                                              constraints[j][0], constraints[j][1], constraints[j][2])
                if point is not None:
                    intersectionPoints.append(point)

        xBounds = (0, max(constraint[2]
                          for constraint in constraints if constraint[0] != 0))
        yBounds = (0, max(constraint[2]
                          for constraint in constraints if constraint[1] != 0))

        endPoints = []
        for constraint in constraints:
            endPoints.extend(self.getEndpoints(
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

        if self.isConsoleOutput:
            print("\nlineSegments")
        for i in range(len(lineSegmentPoints)):
            try:
                if self.isConsoleOutput:
                    print(f" (start: {lineSegmentPoints[i]} end: {
                        lineSegmentPoints[i + 1]})")
            except:
                pass

        if self.isConsoleOutput:
            print("\nfeasible region")
            for i in range(len(feasiblePoints)):
                print(feasiblePoints[i], end="")
            print("\n")

        return feasiblePoints, lineSegmentPoints, intersectionPoints

    def solveGraphical(self, objFunc, feasiblePoints, isMin=False):
        def evaluateObjective(x, y):
            return objFunc[0] * x + objFunc[1] * y

        objectiveValues = [evaluateObjective(x, y) for x, y in feasiblePoints]

        if isMin:
            optimalValue = min(objectiveValues)
        else:
            optimalValue = max(objectiveValues)

        optimalPoint = feasiblePoints[objectiveValues.index(optimalValue)]

        if self.isConsoleOutput:
            print(f"Optimal value: {optimalValue} at {optimalPoint}")

        return optimalValue, optimalPoint

    def grahamScan(self, points):
        # Function to calculate the cross product of vectors p1p2 and p2p3
        def crossProduct(p1, p2, p3):
            return (p2[0] - p1[0]) * (p3[1] - p2[1]) - (p2[1] - p1[1]) * (p3[0] - p2[0])

        # Sort points lexicographically
        points = sorted(points)

        # Calculate the lower hull
        lowerHull = []
        for p in points:
            while len(lowerHull) >= 2 and crossProduct(lowerHull[-2], lowerHull[-1], p) < 0:
                lowerHull.pop()
            lowerHull.append(p)

        # Calculate the upper hull
        upperHull = []
        for p in reversed(points):
            while len(upperHull) >= 2 and crossProduct(upperHull[-2], upperHull[-1], p) < 0:
                upperHull.pop()
            upperHull.append(p)

        # Remove the last point of each hull as it is a duplicate of the first point of the other hull
        return lowerHull[:-1] + upperHull[:-1]

    def drawGraph(self, feasiblePoints, lineSegmentPoints, intersectionPoints, optimalPoint=None, optimalValue=None):
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
            if (xStart, yStart) not in feasiblePoints:
                plt.text(xStart, yStart, f'({xStart}, {yStart})',
                         fontsize=10, va='bottom', ha='left')
            if (xEnd, yEnd) not in feasiblePoints:
                plt.text(xEnd, yEnd, f'({xEnd}, {yEnd})',
                         fontsize=10, va='bottom', ha='left')

            i += 1

        for point in feasiblePoints:
            x, y = point
            plt.text(x, y, f'({x}, {y})', fontsize=10, va='bottom', ha='left')

        # the feasible region
        feasiblePoints.append(feasiblePoints[0])
        plt.fill_between(*zip(*self.grahamScan(feasiblePoints)), color='red',
                         alpha=0.2, label='Feasible Region')

        # the intersection points
        for point in intersectionPoints:
            x, y = point
            plt.plot(x, y, color='black', marker='o')

        # the optimal point
        if optimalPoint is not None:
            x, y = optimalPoint
            plt.scatter(x, y, color='green', marker='o', label=f"Optimal Point at\n{
                        optimalPoint}\n: {optimalValue}", s=150)

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

    def imguiUIElements(self, windowSize, windowPosX = 0, windowPosY = 0):
        imgui.set_next_window_position(windowPosX, windowPosY)  # Set the window position
        imgui.set_next_window_size(
            (windowSize[0]), (windowSize[1]))  # Set the window size
        imgui.begin("Tableaus Output",
                    flags=imgui.WINDOW_NO_TITLE_BAR | imgui.WINDOW_NO_RESIZE | imgui.WINDOW_ALWAYS_HORIZONTAL_SCROLLBAR)
        imgui.begin_child("Scrollable Child", width=0, height=0,
            border=True, flags=imgui.WINDOW_ALWAYS_HORIZONTAL_SCROLLBAR)

        # input ======================================================

        if imgui.radio_button("Max", self.problemType == "Max"):
            self.problemType = "Max"

        if imgui.radio_button("Min", self.problemType == "Min"):
            self.problemType = "Min"

        imgui.text("Problem is: {}".format(self.problemType))

        imgui.spacing()

        for i in range(len(self.objFunc)):
            value = self.objFunc[i]
            imgui.set_next_item_width(50)
            imgui.same_line()
            changed, self.objFunc[i] = imgui.input_float(
                "##objFunc {}".format(i + 1), value)
            imgui.same_line()
            imgui.text(f"x{i + 1}")

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

        # solve button ================================================
        if imgui.button("Solve"):
            try:
                if self.testInput(self.testInputSelected) is not None:
                    self.objFunc, self.constraints, isMin = self.testInput(
                        self.testInputSelected)

                self.feasiblePoints, self.lineSegmentPoints, self.intersectionPoints = self.getSortedPoints(
                    self.constraints)

                self.optimalValue, self.optimalPoint = self.solveGraphical(
                    self.objFunc, self.feasiblePoints, isMin)

                self.drawGraph(self.feasiblePoints, self.lineSegmentPoints,
                               self.intersectionPoints, self.optimalPoint, self.optimalValue)

            except Exception as e:
                print(e)
                imgui.text("Math Error")

        imgui.same_line(0, 30)
        imgui.push_style_color(imgui.COLOR_TEXT, 1.0, 0.0, 0.0)
        if imgui.button("Reset"):
            self.reset()
        imgui.pop_style_color()


        imgui.end_child()
        imgui.end()

    def doGui(self):
        if not glfw.init():
            print("Could not initialize OpenGL context")
            return

        window = glfw.create_window(
            int(1920 / 2), int(1080 / 2), "lp Graphical Solver Prototype", None, None)
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

def main(isConsoleOutput=False):
    classInstance = GraphicalSolver(isConsoleOutput)
    classInstance.doGui()


if __name__ == "__main__":
    main(True)
