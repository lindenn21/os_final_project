from flask import Flask, render_template, request

app = Flask(__name__)

import re

MAX_NUMERIC_VALUE = 1000000
MAX_LIST_ITEMS = 100
CPU_MAX_NUMERIC_VALUE = 100
CPU_MAX_LIST_ITEMS = 50
DISK_MAX_NUMERIC_VALUE = 1000


def parse_int_list(raw_value, field_name, max_items=None, max_value=None):
    if raw_value is None or raw_value.strip() == "":
        raise ValueError(f"{field_name} is required.")

    if "," not in raw_value and not raw_value.strip().isdigit():
        raise ValueError(f"{field_name} requires comma-separated numeric values.")

    values = []
    items = [item.strip() for item in raw_value.split(",")]

    if any(item == "" for item in items):
        raise ValueError(
            f"{field_name} contains empty values; use commas to separate numbers."
        )

    if max_items is None:
        max_items = MAX_LIST_ITEMS

    if len(items) > max_items:
        raise ValueError(
            f"{field_name} contains too many values. Maximum {max_items} values are allowed."
        )

    if max_value is None:
        max_value = MAX_NUMERIC_VALUE

    for item in items:
        if not re.fullmatch(r"\d+", item):
            raise ValueError(
                f"Invalid characters in {field_name}. Only digits and commas are allowed."
            )

        value = int(item)
        if value > max_value:
            raise ValueError(
                f"Value too large in {field_name}. Maximum allowed value is {max_value}."
            )

        values.append(value)

    return values


def parse_int(raw_value, field_name, min_value=None, max_value=None):
    if raw_value is None or raw_value.strip() == "":
        raise ValueError(f"{field_name} is required.")

    if not re.fullmatch(r"\d+", raw_value.strip()):
        raise ValueError(f"{field_name} must be a whole number.")

    value = int(raw_value.strip())

    if max_value is None:
        max_value = MAX_NUMERIC_VALUE

    if value > max_value:
        raise ValueError(
            f"{field_name} is too large. Maximum allowed value is {max_value}."
        )

    if min_value is not None and value < min_value:
        raise ValueError(f"{field_name} must be at least {min_value}.")

    return value


# CPU SCHED ALGORITHMS DITO

def fcfs(processes):

    processes.sort(key=lambda x: x["arrival"])

    current_time = 0
    timeline = []

    for p in processes:

        if current_time < p["arrival"]:
            current_time = p["arrival"]

        start = current_time
        p["waiting"] = start - p["arrival"]
        current_time += p["burst"]
        p["turnaround"] = p["waiting"] + p["burst"]

        timeline.append({
            "pid": p["pid"],
            "start": start,
            "end": current_time
        })

    return processes, timeline

def sjf(processes):

    processes = [p.copy() for p in processes]

    completed = []
    current_time = 0
    timeline = []

    while len(completed) < len(processes):

        available = [
            p for p in processes
            if p not in completed and p["arrival"] <= current_time
        ]

        if not available:
            current_time += 1
            continue

        shortest = min(available, key=lambda x: x["burst"])

        start = current_time
        shortest["waiting"] = start - shortest["arrival"]
        current_time += shortest["burst"]
        shortest["turnaround"] = (
            shortest["waiting"] + shortest["burst"]
        )

        timeline.append({
            "pid": shortest["pid"],
            "start": start,
            "end": current_time
        })

        completed.append(shortest)

    return completed, timeline

