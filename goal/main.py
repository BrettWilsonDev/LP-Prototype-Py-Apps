import copy
import math

import sys
import pygame
import OpenGL.GL as gl
from imgui.integrations.pygame import PygameRenderer
import imgui
import os

gTab = []

def spaceGui(amt):
    for i in range(amt):
        imgui.spacing()

def GetInput():
    # penlites = [200, 100, 50]

    # # 0 is <= and 1 is >= and 2 is =
    # goalConstraints = [
    #     [7, 3, 40, 1],
    #     [10, 5, 60, 1],
    #     [5, 4, 35, 1],
    # ]

    # # 0 is <= and 1 is >= and 2 is =
    # constraints = [
    #     [100, 60, 600, 0],
    # ]

    penlites = []

    # 0 is <= and 1 is >= and 2 is =
    goalConstraints = [
        [400, 300, 250, 28000, 0],
        [60, 50, 40, 5000, 1],
        [20, 35, 20, 3000, 1],
        [20, 15, 40, 1000, 1],
    ]

    # 0 is <= and 1 is >= and 2 is =
    constraints = [
        # [100, 60, 600, 0],
    ]

    # return penlites, goalConstraints, constraints


def BuildFirstPenlitesTableau(penlites, goalConstraints, constraints):
    tabSizeH = len(constraints) + len(goalConstraints) + len(penlites)

    #          z  + rhs   +    x and x    +              penlites g- g+    +     slack
    tabSizeW = 1 + 1 + \
        (len(goalConstraints[-1]) - 2) + (len(penlites) * 2) + len(constraints)

    amtOfObjVars = (len(goalConstraints[-1]) - 2)
    tab = []

    # initialize table with empty rows
    for i in range(tabSizeH):
        tab.append([])

    # initialize table with zeros
    for i in range(tabSizeH):
        for j in range(tabSizeW):
            tab[i].append(0)

    # put in lhs in the z col
    for i in range(len(penlites)):
        tab[i][0] = 1

    # put in penlites
    gCtr = amtOfObjVars + 1
    for i in range(len(penlites)):
        tab[i][gCtr] = -1 * penlites[i]
        gCtr += 2

    # put in goal constraints
    for i in range(len(penlites), tabSizeH - len(constraints)):
        for j in range(1, amtOfObjVars + 1):
            tab[i][-1] = goalConstraints[i - len(penlites)][-2]
            tab[i][j] = goalConstraints[i - len(penlites)][j - 1]

    # put in normal constraints
    for i in range(tabSizeH - len(constraints), tabSizeH):
        for j in range(1, (len(constraints[-1]) - 2) + 1):
            tab[i][-1] = constraints[i - (tabSizeH - len(constraints))][-2]
            tab[i][j] = constraints[i - (tabSizeH - len(constraints))][j - 1]

    # put the 1 -1 for goal constraints in
    onesCtr = amtOfObjVars + 1
    for i in range(len(penlites), tabSizeH - len(constraints)):
        tab[i][onesCtr] = 1
        tab[i][onesCtr + 1] = -1
        # if onesCtr + 1 < len(tab[i]):
        #     tab[i][onesCtr + 1] = -1
        onesCtr += 2

    # put the 1 for normal constraints in the slack spots
    posOfSlack = (((len(penlites) * 2) + amtOfObjVars))
    onesCtr = 1
    for i in range(tabSizeH - len(constraints), tabSizeH):
        # print(posOfSlack)
        tab[i][posOfSlack + onesCtr] = 1
        onesCtr += 1

    # new calualted tab
    # newTab = tab.copy()
    newTab = copy.deepcopy(tab)

    # calculate the new table goal rows
    gCtr = len(goalConstraints)
    for i in range(len(penlites)):
        for j in range(len(tab[i])):
            newTab[i][j] = tab[i][j] + (tab[gCtr][j] * penlites[i])
        gCtr += 1

    conStart = len(penlites)

    for i in range(len(tab)):
        for j in range(len(tab[i])):
            print("{:10.3f}".format(tab[i][j]), end=" ")
        print()

    print()

    for i in range(len(newTab)):
        for j in range(len(newTab[i])):
            print("{:10.3f}".format(newTab[i][j]), end=" ")
        print()

    global gTab
    gTab.append(copy.deepcopy(tab))
    gTab.append(copy.deepcopy(newTab))

    return tab, newTab, conStart


