from turtle import left

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


# MEMORY MANAGEMENT PAGE

@app.route("/memory-management", methods=["GET", "POST"])
def memory_management():

    memory_blocks = []
    memory_map = []
    ram_segments = []
    job_sizes = []
    algorithm = None
    algorithm_label = None
    job_results = []

    if request.method == "POST":

        try:

            memory_blocks = [
                int(x.strip())
                for x in request.form["blocks"].split(",")
            ]

            job_sizes = [
                int(x.strip())
                for x in request.form["job_size"].split(",")
            ]

            algorithm = request.form["algorithm"]

            algorithm_labels = {
                "FIRST": "First Fit",
                "BEST": "Best Fit",
                "WORST": "Worst Fit"
            }
    
            algorithm_label = algorithm_labels.get(algorithm)

            current_holes = memory_blocks.copy()

            ram_segments = [
                {"size": b, "status": "FREE"} for b in memory_blocks
            ]

            for job_size in job_sizes:

                chosen_index = -1

                # FIRST FIT
                if algorithm == "FIRST":

                    for i, block in enumerate(current_holes):

                        if block >= job_size:
                            chosen_index = i
                            break

                # BEST FIT
                elif algorithm == "BEST":

                    best_size = float("inf")

                    for i, block in enumerate(current_holes):

                        if block >= job_size and block < best_size:
                            best_size = block
                            chosen_index = i

                # WORST FIT
                elif algorithm == "WORST":

                    worst_size = -1

                    for i, block in enumerate(current_holes):

                        if block >= job_size and block > worst_size:
                            worst_size = block
                            chosen_index = i

                if chosen_index != -1:

                    selected_block = current_holes[chosen_index]
                    remaining = selected_block - job_size

                    job_results.append({
                        "size": job_size,
                        "message": f"Allocated in block of size {selected_block}K. Remaining: {remaining}K."
                    })

                    if remaining > 0:
                        current_holes[chosen_index] = remaining
                    else:
                        current_holes.pop(chosen_index)

                    for segment in ram_segments:

                        if segment["status"] == "FREE" and segment["size"] == selected_block:

                            segment["status"] = "JOB"
                            segment["size"] = job_size
                            if remaining > 0:
                            
                                idx = ram_segments.index(segment)
                                ram_segments.insert(idx + 1, {
                                    "size": remaining,
                                    "status": "FREE"
                                })
                            break
                
                else:
                    job_results.append({
                        "size": job_size,
                        "message": "No suitable memory block found."
                    })

            for block in current_holes:
                memory_map.append({
                    "size": block,
                    "status": "FREE"
                })
                
        except Exception as e:
            
            print("ERROR:", e)

    return render_template(
        "mm_mng.html",
        memory_blocks=memory_blocks,
        memory_map=memory_map,
        ram_segments=ram_segments,
        job_sizes=job_sizes,
        algorithm=algorithm,
        algorithm_label=algorithm_label,
        job_results=job_results
    )

# VIRTUAL MEMORY MANAGEMENT PAGE

@app.route("/virtual-memory", methods=["GET", "POST"])
def virtual_memory():

    frames = None
    reference_string = []
    algorithm = ""
    memory = []

    history = []
    page_faults = 0
    page_hits = 0
    
    if request.method == "POST":

        try:

            frames = int(request.form["frames"])
            reference_string = [
                int(x.strip())
                for x in request.form["reference"].split(",")
            ]

            algorithm = request.form["algorithm"]

            memory = []
            history = []

            for page in reference_string:

                if page in memory:
                    page_hits += 1
                    history.append({
                        "page": page,
                        "status": "HIT",
                        "memory": memory.copy()
                    })

                else:
                    page_faults += 1

                    if len(memory) < frames:
                        memory.append(page)

                    else:
                        if algorithm == "FIFO":
                            memory.pop(0)
                            memory.append(page)

                        elif algorithm == "LRU":

                            least_recent = float("inf")
                            lru_page = None

                            for mem_page in memory:

                                last_used = -1

                                for i in range(len(history)-1, -1, -1):

                                    if history[i]["page"] == mem_page:
                                        last_used = i
                                        break

                                if last_used < least_recent:
                                    least_recent = last_used
                                    lru_page = mem_page

                            memory.remove(lru_page)
                            memory.append(page)

                        elif algorithm == "Optimal":

                            farthest = -1
                            optimal_page = None

                            for mem_page in memory:

                                next_use = float("inf")

                                for i in range(len(history), len(reference_string)):

                                    if reference_string[i] == mem_page:
                                        next_use = i
                                        break

                                if next_use > farthest:
                                    farthest = next_use
                                    optimal_page = mem_page

                            memory.remove(optimal_page)
                            memory.append(page)

                    history.append({
                        "page": page,
                        "status": "FAULT",
                        "memory": memory.copy()
                    })

        except Exception as e:
            print("ERROR:", e)

    return render_template(
        "virtual_mem.html",
        frames=frames,
        reference_string=reference_string,
        algorithm=algorithm,
        memory=memory,
        history=history,
        page_faults=page_faults,
        page_hits=page_hits
    )

