import sys

jobs = [
    [1, 6, 10],   # Job 1: processing time 6, due date 10
    [2, 6, 14],   # Job 2: processing time 6, due date 14
    [3, 7, 15],   # Job 3: processing time 7, due date 15
    [4, 11, 16]   # Job 4: processing time 11, due date 16
]

penalties = [5, 6, 5, 6]  # penalty rates (per overdue day)

def sequenceFinder():

    for i in range(len(jobs)):
        jobs[i].append(0)  # Flag for picked

    # Global best
    bestCandidate = sys.maxsize
    bestSequence = []
    problemCounter = [0] * (len(jobs)+1)  # For problem numbering like 3.2.1

    def calculateRemainingTime():
        return sum(job[1] for job in jobs if job[3] != 1)

    def branch(position, currentPenalty, currentSequence):
        global bestCandidate, bestSequence
        if position == 0:
            if currentPenalty < bestCandidate:
                bestCandidate = currentPenalty
                bestSequence = currentSequence[:]
            return

        remainingTime = calculateRemainingTime()
        evals = []
        for i in range(len(jobs)):
            if jobs[i][3] == 1:
                continue
            overdue = remainingTime - jobs[i][2]
            overdueDays = max(0, overdue)
            jobPenalty = overdueDays * penalties[i]
            nextPenalty = currentPenalty + jobPenalty
            pruned = nextPenalty > bestCandidate  # your pruning rule
            evals.append((nextPenalty, i, overdueDays, jobPenalty, pruned))

        # >>> Key change: top level printed/branched by job id so x14=Problem 1 ... x44=Problem 4
        if position == len(jobs):
            evals.sort(key=lambda t: jobs[t[1]][0])               # by job id (1,2,3,4)
        else:
            evals.sort(key=lambda t: (t[0], jobs[t[1]][0]))       # by nextPenalty then id

        for nextPenalty, i, overdueDays, jobPenalty, pruned in evals:

            if pruned:
                continue
            jobs[i][3] = 1
            branch(position - 1, nextPenalty, currentSequence + [f"x{jobs[i][0]}{position}"])
            jobs[i][3] = 0  # Backtrack

    # Run greedy for initial bound
    def runGreedy():
        global bestCandidate
        tempBest = sys.maxsize
        position = len(jobs)
        pickedPenalty = 0
        sequence = []
        pickedJobs = [0] * len(jobs)
        while position > 0:
            remainingTime = sum(jobs[i][1] for i in range(len(jobs)) if pickedJobs[i] != 1)
            minPenalty = sys.maxsize
            bestI = -1
            for i in range(len(jobs)):
                if pickedJobs[i] == 1:
                    continue
                overdue = remainingTime - jobs[i][2]
                overdueDays = max(0, overdue)
                jobPenalty = overdueDays * penalties[i]
                nextPenalty = pickedPenalty + jobPenalty
                if nextPenalty < minPenalty:
                    minPenalty = nextPenalty
                    bestI = i
            if bestI == -1:
                break
            pickedPenalty = minPenalty
            pickedJobs[bestI] = 1
            sequence.append(f"x{jobs[bestI][0]}{position}")
            position -= 1
        if pickedPenalty < tempBest:
            tempBest = pickedPenalty
        return tempBest, sequence[::-1]  # Reverse to forward order

    # Run greedy first
    initialPenalty, initialSequence = runGreedy()
    bestCandidate = initialPenalty
    bestSequence = initialSequence
    print(f"Initial greedy total penalty: {initialPenalty}")
    print(f"Initial sequence (forward): {initialSequence}")

    # Run branch-and-bound
    branch(len(jobs), 0, [])

    # print()
    # print(f"Best total penalty: {bestCandidate}")
    # print(f"Best sequence: {bestSequence}")


for i in range(len(jobs)):
    jobs[i].append(0)  # Flag for picked

# Global best
bestCandidate = sys.maxsize
bestSequence = []
bestCandidateLetter = ""
candidateCount = 0

# Store all problems for ordered printing
allProblems = []

def calculateRemainingTime():
    return sum(job[1] for job in jobs if job[3] != 1)

def getProblemNumber(currentSequence, jobId, position):
    """Generate problem number based on the logical order of job selections"""
    if not currentSequence:
        # Top level: Problem 1, 2, 3, 4 based on jobId
        return str(jobId)
    else:
        # Build hierarchical number based on sequence
        parts = []
        
        # Get the root job from first selection
        firstJobId = int(currentSequence[0][1])  # Extract job ID from x14, x24, etc.
        parts.append(str(firstJobId))
        
        # For subsequent levels, determine the order based on available jobs
        levelJobs = []
        tempPicked = [0] * len(jobs)
        
        # Simulate the sequence to this point
        for seqItem in currentSequence:
            seqJobId = int(seqItem[1])  # Extract job ID
            for j in range(len(jobs)):
                if jobs[j][0] == seqJobId:
                    tempPicked[j] = 1
                    break
        
        # Find available jobs at this level
        availableJobs = []
        for j in range(len(jobs)):
            if tempPicked[j] == 0:
                availableJobs.append(jobs[j][0])
        availableJobs.sort()
        
        # Find position of current job in available jobs
        if availableJobs:
            try:
                jobPosition = availableJobs.index(jobId) + 1
                parts.append(str(jobPosition))
            except ValueError:
                parts.append("1")
        
        return ".".join(parts)

