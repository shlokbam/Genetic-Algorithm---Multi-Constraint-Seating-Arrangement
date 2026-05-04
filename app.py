"""
Flask Web UI for Exam Seating Optimization
"""

from flask import Flask, render_template, request, jsonify, send_file
import json
import threading
import os
import sys
import io
import pandas as pd
from fpdf import FPDF

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from input_module import get_input
from ga_engine import GeneticAlgorithm
from fitness_module import evaluate_fitness
from data_representation import seat_to_position

app = Flask(__name__)

# Global state
progress_data = {
    "running": False,
    "generation": 0,
    "best_fitness": 0,
    "avg_fitness": 0,
    "history": [],
    "done": False,
    "result": None,
    "conflict_summary": {},
    "students": [],        # last used student list (for attendance management)
    "hall_config": {},
    "ga_params": {}
}


def build_students(form_data):
    branches  = form_data.getlist("branch[]")
    names     = form_data.getlist("name[]")
    rolls     = form_data.getlist("roll[]")
    subjects  = form_data.getlist("subject[]")
    divisions = form_data.getlist("division[]")

    students = []
    for i, (branch, name, roll, subject, division) in enumerate(
            zip(branches, names, rolls, subjects, divisions)):
        students.append({
            "id"      : i + 1,
            "name"    : name,
            "branch"  : branch,
            "roll_no" : roll,
            "subject" : subject,
            "division": division
        })
    return students


def build_students_from_excel(file_storage):
    import pandas as pd

    def normalize_column(value):
        return str(value).strip().lower().replace(' ', '_')

    try:
        df = pd.read_excel(file_storage)
    except Exception as exc:
        raise ValueError(f"Unable to read Excel file: {exc}")

    if df.empty:
        raise ValueError("Excel file is empty.")

    header_map = {normalize_column(col): col for col in df.columns}
    alias_map = {
        'name': ['name', 'student_name', 'student', 'full_name'],
        'roll_no': ['roll_no', 'roll number', 'rollnumber', 'roll', 'roll_number'],
        'branch': ['branch', 'course_branch'],
        'subject': ['subject', 'paper', 'course'],
        'division': ['division', 'div', 'section']
    }

    column_lookup = {}
    for key, aliases in alias_map.items():
        for alias in aliases:
            if alias in header_map:
                column_lookup[key] = header_map[alias]
                break

    missing = [key for key in ['name', 'branch', 'roll_no', 'subject', 'division'] if key not in column_lookup]
    if missing:
        raise ValueError(
            f"Excel file missing required column(s): {', '.join(missing)}. "
            "Use Name, Roll No, Branch, Subject, Division."
        )

    students = []
    for idx, row in df.iterrows():
        name = str(row[column_lookup['name']]).strip()
        branch = str(row[column_lookup['branch']]).strip()
        roll_no = str(row[column_lookup['roll_no']]).strip()
        subject = str(row[column_lookup['subject']]).strip()
        division = str(row[column_lookup['division']]).strip()

        if not all([name, branch, roll_no, subject, division]):
            raise ValueError(f"Row {idx + 2} contains empty required fields.")

        students.append({
            'id': len(students) + 1,
            'name': name,
            'branch': branch,
            'roll_no': roll_no,
            'subject': subject,
            'division': division
        })

    return students


