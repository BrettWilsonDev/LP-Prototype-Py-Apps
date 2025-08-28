def printBoard(board, blockedPositions=None, stepNumber=None, queenCount=None, attemptedPosition=None, conflictReason=None):
    """Print the chess board in ASCII format with bottom-left as (0,0)."""
    boardSize = len(board)
    if blockedPositions is None:
        blockedPositions = set()
    
    if stepNumber is not None:
        print(f"\n{'='*50}")
        print(f"STEP {stepNumber}: ", end="")
        if queenCount is not None:
            print(f"Placing Queen #{queenCount}", end="")
        if attemptedPosition is not None:
            print(f" at position {attemptedPosition}", end="")
        if conflictReason is not None:
            print(f" - {conflictReason}")
        else:
            print()
        print('='*50)
    
    # Print column numbers header
    print("   ", end="")
    for col in range(boardSize):
        print(f"{col:2}", end=" ")
    print()
    
    # Print top border
    print("  +" + "-" * (boardSize * 3 - 1) + "+")
    
    # Print each row (reversed order so bottom-left is 0,0)
    for displayRow in range(boardSize - 1, -1, -1):
        print(f"{displayRow} |", end="")
        for col in range(boardSize):
            if board[displayRow][col] == 1:
                symbol = " Q"
            elif board[displayRow][col] == 2:  # Attempted placement
                symbol = " ?"
            elif (displayRow, col) in blockedPositions:
                symbol = " X"
            else:
                symbol = " ."
            print(symbol, end=" " if col < boardSize - 1 else "")
        print("|")
    
    # Print bottom border
    print("  +" + "-" * (boardSize * 3 - 1) + "+")
    print("Legend: Q=Queen, X=Blocked, .=Empty, ?=Attempted")

def isQueenSafe(board, row, col, boardSize):
    """Check if placing a queen at (row, col) is safe from other existing queens."""
    # Check this row
    for c in range(boardSize):
        if c != col and board[row][c] == 1:
            return False, f"Conflicts with queen in same row at ({row},{c})"
    
    # Check this column
    for r in range(boardSize):
        if r != row and board[r][col] == 1:
            return False, f"Conflicts with queen in same column at ({r},{col})"
    
    # Check diagonals
    for r in range(boardSize):
        for c in range(boardSize):
            if board[r][c] == 1 and (r != row and c != col):
                if abs(r - row) == abs(c - col):
                    return False, f"Conflicts with queen on diagonal at ({r},{c})"
    
    return True, "Safe placement"

def solveQueensStepByStep(boardSize, firstQueenPos, blockedPositions):
    """Solve N-Queens step by step, showing each attempt."""
    board = [[0 for _ in range(boardSize)] for _ in range(boardSize)]
    
    # Place the first queen
    board[firstQueenPos[0]][firstQueenPos[1]] = 1
    stepNumber = 1
    queenCount = 1
    
    print("INITIAL STATE:")
    printBoard(board, blockedPositions, stepNumber, queenCount, firstQueenPos, "PLACED (Starting position)")
    
    # Try to place remaining queens
    while True:
        queenCount += 1
        stepNumber += 1
        queenPlaced = False
        
        print(f"\nSearching for position for Queen #{queenCount}...")
        
        # Try each position on the board
        for row in range(boardSize):
            for col in range(boardSize):
                if (row, col) in blockedPositions:
                    continue
                if board[row][col] != 0:  # Position already occupied
                    continue
                
                # Show attempt
                board[row][col] = 2  # Mark as attempted
                printBoard(board, blockedPositions, stepNumber, queenCount, (row, col), "ATTEMPTING...")
                
                # Check if this position is safe
                isSafe, reason = isQueenSafe(board, row, col, boardSize)
                
                if isSafe:
                    # Place the queen
                    board[row][col] = 1
                    stepNumber += 1
                    printBoard(board, blockedPositions, stepNumber, queenCount, (row, col), "PLACED - " + reason)
                    queenPlaced = True
                    break
                else:
                    # Remove the attempt marker and continue
                    board[row][col] = 0
                    stepNumber += 1
                    printBoard(board, blockedPositions, stepNumber, queenCount, (row, col), "REJECTED - " + reason)
            
            if queenPlaced:
                break
        
        # If no queen could be placed, we're done
        if not queenPlaced:
            print(f"\n{'='*50}")
            print(f"FINAL RESULT: No more queens can be placed!")
            print(f"Total queens placed: {queenCount - 1}")
            print(f"Final configuration:")
            print('='*50)
            printBoard(board, blockedPositions)
            break
    
    return board, queenCount - 1