def branch(position, currentPenalty, currentSequence):
    global bestCandidate, bestSequence, bestCandidateLetter, candidateCount, allProblems
    
    if position == 0:
        if currentPenalty < bestCandidate:
            candidateCount += 1
            bestCandidateLetter = chr(ord('A') + candidateCount - 1)
            # Store the solution problem
            problemData = {
                'number': getProblemNumber(currentSequence[:-1] if currentSequence else [], 
                                           int(currentSequence[-1][1]) if currentSequence else 0, position),
                'sequence': ' & '.join(currentSequence),
                'penalty': currentPenalty,
                'isSolution': True,
                'candidateLetter': bestCandidateLetter
            }
            allProblems.append(problemData)
            bestCandidate = currentPenalty
            bestSequence = currentSequence[:]
        return

    remainingTime = calculateRemainingTime()
    evals = []
    for i in range(len(jobs)):
        if jobs[i][3] == 1:
            continue
        overdue = remainingTime - jobs[i][2]
        overdueDays = max(0, overdue)
        jobPenalty = overdueDays * penalties[i]
        nextPenalty = currentPenalty + jobPenalty
        pruned = nextPenalty > bestCandidate
        evals.append((nextPenalty, i, overdueDays, jobPenalty, pruned))

    # Sort by job ID for consistent ordering
    if position == len(jobs):
        evals.sort(key=lambda t: jobs[t[1]][0])
    else:
        evals.sort(key=lambda t: jobs[t[1]][0])  # Always sort by job ID for logical order

    for nextPenalty, i, overdueDays, jobPenalty, pruned in evals:
        jobId = jobs[i][0]
        problemNum = getProblemNumber(currentSequence, jobId, position)
        newSequenceItem = f"x{jobId}{position}"
        displaySequence = ' & '.join(currentSequence + [newSequenceItem]) if currentSequence else newSequenceItem
        
        # Store problem data
        problemData = {
            'number': problemNum,
            'sequence': displaySequence,
            'remainingTime': remainingTime,
            'dueDate': jobs[i][2],
            'overdueDays': overdueDays,
            'penaltyRate': penalties[i],
            'jobPenalty': jobPenalty,
            'currentPenalty': currentPenalty,
            'totalPenalty': nextPenalty,
            'pruned': pruned,
            'bestCandidate': bestCandidate if pruned else None,
            'bestCandidateLetter': bestCandidateLetter if pruned else None,
            'isSolution': False
        }
        allProblems.append(problemData)
        
        if pruned:
            continue
            
        jobs[i][3] = 1
        branch(position - 1, nextPenalty, currentSequence + [newSequenceItem])
        jobs[i][3] = 0

def runGreedy():
    tempBest = sys.maxsize
    position = len(jobs)
    pickedPenalty = 0
    sequence = []
    pickedJobs = [0] * len(jobs)
    
    while position > 0:
        remainingTime = sum(jobs[i][1] for i in range(len(jobs)) if pickedJobs[i] != 1)
        minPenalty = sys.maxsize
        bestI = -1
        for i in range(len(jobs)):
            if pickedJobs[i] == 1:
                continue
            overdue = remainingTime - jobs[i][2]
            overdueDays = max(0, overdue)
            jobPenalty = overdueDays * penalties[i]
            nextPenalty = pickedPenalty + jobPenalty
            if nextPenalty < minPenalty:
                minPenalty = nextPenalty
                bestI = i
        if bestI == -1:
            break
        pickedPenalty = minPenalty
        pickedJobs[bestI] = 1
        sequence.append(f"x{jobs[bestI][0]}{position}")
        position -= 1
    
    return pickedPenalty, sequence[::-1]

# Run greedy first
initialPenalty, initialSequence = runGreedy()
bestCandidate = initialPenalty
bestSequence = initialSequence
candidateCount = 1
bestCandidateLetter = "A"

print(f"Initial greedy total penalty: {initialPenalty}")
print(f"Initial sequence (forward): {initialSequence}")
print()

# Run branch-and-bound
branch(len(jobs), 0, [])

# Sort problems by their number for logical display order
def sortKey(problem):
    # Convert problem number to sortable format
    parts = problem['number'].split('.')
    # Pad each part to ensure proper sorting
    return [int(p) for p in parts]

allProblems.sort(key=sortKey)

# Print all problems in order
for problem in allProblems:
    print("=" * 20)
    if problem['isSolution']:
        print(f"Problem {problem['number']}")
        print(f"Total penalty = {problem['penalty']} *")
    else:
        print(f"Problem {problem['number']}")
        print(problem['sequence'])
        print(f"Time required = {'+'.join(str(job[1]) for job in jobs if job[3] != 1)} = {problem['remainingTime']} days")
        print(f"Overdue = {problem['remainingTime']}-{problem['dueDate']} = {problem['overdueDays']} days")
        print(f"Penalty = {problem['overdueDays']} * {problem['penaltyRate']} = {problem['jobPenalty']}")
        print(f"Total penalty = {problem['currentPenalty']}+{problem['jobPenalty']} = {problem['totalPenalty']}")
        if problem['pruned']:
            print(f"Eliminated by Candidate {problem['bestCandidate']} {problem['bestCandidateLetter']}")
        else:
            print(f"Branching on x{problem['sequence'].split(' & ')[-1][1]}{len([x for x in problem['sequence'].split(' & ') if x])}")

print()
print(f"Best total penalty: {bestCandidate} {bestCandidateLetter}")
# print(f"Best sequence (backward positions): {bestSequence}")
sequenceFinder()