def run_ga(students, hall_config, ga_params):
    global progress_data
    progress_data["running"]     = True
    progress_data["done"]        = False
    progress_data["history"]     = []
    progress_data["students"]    = students
    progress_data["hall_config"] = hall_config
    progress_data["ga_params"]   = ga_params

    class TrackingGA(GeneticAlgorithm):
        def run(self):
            from fitness_module import rank_population
            from genetic_operators import tournament_selection, order_crossover, swap_mutation, scramble_mutation
            import random, copy

            population  = self._init_population()
            best_chrom  = None
            best_fit    = -1.0
            stagnation  = 0
            STAGNATION_LIMIT = 50

            for gen in range(1, self.generations + 1):
                scored  = rank_population(population, self.hall_config)
                top_fit = scored[0][1]
                avg_fit = sum(f for _, f in scored) / len(scored)

                if top_fit > best_fit:
                    best_fit   = top_fit
                    best_chrom = copy.deepcopy(scored[0][0])
                    stagnation = 0
                else:
                    stagnation += 1

                progress_data["generation"]    = gen
                progress_data["best_fitness"]  = round(top_fit, 6)
                progress_data["avg_fitness"]   = round(avg_fit, 6)
                progress_data["history"].append((gen, round(top_fit, 6), round(avg_fit, 6)))

                if best_fit >= 1.0 or stagnation >= STAGNATION_LIMIT:
                    break

                population = self._evolve(population)

            return best_chrom, best_fit, progress_data["history"]

    ga = TrackingGA(students, hall_config, ga_params)
    best_arrangement, best_fitness, history = ga.run()

    # Build result grid
    rows = hall_config["rows"]
    cols = hall_config["cols"]
    grid = []
    for r in range(rows):
        row = []
        for c in range(cols):
            seat_idx = r * cols + c
            gene = best_arrangement[seat_idx]
            row.append(gene)
        grid.append(row)

    # Count conflicts
    offsets = [(-1,0),(1,0),(0,-1),(0,1)]
    branch_c = subject_c = division_c = 0
    total = hall_config["total_seats"]
    for seat_idx in range(total):
        student = best_arrangement[seat_idx]
        if not student: continue
        r, c = divmod(seat_idx, cols)
        for dr, dc in offsets:
            nr, nc = r+dr, c+dc
            if 0 <= nr < rows and 0 <= nc < cols:
                nb = best_arrangement[nr*cols+nc]
                if nb:
                    if nb["branch"]   == student["branch"]:   branch_c   += 1
                    if nb["subject"]  == student["subject"]:  subject_c  += 1
                    if nb["branch"] == student["branch"] and nb["division"] == student["division"]:
                        division_c += 1

    progress_data["result"] = {
        "grid"        : grid,
        "best_fitness": round(best_fitness, 6),
        "history"     : history,
        "hall_config" : hall_config,
        "conflicts"   : {
            "branch"  : branch_c   // 2,
            "subject" : subject_c  // 2,
            "division": division_c // 2
        }
    }
    progress_data["done"]    = True
    progress_data["running"] = False


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/run", methods=["POST"])
def run():
    global progress_data
    if progress_data["running"]:
        return jsonify({"error": "Already running"}), 400

    data = request.form
    rows = int(data.get("rows", 6))
    cols = int(data.get("cols", 10))

    hall_config = {"rows": rows, "cols": cols, "total_seats": rows * cols}
    ga_params   = {
        "population_size": int(data.get("pop_size", 150)),
        "generations"    : int(data.get("generations", 500)),
        "crossover_rate" : float(data.get("cx_rate", 0.85)),
        "mutation_rate"  : float(data.get("mut_rate", 0.04)),
        "elitism_count"  : int(data.get("elitism", 8))
    }

    use_demo = data.get("use_demo") == "true"
    if use_demo:
        students, _, _ = get_input(use_demo=True)
    else:
        excel_file = request.files.get('excel_file')
        if excel_file and excel_file.filename:
            try:
                students = build_students_from_excel(excel_file)
            except ValueError as exc:
                return jsonify({"error": str(exc)}), 400
        else:
            students = build_students(data)

    if len(students) > hall_config["total_seats"]:
        return jsonify({
            "error": f"Too many students ({len(students)}) for hall ({hall_config['total_seats']} seats)"
        }), 400

    progress_data = {
        "running": False, "generation": 0,
        "best_fitness": 0, "avg_fitness": 0,
        "history": [], "done": False, "result": None,
        "students": students,
        "hall_config": hall_config,
        "ga_params": ga_params
    }

    t = threading.Thread(target=run_ga, args=(students, hall_config, ga_params))
    t.daemon = True
    t.start()

    return jsonify({"status": "started"})


@app.route("/progress")
def progress():
    return jsonify({
        "generation"  : progress_data["generation"],
        "best_fitness": progress_data["best_fitness"],
        "avg_fitness" : progress_data["avg_fitness"],
        "done"        : progress_data["done"],
        "running"     : progress_data["running"]
    })


@app.route("/result")
def result():
    if not progress_data["done"]:
        return jsonify({"error": "Not done yet"}), 400
    return jsonify(progress_data["result"])


@app.route("/students")
def get_students():
    """Return the current student list so the UI can build the attendance panel."""
    if not progress_data["done"]:
        return jsonify({"error": "No result yet"}), 400
    return jsonify({"students": progress_data["students"]})