def DoPivotOperations(tab, conStart, zRow, tabNum=1):
    # newTab = copy.deepcopy(tab)
    oldTab = copy.deepcopy(tab)
    newTab = []

    newTab = [[0 for _ in row] for row in oldTab]

    currentZRow = zRow
    currentZ = tab[currentZRow][:-1]
    # currentZ = currentZ[1:]
    currentZ[0] = 0

    # print(currentZ)

    # find the largest z and its index for the pivot col
    largestZ = max(currentZ)
    pivotCol = currentZ.index(largestZ)
    # print(f"pivot col is {pivotCol}")

    # find the pivot row
    useZero = False
    ratios = []
    for i in range(conStart, len(tab)):
        div = tab[i][pivotCol]
        if div == 0:
            ratios.append(float('inf'))
        else:
            ratios.append(tab[i][-1] / tab[i][pivotCol])

            if (tab[i][-1] / tab[i][pivotCol]) == 0 and ((tab[i][pivotCol]) == abs(tab[i][pivotCol])):
                # print("use the damm zero to pivot")
                useZero = True

    # print(ratios)

    if useZero:
        positiveRatios = [ratio for ratio in ratios if ratio >= 0]
    else:
        positiveRatios = [ratio for ratio in ratios if ratio > 0]

    pivotRow = ratios.index(min(positiveRatios))
    pivotRow += conStart
    # print(f"pivot row is {pivotRow}")

    divNumber = tab[pivotRow][pivotCol]
    # print(divNumber)

    # do the pivot division operations
    for i in range(len(tab)):
        for j in range(len(tab[i])):
            newTab[i][j] = oldTab[i][j] / divNumber

    # do the pivot operations
    # the formula: Element_New_Table((i, j)) = Element_Old_Table((i, j)) - (Element_Old_Table((i, Pivot_column)) * Element_New_Table((Pivot_Row, j)))
    for i in range(len(tab)):
        for j in range(len(tab[i])):
            if i == pivotRow:
                continue

            # print(f"{oldTab[i][j]} - ({oldTab[i][pivotCol]} * {newTab[pivotRow][j]}) = {oldTab[i][j] - (newTab[i][pivotCol] * oldTab[pivotRow][j])}")

            newTab[i][j] = oldTab[i][j] - \
                (oldTab[i][pivotCol] * newTab[pivotRow][j])

    newTab = [[0.0 if abs(val) < 1e-10 else val for val in sublist]
              for sublist in newTab]

    for items in newTab:
        for i, item in enumerate(items):
            if item == 0.0 and math.copysign(1, item) == -1:
                newTab[i][i] = abs(item)

    zRhs = []

    for i in range(conStart):
        zRhs.append(newTab[i][-1])

    print(f"pivoting on table {tabNum}\nIn row {
          pivotRow + 1} and col {pivotCol + 1 - 1}\n")
    
    
    # for i in range(len(newTab)):
    #     for j in range(len(newTab[i])):
    #         print("{:10.3f}".format(newTab[i][j]), end=" ")
    #     print()

    global gTab

    gTab.append(copy.deepcopy(newTab))

    return newTab, zRhs


def DoPenlites(penlites, goalConstraints, constraints):
    zRow = 0

    # penlites, goalConstraints, constraints = GetInput()

    tableaus = []

    metRhs = []

    fistTab, secondTab, conStart = BuildFirstPenlitesTableau(
        penlites, goalConstraints, constraints)
    tableaus.append(fistTab)
    tableaus.append(secondTab)

    tabNum = 1
    loopFlag = True
    while loopFlag:
        tab, zRhs = DoPivotOperations(tableaus[-1], conStart, zRow, tabNum)
        tableaus.append(tab)
        tabNum += 1

        if zRhs[zRow] == 0.0:
            metRhs.append(True)
            # metRhs[zRow] = True
            zRow += 1

        for i in range(len(metRhs)):
            if zRhs[i] == 0.0:
                metRhs[i] = True
            else:
                metRhs[i] = False

        for i in range(len(metRhs)):
            if i < zRow and metRhs[i] == False:
                loopFlag = False

        if tabNum > 100:
            return tableaus, tabNum

    if loopFlag == False:
        print(f"Tableau {tabNum} may be the optimal tableau\n")

    for i in range(len(tableaus)):
        print("Tableau {}".format(i + 1))
        for j in range(len(tableaus[i])):
            for k in range(len(tableaus[i][j])):
                print("{:10.3f}".format(tableaus[i][j][k]), end=" ")
            print()
        print()

    return tableaus, tabNum


