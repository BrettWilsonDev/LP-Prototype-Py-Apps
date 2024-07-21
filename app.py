import imgui
from imgui.integrations.glfw import GlfwRenderer
import glfw

try:
    # for the exe all files are in root
    from addingactscons import AddingActsCons
    from deasolver import DEASolver
    from dualsimplex import DualSimplex
    from lpduality import LPDuality
    from penaltiessimplex import PenaltiesSimplex
    from preemptivesimplex import PreemptiveSimplex
    from graphicalsolver import GraphicalSolver
    from mathpreliminaries import MathPreliminaries
    from twophasesimplex import TwoPhaseSimplex
except:
    try:
        from LPSolverTools.addingActsCons.addingactscons import AddingActsCons
        from LPSolverTools.DEA.deasolver import DEASolver
        from LPSolverTools.dual.dualsimplex import DualSimplex
        from LPSolverTools.duality.lpduality import LPDuality
        from LPSolverTools.goal.penaltiessimplex import PenaltiesSimplex
        from LPSolverTools.goal.preemptivesimplex import PreemptiveSimplex
        from LPSolverTools.graphicalSolver.graphicalsolver import GraphicalSolver
        from LPSolverTools.mathPrelim.mathpreliminaries import MathPreliminaries
        from LPSolverTools.twoPhase.twophasesimplex import TwoPhaseSimplex
    except:
        print("Could not import modules")


