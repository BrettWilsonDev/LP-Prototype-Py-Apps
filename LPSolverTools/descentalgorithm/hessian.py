import sympy as sp
import numpy as np
from sympy import symbols, diff, Matrix, pprint
import warnings
warnings.filterwarnings('ignore')

class HessianAnalyzer:
    """
    Step-by-step Hessian analyzer for NLP applications.
    Shows all computation steps while focusing on concavity/convexity.
    """
    
    def __init__(self, functionStr, variablesStr):
        """
        Initialize the analyzer.
        
        Parameters:
        functionStr (str): Function string (e.g., "x**2 + y**2 + x*y")
        variablesStr (str): Variables (e.g., "x,y,z")
        """
        self.functionStr = functionStr
        self.variables = [var.strip() for var in variablesStr.split(',')]
        self.n = len(self.variables)
        
        # Create symbolic variables
        self.symVars = symbols(' '.join(self.variables))
        if self.n == 1:
            self.symVars = [self.symVars]
        
        # Parse function
        self.function = sp.sympify(functionStr, locals=dict(zip(self.variables, self.symVars)))
        
        print("="*60)
        print("HESSIAN ANALYZER FOR NLP - STEP BY STEP")
        print("="*60)
        print(f"Function: f({', '.join(self.variables)}) = {self.function}")
        print(f"Variables: {self.variables}")
        
    def step1FirstDerivatives(self):
        """Step 1: Compute first derivatives."""
        print(f"\n{'='*60}")
        print("STEP 1: COMPUTING FIRST DERIVATIVES")
        print("="*60)
        
        self.firstDerivs = []
        for i, var in enumerate(self.variables):
            deriv = diff(self.function, self.symVars[i])
            self.firstDerivs.append(deriv)
            print(f"∂f/∂{var} = {deriv}")
        
        return self.firstDerivs
    
    def step2SecondDerivatives(self):
        """Step 2: Compute second derivatives for Hessian."""
        print(f"\n{'='*60}")
        print("STEP 2: COMPUTING SECOND DERIVATIVES (HESSIAN ELEMENTS)")
        print("="*60)
        
        self.secondDerivs = {}
        print("Computing all second partial derivatives...")
        
        for i, var1 in enumerate(self.variables):
            for j, var2 in enumerate(self.variables):
                # H[i,j] = ∂²f/∂var1∂var2
                secondDeriv = diff(self.firstDerivs[i], self.symVars[j])
                key = f"d2f_d{var1}d{var2}"
                self.secondDerivs[key] = secondDeriv
                
                if i == j:
                    print(f"∂²f/∂{var1}² = ∂/∂{var1}(∂f/∂{var1}) = ∂/∂{var1}({self.firstDerivs[i]}) = {secondDeriv}")
                else:
                    print(f"∂²f/∂{var1}∂{var2} = ∂/∂{var2}(∂f/∂{var1}) = ∂/∂{var2}({self.firstDerivs[i]}) = {secondDeriv}")
        
        return self.secondDerivs
    
    def step3BuildHessian(self):
        """Step 3: Construct Hessian matrix."""
        print(f"\n{'='*60}")
        print("STEP 3: CONSTRUCTING HESSIAN MATRIX")
        print("="*60)
        
        print(f"Building {self.n}×{self.n} Hessian matrix H where H[i,j] = ∂²f/∂xᵢ∂xⱼ")
        
        hessianElements = []
        for i, var1 in enumerate(self.variables):
            row = []
            print(f"\nRow {i+1} (∂²f/∂{var1}∂•):")
            for j, var2 in enumerate(self.variables):
                key = f"d2f_d{var1}d{var2}"
                element = self.secondDerivs[key]
                row.append(element)
                print(f"  H[{i+1},{j+1}] = ∂²f/∂{var1}∂{var2} = {element}")
            hessianElements.append(row)
        
        self.hessianMatrix = Matrix(hessianElements)
        
        print(f"\nHessian Matrix H:")
        print("=" * 30)
        
        # Display matrix showing the actual expressions with variables
        for i in range(self.n):
            rowElements = []
            for j in range(self.n):
                element = self.hessianMatrix[i, j]
                rowElements.append(str(element))
            print(" ".join(rowElements))
        
        print(f"\nSymPy matrix:")
        pprint(self.hessianMatrix)
        
        return self.hessianMatrix
    
    def step3bHessianDeterminant(self):
        """Step 3b: Compute determinant of the Hessian matrix (symbolic)."""
        print(f"\n{'='*60}")
        print("STEP 3B: HESSIAN DETERMINANT")
        print("="*60)

        if not hasattr(self, "hessianMatrix"):
            print("Hessian matrix not built yet. Run step3BuildHessian first.")
            return None

        self.hessianDet = self.hessianMatrix.det()
        print(f"Determinant of Hessian (symbolic): {self.hessianDet}")

        return self.hessianDet

    def step4bNumericDeterminant(self):
        """Step 4b: Evaluate determinant numerically at the given point."""
        print(f"\n{'='*60}")
        print("STEP 4B: NUMERICAL DETERMINANT")
        print("="*60)

        if not hasattr(self, "numericalHessian"):
            print("Numerical Hessian not available. Run step4EvaluateAtPoint first.")
            return None

        self.numericDet = float(self.numericalHessian.det())
        print(f"Determinant of Hessian (numeric): {self.numericDet:.6f}")

        return self.numericDet


    def step4EvaluateAtPoint(self, point):
        """Step 4: Evaluate Hessian numerically at given point."""
        print(f"\n{'='*60}")
        print("STEP 4: NUMERICAL EVALUATION")
        print("="*60)
        
        print(f"Evaluating Hessian at point: {point}")
        
        # Show the symbolic Hessian again before substitution
        print(f"\nSymbolic Hessian H:")
        
        # Display clean matrix with expressions
        maxWidth = max(len(str(self.hessianMatrix[i,j])) for i in range(self.n) for j in range(self.n))
        
        for i in range(self.n):
            if i == 0 and self.n > 1:
                print("⎡", end="")
            elif i == self.n - 1 and self.n > 1:
                print("⎣", end="")
            elif self.n > 1:
                print("⎢", end="")
            else:
                print("[", end="")
            
            for j in range(self.n):
                element = str(self.hessianMatrix[i, j])
                print(f" {element:>{maxWidth}}", end="")
                if j < self.n - 1:
                    print("  ", end="")
            
            if i == 0 and self.n > 1:
                print(" ⎤")
            elif i == self.n - 1 and self.n > 1:
                print(" ⎦")  
            elif self.n > 1:
                print(" ⎥")
            else:
                print("]")
        
        # Create substitution list
        substitutions = []
        for i, var in enumerate(self.variables):
            if var in point:
                substitutions.append((self.symVars[i], point[var]))
                print(f"Substituting: {var} = {point[var]}")
        
        # Substitute values
        print(f"\nAfter substituting values:")
        self.numericalHessian = self.hessianMatrix.subs(substitutions)
        
        print(f"\nNumerical Hessian H({', '.join([f'{var}={point[var]}' for var in self.variables if var in point])}):")
        
        # Display clean numerical matrix
        maxWidth = max(len(f"{self.numericalHessian[i,j]:.3f}") for i in range(self.n) for j in range(self.n))
        
        for i in range(self.n):
            if i == 0 and self.n > 1:
                print("⎡", end="")
            elif i == self.n - 1 and self.n > 1:
                print("⎣", end="")
            elif self.n > 1:
                print("⎢", end="")
            else:
                print("[", end="")
            
            for j in range(self.n):
                element = f"{float(self.numericalHessian[i, j]):.3f}"
                print(f" {element:>{maxWidth}}", end="")
                if j < self.n - 1:
                    print("  ", end="")
            
            if i == 0 and self.n > 1:
                print(" ⎤")
            elif i == self.n - 1 and self.n > 1:
                print(" ⎦")
            elif self.n > 1:
                print(" ⎥")
            else:
                print("]")
        
        # Convert to numpy
        try:
            self.npHessian = np.array(self.numericalHessian.evalf()).astype(np.float64)
            print(f"\nAs NumPy array:")
            print(self.npHessian)
            
            # Show the numerical matrix with variable labels too
            print(f"\nNumerical Hessian with variable labels:")
            print("-" * (20 + 12 * self.n))
            
            # Header
            header = "     \t"
            for var in self.variables:
                header += f"    {var}\t"
            print(header)
            print("-" * (20 + 12 * self.n))
            
            # Rows
            for i, var in enumerate(self.variables):
                row = f"  {var}  \t"
                for j in range(self.n):
                    row += f"{self.npHessian[i,j]:8.3f}\t"
                print(row)
            
            return self.npHessian
        except Exception as e:
            print(f"Could not convert to numpy: {e}")
            return None
    
    def step5EigenvalueAnalysis(self):
        """Step 5: Compute eigenvalues for definiteness analysis."""
        print(f"\n{'='*60}")
        print("STEP 5: EIGENVALUE ANALYSIS")
        print("="*60)
        
        if self.npHessian is None:
            print("No numerical Hessian available for eigenvalue analysis")
            return None, None
        
        print("Computing eigenvalues to determine definiteness...")
        eigenvals = np.linalg.eigvals(self.npHessian)
        
        print(f"Eigenvalues: {eigenvals}")
        
        # Analyze eigenvalues
        tolerance = 1e-10
        positive = []
        negative = []
        zero = []
        
        for i, ev in enumerate(eigenvals):
            print(f"  λ_{i+1} = {ev:.6f}", end="")
            if ev > tolerance:
                print(" (positive)")
                positive.append(ev)
            elif ev < -tolerance:
                print(" (negative)")
                negative.append(ev)
            else:
                print(" (zero)")
                zero.append(ev)
        
        print(f"\nEigenvalue summary:")
        print(f"  Positive: {len(positive)} eigenvalues")
        print(f"  Negative: {len(negative)} eigenvalues")
        print(f"  Zero: {len(zero)} eigenvalues")
        
        return eigenvals, (len(positive), len(negative), len(zero))
    
    def step6DefinitenessClassification(self, eigenvals, counts):
        """Step 6: Classify definiteness and determine concavity/convexity."""
        print(f"\n{'='*60}")
        print("STEP 6: DEFINITENESS CLASSIFICATION")
        print("="*60)
        
        if eigenvals is None:
            return "EVALUATION_FAILED"
        
        posCount, negCount, zeroCount = counts
        total = len(eigenvals)
        
        print("Applying definiteness criteria:")
        print(f"  Total eigenvalues: {total}")
        print(f"  Positive: {posCount}, Negative: {negCount}, Zero: {zeroCount}")
        
        # Classification logic
        if posCount == total:
            definiteness = "Positive Definite"
            classification = "CONVEX"
            meaning = "Local minimum (good for minimization)"
        elif negCount == total:
            definiteness = "Negative Definite"
            classification = "CONCAVE"
            meaning = "Local maximum (good for maximization)"
        elif posCount > 0 and negCount > 0:
            definiteness = "Indefinite"
            classification = "SADDLE POINT"
            meaning = "Neither minimum nor maximum"
        elif zeroCount > 0:
            if posCount > 0 and negCount == 0:
                definiteness = "Positive Semidefinite"
                classification = "WEAKLY CONVEX"
                meaning = "Possibly minimum (inconclusive)"
            elif negCount > 0 and posCount == 0:
                definiteness = "Negative Semidefinite"
                classification = "WEAKLY CONCAVE"
                meaning = "Possibly maximum (inconclusive)"
            else:
                definiteness = "Zero Matrix"
                classification = "DEGENERATE"
                meaning = "Flat region (degenerate case)"
        
        print(f"\nClassification:")
        print(f"  Matrix Type: {definiteness}")
        print(f"  Result: {classification}")
        print(f"  Interpretation: {meaning}")
        
        return classification
    
    def step6bSylvestersCriterion(self):
        """
        Step 6c: Sylvester's criterion with detailed step-by-step explanation.
        Prints each principal minor and concludes convexity/concavity/saddle.
        """
        print(f"\n{'='*60}")
        print("STEP 6C: SYLVESTER'S CRITERION STEP-BY-STEP")
        print("="*60)

        if not hasattr(self, "npHessian") or self.npHessian is None:
            print("Numeric Hessian not available. Run step4EvaluateAtPoint first.")
            return None

        H = self.npHessian
        n = self.n
        minors = []

        # Compute leading principal minors
        for k in range(1, n+1):
            subH = H[:k, :k]
            detK = np.linalg.det(subH)
            minors.append(detK)
            if k == 1:
                print(f"First principal minor (diagonal entry): {detK:.6f}")
            else:
                print(f"{k}-th principal minor (det of top-left {k}x{k}): {detK:.6f}")

        # Step-by-step reasoning
        allPositive = all(m > 0 for m in minors)
        allAlternate = all(((-1) ** (i + 1)) * minors[i] > 0 for i in range(n))
        
        print("\nAnalysis of principal minors:")
        for i, m in enumerate(minors):
            sign = "positive" if m > 0 else "negative" if m < 0 else "zero"
            print(f"  Δ{i+1} = {m:.6f} ({sign})")

        # Classification
        if allPositive:
            classification = "CONVEX (Positive Definite)"
            reasoning = "All principal minors > 0"
        elif allAlternate:
            classification = "CONCAVE (Negative Definite)"
            reasoning = "Signs of principal minors alternate starting with negative"
        elif any(abs(m) < 1e-12 for m in minors):
            classification = "INCONCLUSIVE (Semi-definite / Degenerate)"
            reasoning = "Some minors are zero"
        else:
            classification = "SADDLE POINT (Indefinite)"
            reasoning = "Minors do not satisfy convex or concave pattern"

        print(f"\nConclusion: {classification} -> {reasoning}\n")
        return classification


    def step7NlpImplications(self, classification):
        """Step 7: NLP-specific implications."""
        print(f"\n{'='*60}")
        print("STEP 7: NLP OPTIMIZATION IMPLICATIONS")
        print("="*60)
        
        print(f"Classification: {classification}")
        print(f"Implications for optimization algorithms:")
        
        if classification == "CONVEX":
            print("✓ CONVEX function at this point")
            print("  → Gradient descent will converge to local minimum")
            print("  → Second-order conditions satisfied for minimum")
            print("  → Newton's method will work well")
            print("  → Any local minimum is global minimum (if globally convex)")
            
        elif classification == "CONCAVE":
            print("✓ CONCAVE function at this point")
            print("  → Gradient ascent will converge to local maximum")
            print("  → Second-order conditions satisfied for maximum")
            print("  → Good for maximization problems")
            print("  → Any local maximum is global maximum (if globally concave)")
            
        elif classification == "SADDLE POINT":
            print("⚠ SADDLE POINT detected")
            print("  → Not a local optimum")
            print("  → Gradient-based methods will move away from this point")
            print("  → May cause convergence issues for some algorithms")
            print("  → Consider using momentum or adaptive learning rates")
            
        elif "WEAKLY" in classification:
            print("⚠ WEAKLY definite (inconclusive)")
            print("  → Higher-order analysis needed")
            print("  → May be minimum/maximum or saddle point")
            print("  → Use with caution in optimization")
            
        else:
            print("⚠ DEGENERATE case")
            print("  → Flat region detected")
            print("  → Optimization may be difficult")
            print("  → Consider regularization or different approach")


    def fullAnalysis(self, point):
        self.step1FirstDerivatives()
        self.step2SecondDerivatives()
        self.step3BuildHessian()
        self.step3bHessianDeterminant()       # Symbolic determinant
        self.step4EvaluateAtPoint(point)
        self.step4bNumericDeterminant()       # Numeric determinant
        eigenvals, counts = self.step5EigenvalueAnalysis()
        classification = self.step6DefinitenessClassification(eigenvals, counts)
        sylvesterClass = self.step6bSylvestersCriterion()   # Sylvester's test
        self.step7NlpImplications(classification)

        print(f"\n{'='*60}")
        print("FINAL RESULT")
        print("="*60)
        print(f"Function: {self.function}")
        print(f"Point: {point}")
        print(f"Eigenvalue Classification: {classification}")
        print(f"Sylvester Classification: {sylvesterClass}")

        return {
            'function': str(self.function),
            'point': point,
            'classificationEigen': classification,
            'classificationSylvester': sylvesterClass,
            'eigenvalues': eigenvals.tolist() if eigenvals is not None else None,
            'hessian': self.npHessian.tolist() if hasattr(self, 'npHessian') and self.npHessian is not None else None,
            'hessianDeterminantSymbolic': str(self.hessianDet) if hasattr(self, 'hessianDet') else None,
            'hessianDeterminantNumeric': self.numericDet if hasattr(self, 'numericDet') else None
        }


