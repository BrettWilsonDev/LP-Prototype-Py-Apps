import numpy as np

class NearestNeighbourTSP:
    def __init__(self, distanceMatrix):
        self.distanceMatrix = np.array(distanceMatrix)
        self.numCities = self.distanceMatrix.shape[0]

    def printFormulation(self, distanceMatrix):
        n = len(distanceMatrix)
        # Objective function
        print("Objective function:")
        terms = []
        for i in range(n):
            for j in range(n):
                if i != j:
                    terms.append(f"{distanceMatrix[i][j]}x{i+1}{j+1}")
        print("min z = " + " + ".join(terms))
        print()

        # Arriving once in a city constraints
        print("Arriving once in a city constraints:")
        for j in range(n):
            terms = [f"x{i+1}{j+1}" for i in range(n) if i != j]
            print(" + ".join(terms) + " = 1")

        for i in range(n):
            terms = [f"x{i+1}{j+1}" for j in range(n) if i != j]
            print(" + ".join(terms) + " = 1")
        print()

        # Sub-tour elimination constraints (MTZ)
        print("Sub-tour constraints:")
        for i in range(1, n):       # Ui for cities 2..n
            for j in range(1, n):
                if i != j:
                    print(f"U{i+1} - U{j+1} + {n}x{i+1}{j+1} <= {n-1}")

    def getDistance(self, fromCity, toCity):
        return self.distanceMatrix[fromCity-1][toCity-1]

    def solveNnhVerbose(self, startCity=1):
        print("\n=== Formulation ===\n")

        self.printFormulation(self.distanceMatrix)

        route = [startCity]
        remainingCities = set(range(1, self.numCities+1)) - {startCity}
        step = 1

        print(f"\nInitial city: x{startCity}")

        while remainingCities:
            lastCity = route[-1]

            # Build list of available next steps
            candidates = [(city, self.getDistance(lastCity, city)) for city in remainingCities]
            nearestCity, nearestDist = min(candidates, key=lambda x: x[1])

            # Print available options
            print(f"\nRoute {step}: Current city x{lastCity}")
            print("Available next moves:")
            for city, dist in candidates:
                marker = " <-- chosen" if city == nearestCity else ""
                print(f"  x{lastCity}{city} : {dist}{marker}")

            route.append(nearestCity)
            remainingCities.remove(nearestCity)

            # Print updated route
            routeStr = " → ".join(f"x{route[i]}{route[i+1]}" for i in range(len(route)-1))
            print(f"Updated route after step {step}: {routeStr}")
            step += 1

        # Return to start
        route.append(startCity)
        print("\nReturn to start:")
        routeStr = " → ".join(f"x{route[i]}{route[i+1]}" for i in range(len(route)-1))
        print(routeStr)

        distances = [self.getDistance(route[i], route[i+1]) for i in range(len(route)-1)]
        print("\nZ =", " + ".join(map(str, distances)))
        print("Z =", sum(distances))
        return route, sum(distances)


# Example usage
if __name__ == "__main__":
    # distanceMatrix = [
    #     [0, 264, 434, 328, 116, 174],  # City 1
    #     [132, 0, 290, 201, 79, 119],   # City 2
    #     [217, 580, 0, 226, 606, 909],  # City 3
    #     [164, 402, 113, 0, 196, 294],  # City 4
    #     [58, 158, 303, 392, 0, 441],  # City 5
    #     [87, 237, 455, 588, 662, 0]    # City 6
    # ]

    # solver = NearestNeighbourTSP(distance_matrix)
    # final_route, total_cost = solver.solve_nnh_verbose(start_city=1)

    distanceMatrix = [
        [0, 520, 980, 450, 633],  # City 1
        [520, 0, 204, 888, 557],   # City 2
        [980, 204, 0, 446, 1020],  # City 3
        [450, 888, 446, 0, 249],  # City 4
        [633, 557, 1020, 249, 0],  # City 5
    ]

    solver = NearestNeighbourTSP(distanceMatrix)
    finalRoute, totalCost = solver.solveNnhVerbose(1)
