import copy
import math

import pygame
from imgui.integrations.pygame import PygameRenderer
import imgui
import os
import sys

try:
    from dualsimplex import DualSimplex as Dual
    from mathpreliminaries import MathPreliminaries as MathPrelims
except:
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    from dual.dualsimplex import DualSimplex as Dual
    from mathPrelim.mathpreliminaries import MathPreliminaries as MathPrelims   


class DEASolver:
    dual = Dual()

    isConsoleOutput = False

    def __init__(self, isConsoleOutput=False):
        self.isConsoleOutput = isConsoleOutput

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
        print(objfunc, constraints)
        tableaus, changingVars, optimalSolution = self.dual.doDualSimplex(
            objfunc, constraints, isMin)
        print(changingVars, optimalSolution)

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

    def doGui(self):
        # window setup
        pygame.init()
        size = 1920 / 2, 1080 / 2

        os.system('cls' if os.name == 'nt' else 'clear')
        print("\nData Envelopment Analysis prototype tool for lp DEA problems\n")

        pygame.display.set_mode(size, pygame.DOUBLEBUF |
                                pygame.OPENGL | pygame.RESIZABLE)

        pygame.display.set_caption("Data Envelopment Analysis Prototype")

        icon = pygame.Surface((1, 1)).convert_alpha()
        icon.fill((0, 0, 0, 1))
        pygame.display.set_icon(icon)

        imgui.create_context()
        impl = PygameRenderer()

        io = imgui.get_io()
        io.display_size = size

        # var setup

        amtOfItems = 1

        amtOfOutputs = 1
        LpOutputs = [[0.0]]

        amtOfInputs = 1
        LpInputs = [[0.0]]

        tables = []
        header = []
        allInputTotals = []
        allOutputTotals = []
        allRangesO = []
        allRangesI = []
        changingVars = []

        problemType = "Max"
        isMin = False

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

            # input =============================

            if imgui.radio_button("Max", problemType == "Max"):
                problemType = "Max"

            if imgui.radio_button("Min", problemType == "Min"):
                problemType = "Min"

            if problemType == "Max":
                isMin = False
            else:
                isMin = True

            # item rows ===========================================
            if imgui.button("Item Row +"):
                amtOfItems += 1
                LpOutputs.append([0.0] * amtOfOutputs)
                LpInputs.append([0.0] * amtOfInputs)

            imgui.same_line()

            if imgui.button("Item Row -"):
                if amtOfItems != 1:
                    amtOfItems += -1
                    LpOutputs.pop()
                    LpInputs.pop()

            # inputs ===========================================
            if imgui.button("Inputs +"):
                amtOfInputs += 1
                for i in range(len(LpInputs)):
                    LpInputs[i].append(0.0)

            imgui.same_line()

            if imgui.button("Inputs -"):
                if amtOfInputs != 1:
                    amtOfInputs += -1
                    for i in range(len(LpInputs)):
                        LpInputs[i].pop()

            imgui.same_line(0, 20)

            # outputs ===========================================
            if imgui.button("Outputs +"):
                amtOfOutputs += 1
                for i in range(len(LpOutputs)):
                    LpOutputs[i].append(0.0)

            imgui.same_line()

            if imgui.button("Outputs -"):
                if amtOfOutputs != 1:
                    amtOfOutputs += -1
                    for i in range(len(LpOutputs)):
                        LpOutputs[i].pop()

            for i in range(amtOfItems):
                imgui.spacing()
                # input gui input
                if len(LpInputs) <= i:
                    LpInputs.append([0.0] * (amtOfItems))

                for j in range(amtOfInputs):
                    value = LpInputs[i][j]
                    imgui.set_next_item_width(50)
                    imgui.same_line()
                    changed, xValue = imgui.input_float(
                        "##i{}{}".format(i, j), value)
                    imgui.same_line()
                    imgui.text(f"i{j + 1}")
                    if changed:
                        LpInputs[i][j] = xValue
                    imgui.same_line()

                imgui.spacing()
                imgui.same_line()
                imgui.spacing()
                imgui.same_line()
                imgui.spacing()
                imgui.same_line()
                imgui.spacing()

                # output gui input
                if len(LpOutputs) <= i:
                    LpOutputs.append([0.0] * (amtOfItems))

                for j in range(amtOfOutputs):
                    value = LpOutputs[i][j]
                    imgui.set_next_item_width(50)
                    imgui.same_line()
                    changed, xValue = imgui.input_float(
                        "##o{}{}".format(i, j), value)
                    imgui.same_line()
                    imgui.text(f"o{j + 1}")
                    if changed:
                        LpOutputs[i][j] = xValue
                    imgui.same_line()

                imgui.spacing()

            imgui.spacing()
            # solve button ========================================================
            if imgui.button("Solve"):
                try:
                    if self.testInput() is not None:
                        LpInputs, LpOutputs = self.testInput()

                    tables, header, allInputTotals, allOutputTotals, allRangesO, allRangesI, changingVars = self.doDEA(
                        LpInputs, LpOutputs, isMin)

                    print(tables[0])
                except Exception as e:
                    print(f"math error {e}")

            # output ============================================================
            try:
                imgui.spacing()
                imgui.spacing()
                for i in range(len(tables)):
                    imgui.push_style_color(imgui.COLOR_TEXT, 0.0, 1.0, 0.0)
                    imgui.text("cv   ")
                    imgui.same_line()
                    for cvCtr in range(len(changingVars)):
                        imgui.text("{:10.4f}".format(changingVars[cvCtr]))
                        imgui.same_line()
                    imgui.pop_style_color()
                    imgui.spacing()
                    imgui.text("       ")
                    imgui.same_line()
                    imgui.push_style_color(
                        imgui.COLOR_TEXT, 204/255.0, 204/255.0, 0.0)
                    for hctr in range(len(header)):
                        imgui.text("  {:8}".format(header[hctr]))
                        imgui.same_line()
                    imgui.pop_style_color()
                    imgui.spacing()
                    for j in range(len(tables[i])):
                        imgui.push_style_color(
                            imgui.COLOR_TEXT, 204/255.0, 204/255.0, 0.0)
                        if j == 0:
                            imgui.text(f"{problemType} z")
                            imgui.same_line()
                        elif j < (len(LpOutputs) + 1):
                            imgui.text(f"c{j}   ")
                            imgui.same_line()
                        elif j == (len(LpOutputs) + 1):
                            imgui.push_style_color(
                                imgui.COLOR_TEXT, 255/255.0, 165/255.0, 0.0)
                            imgui.text(f"con  ")
                            imgui.pop_style_color()
                            imgui.same_line()
                        else:
                            imgui.text(f"{j - len(LpOutputs) - 1}    ")
                            imgui.same_line()
                        imgui.pop_style_color()
                        for k in range(len(tables[i][j])):
                            if j == (len(LpOutputs) + 1):
                                imgui.push_style_color(
                                    imgui.COLOR_TEXT, 255/255.0, 165/255.0, 0.0)
                            if k == (len(tables[i][j]) - 3) and j == 0:
                                imgui.push_style_color(
                                    imgui.COLOR_TEXT, 0.0, 1.0, 1.0)
                            if k == (len(LpOutputs[-1]) + len(LpInputs[-1]) + 1):
                                if tables[i][j][k] == 0:
                                    imgui.text("{:10}".format("    <="))
                                elif tables[i][j][k] == 1:
                                    imgui.text("{:10}".format("    >="))
                                else:
                                    imgui.text("{:10}".format("     ="))
                            else:
                                imgui.text("{:10.4f}".format(tables[i][j][k]))

                            if j == (len(LpOutputs) + 1):
                                imgui.pop_style_color()
                            if k == (len(tables[i][j]) - 3) and j == 0:
                                imgui.pop_style_color()

                            imgui.same_line()
                        imgui.spacing()
                    imgui.spacing()
                    imgui.spacing()
                    imgui.spacing()

                    imgui.text("\nRanges:")
                    imgui.spacing()
                    for j in range(len(LpOutputs[-1])):
                        imgui.text("  {:8}".format("o" + str(j + 1)))
                        imgui.same_line()

                    imgui.spacing()
                    for j in range(len(LpOutputs[-1])):
                        imgui.text("{:10.6f}".format(allRangesO[i][j]))
                        imgui.same_line()
                    imgui.push_style_color(imgui.COLOR_TEXT, 0.0, 1.0, 1.0)
                    imgui.text(f"  Output total: {allOutputTotals[i]}")
                    imgui.pop_style_color()

                    imgui.text("\n")
                    for j in range(len(LpInputs[-1])):
                        imgui.text("  {:8}".format("i" + str(j + 1)))
                        imgui.same_line()

                    imgui.spacing()
                    for j in range(len(LpInputs[-1])):
                        imgui.text("{:10.6f}".format(allRangesI[i][j]))
                        imgui.same_line()
                    imgui.push_style_color(imgui.COLOR_TEXT, 0.0, 1.0, 1.0)
                    imgui.text(f"   Input total: {allInputTotals[i]}")
                    imgui.pop_style_color()

                    imgui.push_style_color(imgui.COLOR_TEXT, 0.0, 1.0, 1.0)
                    imgui.text(f"\n\nTotals: {
                               allOutputTotals[i]} / {allInputTotals[i]} = {allOutputTotals[i] / allInputTotals[i]}")
                    imgui.pop_style_color()
                    imgui.spacing()
                    imgui.spacing()
                    imgui.spacing()
                    imgui.spacing()
            except:
                pass

            # close =============================

            imgui.end()

            imgui.render()
            impl.render(imgui.get_draw_data())

            pygame.display.flip()


def main(isConsoleOutput=False):
    classInstance = DEASolver(isConsoleOutput)
    classInstance.doGui()


if __name__ == "__main__":
    main(True)
