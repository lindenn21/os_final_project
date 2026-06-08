from flask import Flask, render_template, request

app = Flask(__name__)



# CPU SCHED ALGORITHMS DITO

def fcfs(processes):

    processes.sort(key=lambda x: x["arrival"])

    current_time = 0

    for p in processes:

        if current_time < p["arrival"]:
            current_time = p["arrival"]

        p["waiting"] = current_time - p["arrival"]

        current_time += p["burst"]

        p["turnaround"] = p["waiting"] + p["burst"]

    return processes

def sjf(processes):

    processes = [p.copy() for p in processes]

    completed = []
    current_time = 0

    while len(completed) < len(processes):

        available = [
            p for p in processes
            if p not in completed and p["arrival"] <= current_time
        ]

        if not available:
            current_time += 1
            continue

        shortest = min(available, key=lambda x: x["burst"])

        shortest["waiting"] = current_time - shortest["arrival"]

        current_time += shortest["burst"]

        shortest["turnaround"] = (
            shortest["waiting"] + shortest["burst"]
        )

        completed.append(shortest)

    return completed

def priority_non_preemptive(processes):

    processes = [p.copy() for p in processes]

    completed = []
    current_time = 0

    while len(completed) < len(processes):

        available = [
            p for p in processes
            if p not in completed and p["arrival"] <= current_time
        ]

        if not available:
            current_time += 1
            continue

        highest = min(
            available,
            key=lambda x: (x["priority"], x["arrival"])
        )

        highest["waiting"] = (
            current_time - highest["arrival"]
        )

        current_time += highest["burst"]

        highest["turnaround"] = (
            highest["waiting"] + highest["burst"]
        )

        completed.append(highest)

    return completed

def priority_preemptive(processes):

    processes = [p.copy() for p in processes]

    n = len(processes)

    remaining = {
        p["pid"]: p["burst"]
        for p in processes
    }

    completion = {}

    current_time = 0
    completed = 0

    while completed < n:

        available = [
            p for p in processes
            if p["arrival"] <= current_time
            and remaining[p["pid"]] > 0
        ]

        if not available:
            current_time += 1
            continue

        current = min(
            available,
            key=lambda x: (
                x["priority"],
                x["arrival"]
            )
        )

        remaining[current["pid"]] -= 1
        current_time += 1

        if remaining[current["pid"]] == 0:

            completion[current["pid"]] = current_time
            completed += 1

    results = []

    for p in processes:

        turnaround = (
            completion[p["pid"]]
            - p["arrival"]
        )

        waiting = (
            turnaround
            - p["burst"]
        )

        p["waiting"] = waiting
        p["turnaround"] = turnaround

        results.append(p)

    return results

def round_robin(processes, quantum):

    processes = [p.copy() for p in processes]

    n = len(processes)

    remaining = {
        p["pid"]: p["burst"]
        for p in processes
    }

    completion = {}

    current_time = 0
    ready_queue = []

    processes.sort(key=lambda x: x["arrival"])

    i = 0

    while len(completion) < n:

        while i < n and processes[i]["arrival"] <= current_time:
            ready_queue.append(processes[i])
            i += 1

        if not ready_queue:

            if i < n:
                current_time = processes[i]["arrival"]
                continue

        current = ready_queue.pop(0)

        run_time = min(
            quantum,
            remaining[current["pid"]]
        )

        current_time += run_time

        remaining[current["pid"]] -= run_time

        while i < n and processes[i]["arrival"] <= current_time:
            ready_queue.append(processes[i])
            i += 1

        if remaining[current["pid"]] > 0:
            ready_queue.append(current)

        else:
            completion[current["pid"]] = current_time

    results = []

    for p in processes:

        turnaround = (
            completion[p["pid"]]
            - p["arrival"]
        )

        waiting = (
            turnaround
            - p["burst"]
        )

        p["waiting"] = waiting
        p["turnaround"] = turnaround

        results.append(p)

    return results

# DITO YUNG INDEX

@app.route("/")
def index():
    return render_template("index.html")

#About page potaenanyo
@app.route('/about')
def about():
    return render_template('about.html')

# CPU SCHEDULING PAGE

@app.route("/cpu-scheduling", methods=["GET", "POST"])
def cpu_scheduling():

    results = []
    avg_waiting = 0
    avg_turnaround = 0

    if request.method == "POST":

        try:
            arrivals = request.form["arrival"].split(",")
            bursts = request.form["burst"].split(",")
            priorities = request.form["priority"].split(",")

            n = min(len(arrivals), len(bursts), len(priorities))

            processes = []

            for i in range(n):
                processes.append({
                    "pid": f"P{i+1}",
                    "arrival": int(arrivals[i].strip()),
                    "burst": int(bursts[i].strip()),
                    "priority": int(priorities[i].strip())
                })

            algorithm = request.form.get("algorithm", "FCFS")

            if algorithm == "FCFS":
                results = fcfs(processes)

            elif algorithm == "SJF":
                results = sjf(processes)

            elif algorithm == "PNP":
                results = priority_non_preemptive(processes)

            elif algorithm == "PP":
                results = priority_preemptive(processes)

            elif algorithm == "RR":
                quantum = int(request.form["quantum"])
                results = round_robin(processes, quantum)

            if results:
                avg_waiting = sum(
                    p["waiting"] for p in results
                ) / len(results)

                avg_turnaround = sum(
                    p["turnaround"] for p in results
                ) / len(results)

        except Exception as e:
            print("ERROR:", e)

    return render_template(
        "cpu_sched.html",
        results=results,
        avg_waiting=avg_waiting,
        avg_turnaround=avg_turnaround
    )


if __name__ == "__main__":
    app.run(debug=True)