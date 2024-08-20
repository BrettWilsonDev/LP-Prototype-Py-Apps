import imgui
from imgui.integrations.glfw import GlfwRenderer
import glfw

import math
import copy
import sys
import os

try:
    from dualsimplex import DualSimplex as Dual
except:
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    from dual.dualsimplex import DualSimplex as Dual


class DEASolver:

    def __init__(self, isConsoleOutput=False):
        self.isConsoleOutput = isConsoleOutput

        self.reset()

    def reset(self):
        self.dual = Dual()
        self.testInputSelected = -1

        self.amtOfItems = 1

        self.amtOfOutputs = 1
        self.LpOutputs = [[0.0]]

        self.amtOfInputs = 1
        self.LpInputs = [[0.0]]

        self.tables = []
        self.header = []
        self.allInputTotals = []
        self.allOutputTotals = []
        self.allRangesO = []
        self.allRangesI = []
        self.changingVars = []

        self.problemType = "Max"
        self.isMin = False

    def testInput(self, testNum=-1):
        if testNum == 0:
            LpInputs = [
                [5, 14],
                [8, 15],
                [7, 12],
            ]

            LpOutputs = [
                [9, 4, 16],
                [5, 7, 10],
                [4, 9, 13],
            ]
        elif testNum == 1:
            LpInputs = [
                [15, 20, 50],
                [14, 23, 51],
                [16, 19, 51],
            ]

            LpOutputs = [
                [200, 15, 35],
                [220, 18, 45],
                [210, 17, 20],
            ]

        if testNum == -1:
            return None
        else:
            return LpInputs, LpOutputs

    def buildTable(self, LpInputs, LpOutputs, currentSelection=0):
        tabWLen = len(LpInputs[-1]) + len(LpOutputs[-1])

        # build bottom rows
        bottomRows = []
        # for i in range(len(LpInputs) + 2):
        #     row = [0] * (len(LpInputs) + 2)
        #     row[i] = 1
        #     bottomRows.append(row)

        print(len(LpInputs[-1]) + len(LpOutputs[-1]))

        for i in range(len(LpInputs[-1]) + len(LpOutputs[-1])):
            row = [0] * (len(LpInputs[-1]) + len(LpOutputs[-1]))
            row[i] = 1
            bottomRows.append(row)

        # print(bottomRows)
        # print()

        # build top rows
        topRows = []
        for i in range(len(LpOutputs)):
            topRows.append(copy.deepcopy(LpOutputs[i]))

        for i in range(len(LpInputs)):
            for j in range(len(LpInputs[i])):
                topRows[i].append(copy.deepcopy(-LpInputs[i][j]))

        # build middle row
        middleRow = []
        for i in range(tabWLen):
            middleRow.append(0)

        currentMiddleRow = LpInputs[currentSelection]
        for i in range(len(currentMiddleRow)):
            del middleRow[i]
            middleRow.append(currentMiddleRow[i])

        zRow = copy.deepcopy(LpOutputs[currentSelection])

        for i in range(tabWLen - len(zRow)):
            zRow.append(0)

        table = []
        table.append(zRow)
        for i in range(len(topRows)):
            table.append(copy.deepcopy(topRows[i]))

        table.append(middleRow)

        for i in range(len(bottomRows)):
            table.append(bottomRows[i])

        constraints = []
        for i in range(len(topRows)):
            constraints.append(copy.deepcopy(topRows[i]))
            constraints[i].append(0)
            constraints[i].append(0)

        tempMiddleRow = copy.deepcopy(middleRow)
        tempMiddleRow.append(1)
        tempMiddleRow.append(0)
        constraints.append(tempMiddleRow)
        tempMiddleRow = copy.deepcopy(middleRow)
        tempMiddleRow.append(1)
        tempMiddleRow.append(1)
        constraints.append(tempMiddleRow)

        # constraints.append(middleRow)

        tempCons = []
        for i in range(len(bottomRows)):
            tempCons.append(copy.deepcopy(bottomRows[i]))
            tempCons[i].append(0.0001)
            tempCons[i].append(1)
            constraints.append(tempCons[i])

        conRow = LpInputs[currentSelection]

        return table, zRow, constraints, conRow

    def solveTable(self, table, objfunc, constraints, conRow, isMin=False):
        tableaus, changingVars, optimalSolution = self.dual.doDualSimplex(
            objfunc, constraints, isMin)
        print("changingVars", changingVars)
        print("optimalSolution", optimalSolution)

        mathCons = []
        for i in range(len(constraints)):
            mathCons.append([])
            for j in range(len(constraints[i]) - 1):
                mathCons[i].append(copy.deepcopy(constraints[i][j]))

        # get the cell ref for display purposes
        cellRef = []
        cellRef.append(optimalSolution)
        for i in range(len(mathCons)):
            tSum = sum([a * b for a, b in zip(changingVars, mathCons[i])])
            cellRef.append(tSum)

        # get the len of the outputs
        objFuncLen = 0
        for i in range(len(objfunc)):
            if objfunc[i] != 0:
                objFuncLen += 1

        # get the outputs multiplied by the changing vars
        outputRange = []
        for i in range(objFuncLen):
            outputRange.append(objfunc[i] * changingVars[i])

        # get the inputs multiplied by the changing vars
        inputRange = []
        for i in range(len(objfunc) - objFuncLen):
            inputRange.append(conRow[i] * changingVars[i + objFuncLen])

        # get the totals
        outputTotal = sum(outputRange)
        inputTotal = sum(inputRange)

        return outputTotal, inputTotal, outputRange, inputRange, cellRef, changingVars

    def doDEA(self, LpInputs, LpOutputs, isMin):
        tables = []
        allRangesO = []
        allRangesI = []
        allOutputTotals = []
        allInputTotals = []

        for i in range(len(LpInputs)):
            table, objfunc, constraints, conRow = self.buildTable(
                LpInputs, LpOutputs, i)
            outputTotal, inputTotal, outputRange, inputRange, cellRef, changingVars = self.solveTable(
                table, objfunc, constraints, conRow, isMin)

            allRangesO.append(outputRange)
            allRangesI.append(inputRange)

            allOutputTotals.append(outputTotal)
            allInputTotals.append(inputTotal)

            # add the cell ref to the table
            for j in range(len(cellRef) - 1):
                table[j].append(cellRef[j])

            # add the sign
            for j in range(len(LpOutputs) + 1):
                table[j].append(0)
            table[len(LpOutputs) + 1].append(2)
            for j in range((len(LpInputs[-1]) + len(LpOutputs[-1]))):
                table[j + len(LpOutputs) + 2].append(1)

            # add the rhs
            for j in range(len(LpOutputs) + 1):
                table[j].append(0)
            table[len(LpOutputs) + 1].append(1)
            for j in range((len(LpInputs[-1]) + len(LpOutputs[-1]))):
                table[j + len(LpOutputs) + 2].append(0.0001)

            tables.append(table)

        # build header
        header = []
        for i in range(len(LpOutputs[-1])):
            header.append("o" + str(i + 1))
        for i in range(len(LpInputs[-1])):
            header.append("i" + str(i + 1))
        header.append("ref")
        header.append("sign")
        header.append("rhs")

        for i in range(len(tables)):
            for cvCtr in range(len(changingVars)):
                print("{:10.4f}".format(changingVars[cvCtr]), end=" ")
            print()
            for hctr in range(len(header)):
                print("    {:6}".format(header[hctr]), end=" ")
            print()
            for j in range(len(tables[i])):
                for k in range(len(tables[i][j])):
                    if k == (len(LpOutputs[-1]) + len(LpInputs[-1]) + 1):
                        if tables[i][j][k] == 0:
                            print("{:10}".format("    <="), end=" ")
                        elif tables[i][j][k] == 1:
                            print("{:10}".format("    >="), end=" ")
                        else:
                            print("{:10}".format("     ="), end=" ")
                    else:
                        print("{:10.4f}".format(tables[i][j][k]), end=" ")
                print()

            print("\nranges:")
            print()
            for j in range(len(LpOutputs[-1])):
                print("  {:8}".format("o" + str(j + 1)), end=" ")

            print()
            for j in range(len(LpOutputs[-1])):
                print("{:10.6f}".format(allRangesO[i][j]), end=" ")
            print(f"  Output total: {allOutputTotals[i]}", end=" ")

            print("\n")
            for j in range(len(LpInputs[-1])):
                print("  {:8}".format("i" + str(j + 1)), end=" ")

            print()
            for j in range(len(LpInputs[-1])):
                print("{:10.6f}".format(allRangesI[i][j]), end=" ")
            print(f"   Input total: {allInputTotals[i]}", end=" ")

            print(f"\n\nTotals:\n\n{allOutputTotals[i]}\ndivided by\n{
                allInputTotals[i]}\n\n= {allOutputTotals[i] / allInputTotals[i]}")
            print()

            return tables, header, allInputTotals, allOutputTotals, allRangesO, allRangesI, changingVars

    def imguiUIElements(self, windowSize, windowPosX = 0, windowPosY = 0):
        imgui.set_next_window_position(windowPosX, windowPosY)  # Set the window position
        imgui.set_next_window_size(
            (windowSize[0]), (windowSize[1]))  # Set the window size
        imgui.begin("Tableaus Output",
                    flags=imgui.WINDOW_NO_TITLE_BAR | imgui.WINDOW_NO_RESIZE | imgui.WINDOW_ALWAYS_HORIZONTAL_SCROLLBAR)
        imgui.begin_child("Scrollable Child", width=0, height=0,
            border=True, flags=imgui.WINDOW_ALWAYS_HORIZONTAL_SCROLLBAR)

        # input =============================

        if imgui.radio_button("Max", self.problemType == "Max"):
            self.problemType = "Max"

        if imgui.radio_button("Min", self.problemType == "Min"):
            self.problemType = "Min"

        if self.problemType == "Max":
            self.isMin = False
        else:
            self.isMin = True

        # item rows ===========================================
        if imgui.button("Item Row +"):
            self.amtOfItems += 1
            self.LpOutputs.append([0.0] * self.amtOfOutputs)
            self.LpInputs.append([0.0] * self.amtOfInputs)

        imgui.same_line()

        if imgui.button("Item Row -"):
            if self.amtOfItems != 1:
                self.amtOfItems += -1
                self.LpOutputs.pop()
                self.LpInputs.pop()

        # inputs ===========================================
        if imgui.button("Inputs +"):
            self.amtOfInputs += 1
            for i in range(len(self.LpInputs)):
                self.LpInputs[i].append(0.0)

        imgui.same_line()

        if imgui.button("Inputs -"):
            if self.amtOfInputs != 1:
                self.amtOfInputs += -1
                for i in range(len(self.LpInputs)):
                    self.LpInputs[i].pop()

        imgui.same_line(0, 20)

        # outputs ===========================================
        if imgui.button("Outputs +"):
            self.amtOfOutputs += 1
            for i in range(len(self.LpOutputs)):
                self.LpOutputs[i].append(0.0)

        imgui.same_line()

        if imgui.button("Outputs -"):
            if self.amtOfOutputs != 1:
                self.amtOfOutputs += -1
                for i in range(len(self.LpOutputs)):
                    self.LpOutputs[i].pop()

        for i in range(self.amtOfItems):
            imgui.spacing()
            # input gui input
            if len(self.LpInputs) <= i:
                self.LpInputs.append([0.0] * (self.amtOfItems))

            for j in range(self.amtOfInputs):
                value = self.LpInputs[i][j]
                imgui.set_next_item_width(50)
                imgui.same_line()
                changed, xValue = imgui.input_float(
                    "##i{}{}".format(i, j), value)
                imgui.same_line()
                imgui.text(f"i{j + 1}")
                if changed:
                    self.LpInputs[i][j] = xValue
                imgui.same_line()

            imgui.spacing()
            imgui.same_line()
            imgui.spacing()
            imgui.same_line()
            imgui.spacing()
            imgui.same_line()
            imgui.spacing()

            # output gui input
            if len(self.LpOutputs) <= i:
                self.LpOutputs.append([0.0] * (self.amtOfItems))

            for j in range(self.amtOfOutputs):
                value = self.LpOutputs[i][j]
                imgui.set_next_item_width(50)
                imgui.same_line()
                changed, xValue = imgui.input_float(
                    "##o{}{}".format(i, j), value)
                imgui.same_line()
                imgui.text(f"o{j + 1}")
                if changed:
                    self.LpOutputs[i][j] = xValue
                imgui.same_line()

            imgui.spacing()

        imgui.spacing()
        # solve button ========================================================
        if imgui.button("Solve"):
            try:
                if self.testInput(self.testInputSelected) is not None:
                    self.LpInputs, self.LpOutputs = self.testInput(
                        self.testInputSelected)

                self.tables, self.header, self.allInputTotals, self.allOutputTotals, self.allRangesO, self.allRangesI, self.changingVars = self.doDEA(
                    self.LpInputs, self.LpOutputs, self.isMin)

                print(self.tables[0])
            except Exception as e:
                print(f"math error {e}")

        imgui.same_line(0, 30)
        imgui.push_style_color(imgui.COLOR_TEXT, 1.0, 0.0, 0.0)
        if imgui.button("Reset"):
            self.reset()
        imgui.pop_style_color()

        # output ============================================================
        try:
            imgui.spacing()
            imgui.spacing()
            for i in range(len(self.tables)):
                imgui.push_style_color(imgui.COLOR_TEXT, 0.0, 1.0, 0.0)
                imgui.text("cv   ")
                imgui.same_line()
                for cvCtr in range(len(self.changingVars)):
                    imgui.text("{:10.4f}".format(self.changingVars[cvCtr]))
                    imgui.same_line()
                imgui.pop_style_color()
                imgui.spacing()
                imgui.text("       ")
                imgui.same_line()
                imgui.push_style_color(
                    imgui.COLOR_TEXT, 204/255.0, 204/255.0, 0.0)
                for hctr in range(len(self.header)):
                    imgui.text("  {:8}".format(self.header[hctr]))
                    imgui.same_line()
                imgui.pop_style_color()
                imgui.spacing()
                for j in range(len(self.tables[i])):
                    imgui.push_style_color(
                        imgui.COLOR_TEXT, 204/255.0, 204/255.0, 0.0)
                    if j == 0:
                        imgui.text(f"{self.problemType} z")
                        imgui.same_line()
                    elif j < (len(self.LpOutputs) + 1):
                        imgui.text(f"c{j}   ")
                        imgui.same_line()
                    elif j == (len(self.LpOutputs) + 1):
                        imgui.push_style_color(
                            imgui.COLOR_TEXT, 255/255.0, 165/255.0, 0.0)
                        imgui.text(f"con  ")
                        imgui.pop_style_color()
                        imgui.same_line()
                    else:
                        imgui.text(f"{j - len(self.LpOutputs) - 1}    ")
                        imgui.same_line()
                    imgui.pop_style_color()
                    for k in range(len(self.tables[i][j])):
                        if j == (len(self.LpOutputs) + 1):
                            imgui.push_style_color(
                                imgui.COLOR_TEXT, 255/255.0, 165/255.0, 0.0)
                        if k == (len(self.tables[i][j]) - 3) and j == 0:
                            imgui.push_style_color(
                                imgui.COLOR_TEXT, 0.0, 1.0, 1.0)
                        if k == (len(self.LpOutputs[-1]) + len(self.LpInputs[-1]) + 1):
                            if self.tables[i][j][k] == 0:
                                imgui.text("{:10}".format("    <="))
                            elif self.tables[i][j][k] == 1:
                                imgui.text("{:10}".format("    >="))
                            else:
                                imgui.text("{:10}".format("     ="))
                        else:
                            imgui.text("{:10.4f}".format(self.tables[i][j][k]))

                        if j == (len(self.LpOutputs) + 1):
                            imgui.pop_style_color()
                        if k == (len(self.tables[i][j]) - 3) and j == 0:
                            imgui.pop_style_color()

                        imgui.same_line()
                    imgui.spacing()
                imgui.spacing()
                imgui.spacing()
                imgui.spacing()

                imgui.text("\nRanges:")
                imgui.spacing()
                for j in range(len(self.LpOutputs[-1])):
                    imgui.text("  {:8}".format("o" + str(j + 1)))
                    imgui.same_line()

                imgui.spacing()
                for j in range(len(self.LpOutputs[-1])):
                    imgui.text("{:10.6f}".format(self.allRangesO[i][j]))
                    imgui.same_line()
                imgui.push_style_color(imgui.COLOR_TEXT, 0.0, 1.0, 1.0)
                imgui.text(f"  Output total: {self.allOutputTotals[i]}")
                imgui.pop_style_color()

                imgui.text("\n")
                for j in range(len(self.LpInputs[-1])):
                    imgui.text("  {:8}".format("i" + str(j + 1)))
                    imgui.same_line()

                imgui.spacing()
                for j in range(len(self.LpInputs[-1])):
                    imgui.text("{:10.6f}".format(self.allRangesI[i][j]))
                    imgui.same_line()
                imgui.push_style_color(imgui.COLOR_TEXT, 0.0, 1.0, 1.0)
                imgui.text(f"   Input total: {self.allInputTotals[i]}")
                imgui.pop_style_color()

                imgui.push_style_color(imgui.COLOR_TEXT, 0.0, 1.0, 1.0)
                imgui.text(f"\n\nTotals: {
                    self.allOutputTotals[i]} / {self.allInputTotals[i]} = {self.allOutputTotals[i] / self.allInputTotals[i]}")
                imgui.pop_style_color()
                imgui.spacing()
                imgui.spacing()
                imgui.spacing()
                imgui.spacing()
        except:
            pass

        # close =============================
        
        imgui.end_child()
        imgui.end()

    def doGui(self):
        if not glfw.init():
            print("Could not initialize OpenGL context")
            return

        window = glfw.create_window(
            int(1920 / 2), int(1080 / 2), "Data Envelopment Analysis Prototype", None, None)
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
    classInstance = DEASolver(isConsoleOutput)
    classInstance.doGui()


if __name__ == "__main__":
    main(True)