def BuildFirstPreemptiveTableau(goalConstraints, constraints):
    tabSizeH = len(constraints) + len(goalConstraints) * 2
    tabSizeW = 1 + 1 + (len(goalConstraints) * 2) + \
        len(constraints) + (len(goalConstraints[-1]) - 2)

    penlites = len(goalConstraints)

    amtOfObjVars = (len(goalConstraints[-1]) - 2)

    tab = []

    # initialize table with empty rows
    for i in range(tabSizeH):
        tab.append([])

    # initialize table with zeros
    for i in range(tabSizeH):
        for j in range(tabSizeW):
            tab[i].append(0)

    # put in lhs in the z col
    for i in range(penlites):
        tab[i][0] = 1

    # print(goalConstraints)

    # # put in penlites
    gCtr = amtOfObjVars + 1
    for i in range(len(goalConstraints)):
        if goalConstraints[i][-1] == 0:
            tab[i][gCtr + 1] = -1
        else:
            tab[i][gCtr] = -1
        gCtr += 2

    # put in goal constraints
    for i in range(penlites, tabSizeH - len(constraints)):
        for j in range(1, amtOfObjVars + 1):
            tab[i][-1] = goalConstraints[i - penlites][-2]
            tab[i][j] = goalConstraints[i - penlites][j - 1]

    # put in normal constraints
    for i in range(tabSizeH - len(constraints), tabSizeH):
        for j in range(1, (len(constraints[-1]) - 2) + 1):
            tab[i][-1] = constraints[i - (tabSizeH - len(constraints))][-2]
            tab[i][j] = constraints[i - (tabSizeH - len(constraints))][j - 1]

    # put the 1 -1 for goal constraints in
    onesCtr = amtOfObjVars + 1
    for i in range(penlites, tabSizeH - len(constraints)):
        tab[i][onesCtr] = 1
        tab[i][onesCtr + 1] = -1
        onesCtr += 2

    # make new tab
    newTab = copy.deepcopy(tab)

    gCtr = len(goalConstraints)
    for i in range(penlites):
        for j in range(len(tab[i])):
            if goalConstraints[i][-1] == 0:
                newTab[i][j] = tab[i + penlites][j] - tab[i][j]
            elif goalConstraints[i][-1] == 1:
                newTab[i][j] = tab[i + penlites][j] + tab[i][j]
        gCtr += 1

    for i in range(len(tab)):
        for j in range(len(tab[i])):
            print("{:10.3f}".format(tab[i][j]), end=" ")
        print()

    print()

    # for i in range(len(newTab)):
    #     for j in range(len(newTab[i])):
    #         print("{:10.3f}".format(newTab[i][j]), end=" ")
    #     print()

    global gTab
    gTab.append(copy.deepcopy(tab))
    gTab.append(copy.deepcopy(newTab))

    return tab, newTab, penlites


