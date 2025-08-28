import sys

jobs = [
    [1, 6, 8],   # Job 1: processing time 6, due date 8
    [2, 4, 4],   # Job 2: processing time 4, due date 4
    [3, 5, 12],  # Job 3: processing time 5, due date 12
    [4, 8, 16]   # Job 4: processing time 8, due date 16
]

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
        return str(jobId)
    else:
        parts = []
        firstJobId = int(currentSequence[0][1])
        parts.append(str(firstJobId))
        
        tempPicked = [0] * len(jobs)
        for seqItem in currentSequence:
            seqJobId = int(seqItem[1])
            for j in range(len(jobs)):
                if jobs[j][0] == seqJobId:
                    tempPicked[j] = 1
                    break
        
        availableJobs = []
        for j in range(len(jobs)):
            if tempPicked[j] == 0:
                availableJobs.append(jobs[j][0])
        availableJobs.sort()
        
        if availableJobs:
            try:
                jobPosition = availableJobs.index(jobId) + 1
                parts.append(str(jobPosition))
            except ValueError:
                parts.append("1")
        
        return ".".join(parts)

def branch(position, currentOverdue, currentSequence):
    global bestCandidate, bestSequence, bestCandidateLetter, candidateCount, allProblems
    
    if position == 0:
        if currentOverdue < bestCandidate:
            candidateCount += 1
            bestCandidateLetter = chr(ord('A') + candidateCount - 1)
            problemData = {
                'number': getProblemNumber(currentSequence[:-1] if currentSequence else [], 
                                           int(currentSequence[-1][1]) if currentSequence else 0, position),
                'sequence': ' & '.join(currentSequence),
                'overdue': currentOverdue,
                'is_solution': True,
                'candidate_letter': bestCandidateLetter
            }
            allProblems.append(problemData)
            bestCandidate = currentOverdue
            bestSequence = currentSequence[:]
        return

    remainingTime = calculateRemainingTime()
    evals = []
    for i in range(len(jobs)):
        if jobs[i][3] == 1:
            continue
        overdue = remainingTime - jobs[i][2]
        overdueDays = max(0, overdue)
        nextOverdue = currentOverdue + overdueDays
        pruned = nextOverdue > bestCandidate
        evals.append((nextOverdue, i, overdue, overdueDays, pruned))

    evals.sort(key=lambda t: jobs[t[1]][0])

    for nextOverdue, i, overdue, overdueDays, pruned in evals:
        jobId = jobs[i][0]
        problemNum = getProblemNumber(currentSequence, jobId, position)
        newSequenceItem = f"x{jobId}{position}"
        displaySequence = ' & '.join(currentSequence + [newSequenceItem]) if currentSequence else newSequenceItem
        
        problemData = {
            'number': problemNum,
            'sequence': displaySequence,
            'remaining_time': remainingTime,
            'due_date': jobs[i][2],
            'overdue': overdue,
            'overdue_days': overdueDays,
            'current_overdue': currentOverdue,
            'total_overdue': nextOverdue,
            'pruned': pruned,
            'best_candidate': bestCandidate if pruned else None,
            'best_candidate_letter': bestCandidateLetter if pruned else None,
            'is_solution': False
        }
        allProblems.append(problemData)
        
        if pruned:
            continue
            
        jobs[i][3] = 1
        branch(position - 1, nextOverdue, currentSequence + [newSequenceItem])
        jobs[i][3] = 0

def runGreedy():
    tempBest = sys.maxsize
    position = len(jobs)
    pickedOverdue = 0
    sequence = []
    pickedJobs = [0] * len(jobs)
    
    while position > 0:
        remainingTime = sum(jobs[i][1] for i in range(len(jobs)) if pickedJobs[i] != 1)
        minOverdue = sys.maxsize
        bestI = -1
        for i in range(len(jobs)):
            if pickedJobs[i] == 1:
                continue
            overdue = remainingTime - jobs[i][2]
            nextOverdue = pickedOverdue + max(0, overdue)
            if nextOverdue < minOverdue:
                minOverdue = nextOverdue
                bestI = i
        if bestI == -1:
            break
        pickedOverdue = minOverdue
        pickedJobs[bestI] = 1
        sequence.append(f"x{jobs[bestI][0]}{position}")
        position -= 1
    
    return pickedOverdue, sequence[::-1]

# Run greedy first
initialOverdue, initialSequence = runGreedy()
bestCandidate = initialOverdue
bestSequence = initialSequence
candidateCount = 1
bestCandidateLetter = "A"

print(f"Initial greedy sum tardiness: {initialOverdue}")
print(f"Initial sequence (forward): {initialSequence}")
print()

# Run branch-and-bound
branch(len(jobs), 0, [])

# Sort problems by their number
def sortKey(problem):
    parts = problem['number'].split('.')
    return [int(p) for p in parts]

allProblems.sort(key=sortKey)

# Print all problems
for problem in allProblems:
    print("=" * 20)
    if problem['is_solution']:
        print(f"Problem {problem['number']}")
        print(f"Total overdue = {problem['overdue']} days *")
    else:
        print(f"Problem {problem['number']}")
        print(problem['sequence'])
        print(f"Time required = {'+'.join(str(job[1]) for job in jobs if job[3] != 1)} = {problem['remaining_time']} days")
        print(f"Overdue = {problem['remaining_time']}-{problem['due_date']} = {problem['overdue_days']} days")
        print(f"Total overdue = {problem['current_overdue']}+{problem['overdue_days']} = {problem['total_overdue']} days")
        if problem['pruned']:
            print(f"Eliminated by Candidate {problem['best_candidate']} {problem['best_candidate_letter']}")
        else:
            print(f"Branching on x{problem['sequence'].split(' & ')[-1][1]}{len([x for x in problem['sequence'].split(' & ') if x])}")

print()
print(f"Best sum tardiness: {bestCandidate} {bestCandidateLetter}")
print(f"Best sequence (backward positions): {bestSequence}")