def priority_non_preemptive(processes):

    processes = [p.copy() for p in processes]

    completed = []
    current_time = 0
    timeline = []

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

        start = current_time
        highest["waiting"] = (
            start - highest["arrival"]
        )

        current_time += highest["burst"]

        highest["turnaround"] = (
            highest["waiting"] + highest["burst"]
        )

        timeline.append({
            "pid": highest["pid"],
            "start": start,
            "end": current_time
        })

        completed.append(highest)

    return completed, timeline

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
    timeline = []
    current_proc = None
    segment_start = None

    while completed < n:

        available = [
            p for p in processes
            if p["arrival"] <= current_time
            and remaining[p["pid"]] > 0
        ]

        if not available:
            current_time += 1
            continue

        next_proc = min(
            available,
            key=lambda x: (
                x["priority"],
                x["arrival"]
            )
        )

        if current_proc is None or current_proc["pid"] != next_proc["pid"]:
            if current_proc is not None:
                timeline.append({
                    "pid": current_proc["pid"],
                    "start": segment_start,
                    "end": current_time
                })

            current_proc = next_proc
            segment_start = current_time

        remaining[current_proc["pid"]] -= 1
        current_time += 1

        if remaining[current_proc["pid"]] == 0:

            completion[current_proc["pid"]] = current_time
            completed += 1
            timeline.append({
                "pid": current_proc["pid"],
                "start": segment_start,
                "end": current_time
            })
            current_proc = None
            segment_start = None

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

    return results, timeline

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
    timeline = []
    current_proc = None
    segment_start = None

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

        if current_proc is None or current_proc["pid"] != current["pid"]:
            if current_proc is not None:
                timeline.append({
                    "pid": current_proc["pid"],
                    "start": segment_start,
                    "end": current_time
                })

            current_proc = current
            segment_start = current_time

        current_time += run_time
        remaining[current["pid"]] -= run_time

        while i < n and processes[i]["arrival"] <= current_time:
            ready_queue.append(processes[i])
            i += 1

        if remaining[current["pid"]] > 0:
            ready_queue.append(current)
        else:
            completion[current["pid"]] = current_time
            timeline.append({
                "pid": current["pid"],
                "start": segment_start,
                "end": current_time
            })
            current_proc = None
            segment_start = None

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

    return results, timeline

# DITO YUNG INDEX

@app.route("/")
def index():
    return render_template("index.html")

#About page potaenanyo
@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/members')
def members():
    return render_template('members.html')

# CPU SCHEDULING PAGE

@app.route("/cpu-scheduling", methods=["GET", "POST"])
def cpu_scheduling():

    results = []
    timeline = []
    avg_waiting = 0
    avg_turnaround = 0
    timeline_end = 0
    error_message = None

    if request.method == "POST":

        try:
            arrivals = parse_int_list(
                request.form["arrival"],
                "Arrival Times",
                max_items=CPU_MAX_LIST_ITEMS,
                max_value=CPU_MAX_NUMERIC_VALUE
            )
            bursts = parse_int_list(
                request.form["burst"],
                "Burst Times",
                max_items=CPU_MAX_LIST_ITEMS,
                max_value=CPU_MAX_NUMERIC_VALUE
            )
            priorities = parse_int_list(
                request.form["priority"],
                "Priorities",
                max_items=CPU_MAX_LIST_ITEMS,
                max_value=CPU_MAX_NUMERIC_VALUE
            )

            if not (len(arrivals) == len(bursts) == len(priorities)):
                raise ValueError(
                    "Arrival, Burst, and Priority inputs must have the same number of values."
                )

            if any(a < 0 for a in arrivals):
                raise ValueError("Arrival Times must be non-negative numbers.")

            if any(b <= 0 for b in bursts):
                raise ValueError("Burst Times must be positive numbers.")

            if any(p < 0 for p in priorities):
                raise ValueError("Priorities must be non-negative numbers.")

            processes = []
            for i in range(len(arrivals)):
                processes.append({
                    "pid": f"P{i+1}",
                    "arrival": arrivals[i],
                    "burst": bursts[i],
                    "priority": priorities[i]
                })

            algorithm = request.form.get("algorithm", "FCFS")

            if algorithm == "FCFS":
                results, timeline = fcfs(processes)

            elif algorithm == "SJF":
                results, timeline = sjf(processes)

            elif algorithm == "PNP":
                results, timeline = priority_non_preemptive(processes)

            elif algorithm == "PP":
                results, timeline = priority_preemptive(processes)

            elif algorithm == "RR":
                quantum = parse_int(
                    request.form.get("quantum", ""),
                    "Time Quantum",
                    min_value=1
                )
                results, timeline = round_robin(processes, quantum)

            if results:
                avg_waiting = sum(
                    p["waiting"] for p in results
                ) / len(results)

                avg_turnaround = sum(
                    p["turnaround"] for p in results
                ) / len(results)

                timeline_end = max(segment["end"] for segment in timeline)

        except ValueError as e:
            error_message = str(e)

        except Exception as e:
            print("ERROR:", e)
            error_message = (
                "Invalid input detected. Please use only digits and commas where required."
            )

    return render_template(
        "cpu_sched.html",
        results=results,
        timeline=timeline,
        timeline_end=timeline_end,
        avg_waiting=avg_waiting,
        avg_turnaround=avg_turnaround,
        error_message=error_message
    )


# MEMORY MANAGEMENT PAGE