@app.route("/update_attendance", methods=["POST"])
def update_attendance():
    """
    Accepts JSON:
      {
        "absent_ids": [1, 5, 12, ...],
        "new_students": [
          {"name":..., "branch":..., "roll_no":..., "subject":..., "division":...},
          ...
        ]
      }
    Returns the updated student list (present students + new students).
    """
    if not progress_data.get("students"):
        return jsonify({"error": "No student data yet"}), 400

    body       = request.get_json(force=True)
    absent_ids = set(body.get("absent_ids", []))
    new_raw    = body.get("new_students", [])

    # Keep only present students
    present = [s for s in progress_data["students"] if s["id"] not in absent_ids]

    # Assign new IDs to new students (avoid collisions)
    max_id = max((s["id"] for s in progress_data["students"]), default=0)
    new_students = []
    for i, ns in enumerate(new_raw):
        max_id += 1
        new_students.append({
            "id"      : max_id,
            "name"    : ns.get("name",     f"New_{max_id:03d}"),
            "branch"  : ns.get("branch",   "CS"),
            "roll_no" : ns.get("roll_no",  f"NEW{max_id:03d}"),
            "subject" : ns.get("subject",  ""),
            "division": ns.get("division", "A")
        })

    updated = present + new_students
    return jsonify({
        "student_count": len(updated),
        "students"     : updated
    })


@app.route("/rerun", methods=["POST"])
def rerun():
    """
    Re-runs the GA with absent students removed and new students added.
    Body JSON: {
      "absent_ids": [...],
      "new_students": [...],
      "rows": <optional>, "cols": <optional>,
      "pop_size": <optional>, "generations": <optional>,
      "cx_rate": <optional>, "mut_rate": <optional>, "elitism": <optional>
    }
    """
    global progress_data
    if progress_data["running"]:
        return jsonify({"error": "Already running"}), 400
    if not progress_data.get("hall_config"):
        return jsonify({"error": "No previous run found"}), 400

    body = request.get_json(force=True)
    absent_ids = set(body.get("absent_ids", []))
    new_raw = body.get("new_students", [])

    # State Recovery: if server restarted, use students from request
    base_students = progress_data.get("students")
    if not base_students and "all_students" in body:
        base_students = body["all_students"]

    if not base_students:
        return jsonify({"error": "No student data available. Please run the full optimizer once."}), 400

    present = [s for s in base_students if s["id"] not in absent_ids]
    max_id = max((s["id"] for s in base_students), default=0)
    new_students = []
    for ns in new_raw:
        max_id += 1
        new_students.append({
            "id"      : max_id,
            "name"    : ns.get("name",     f"New_{max_id:03d}"),
            "branch"  : ns.get("branch",   "CS"),
            "roll_no" : ns.get("roll_no",  f"NEW{max_id:03d}"),
            "subject" : ns.get("subject",  ""),
            "division": ns.get("division", "A")
        })

    students = present + new_students
    if not students:
        return jsonify({"error": "No students provided"}), 400

    # Handle missing hall_config if server restarted
    prev_hall = progress_data.get("hall_config") or {}
    rows = int(body.get("rows", prev_hall.get("rows", 6)))
    cols = int(body.get("cols", prev_hall.get("cols", 10)))
    hall_config = {"rows": rows, "cols": cols, "total_seats": rows * cols}

    prev_params = progress_data.get("ga_params") or {}
    ga_params = {
        "population_size": int(body.get("pop_size", prev_params.get("population_size", 150))),
        "generations"    : int(body.get("generations", prev_params.get("generations", 500))),
        "crossover_rate" : float(body.get("cx_rate", prev_params.get("crossover_rate", 0.85))),
        "mutation_rate"  : float(body.get("mut_rate", prev_params.get("mutation_rate", 0.04))),
        "elitism_count"  : int(body.get("elitism", prev_params.get("elitism_count", 8)))
    }

    total_seats = hall_config["total_seats"]
    if len(students) > total_seats:
        return jsonify({
            "error": f"Too many students ({len(students)}) for hall ({total_seats} seats)"
        }), 400

    progress_data = {
        "running": False, "generation": 0,
        "best_fitness": 0, "avg_fitness": 0,
        "history": [], "done": False, "result": None,
        "students"   : students,
        "hall_config": hall_config,
        "ga_params"  : ga_params
    }

    t = threading.Thread(target=run_ga, args=(students, hall_config, ga_params))
    t.daemon = True
    t.start()

    return jsonify({"status": "started", "student_count": len(students)})


if __name__ == "__main__":
    os.makedirs("templates", exist_ok=True)
    # Get port from environment variable for deployment (Render, etc.)
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)