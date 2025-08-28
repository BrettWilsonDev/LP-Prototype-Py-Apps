import sympy as sp
import numpy as np
from typing import List, Tuple, Optional, Callable
import matplotlib.pyplot as plt

class DetailedSteepestDescentOptimizer:
    """
    Implements the Steepest Ascent/Descent Algorithm with detailed step-by-step output.
    """
    
    def __init__(self, functionExpr: str, variables: List[str], maximize: bool = False):
        """
        Initialize the optimizer.
        
        Args:
            functionExpr: String representation of the function (e.g., "x**2 + y**2 + 2*x + 4")
            variables: List of variable names (e.g., ["x", "y"])
            maximize: If True, finds maximum; if False, finds minimum
        """
        self.variables = [sp.Symbol(var) for var in variables]
        self.varNames = variables
        self.function = sp.sympify(functionExpr)
        self.maximize = maximize
        self.gradient = self._computeGradient()
        self.hessian = self._computeHessian()

    def _computeGradient(self) -> List[sp.Expr]:
        """Compute the gradient of the function."""
        return [sp.diff(self.function, var) for var in self.variables]
    
    def _computeHessian(self) -> sp.Matrix:
        """Compute the Hessian matrix of the function."""
        n = len(self.variables)
        hessian = sp.zeros(n, n)
        for i in range(n):
            for j in range(n):
                hessian[i, j] = sp.diff(self.function, self.variables[i], self.variables[j])
        return hessian
    
    def evaluateFunction(self, point: List[float]) -> float:
        """Evaluate the function at a given point."""
        substitutions = {var: val for var, val in zip(self.variables, point)}
        return float(self.function.subs(substitutions))
    
    def evaluateGradient(self, point: List[float]) -> List[float]:
        """Evaluate the gradient at a given point."""
        substitutions = {var: val for var, val in zip(self.variables, point)}
        return [float(grad.subs(substitutions)) for grad in self.gradient]
    
    def evaluateHessian(self, point: List[float]) -> np.ndarray:
        """Evaluate the Hessian matrix at a given point."""
        substitutions = {var: val for var, val in zip(self.variables, point)}
        hessianVals = self.hessian.subs(substitutions)
        return np.array(hessianVals).astype(float)
    
    def checkCriticalPointNature(self, point: List[float]) -> str:
        """
        Check if a critical point is a minimum, maximum, or saddle point using the Hessian.
        """
        H = self.evaluateHessian(point)
        eigenVals = np.linalg.eigvals(H)
        
        if all(eig > 0 for eig in eigenVals):
            return "Local Minimum"
        elif all(eig < 0 for eig in eigenVals):
            return "Local Maximum"
        else:
            return "Saddle Point"
    
    def detailedStepSizeCalculation(self, currentPoint: List[float], gradient: List[float], verbose: bool = True) -> float:
        """
        Find the optimal step size with detailed algebraic steps shown.
        """
        h = sp.Symbol('h')
        
        if verbose:
            print(f"    Finding optimal step size 'h':")
            print(f"    Current point: {currentPoint}")
            print(f"    Gradient vector: {gradient}")
        
        direction = gradient if self.maximize else [-g for g in gradient]
        directionType = "ascent" if self.maximize else "descent"
        
        if verbose:
            print(f"    Direction vector (for {directionType}): {direction}")
            print(f"    Formula: x_(i+1) = x_i + h * direction")
        
        newPoint = [currentPoint[i] + h * direction[i] for i in range(len(currentPoint))]
        
        if verbose:
            print(f"    New point expressions:")
            for i, varName in enumerate(self.varNames):
                print(f"      {varName}_(i+1) = {currentPoint[i]} + h * ({direction[i]}) = {newPoint[i]}")
        
        substitutions = {var: val for var, val in zip(self.variables, newPoint)}
        gH = self.function.subs(substitutions)
        
        if verbose:
            print(f"\n    Substituting new point into function f({', '.join(self.varNames)}):")
            originalFuncStr = str(self.function)
            print(f"    Original function: f({', '.join(self.varNames)}) = {originalFuncStr}")
            
            print(f"    Substituting:")
            for i, varName in enumerate(self.varNames):
                print(f"      {varName} = {newPoint[i]}")
            
            print(f"    f(x_(i+1)) = {gH}")
            
            gHExpanded = sp.expand(gH)
            print(f"    Expanded: g(h) = {gHExpanded}")
            
            gHCollected = sp.collect(gHExpanded, h)
            print(f"    Collected: g(h) = {gHCollected}")
        
        dgDh = sp.diff(gH, h)
        
        if verbose:
            print(f"\n    Taking derivative with respect to h:")
            print(f"    dg/dh = {dgDh}")
            print(f"    Setting dg/dh = 0 to find optimal h:")
        
        try:
            hOptimalSolutions = sp.solve(dgDh, h)
            if hOptimalSolutions:
                hOptimal = float(hOptimalSolutions[0])
                if verbose:
                    print(f"    Solving: {dgDh} = 0")
                    print(f"    Solution: h = {hOptimal}")
                return hOptimal
        except:
            if verbose:
                print(f"    Analytical solution failed, using numerical method")
            return self._goldenSectionSearch(currentPoint, gradient)
        
        if verbose:
            print(f"    No analytical solution found, using numerical method")
        return self._goldenSectionSearch(currentPoint, gradient)
    
    def _goldenSectionSearch(self, currentPoint: List[float], gradient: List[float], 
                             a: float = -2.0, b: float = 2.0, tol: float = 1e-6) -> float:
        phi = (1 + np.sqrt(5)) / 2
        resPhi = 2 - phi
        
        direction = gradient if self.maximize else [-g for g in gradient]
        
        def objective(h):
            newPoint = [currentPoint[i] + h * direction[i] for i in range(len(currentPoint))]
            value = self.evaluateFunction(newPoint)
            return -value if self.maximize else value
        
        x1 = a + resPhi * (b - a)
        x2 = a + (1 - resPhi) * (b - a)
        f1 = objective(x1)
        f2 = objective(x2)
        
        while abs(b - a) > tol:
            if f1 < f2:
                b = x2
                x2 = x1
                f2 = f1
                x1 = a + resPhi * (b - a)
                f1 = objective(x1)
            else:
                a = x1
                x1 = x2
                f1 = f2
                x2 = a + (1 - resPhi) * (b - a)
                f2 = objective(x2)
        
        return (a + b) / 2
    
    def optimize(self, initialPoint: List[float], maxIterations: int = 100, 
                 tolerance: float = 1e-6, verbose: bool = True) -> Tuple[List[float], float, List[dict]]:
        currentPoint = initialPoint.copy()
        history = []
        
        if verbose:
            method = "Steepest Ascent" if self.maximize else "Steepest Descent"
            print(f"\n{'='*80}")
            print(f"{method} Algorithm - Detailed Steps")
            print(f"{'='*80}")
            print(f"Function: f({', '.join(self.varNames)}) = {self.function}")
            print(f"Objective: Find {'maximum' if self.maximize else 'minimum'}")
            print(f"Initial point: {currentPoint}")
            print(f"Initial function value: f({', '.join([str(p) for p in currentPoint])}) = {self.evaluateFunction(currentPoint)}")
            
            print(f"\nGradient formulas:")
            for i, grad in enumerate(self.gradient):
                print(f"  ∂f/∂{self.varNames[i]} = {grad}")
            
            print("-" * 80)
        
        for iteration in range(maxIterations):
            if verbose:
                print(f"\n ITERATION {iteration + 1}:")
                print(f"{'='*40}")
            
            grad = self.evaluateGradient(currentPoint)
            gradNorm = np.linalg.norm(grad)
            
            if verbose:
                print(f"Step 1: Calculate gradient at current point {currentPoint}")
                for i, (gradVal, varName) in enumerate(zip(grad, self.varNames)):
                    substitutionStr = str(self.gradient[i]).replace(str(self.variables[i]), str(currentPoint[i]))
                    for j, (var, val) in enumerate(zip(self.variables, currentPoint)):
                        if j != i:
                            substitutionStr = substitutionStr.replace(str(var), str(val))
                    print(f"  ∂f/∂{varName} = {self.gradient[i]} = {substitutionStr} = {gradVal}")
                
                print(f"  Gradient vector: ∇f = [{', '.join([f'{g:.6f}' for g in grad])}]")
                print(f"  Gradient norm: ||∇f|| = {gradNorm:.6f}")
            
            iterInfo = {
                'iteration': iteration + 1,
                'point': currentPoint.copy(),
                'functionValue': self.evaluateFunction(currentPoint),
                'gradient': grad.copy(),
                'gradientNorm': gradNorm
            }
            
            if gradNorm < tolerance:
                if verbose:
                    print(f"\n CONVERGED! Gradient norm {gradNorm:.6f} < tolerance {tolerance}")
                    print(f"The gradient is approximately zero, indicating we're at a critical point.")
                history.append(iterInfo)
                break
            
            if verbose:
                print(f"\nStep 2: Find optimal step size")
            
            stepSize = self.detailedStepSizeCalculation(currentPoint, grad, verbose)
            iterInfo['stepSize'] = stepSize
            
            direction = grad if self.maximize else [-g for g in grad]
            newPoint = [currentPoint[i] + stepSize * direction[i] for i in range(len(currentPoint))]
            
            if verbose:
                print(f"\nStep 3: Update point using optimal step size")
                print(f"  Step size h = {stepSize:.6f}")
                print(f"  Direction vector: {direction}")
                print(f"  New point calculation:")
                for i, varName in enumerate(self.varNames):
                    print(f"    {varName}_(new) = {currentPoint[i]} + ({stepSize:.6f}) * ({direction[i]:.6f}) = {newPoint[i]:.6f}")
                
                oldValue = self.evaluateFunction(currentPoint)
                newValue = self.evaluateFunction(newPoint)
                print(f"\nStep 4: Verify improvement")
                print(f"  f(oldPoint) = f({currentPoint}) = {oldValue:.6f}")
                print(f"  f(newPoint) = f({[round(p, 6) for p in newPoint]}) = {newValue:.6f}")
                
                if self.maximize:
                    improvement = newValue > oldValue
                    print(f"  {' Better' if improvement else ' Worse'}: {newValue:.6f} {'>' if improvement else '<='} {oldValue:.6f}")
                else:
                    improvement = newValue < oldValue
                    print(f"  {' Better' if improvement else ' Worse'}: {newValue:.6f} {'<' if improvement else '>='} {oldValue:.6f}")
            
            currentPoint = newPoint
            history.append(iterInfo)
        
        optimalValue = self.evaluateFunction(currentPoint)
        
        if verbose:
            print(f"\n{'='*80}")
            print(" FINAL RESULTS")
            print(f"{'='*80}")
            finalPointStr = ", ".join([f"{self.varNames[i]}={currentPoint[i]:.6f}" for i in range(len(currentPoint))])
            print(f"Optimal point: ({finalPointStr})")
            print(f"Optimal value: {optimalValue:.6f}")
            
            print(f"\nHessian Analysis:")
            print(f"Hessian matrix symbolic form:")
            print(f"{self.hessian}")
            
            H = self.evaluateHessian(currentPoint)
            print(f"Hessian matrix at optimal point:")
            print(f"{H}")
            
            eigenVals = np.linalg.eigvals(H)
            print(f"Eigenvalues: {eigenVals}")
            
            nature = self.checkCriticalPointNature(currentPoint)
            print(f"Nature of critical point: {nature}")
            
            if len(eigenVals) == 2:
                detH = np.linalg.det(H)
                traceH = np.trace(H)
                print(f"Determinant: {detH:.6f}")
                print(f"Trace: {traceH:.6f}")
                if detH > 0 and traceH > 0:
                    print(" det(H) > 0 and tr(H) > 0 → Local Minimum")
                elif detH > 0 and traceH < 0:
                    print(" det(H) > 0 and tr(H) < 0 → Local Maximum")
                elif detH < 0:
                    print(" det(H) < 0 → Saddle Point")
                else:
                    print("  Inconclusive test")
        
        return currentPoint, optimalValue, history


if __name__ == "__main__":
    # solve_all_problems()
    # custom_optimizer = DetailedSteepestDescentOptimizer("x**2 + y**2 + 2*x + 4", ["x", "y"], maximize=False)
    # custom_result = custom_optimizer.optimize([2, 1], verbose=True)

    # custom_optimizer = DetailedSteepestDescentOptimizer("x * y + y - x**2 - y**2", ["x", "y"], maximize=False)
    # custom_result = custom_optimizer.optimize([1, 1], verbose=True)

    # custom_optimizer = DetailedSteepestDescentOptimizer("x**2 + y**2 + 2*x + 4", ["x", "y"], maximize=False)
    # custom_result = custom_optimizer.optimize([2, 1], verbose=True)

    custom_optimizer = DetailedSteepestDescentOptimizer("2*x*y + 4*x - 2*x**2 - y**2", ["x", "y"], maximize=False)
    custom_result = custom_optimizer.optimize([0.5, 0.5], verbose=True)