class App:
    def __init__(self):
        # initialize tools
        self.addingActsCons = AddingActsCons()
        self.deaSolver = DEASolver()
        self.dualSimplex = DualSimplex()
        self.lPDuality = LPDuality()
        self.penaltiesSimplex = PenaltiesSimplex()
        self.preemptiveSimplex = PreemptiveSimplex()
        self.graphicalSolver = GraphicalSolver()
        self.mathPreliminaries = MathPreliminaries()
        self.twoPhaseSimplex = TwoPhaseSimplex()

        self.currentTool = 0

        self.paddingTop = 18

        self.buttonLabels = [
            "Menu", "Adding Acts, Cons", "DEA Solver",
            "Dual Simplex", "Duality", "Goal Penalties",
            "Goal Preemptive", "Graphical Solver",
            "Preliminaries", "Two Phase Simplex", "Help"
        ]

        self.originalButtonColor = ()
        self.hoveredButtonColor = ()
        self.selectedButtonColor = ()
        self.activeButtonColor = ()

        self.toolUIs = {
            0: self.imguiMainMenu,
            1: self.addingActsCons.imguiUIElements,
            2: self.deaSolver.imguiUIElements,
            3: self.dualSimplex.imguiUIElements,
            4: self.lPDuality.imguiUIElements,
            5: self.penaltiesSimplex.imguiUIElements,
            6: self.preemptiveSimplex.imguiUIElements,
            7: self.graphicalSolver.imguiUIElements,
            8: self.mathPreliminaries.imguiUIElements,
            9: self.twoPhaseSimplex.imguiUIElements,
            10: self.imguiHelpMenu
        }

    def imguiMainMenu(self, windowSize, windowPosX=0, windowPosY=0):
        imgui.set_next_window_position(
            windowPosX, windowPosY)  # Set the window position
        imgui.set_next_window_size(
            (windowSize[0]), (windowSize[1]))  # Set the window size
        imgui.begin("Main Menu",
                    flags=imgui.WINDOW_NO_TITLE_BAR | imgui.WINDOW_NO_RESIZE)

        imgui.text(
            "Welcome To Linier Programming Tool Prototypes!\nBy Brett Wilson")

        imgui.spacing()
        imgui.spacing()
        for i in range(1, len(self.buttonLabels)):
            imgui.spacing()
            imgui.spacing()
            if imgui.button(self.buttonLabels[i]):
                self.currentTool = i

        imgui.spacing()
        imgui.spacing()
        imgui.text("See Help for more info!")

        imgui.end()

    def imguiHelpMenu(self, windowSize, windowPosX=0, windowPosY=0):
        imgui.set_next_window_position(
            windowPosX, windowPosY)  # Set the window position
        imgui.set_next_window_size(
            (windowSize[0]), (windowSize[1]))  # Set the window size
        imgui.begin("Help Menu",
                    # flags=imgui.WINDOW_NO_TITLE_BAR | imgui.WINDOW_NO_RESIZE | imgui.WINDOW_ALWAYS_HORIZONTAL_SCROLLBAR)
                    flags=imgui.WINDOW_NO_TITLE_BAR | imgui.WINDOW_NO_RESIZE | imgui.WINDOW_ALWAYS_HORIZONTAL_SCROLLBAR )
        imgui.begin_child("Scrollable Child", width=0, height=0,
                          border=True, flags=imgui.WINDOW_ALWAYS_HORIZONTAL_SCROLLBAR)

        imgui.text("LP Tool by Brett Wilson: Github.com/brettwilsonbdw")

        helpTextInput = (
            "In the Input:\n\n"
            "Click on the boxes and enter values.\n\n"
            "Objective Variables: x1, x2, x3, etc. are your objective variables (also known as decision variables). Both decision variables and constraints can be increased or decreased using their respective '+' and '-' buttons.\n\n"
            "Constraints also use x1, x2, x3, etc. Align their respective values with the objective variables. Use the drop-down box to select the constraint type (<=, >=).\n\n"
            "Use the radio buttons to choose between 'Maximize' or 'Minimize'.\n\n"
            "Click 'Solve' to run the solver.\n\n"
            "Click 'Reset' to clear all inputs.\n\n"
            "If no output appears, check if your input is correct. Most likely, an error in the input is causing the issue."
        )
        imgui.spacing()
        imgui.spacing()
        imgui.spacing()
        imgui.spacing()
        imgui.separator()
        imgui.text(helpTextInput)

        helpTextOutput = (
            "In the output:\n\n"
            "The header will have:\n"
            "- 'x' for objective values\n"
            "- 's' for slack\n"
            "- 'e' for excess\n"
            "- 'rhs' for right-hand side values\n\n"
            "For the columns:\n"
            "- 'c' represents constraints with the constraint number\n"
            "- 'z' represents the objective row\n\n"
            "The optimal tableau will have the words optimal tableau or be the last tableau.\n\n"
            "The optimal value is in the top right corner of each tableau under rhs.\n\n"
            "The pivot row and column will be highlighted.\n\n"
        )
        imgui.spacing()
        imgui.spacing()
        imgui.spacing()
        imgui.spacing()
        imgui.separator()
        imgui.text(helpTextOutput)

        helpTextExtra = (
            "Extras:\n\n"
            "For Goal Simplex:\n"
            "The header will include 'g-' and 'g+' indicating the goal with its number.\n"
            "There is also a 'Show Goal Order' button that allows you to rearrange the goals from top to bottom, indicating their importance from most to least important.\n\n"
            "In Duality:\n"
            "There will be an extra 'slack' column and a 'ref' column. The 'ref' column can be safely ignored, based on the Excel Solver way of showing results.\n\n"
            "In DEA (Data Envelopment Analysis):\n"
            "The 'ref' column can be safely ignored, similar to Duality.\n\n"
            "In Adding Acts and Cons:\n"
            "'Acts' stands for activities (e.g., x1, x2) and 'cons' stands for constraints there is a radio button to select each. There is an 'Abs On/Off' radio button to force the underlying initial tableau to be all positive.\n\n"
            "In Mathematical Preliminaries:\n"
            "The 'Abs' radio button is also present, allowing the same functionality as in Adding Acts and Cons. Additionally, there is a 'Lock Tab' radio button to prevent the table from automatically being the most optimal, enabling some sensitivity analysis from the first table input.\n\n"
            "In both Adding Acts/Cons and Mathematical Preliminaries:\n"
            "There is an 'Optimize' button which will re-solve the current adjusted table to be optimal.\n\n"
            "In Mathematical Preliminaries:\n"
            "You can enter values with the words '+d' for delta. This will perform algebraic calculations and display the results in each respective part. There is also a 'Solve Delta' radio button to compute the delta for the RHS equation in the changing table.\n\n"
            "For Constraints:\n"
            "Most tools do not have an '=' option in the drop-down. Instead, you must create two constraints for an '=' constraint: one as '>=' and the other as '<='. There is no need to adjust positive and negative signs."
        )
        imgui.spacing()
        imgui.spacing()
        imgui.spacing()
        imgui.spacing()
        imgui.separator()
        imgui.text(helpTextExtra)

        imgui.end_child()
        imgui.end()

    def DoGui(self):
        # Initialize GLFW
        if not glfw.init():
            print("Could not initialize OpenGL context")
            return

        # Create a windowed mode window and its OpenGL context
        window = glfw.create_window(
            1280, 720, "Linier Programming Tool Prototypes", None, None)
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

            windowSize = glfw.get_window_size(window)

            imgui.new_frame()

            style = imgui.get_style()

            self.originalButtonColor = style.colors[imgui.COLOR_BUTTON]
            self.hoveredButtonColor = style.colors[imgui.COLOR_BUTTON_HOVERED]
            self.selectedButtonColor = style.colors[imgui.COLOR_BUTTON_ACTIVE]
            self.activeButtonColor = style.colors[imgui.COLOR_BUTTON_ACTIVE]

            style.colors[imgui.COLOR_BUTTON] = self.originalButtonColor
            style.colors[imgui.COLOR_BUTTON_HOVERED] = self.hoveredButtonColor
            style.colors[imgui.COLOR_BUTTON_ACTIVE] = self.selectedButtonColor

            if imgui.begin_main_menu_bar():

                for i, label in enumerate(self.buttonLabels):
                    if i == self.currentTool:
                        style.colors[imgui.COLOR_BUTTON] = self.activeButtonColor
                    else:
                        style.colors[imgui.COLOR_BUTTON] = self.originalButtonColor

                    if imgui.button(label):
                        self.currentTool = i

                style.colors[imgui.COLOR_BUTTON] = self.originalButtonColor

                imgui.end_main_menu_bar()

            # set the tool UI to display
            if self.currentTool in self.toolUIs:
                self.toolUIs[self.currentTool](windowSize, 0, self.paddingTop)

            # Rendering
            imgui.render()
            impl.render(imgui.get_draw_data())
            glfw.swap_buffers(window)

        # Cleanup
        impl.shutdown()
        glfw.terminate()


def main():
    app = App()
    app.DoGui()


if __name__ == "__main__":
    main()