# Convenience functions
def analyzeFunction(functionStr, variablesStr, pointDict):
    """Complete step-by-step analysis of a function."""
    analyzer = HessianAnalyzer(functionStr, variablesStr)
    return analyzer.fullAnalysis(pointDict)

def quickCheck(functionStr, variablesStr, pointDict):
    """Quick analysis without detailed steps."""
    analyzer = HessianAnalyzer(functionStr, variablesStr)
    result = analyzer.fullAnalysis(pointDict)
    return result['classificationEigen']

# Example usage
if __name__ == "__main__":
    # print("EXAMPLE 1: Convex quadratic function")
    # print("-" * 40)
    # result1 = analyzeFunction("x**2 + 2*y**2", "x,y", {'x': 0, 'y': 0})
    
    # print("\n\nEXAMPLE 2: Saddle point function")
    # print("-" * 40)
    # result2 = analyzeFunction("x**2 * y**2", "x,y", {'x': 2, 'y': 1})
    result2 = analyzeFunction("2*x*y + 4*x - 2*x**2 - y**2", "x,y", {'x': 0, 'y': 0})
    # result2 = analyzeFunction("x**2", "x", {'x': 0})
    
    # print("\n\nEXAMPLE 3: Three-variable function")
    # print("-" * 40)
    # result3 = analyzeFunction("x**2 + y**2 + z**2 + x*y", "x,y,z", {'x': 1, 'y': 1, 'z': 1})

    print("-" * 40)
    # result2 = analyzeFunction("-x**(2) - x * y - 2*y**2", "x,y", {'x': 0, 'y': 0})

    # result2 = analyzeFunction("x**(1/2)", "x", {'x': 0})

# Interactive function
def interactiveAnalysis():
    """Interactive step-by-step analysis."""
    print("\nInteractive Hessian Analysis")
    print("-" * 30)
    
    function = input("Enter function: ")
    variables = input("Enter variables (comma-separated): ")
    
    # Get point
    point = {}
    varList = [v.strip() for v in variables.split(',')]
    print("Enter evaluation point:")
    for var in varList:
        point[var] = float(input(f"  {var} = "))
    
    return analyzeFunction(function, variables, point)