def DoPreemptive(penlites, goalConstraints, constraints):
    zRow = 0

    tableaus = []

    metRhs = []

    # penlites, goalConstraints, constraints = GetInput()
    firstTab, secondTab, conStart = BuildFirstPreemptiveTableau(
        goalConstraints, constraints)
    tableaus.append(firstTab)
    tableaus.append(secondTab)

    tabNum = 1
    loopFlag = True
    while loopFlag:
        tab, zRhs = DoPivotOperations(tableaus[-1], conStart, zRow, tabNum)
        tableaus.append(tab)
        tabNum += 1

        # print(goalConstraints[zRow][-1])
        if goalConstraints[zRow][-1] == 0:
            if zRhs[zRow] <= goalConstraints[zRow][-2]:
                # print(zRhs[zRow])
                # print("met")
                zRow += 1
        else:
            if zRhs[zRow] == 0.0:
                metRhs.append(True)
                # metRhs[zRow] = True
                zRow += 1

        for i in range(len(metRhs)):
            if goalConstraints[i][-1] == 0:
                if zRhs[i] <= goalConstraints[i][-2]:
                    metRhs[i] = True
                elif zRhs[i] > goalConstraints[i][-2]:
                    metRhs[i] = False

        for i in range(len(metRhs)):
            if zRhs[i] == 0.0:
                metRhs[i] = True
            else:
                metRhs[i] = False

        for i in range(len(metRhs)):
            if i < zRow and metRhs[i] == False:
                loopFlag = False

        if tabNum > 100:
            return tableaus, tabNum

    if loopFlag == False:
        print(f"Tableau {tabNum} may be the optimal tableau\n")

    # for i in range(len(tableaus)):
    #     print("Tableau {}".format(i + 1))
    #     for j in range(len(tableaus[i])):
    #         for k in range(len(tableaus[i][j])):
    #             print("{:10.3f}".format(tableaus[i][j][k]), end=" ")
    #         print()
    #     print()

    return tableaus, tabNum


