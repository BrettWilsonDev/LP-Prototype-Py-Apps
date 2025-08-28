import numpy as np


class CheapestInsertionTSP:
    def __init__(self, distanceMatrix):
        self.distanceMatrix = np.array(distanceMatrix)
        self.numCities = self.distanceMatrix.shape[0]
        # Auto-generate city names: City 1, City 2, ...
        self.cities = {i+1: f"City {i+1}" for i in range(self.numCities)}

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
        """Get distance from one city to another (1-indexed)"""
        return self.distanceMatrix[fromCity-1][toCity-1]

    def findInitialRoute(self, startCity=None):
        """
        Pick initial 2-city route in a fully general way.
        - If startCity is given, pick the closest city to it.
        - If no startCity is given, pick the pair of cities with the minimal distance.
        """
        if startCity is not None:
            c1 = startCity
            # pick the closest remaining city
            distances = [(i, self.getDistance(c1, i))
                         for i in range(1, self.numCities+1) if i != c1]
            c2, _ = min(distances, key=lambda x: x[1])
        else:
            # fully general: find the closest pair of cities
            minDist = float('inf')
            c1, c2 = None, None
            for i in range(1, self.numCities+1):
                for j in range(i+1, self.numCities+1):
                    d = self.getDistance(i, j)
                    if d < minDist:
                        minDist = d
                        c1, c2 = i, j

        print(
            f"Initial route chosen: {self.cities[c1]} → {self.cities[c2]} with distance {self.getDistance(c1, c2)}")
        return [c1, c2]

    def getInsertionOptions(self, route, remainingCities):
        """Insertion options for 2-city route, order aligned to slides"""
        assert len(route) == 2, "This is for 2-city route only."
        a, b = route
        edges = [(a, b), (b, a)]
        if a > b:
            edges = [(b, a), (a, b)]

        options = []
        for currentFrom, currentTo in edges:
            currentDist = self.getDistance(currentFrom, currentTo)
            for newCity in remainingCities:
                newDist1 = self.getDistance(currentFrom, newCity)
                newDist2 = self.getDistance(newCity, currentTo)
                detourCost = newDist1 + newDist2 - currentDist

                routePart = f"x{currentFrom}{currentTo} {currentDist}"
                detourPart = f"x{currentFrom}{newCity} x{newCity}{currentTo} {newDist1} {newDist2}"
                calcPart = f"= ({newDist1} + {newDist2}) − {currentDist} = {detourCost}"

                # insert between currentFrom and currentTo
                if currentFrom == route[0] and currentTo == route[1]:
                    newRoute = route[:]
                    newRoute.insert(1, newCity)
                else:
                    newRoute = [currentFrom, newCity, currentTo]

                options.append({
                    'city': newCity,
                    'detourCost': detourCost,
                    'routePart': routePart,
                    'detourPart': detourPart,
                    'calcPart': calcPart,
                    'newRoute': newRoute,
                    'insertPosition': 1
                })
        return options

    def getGeneralInsertionOptions(self, route, remainingCities):
        """Insertion options for 3+ city routes"""
        options = []
        for i in range(len(route)):
            currentFrom = route[i]
            currentTo = route[(i+1) % len(route)]
            currentDist = self.getDistance(currentFrom, currentTo)
            for newCity in remainingCities:
                newDist1 = self.getDistance(currentFrom, newCity)
                newDist2 = self.getDistance(newCity, currentTo)
                detourCost = newDist1 + newDist2 - currentDist

                routePart = f"x{currentFrom}{currentTo} {currentDist}"
                detourPart = f"x{currentFrom}{newCity} x{newCity}{currentTo} {newDist1} {newDist2}"
                calcPart = f"= ({newDist1} + {newDist2}) − {currentDist} = {detourCost}"

                newRoute = route[:]
                newRoute.insert(i+1, newCity)

                options.append({
                    'city': newCity,
                    'detourCost': detourCost,
                    'routePart': routePart,
                    'detourPart': detourPart,
                    'calcPart': calcPart,
                    'newRoute': newRoute,
                    'insertPosition': i+1
                })
        return options

    def calculateTotalDistance(self, route):
        total = 0
        for i in range(len(route)):
            total += self.getDistance(route[i], route[(i+1) % len(route)])
        return total

    def formatRoute(self, route, anchor=None):
        r = route[:]
        if anchor in r:
            k = r.index(anchor)
            r = r[k:] + r[:k]
        return " → ".join(self.cities[c] for c in r)

    def solve(self, startCity=None):
        print("\n=== Formulation ===\n")

        self.printFormulation(self.distanceMatrix)

        print("\n=== Solving TSP using Cheapest Insertion Heuristic ===\n")
        route = self.findInitialRoute(startCity=startCity)
        remainingCities = [c for c in range(
            1, self.numCities+1) if c not in route]

        print(f"\nInitial route: {self.formatRoute(route)}")
        print(
            f"Remaining cities: {[self.cities[c] for c in remainingCities]}\n")

        while remainingCities:
            if len(route) == 2:
                insertionOptions = self.getInsertionOptions(
                    route, remainingCities)
            else:
                insertionOptions = self.getGeneralInsertionOptions(
                    route, remainingCities)

            print("Route           Detour          Detour Length")
            for option in insertionOptions:
                line = f"{option['routePart']} | {option['detourPart']} | {option['calcPart']}"
                print(line)

            # pick cheapest insertion
            bestOption = min(insertionOptions, key=lambda x: x['detourCost'])
            route = bestOption['newRoute']
            remainingCities.remove(bestOption['city'])

            print("\nUpdated route:", self.formatRoute(
                route, anchor=1 if 1 in route else route[0]))
            if remainingCities:
                print()

        totalDistance = self.calculateTotalDistance(route)
        print(
            f"\nFinal route: {self.formatRoute(route, anchor=1 if 1 in route else route[0])}")
        distances = [str(self.getDistance(route[i], route[(i+1) % len(route)]))
                     for i in range(len(route))]
        calculation = " + ".join(distances)
        print(f"z = {calculation}")
        print(f"z = {totalDistance}\n")

        return route, totalDistance


# Example usage
if __name__ == "__main__":
    # distanceMatrix = [
    #     [0, 264, 434, 328, 116, 174],  # City 1
    #     [132, 0, 290, 201, 79, 119],   # City 2
    #     [217, 580, 0, 226, 606, 909],  # City 3
    #     [164, 402, 113, 0, 196, 294],  # City 4
    #     [58, 158, 303, 392, 0, 441],   # City 5
    #     [87, 237, 455, 588, 662, 0]    # City 6
    # ]

    # distanceMatrix = [
    #     [0, 50, 120, 140],
    #     [60, 0, 140, 110],
    #     [90, 130, 0, 60],
    #     [130, 120, 80, 0],

    # ]

    # distanceMatrix = [
    #     [0, 50, 120, 140],
    #     [60, 0, 140, 110],
    #     [90, 130, 0, 60],
    #     [130, 120, 80, 0],
    # ]

    distanceMatrix = [
        [0, 520, 980, 450, 633],  # City 1
        [520, 0, 204, 888, 557],   # City 2
        [980, 204, 0, 446, 1020],  # City 3
        [450, 888, 446, 0, 249],  # City 4
        [633, 557, 1020, 249, 0],  # City 5
    ]

    solver = CheapestInsertionTSP(distanceMatrix)
    finalRoute, totalCost = solver.solve(1)
