from math import sqrt as wurzel
from math import factorial
import sys
import random
import time

if len(sys.argv) > 1:
    if sys.argv[1] == "--mode":
        mode = sys.argv[2]
else:
    mode = "normal"


points = []

def get_possbile_ways():
    x=len(points)
    return factorial(x)

def get_distance_point(p1, p2):
    dx = p2["x"] - p1["x"]
    dy = p2["y"] - p1["y"]

    return wurzel(dx**2 + dy**2)

def get_distance_points(ps):
    distance = 0
    for i in range(len(ps) - 1):
        distance += get_distance_point(ps[i], ps[i + 1])
    return distance

def add_point(x=None, y=None):
    if x is None or y is None:
        try:
            x = int(input("Whats the x coodinate\n>"))
        except ValueError:
            print("Invalid input")
            return
        try:
            y = int(input("Whats the y coodinate\n>"))
        except ValueError:
            print("Invalid input")
            return
    points.append({"x": x, "y": y})

def generate_points():
    try:
        n = int(input("How many points?\n>"))
    except ValueError:
        print("Invalid input")
        return
    for _ in range(n):
        add_point(x=random.randint(0, 100 if n < 50 else 1000), y=random.randint(0, 100 if n < 50 else 1000))

def bruteforce():
    max_ways = get_possbile_ways()
    if mode == "verbose":
        print(f"Possible ways: {max_ways}")
        time.sleep(2)
    ways = []
    while len(ways) < max_ways:
        new_way_dict = get_way()
        if new_way_dict not in ways:
            ways.append(new_way_dict)

    return ways

def get_way():
    new_way = []
    while len(new_way) < len(points):
        n = random.choice(points)
        if n not in new_way:
            new_way.append(n)
    distance = get_distance_points(new_way)
    return {"way": new_way, "distance": distance}

def smartforce(limit):
    way_dict = get_way()
    start = time.monotonic()
    while start + limit > time.monotonic():
        if mode == "verbose":
            print(f"\rWay: {way_dict['way']}, distance: {way_dict['distance']}", end="")
            time.sleep(2)
        route = way_dict['way']
        i = random.randrange(len(route))
        j = random.randrange(len(route))

        route[i], route[j] = route[j], route[i]
        new_distance = get_distance_points(route)
        if new_distance < way_dict['distance']:
            way_dict = {"way": route, "distance": new_distance}
        else:
            route[i], route[j] = route[j], route[i]
    return way_dict


def start():
    print("TSM algorithm")
    print("\nBRUTEFORCE\n")
    start = time.monotonic()
    ways = bruteforce()
    end = time.monotonic()
    print(f"Took: {end - start}")
    distances = []
    for i in range(len(ways)):
        distances.append(ways[i]["distance"])
    print(f"Fastest: {min(distances)}, slowest: {max(distances)}")
    print("\n")
    time.sleep(2)
    limit = float(input("Enter limit for smartforce: "))
    way = smartforce(limit)
    print(f"Smartforce: {way}")
    print("\n")
    time.sleep(2)



def main():
    while True:
        print("1: add point")
        print("2: generate points")
        print("3: start")
        print("q: quit")
        cmd = input("> ").strip().lower()
        if cmd in ["1", "add point"]:
            add_point()
        elif cmd in ["2", "generate points"]:
            generate_points()
        elif cmd in ["3", "start"]:
            if len(points) < 2:
                print("Not enough points")
            else:
                start()
        elif cmd in ["q", "quit"]:
            sys.exit(0)



if __name__ == "__main__":
    main()
