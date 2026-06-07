from flask import Flask, render_template, request

app = Flask(__name__)


# =========================
# FCFS SCHEDULING
# =========================
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


# =========================
# HOME ROUTE
# =========================
@app.route("/", methods=["GET", "POST"])
def home():

    results = []
    avg_waiting = 0
    avg_turnaround = 0

    if request.method == "POST":

        try:
            arrivals = request.form["arrival"].split(",")
            bursts = request.form["burst"].split(",")
            priorities = request.form["priority"].split(",")

            # safety check (prevents IndexError)
            n = min(len(arrivals), len(bursts), len(priorities))

            processes = []

            for i in range(n):

                processes.append({
                    "pid": f"P{i+1}",
                    "arrival": int(arrivals[i].strip()),
                    "burst": int(bursts[i].strip()),
                    "priority": int(priorities[i].strip()),
                })

            algorithm = request.form.get("algorithm", "FCFS")

            if algorithm == "FCFS":
                results = fcfs(processes)

            else:
                # fallback for now
                results = fcfs(processes)

            if len(results) > 0:

                avg_waiting = sum(
                    p["waiting"] for p in results
                ) / len(results)

                avg_turnaround = sum(
                    p["turnaround"] for p in results
                ) / len(results)

        except Exception as e:
            print("Error:", e)
            results = []

    return render_template(
        "index.html",
        results=results,
        avg_waiting=avg_waiting,
        avg_turnaround=avg_turnaround
    )


if __name__ == "__main__":
    app.run(debug=True)