@app.route("/memory-management", methods=["GET", "POST"])
def memory_management():

    memory_blocks = []
    memory_map = []
    ram_segments = []
    job_sizes = []
    algorithm = None
    allocation_result = []
    error_message = None

    if request.method == "POST":

        try:
            memory_blocks = parse_int_list(
                request.form["blocks"],
                "Memory Holes"
            )

            job_sizes = parse_int_list(
                request.form["job_size"],
                "Incoming Job Size"
            )

            if any(b < 1 for b in memory_blocks):
                raise ValueError("Memory Holes must be greater than 0.")
            if any(j < 1 for j in job_sizes):
                raise ValueError("Job sizes must be greater than 0.")

            algorithm = request.form["algorithm"]

            for job_size in job_sizes:
                chosen_index = -1

                if algorithm == "FIRST":
                    for i, block in enumerate(memory_blocks):
                        if block >= job_size:
                            chosen_index = i
                            break

                elif algorithm == "BEST":
                    best_size = float("inf")
                    for i, block in enumerate(memory_blocks):
                        if block >= job_size and block < best_size:
                            best_size = block
                            chosen_index = i

                elif algorithm == "WORST":
                    worst_size = -1
                    for i, block in enumerate(memory_blocks):
                        if block >= job_size and block > worst_size:
                            worst_size = block
                            chosen_index = i

                if chosen_index != -1:
                    selected_block = memory_blocks[chosen_index]
                    remaining = selected_block - job_size

                    memory_blocks[chosen_index] = remaining

                    allocation_result.append(
                        f"Job {job_size}K allocated to block of {selected_block}K "
                        f"({remaining}K left over)" if remaining > 0
                        else f"Job {job_size}K allocated to block of {selected_block}K (exact fit)"
                    )

                else:
                    allocation_result.append(
                        f"Job {job_size}K: No suitable memory block found."
                    )

            for block in memory_blocks:
                memory_map.append({
                    "size": block,
                    "status": "FREE" if block > 0 else "USED"
                })

        except ValueError as e:
            error_message = str(e)

        except Exception as e:
            print("ERROR:", e)
            error_message = (
                "Invalid input detected. Please use only digits and commas where required."
            )

    return render_template(
        "mm_mng.html",
        memory_blocks=memory_blocks,
        memory_map=memory_map,
        ram_segments=ram_segments,
        job_sizes=job_sizes,
        algorithm=algorithm,
        allocation_result=allocation_result,
        error_message=error_message
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
    error_message = None
    
    if request.method == "POST":

        try:
            frames = parse_int(
                request.form["frames"],
                "Number of Frames",
                min_value=1,
                max_value=10
            )

            reference_string = parse_int_list(
                request.form["reference"],
                "Reference String"
            )

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

        except ValueError as e:
            error_message = str(e)

        except Exception as e:
            print("ERROR:", e)
            error_message = (
                "Invalid input detected. Please use only digits and commas where required."
            )

    return render_template(
        "virtual_mem.html",
        frames=frames,
        reference_string=reference_string,
        algorithm=algorithm,
        memory=memory,
        history=history,
        page_faults=page_faults,
        page_hits=page_hits,
        error_message=error_message
    )

# DISK MANAGEMENT PAGE

@app.route("/disk-management", methods=["GET", "POST"])
def disk_management():

    seek_sequence = []
    total_seek = 0
    algorithm = ""
    direction = ""
    error_message = None

    if request.method == "POST":

        try:
            tracks = parse_int(
                request.form["tracks"],
                "Number of Tracks",
                min_value=1,
                max_value=DISK_MAX_NUMERIC_VALUE
            )

            initial_head = parse_int(
                request.form["initial_head"],
                "Initial Head Position",
                min_value=0,
                max_value=DISK_MAX_NUMERIC_VALUE
            )

            if initial_head >= tracks:
                raise ValueError(
                    "Initial Head Position must be between 0 and Number of Tracks - 1."
                )

            requests = parse_int_list(
                request.form["requests"],
                "Request Queue",
                max_value=DISK_MAX_NUMERIC_VALUE
            )

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
                    closest = min(pending, key=lambda x: abs(current - x))
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

        except ValueError as e:
            error_message = str(e)

        except Exception as e:
            print("ERROR:", e)
            error_message = (
                "Invalid input detected. Please use only digits and commas where required."
            )

    return render_template("disk_management.html",
                            seek_sequence=seek_sequence,
                            total_seek=total_seek,
                            algorithm=algorithm,
                            direction=direction,
                            error_message=error_message)


if __name__ == "__main__":
    app.run(debug=True)