def DoGui():
    pygame.init()
    size = 1920 / 2, 1080 / 2
    
    os.system('cls' if os.name == 'nt' else 'clear')
    print("\nBrett's simplex prototype tool for goal simplex problems\n")

    pygame.display.set_mode(size, pygame.DOUBLEBUF |
                            pygame.OPENGL | pygame.RESIZABLE)

    pygame.display.set_caption("Goal Simplex Prototype")

    icon = pygame.Surface((1, 1)).convert_alpha()
    icon.fill((0, 0, 0, 1))
    pygame.display.set_icon(icon)

    imgui.create_context()
    impl = PygameRenderer()

    io = imgui.get_io()
    io.display_size = size

    # tableaus = [[[1.234, 2.345, 3.456], [4.567, 5.678, 6.789]],
    #             [[7.890, 8.901, 9.012], [1.123, 2.234, 3.345]]]

    # problemType = "Max"

    # penlites
    goalType = "Penalties"
    # values = [0.0, 0.0, 0.0, 0.0, 0.0]
    amtOfPenalties = 1
    penlites = [0.0]

    # goal constraints
    amtOfObjVars = 2

    # goal constraints
    amtOfGoalConstraints = 1
    goalConstraints = [[0.0, 0.0, 0.0, 0.0]] 
    signItems = ["<=", ">="]
    signItemsChoices = [0]

    # goal constraints
    amtOfConstraints = 0
    # constraints = [[0.0, 0.0, 0.0, 0.0]] 
    constraints = [] 
    signItemsChoicesC = [0]

    tableaus = [[[0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0]],]

    while 1:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()

            impl.process_event(event)

        imgui.new_frame()

        # imgui.show_test_window()

        window_size = pygame.display.get_window_size()

        imgui.set_next_window_position(0, 0)  # Set the window position
        imgui.set_next_window_size(
            (window_size[0]), (window_size[1]))  # Set the window size
        imgui.begin("Tableaus Output",
                    flags=imgui.WINDOW_NO_TITLE_BAR | imgui.WINDOW_NO_RESIZE)

        # Display the radio buttons
        if imgui.radio_button("Penalties", goalType == "Penalties"):
            goalType = "Penalties"

        if imgui.radio_button("Preemptive", goalType == "Preemptive"):
            goalType = "Preemptive"

        imgui.text("Problem is: {}".format(goalType))

        spaceGui(6)

        # if imgui.radio_button("Max", problemType == "Max"):
        #     problemType = "Max"

        # if imgui.radio_button("Min", problemType == "Min"):
        #     problemType = "Min"

        # imgui.text("Problem is: {}".format(problemType))
        
        # penalties ==========================================
        if goalType == "Penalties":
            if imgui.button("Penalties +"):
                amtOfPenalties += 1
                penlites.append(0.0)

            imgui.same_line()

            if imgui.button("Penalties -"):
                if len(penlites) != 1:
                    amtOfPenalties += -1
                    penlites.pop()

            imgui.spacing()
            for i in range(amtOfPenalties):
                value = penlites[i]
                imgui.set_next_item_width(50)
                imgui.same_line()
                changed, penlites[i] = imgui.input_float(
                    "penalty {}".format(i + 1), value)

                if changed:
                    # Value has been updated
                    pass

        spaceGui(6)

        # imgui.text("Values:")
        # for i, value in enumerate(penlites):
        #     imgui.text("{:<10}{:.2f}".format("Value {}".format(i + 1), value))

        # obj vars ===========================================
        if imgui.button("decision variables +"):
            amtOfObjVars += 1
            for i in range(len(goalConstraints)):
                goalConstraints[i].append(0.0)

        imgui.same_line()

        if imgui.button("decision variables -"):
            if amtOfObjVars != 2:
                amtOfObjVars += -1
                for i in range(len(goalConstraints)):
                    goalConstraints[i].pop()

        spaceGui(3)


        # goal constraints ===========================================
        if imgui.button("GoalConstraint +"):
            amtOfGoalConstraints += 1
            # goalConstraints.append([0.0, 0.0])
            goalConstraints.append([0.0] * amtOfObjVars)
            goalConstraints[-1].append(0.0) # add sign spot
            goalConstraints[-1].append(0.0) # add rhs spot
            signItemsChoices.append(0)

        imgui.same_line()

        if imgui.button("GoalConstraint -"):
            if amtOfGoalConstraints != 1:
                amtOfGoalConstraints += -1
                goalConstraints.pop()
                signItemsChoices.pop()

        # spaceGui(3)

        imgui.spacing()
        for i in range(amtOfGoalConstraints):
            imgui.spacing()
            if len(goalConstraints) <= i:
                # Fill with default values if needed
                goalConstraints.append([0.0] * (amtOfObjVars + 2))

            for j in range(amtOfObjVars):
                value = goalConstraints[i][j]
                imgui.set_next_item_width(50)
                imgui.same_line()
                changed, xValue = imgui.input_float(
                    "x{}{}".format(i, j), value)
                if changed:
                    goalConstraints[i][j] = xValue

            imgui.same_line()  
            imgui.push_item_width(50)
            changed, selectedItemSign = imgui.combo("combo{}{}".format(i, j), signItemsChoices[i], signItems)
            if changed:
                signItemsChoices[i] = selectedItemSign
                goalConstraints[i][-1] = signItemsChoices[i]

            imgui.pop_item_width()
            imgui.same_line()   
            imgui.set_next_item_width(50)
            rhsValue = goalConstraints[i][-2]
            rhsChanged, rhs = imgui.input_float(
                "RHS{}{}".format(i, j), rhsValue)
                
            if rhsChanged:
                goalConstraints[i][-2] = rhs 

        spaceGui(6)


        # normal constraints ===========================================
        if len(constraints) == 0:
            pass

        if imgui.button("Constraint +"):
            amtOfConstraints += 1
            # goalConstraints.append([0.0, 0.0])
            constraints.append([0.0] * amtOfObjVars)
            constraints[-1].append(0.0) # add sign spot
            constraints[-1].append(0.0) # add rhs spot
            signItemsChoicesC.append(0)

        imgui.same_line()

        if len(constraints) != 0:
            if imgui.button("Constraint -"):
                if amtOfConstraints != 0:
                    amtOfConstraints += -1
                    constraints.pop()
                    signItemsChoicesC.pop()

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
                changed, selectedItemSignC = imgui.combo("comboC{}{}".format(i, j), signItemsChoicesC[i], signItems)
                if changed:
                    signItemsChoicesC[i] = selectedItemSignC
                    constraints[i][-1] = signItemsChoicesC[i]

                imgui.pop_item_width()
                imgui.same_line()   
                imgui.set_next_item_width(50)
                rhsValue = constraints[i][-2]
                rhsChanged, rhs = imgui.input_float(
                    "RHSC{}{}".format(i, j), rhsValue)
                    
                if rhsChanged:
                    constraints[i][-2] = rhs 

        spaceGui(6)
        if imgui.button("Solve"):
            goalConstraints = [
                [400, 300, 250, 28000, 0],
                [60, 50, 40, 5000, 1],
                [20, 35, 20, 3000, 1],
                [20, 15, 40, 1000, 1],
            ]
            # tableaus = DoPreemptive([], goalConstraints, constraints)
            global gTab
            try:
                if goalType == "Penalties":
                    tableaus = DoPenlites(penlites, goalConstraints, constraints)
                else:
                    print(len(gTab))
                    print([], goalConstraints, constraints)
                    tableaus = DoPreemptive([], goalConstraints, constraints)
                    # print(len(tableaus))
                    # print(tableaus)
            #     # table print =================================================
            except Exception as e:
                print("math error:", e) 
            #     imgui.spacing()
            #     imgui.text(f"Math Error: {e}")

            # for i in range(len(gTab)):
            #     print("Tableau {}".format(i + 1))
            for j in range(len(gTab[i])):
                for k in range(len(gTab[i][j])):
                    print("{:10.3f}".format(gTab[i][j][k]), end=" ")
                print()
            print()


            # penlites = []

            # # 0 is <= and 1 is >= and 2 is =
            # goalConstraints = [
            #     [400, 300, 250, 28000, 0],
            #     [60, 50, 40, 5000, 1],
            #     [20, 35, 20, 3000, 1],
            #     [20, 15, 40, 1000, 1],
            # ]

            # # 0 is <= and 1 is >= and 2 is =
            # constraints = [
            #     # [100, 60, 600, 0],
            # ]

            # print(goalConstraints)
            # print(penlites, goalConstraints, constraints)
            # # print(penlites, goalConstraints)
            # if goalType == "Penalties":
            #     tableaus = DoPenlites(penlites, goalConstraints, constraints)
            #     print(tableaus)
            # else:
            #     tableaus = DoPreemptive([], goalConstraints, constraints)
            #     print(len(tableaus))
            #     print(tableaus)

            # print()

            # try:
            #     if goalType == "Penalties":
            #         tableaus = DoPenlites(penlites, goalConstraints, constraints)
            #         print(tableaus)
            #     else:
            #         tableaus = DoPreemptive([], goalConstraints, constraints)
            #         print(len(tableaus))
            #         # print(tableaus)
            #     # table print =================================================
            # except Exception as e:
            #     # print("math error", e) 
            #     imgui.spacing()
            #     imgui.text(f"Math Error {e}")
            
        # imgui.spacing()
        # for i in range(len(tableaus)):
        #     imgui.text("Tableau {}".format(i + 1))
        #     for j in range(len(tableaus[i])):
        #         for k in range(len(tableaus[i][j])):
        #             imgui.text("{:10.3f}".format(tableaus[i][j][k]))
        #             imgui.same_line()
        #         imgui.new_line()

        # try:
        #     if goalType == "Penalties":
        #         tableaus = DoPenlites(penlites, goalConstraints, constraints)
        #     else:
        #         tableaus = DoPreemptive([], goalConstraints, constraints)

        #     imgui.spacing()
        #     # table print =================================================
        #     for i in range(len(tableaus)):
        #         imgui.text("Tableau {}".format(i + 1))
        #         for j in range(len(tableaus[i])):
        #             for k in range(len(tableaus[i][j])):
        #                 imgui.text("{:10.3f}".format(tableaus[i][j][k]))
        #                 imgui.same_line()
        #             imgui.new_line()
        # except Exception as e:
        #     # print("math error", e) 
        #     imgui.spacing()
        #     imgui.text(f"Math Error {e}")

        # imgui.spacing()
        # # table print =================================================
        # for i in range(len(tableaus)):
        #     imgui.text("Tableau {}".format(i + 1))
        #     for j in range(len(tableaus[i])):
        #         for k in range(len(tableaus[i][j])):
        #             imgui.text("{:10.3f}".format(tableaus[i][j][k]))
        #             imgui.same_line()
        #         imgui.new_line()

        imgui.end()

        # gl stuff
        gl.glClearColor(0, 0, 0, 1)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        imgui.render()
        impl.render(imgui.get_draw_data())

        pygame.display.flip()

def main():
    DoGui()

    # DoPenlites()
    # DoPreemptive()
main()