# DISK MANAGEMENT PAGE

@app.route("/disk-management", methods=["GET", "POST"])
def disk_management():

    seek_sequence = []
    total_seek = 0
    algorithm = ""
    direction = ""

    if request.method == "POST":

        tracks = int(request.form["tracks"])
        initial_head = int(request.form["initial_head"])

        if not (0 <= initial_head < tracks):
            raise ValueError("Invalid initial head position")

        raw_requests = request.form["requests"].split(",")

        requests = []
        for r in raw_requests:
            try:
                req = int(r.strip())
                if 0 <= req < tracks:
                    requests.append(req)
            except ValueError:
                continue

        algorithm = request.form["algorithm"]
        direction = request.form["direction"]

        current = initial_head

        if algorithm == "FCFS":

            seek_sequence = [initial_head]

            for req in requests:

                total_seek += abs(current - req)

                seek_sequence.append(req)

                current = req

        elif algorithm == "SSTF":

            seek_sequence = [initial_head]

            pending = requests.copy()

            while pending:

                closest = min(
                    pending,
                    key=lambda x: abs(current - x)
                )

                total_seek += abs(current - closest)

                seek_sequence.append(closest)

                current = closest

                pending.remove(closest)

        elif algorithm == "SCAN":

            left = sorted([r for r in requests if r < initial_head])
            right = sorted([r for r in requests if r >= initial_head])

            seek_sequence = [initial_head]

            if direction == "RIGHT":

                for r in right:
                    total_seek += abs(current - r)
                    current = r
                    seek_sequence.append(r)

                if current != tracks - 1:
                    total_seek += abs(current - (tracks - 1))
                    current = tracks - 1
                    seek_sequence.append(current)

                for r in reversed(left):
                    total_seek += abs(current - r)
                    current = r
                    seek_sequence.append(r)

            else:
                for r in reversed(left):
                    total_seek += abs(current - r)
                    current = r
                    seek_sequence.append(r)

                if current != 0:
                    total_seek += abs(current - 0)
                    current = 0
                    seek_sequence.append(current)

                for r in right:
                    total_seek += abs(current - r)
                    current = r
                    seek_sequence.append(r)

        elif algorithm == "C-SCAN":

            left = sorted([r for r in requests if r < initial_head])
            right = sorted([r for r in requests if r > initial_head])

            seek_sequence = [initial_head]

            if direction == "RIGHT":

                for r in right:
                    total_seek += abs(current - r)
                    current = r
                    seek_sequence.append(r)

                total_seek += abs(current - (tracks - 1))
                current = tracks - 1
                seek_sequence.append(current)

                total_seek += abs(current - 0)
                current = 0
                seek_sequence.append(current)

                for r in left:
                    total_seek += abs(current - r)
                    current = r
                    seek_sequence.append(r)

            else:
                for r in reversed(left):
                    total_seek += abs(current - r)
                    current = r
                    seek_sequence.append(r)

                total_seek += abs(current - 0)
                current = 0
                seek_sequence.append(current)

                total_seek += abs(current - (tracks - 1))
                current = tracks - 1
                seek_sequence.append(current)

                for r in reversed(right):
                    total_seek += abs(current - r)
                    current = r
                    seek_sequence.append(r)

    return render_template("disk_management.html",
                            seek_sequence=seek_sequence,
                            total_seek=total_seek,
                            algorithm=algorithm,
                            direction=direction)


if __name__ == "__main__":
    app.run(debug=True)