def countQueens(board):
    """Count the number of queens on the board."""
    count = 0
    positions = []
    for row in range(len(board)):
        for col in range(len(board[row])):
            if board[row][col] == 1:
                count += 1
                positions.append((row, col))
    return count, positions

def evaluateFinalSolution(board, boardSize):
    """Evaluate if the final solution is optimal."""
    queenCount, queenPositions = countQueens(board)
    
    # Check if all queens are safe (should be, but let's verify)
    allSafe = True
    for i, (row1, col1) in enumerate(queenPositions):
        for j, (row2, col2) in enumerate(queenPositions):
            if i != j:
                if (row1 == row2 or col1 == col2 or 
                    abs(row1 - row2) == abs(col1 - col2)):
                    allSafe = False
                    break
        if not allSafe:
            break
    
    print(f"\nSOLUTION ANALYSIS:")
    print(f"Queens placed: {queenCount}")
    print(f"Queen positions: {queenPositions}")
    print(f"Solution status: {'FEASIBLE' if allSafe else 'INFEASIBLE'}")
    
    # For small boards, we can estimate if it's optimal
    if boardSize <= 4:
        maxPossible = boardSize
        if queenCount == maxPossible:
            print(f"Status: OPTIMAL (achieved theoretical maximum of {maxPossible})")
        else:
            print(f"Status: SUB-OPTIMAL (maximum possible is approximately {maxPossible})")
    else:
        print(f"Status: SOLUTION FOUND (optimality depends on board constraints)")

def main():
    """Main function to run the step-by-step N-Queens solver."""
    print("=== Step-by-Step N-Queens Solver ===")
    print("Bottom-left corner is position (0,0)")
    print()
    
    # INPUT CONFIGURATION - MODIFY THESE VALUES
    # =========================================

        #     0  1  2  3  4  5  6  7  8
        #   +--------------------------+
        # 8 | .  .  .  .  .  .  .  .  .|
        # 7 | .  .  .  .  .  .  .  .  .|
        # 6 | .  .  .  .  .  .  .  .  .|
        # 5 | .  .  .  .  .  .  .  .  .|
        # 4 | .  .  .  .  .  .  .  .  .|
        # 3 | .  .  .  .  .  .  .  .  .|
        # 2 | .  .  .  .  .  .  .  .  .|
        # 1 | .  .  .  .  .  .  .  .  .|
        # 0 | .  .  .  .  .  .  .  .  .|
        #   +--------------------------+

    boardSize = 4  # Size of the chess board
    firstQueenPos = (0, 1)  # Starting position for first queen (row, col) - bottom-left is (0,0)
    
    # Blocked positions where queens cannot be placed
    # Add tuples in format (row, col) - bottom-left is (0,0)
    blockedPositions = {
        (1, 0),  
        (3, 0),
        (1, 2),
        (3, 2),
        (2, 3),
    }
    # =========================================
    
    # Validate input
    if boardSize < 1:
        print("Board size must be positive!")
        return
    
    startRow, startCol = firstQueenPos
    if not (0 <= startRow < boardSize and 0 <= startCol < boardSize):
        print("Starting position is out of bounds!")
        return
    
    # Remove first queen position from blocked positions if it exists there
    if firstQueenPos in blockedPositions:
        blockedPositions.remove(firstQueenPos)
        print(f"Removed first queen position {firstQueenPos} from blocked positions.")
    
    # Validate blocked positions
    validBlockedPositions = set()
    for pos in blockedPositions:
        row, col = pos
        if 0 <= row < boardSize and 0 <= col < boardSize:
            validBlockedPositions.add(pos)
        else:
            print(f"Skipping out-of-bounds blocked position: {pos}")
    
    blockedPositions = validBlockedPositions
    
    print(f"Board size: {boardSize}x{boardSize}")
    print(f"First queen position: {firstQueenPos}")
    print(f"Blocked positions: {list(blockedPositions)}")
    
    # Solve step by step
    finalBoard, totalQueens = solveQueensStepByStep(boardSize, firstQueenPos, blockedPositions)
    
    # Evaluate the solution
    evaluateFinalSolution(finalBoard, boardSize)

if __name__ == "__main__":
    main()