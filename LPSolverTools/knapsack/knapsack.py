import heapq
from typing import List, Tuple, Dict
import copy

class KnapsackItem:
    def __init__(self, index: int, value: int, weight: int):
        self.index = index
        self.value = value
        self.weight = weight
        self.ratio = value / weight
        self.name = f"x{index + 1}"

class KnapsackNode:
    def __init__(self, level: int, profit: float, weight: int, bound: float, 
                 fixedVariables: Dict[int, int] = None, parent=None):
        self.level = level
        self.profit = profit
        self.weight = weight
        self.bound = bound
        self.fixedVariables = fixedVariables or {}
        self.parent = parent
        self.children = []
        
    def __lt__(self, other):
        return self.bound > other.bound  # For max heap behavior

class BranchAndBoundKnapsack:
    def __init__(self, values: List[int], weights: List[int], capacity: int):
        self.values = values
        self.weights = weights
        self.capacity = capacity
        self.items = [KnapsackItem(i, values[i], weights[i]) for i in range(len(values))]
        self.bestValue = 0
        self.bestSolution = [0] * len(values)
        self.nodeCounter = 0
        # Define branching order based on ratio ranking
        sortedByRatio = sorted(range(len(values)), key=lambda i: values[i]/weights[i], reverse=True)
        self.branchingOrder = sortedByRatio  # Branch in order of ratio ranking
        
    def displayRatioTest(self):
        print("Branch & Bound Algorithm - Knapsack Method")
        print("Ratio Test")
        print("Item   z_i/c_i   Rank")
        
        # Sort items by ratio in descending order for ranking
        sortedItems = sorted(self.items, key=lambda x: x.ratio, reverse=True)
        rankMap = {item.index: rank + 1 for rank, item in enumerate(sortedItems)}
        
        for item in self.items:
            print(f"{item.name}    {item.value}/{item.weight} = {item.ratio:.3f}    {rankMap[item.index]}")
        print()
        
        return sortedItems
    
    def calculateUpperBound(self, node: KnapsackNode, sortedItems: List[KnapsackItem]) -> float:
        remainingCapacity = self.capacity - node.weight
        upperBound = node.profit
        
        for item in sortedItems:
            if item.index in node.fixedVariables:
                continue
                
            if remainingCapacity >= item.weight:
                remainingCapacity -= item.weight
                upperBound += item.value
            else:
                # Fractional part
                if remainingCapacity > 0:
                    upperBound += (remainingCapacity / item.weight) * item.value
                break
                
        return upperBound
    
    def displaySubProblem(self, node: KnapsackNode, sortedItems: List[KnapsackItem], 
                         subProblemNumber: str, isRoot: bool = False):
        if subProblemNumber:
            print(f"Sub-Problem {subProblemNumber}")
        else:
            print("Sub-Problem")
        
        remainingCapacity = self.capacity
        totalValue = 0
        
        # Display fixed variables first in order
        fixedItems = set()
        for itemIndex in sorted(node.fixedVariables.keys()):
            value = node.fixedVariables[itemIndex]
            item = self.items[itemIndex]
            if value == 1:
                print(f"* {item.name} = {value}    {remainingCapacity}-{item.weight}={remainingCapacity - item.weight}")
                remainingCapacity -= item.weight
                totalValue += item.value
                fixedItems.add(itemIndex)
            elif value == 0:
                print(f"* {item.name} = {value}    {remainingCapacity}-0={remainingCapacity}")
                fixedItems.add(itemIndex)
        
        # Display remaining items based on greedy selection (sorted by ratio)
        for item in sortedItems:
            if item.index in fixedItems:
                continue
                
            if remainingCapacity >= item.weight:
                print(f"{item.name} = 1    {remainingCapacity}-{item.weight}={remainingCapacity - item.weight}")
                remainingCapacity -= item.weight
                totalValue += item.value
            elif remainingCapacity > 0:
                fractional_display = f"{remainingCapacity}/{item.weight}"
                print(f"{item.name} = {fractional_display}    {remainingCapacity}-{item.weight}")
                totalValue += (remainingCapacity / item.weight) * item.value
                remainingCapacity = 0
            else:
                print(f"{item.name} = 0")
        
        print()
        return totalValue
    
    def displayIntegerModel(self):
        print("Integer Programming Model")
        valueStr = " + ".join([f"{self.values[i]}x{i+1}" for i in range(len(self.values))])
        print(f"max z = {valueStr}")
        
        weightStr = " + ".join([f"{self.weights[i]}x{i+1}" for i in range(len(self.weights))])
        print(f"s.t {weightStr} ≤ {self.capacity}")
        print("xi = 0 or 1")
        print()
    
    def isFeasible(self, node: KnapsackNode) -> bool:
        return node.weight <= self.capacity
    
    def isComplete(self, node: KnapsackNode) -> bool:
        return len(node.fixedVariables) == len(self.items)
    
    def getNextVariableToBranch(self, node: KnapsackNode, sortedItems: List[KnapsackItem]) -> int:
        """Get the next variable to branch on - prioritize fractional variables"""
        # First, find fractional variables in the current LP relaxation solution
        remainingCapacity = self.capacity - node.weight
        
        for item in sortedItems:
            if item.index in node.fixedVariables:
                continue
                
            if remainingCapacity >= item.weight:
                remainingCapacity -= item.weight
            elif remainingCapacity > 0:
                # This variable is fractional - branch on it
                return item.index
            else:
                break
        
        # If no fractional variables, pick the next unfixed variable in ratio order
        for varIndex in self.branchingOrder:
            if varIndex not in node.fixedVariables:
                return varIndex
        return None
    
    def _isIntegerRelaxation(self, node, sortedItems):
        remainingCapacity = self.capacity - node.weight
        for item in sortedItems:
            if item.index in node.fixedVariables:
                continue
            if remainingCapacity >= item.weight:
                remainingCapacity -= item.weight
            elif remainingCapacity > 0:
                return False  # fractional
            else:
                pass
        # Fill greedy completion
        newFixedVars = node.fixedVariables.copy()
        remainingCapacity = self.capacity - node.weight
        newProfit = node.profit
        for item in sortedItems:
            if item.index in newFixedVars:
                continue
            if remainingCapacity >= item.weight:
                newFixedVars[item.index] = 1
                remainingCapacity -= item.weight
                newProfit += item.value
            else:
                newFixedVars[item.index] = 0
        node.fixedVariables = newFixedVars
        node.profit = newProfit
        return True

    
    def solveRecursive(self, node: KnapsackNode, sortedItems: List[KnapsackItem], 
                    nodeLabel: str = "", candidateCounter: List[int] = None):
        """Recursive branch and bound solver with proper integer detection and candidate logging."""
        if candidateCounter is None:
            candidateCounter = [0]
            
        if not self.isFeasible(node):
            print("Infeasible\n")
            return
            
        # If node is explicitly complete
        if self.isComplete(node):
            self._finalizeCandidate(node, candidateCounter)
            return
        
        # Check if LP relaxation is already integer (implicit completeness)
        remainingCapacity = self.capacity - node.weight
        fractional_found = False
        for item in sortedItems:
            if item.index in node.fixedVariables:
                continue
            if remainingCapacity >= item.weight:
                remainingCapacity -= item.weight
            elif remainingCapacity > 0:
                fractional_found = True
                break
            else:
                pass
        
        if not fractional_found:
            # Fill unfixed items with 0/1 according to greedy fill
            newFixedVars = node.fixedVariables.copy()
            remainingCapacity = self.capacity - node.weight
            newProfit = node.profit
            for item in sortedItems:
                if item.index in newFixedVars:
                    continue
                if remainingCapacity >= item.weight:
                    newFixedVars[item.index] = 1
                    remainingCapacity -= item.weight
                    newProfit += item.value
                else:
                    newFixedVars[item.index] = 0
            node.fixedVariables = newFixedVars
            node.profit = newProfit
            
            # Finalize as candidate BEFORE bound pruning
            self._finalizeCandidate(node, candidateCounter)
            return
        
        # Calculate bound AFTER integer check
        node.bound = self.calculateUpperBound(node, sortedItems)
        if node.bound <= self.bestValue:
            print("Bound exceeded, pruned\n")
            return
        
        # Get next variable to branch on
        nextVarIndex = self.getNextVariableToBranch(node, sortedItems)
        if nextVarIndex is None:
            return
        
        # Determine branch labels
        if nodeLabel == "":
            childLabels = ["1", "2"]
            branchDisplay = f"Sub-P 1: x{nextVarIndex + 1} = 0    Sub-P 2: x{nextVarIndex + 1} = 1"
        else:
            childLabels = [f"{nodeLabel}.1", f"{nodeLabel}.2"]
            branchDisplay = f"Sub-P {nodeLabel}.1: x{nextVarIndex + 1} = 0    Sub-P {nodeLabel}.2: x{nextVarIndex + 1} = 1"
        
        print(branchDisplay)
        
        # Process both branches
        for i, branchValue in enumerate([0, 1]):
            newFixedVars = node.fixedVariables.copy()
            newFixedVars[nextVarIndex] = branchValue
            newWeight = node.weight
            newProfit = node.profit
            if branchValue == 1:
                newWeight += self.items[nextVarIndex].weight
                newProfit += self.items[nextVarIndex].value
            
            newNode = KnapsackNode(node.level + 1, newProfit, newWeight, 0, newFixedVars, node)
            currentLabel = childLabels[i]
            self.displaySubProblem(newNode, sortedItems, f"Sub-P {currentLabel}")
            
            if not self.isFeasible(newNode):
                print("Infeasible\n")
            else:
                if self._isIntegerRelaxation(newNode, sortedItems):
                    self._finalizeCandidate(newNode, candidateCounter)
                    continue  # don’t branch further

                newNode.bound = self.calculateUpperBound(newNode, sortedItems)
                if newNode.bound <= self.bestValue:
                    print("Bound exceeded, pruned\n")
                else:
                    self.solveRecursive(newNode, sortedItems, currentLabel, candidateCounter)


    def _finalizeCandidate(self, node, candidateCounter):
        """Helper to log and store a candidate solution."""
        selectedItems = [i for i in range(len(self.items)) if node.fixedVariables.get(i, 0) == 1]
        if selectedItems:
            valueTerms = [str(self.values[i]) for i in selectedItems]
            print(f"z = {' + '.join(valueTerms)} = {int(node.profit)}")
        else:
            print(f"z = 0")
        candidateCounter[0] += 1
        candidateLetter = chr(65 + candidateCounter[0] - 1)
        print(f"Candidate {candidateLetter}")
        if node.profit > self.bestValue:
            self.bestValue = node.profit
            self.bestSolution = [node.fixedVariables.get(i, 0) for i in range(len(self.items))]
            print("Best Candidate")
        print()


    # no no

    def _finalizeCandidate(self, node, candidateCounter):
        """Helper to print and store a candidate solution."""
        selectedItems = [i for i in range(len(self.items)) if node.fixedVariables.get(i, 0) == 1]
        if selectedItems:
            valueTerms = [str(self.values[i]) for i in selectedItems]
            print(f"z = {' + '.join(valueTerms)} = {int(node.profit)}")
        else:
            print(f"z = 0")
        candidateCounter[0] += 1
        candidateLetter = chr(65 + candidateCounter[0] - 1)
        print(f"Candidate {candidateLetter}")
        if node.profit > self.bestValue:
            self.bestValue = node.profit
            self.bestSolution = [node.fixedVariables.get(i, 0) for i in range(len(self.items))]
            print("Best Candidate")
        print()


    
    def solve(self):
        print("=" * 60)
        sortedItems = self.displayRatioTest()
        self.displayIntegerModel()
        
        # Initialize root node
        rootNode = KnapsackNode(0, 0, 0, 0)
        rootNode.bound = self.calculateUpperBound(rootNode, sortedItems)
        
        # Display root problem
        self.displaySubProblem(rootNode, sortedItems, "", True)
        
        # Start recursive solving
        candidateCounter = [0]
        self.solveRecursive(rootNode, sortedItems, "", candidateCounter)
        
        return self.bestValue, self.bestSolution

# Example usage with the given problem
def main():
    # Problem data from your example
    values = [16, 22, 12, 8]
    weights = [5, 7, 4, 3]
    capacity = 14

    # values = [2, 3, 3, 5, 2, 4]
    # weights = [11, 8, 6, 14, 10, 10]
    # capacity = 40
    
    knapsackSolver = BranchAndBoundKnapsack(values, weights, capacity)
    bestValue, bestSolution = knapsackSolver.solve()
    
    print("=" * 60)
    print("FINAL SOLUTION:")
    print(f"Maximum value: {bestValue}")
    print("Solution vector:")
    for i, val in enumerate(bestSolution):
        print(f"x{i+1} = {val}")
    
    # Verify solution
    totalWeight = sum(weights[i] * bestSolution[i] for i in range(len(weights)))
    totalValue = sum(values[i] * bestSolution[i] for i in range(len(values)))
    print(f"\nVerification:")
    print(f"Total weight: {totalWeight} (≤ {capacity})")
    print(f"Total value: {totalValue}")

if __name__ == "__main__":
    main()