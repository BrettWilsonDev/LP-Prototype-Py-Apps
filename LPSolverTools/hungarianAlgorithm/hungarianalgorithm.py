import numpy as np
import copy

class HungarianAlgorithm:
    def __init__(self, cost_matrix):
        self.original_matrix = np.array(cost_matrix, dtype=float)
        self.matrix = copy.deepcopy(self.original_matrix)
        self.n_rows, self.n_cols = self.matrix.shape
        self.step_count = 0
        self.dummy_added = False
        
    def print_matrix(self, matrix, title="Matrix"):
        print(f"\n{title}:")
        print("-" * 50)
        for row in matrix:
            print([f"{val:6.1f}" for val in row])
        print()
    
    def step1_add_dummy(self):
        """Step 1: Add dummy row/column if matrix is not square"""
        self.step_count += 1
        print(f"STEP {self.step_count}: Add dummy row/column if needed")
        print("=" * 60)
        
        if self.n_rows != self.n_cols:
            max_dim = max(self.n_rows, self.n_cols)
            # new_matrix = np.zeros((max_dim, max_dim))

            high_cost = np.max(self.matrix)
            new_matrix = np.full((max_dim, max_dim), high_cost)
            
            if self.n_rows < self.n_cols:
                # Add dummy rows
                new_matrix[:self.n_rows, :] = self.matrix
                print(f"Added {max_dim - self.n_rows} dummy row(s)")
                self.dummy_added = True
            else:
                # Add dummy columns
                new_matrix[:, :self.n_cols] = self.matrix
                print(f"Added {max_dim - self.n_cols} dummy column(s)")
                self.dummy_added = True
            
            self.matrix = new_matrix
            self.n_rows, self.n_cols = max_dim, max_dim
        else:
            print("Matrix is already square - no dummy needed")
        
        self.print_matrix(self.matrix, "Matrix after Step 1")
    
    def step2_row_reduction(self):
        """Step 2: Row reduction - subtract minimum of each row"""
        self.step_count += 1
        print(f"STEP {self.step_count}: Row reduction")
        print("=" * 60)
        
        for i in range(self.n_rows):
            min_val = np.min(self.matrix[i, :])
            print(f"Row {i}: minimum value = {min_val}")
            self.matrix[i, :] -= min_val
        
        self.print_matrix(self.matrix, "Matrix after row reduction")
    
    def step3_column_reduction(self):
        """Step 3: Column reduction - subtract minimum of each column"""
        self.step_count += 1
        print(f"STEP {self.step_count}: Column reduction")
        print("=" * 60)
        
        for j in range(self.n_cols):
            min_val = np.min(self.matrix[:, j])
            print(f"Column {j}: minimum value = {min_val}")
            self.matrix[:, j] -= min_val
        
        self.print_matrix(self.matrix, "Matrix after column reduction")
    
    def find_minimum_lines(self):
        """Find minimum number of lines to cover all zeros"""
        # This is a simplified approach using marking algorithm
        zeros = (self.matrix == 0)
        marked_rows = set()
        marked_cols = set()
        
        # Mark rows with no assignments first
        assignments = self.find_assignment(zeros)
        assigned_rows = set()
        assigned_cols = set()
        
        for row, col in assignments:
            if row is not None and col is not None:
                assigned_rows.add(row)
                assigned_cols.add(col)
        
        # Mark unassigned rows
        for i in range(self.n_rows):
            if i not in assigned_rows:
                marked_rows.add(i)
        
        # Iteratively mark columns and rows
        changed = True
        while changed:
            changed = False
            # Mark columns that have zeros in marked rows
            for row in list(marked_rows):
                for col in range(self.n_cols):
                    if zeros[row, col] and col not in marked_cols:
                        marked_cols.add(col)
                        changed = True
            
            # Mark rows that have assignments in marked columns
            for row, col in assignments:
                if col in marked_cols and row not in marked_rows:
                    marked_rows.add(row)
                    changed = True
        
        # Lines are: unmarked rows + marked columns
        line_rows = set(range(self.n_rows)) - marked_rows
        line_cols = marked_cols
        
        return line_rows, line_cols
    
    def find_assignment(self, zeros_matrix):
        """Find maximum assignment using zeros"""
        assignments = []
        used_rows = set()
        used_cols = set()
        
        # Simple greedy assignment for demonstration
        for i in range(self.n_rows):
            for j in range(self.n_cols):
                if zeros_matrix[i, j] and i not in used_rows and j not in used_cols:
                    assignments.append((i, j))
                    used_rows.add(i)
                    used_cols.add(j)
                    break
        
        return assignments
    
    def step4_check_optimality(self):
        """Step 4: Check if solution is optimal"""
        self.step_count += 1
        print(f"STEP {self.step_count}: Check optimality")
        print("=" * 60)
        
        line_rows, line_cols = self.find_minimum_lines()
        num_lines = len(line_rows) + len(line_cols)
        
        print(f"Lines covering all zeros:")
        print(f"Row lines: {sorted(line_rows)}")
        print(f"Column lines: {sorted(line_cols)}")
        print(f"Total lines: {num_lines}")
        print(f"Matrix size: {self.n_rows}")
        
        if num_lines == self.n_rows:
            print("✓ Number of lines equals matrix size - OPTIMAL!")
            return True, line_rows, line_cols
        else:
            print("✗ Number of lines ≠ matrix size - NOT OPTIMAL")
            return False, line_rows, line_cols
    
    def step5_improve_solution(self, line_rows, line_cols):
        """Step 5: Improve the solution"""
        self.step_count += 1
        print(f"STEP {self.step_count}: Improve solution")
        print("=" * 60)
        
        # Step 5a: Find smallest uncovered value
        covered = np.zeros((self.n_rows, self.n_cols), dtype=bool)
        
        # Mark covered elements
        for i in line_rows:
            covered[i, :] = True
        for j in line_cols:
            covered[:, j] = True
        
        uncovered_values = []
        for i in range(self.n_rows):
            for j in range(self.n_cols):
                if not covered[i, j]:
                    uncovered_values.append(self.matrix[i, j])
        
        a = min(uncovered_values)
        print(f"Step 5a: Smallest uncovered value a = {a}")
        
        # Step 5b: Subtract a from uncovered elements
        print("Step 5b: Subtract a from uncovered elements")
        
        # Step 5c: Add a to doubly covered elements
        print("Step 5c: Add a to doubly covered elements")
        
        # Step 5d: Apply changes
        for i in range(self.n_rows):
            for j in range(self.n_cols):
                row_covered = i in line_rows
                col_covered = j in line_cols
                
                if not row_covered and not col_covered:
                    # Uncovered - subtract a
                    self.matrix[i, j] -= a
                elif row_covered and col_covered:
                    # Doubly covered - add a
                    self.matrix[i, j] += a
                # Singly covered - leave unchanged
        
        self.print_matrix(self.matrix, "Matrix after improvement")
    
    def step6_find_assignment(self):
        """Step 6: Find optimal assignment"""
        self.step_count += 1
        print(f"STEP {self.step_count}: Find optimal assignment")
        print("=" * 60)
        
        zeros = (self.matrix == 0)
        assignment = self.find_optimal_assignment(zeros)
        
        print("Optimal assignment (row, col):")
        total_cost = 0
        for i, (row, col) in enumerate(assignment):
            if row < self.original_matrix.shape[0] and col < self.original_matrix.shape[1]:
                cost = self.original_matrix[row, col]
                total_cost += cost
                print(f"  Assignment {i+1}: Row {row} → Column {col} (cost: {cost})")
        
        print(f"\nTotal optimal cost: {total_cost}")
        return assignment, total_cost
    
    def find_optimal_assignment(self, zeros_matrix):
        """Enhanced assignment finding"""
        assignment = []
        temp_zeros = zeros_matrix.copy()
        
        while True:
            # Find row or column with only one zero
            assigned = False
            
            # Check rows with single zero
            for i in range(self.n_rows):
                zero_cols = [j for j in range(self.n_cols) if temp_zeros[i, j]]
                if len(zero_cols) == 1:
                    j = zero_cols[0]
                    assignment.append((i, j))
                    temp_zeros[i, :] = False
                    temp_zeros[:, j] = False
                    assigned = True
                    break
            
            if assigned:
                continue
                
            # Check columns with single zero
            for j in range(self.n_cols):
                zero_rows = [i for i in range(self.n_rows) if temp_zeros[i, j]]
                if len(zero_rows) == 1:
                    i = zero_rows[0]
                    assignment.append((i, j))
                    temp_zeros[i, :] = False
                    temp_zeros[:, j] = False
                    assigned = True
                    break
            
            if not assigned:
                # If no single zeros, pick arbitrarily
                found = False
                for i in range(self.n_rows):
                    for j in range(self.n_cols):
                        if temp_zeros[i, j]:
                            assignment.append((i, j))
                            temp_zeros[i, :] = False
                            temp_zeros[:, j] = False
                            found = True
                            break
                    if found:
                        break
                
                if not found:
                    break
        
        return assignment
    
    def solve(self):
        """Main solving method"""
        print("HUNGARIAN ALGORITHM - STEP BY STEP SOLUTION")
        print("=" * 60)
        self.print_matrix(self.original_matrix, "Original Cost Matrix")
        
        # Step 1: Add dummy if needed
        self.step1_add_dummy()
        
        # Step 2: Row reduction
        self.step2_row_reduction()
        
        # Step 3: Column reduction
        self.step3_column_reduction()
        
        # Steps 4-5: Iterative improvement
        max_iterations = 10
        iteration = 0
        
        while iteration < max_iterations:
            optimal, line_rows, line_cols = self.step4_check_optimality()
            
            if optimal:
                break
            else:
                self.step5_improve_solution(line_rows, line_cols)
                iteration += 1
        
        # Step 6: Find final assignment
        assignment, total_cost = self.step6_find_assignment()
        
        return assignment, total_cost


# Example usage
if __name__ == "__main__":
    # cost_matrix1 = [
    #     [1, 2, 4],
    #     [5, 3, 4],
    #     [5, 4, 8]
    # ]
    
    # hungarian1 = HungarianAlgorithm(cost_matrix1)
    # assignment1, cost1 = hungarian1.solve()

    cost_matrix1 = [
        [10, 19, 8, 15],
        [10, 18, 7, 17],
        [13, 16, 9, 14],
        [12, 19, 8, 18],
        [14, 17, 10, 19],
    ]
    
    hungarian1 = HungarianAlgorithm(cost_matrix1)
    assignment1, cost1 = hungarian1.solve()
    
    # print("\n" + "="*80)
    # print("EXAMPLE 2: 4x3 Unbalanced Assignment Problem")
    # print("="*80)
    
    # # Test case 2: Unbalanced matrix
    # cost_matrix2 = [
    #     [90, 75, 75],
    #     [35, 85, 55],
    #     [125, 95, 90],
    #     [45, 110, 95]
    # ]
    
    # hungarian2 = HungarianAlgorithm(cost_matrix2)
    # assignment2, cost2 = hungarian2.solve()