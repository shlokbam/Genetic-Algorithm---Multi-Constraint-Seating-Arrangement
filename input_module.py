"""
Input Module
Collects and validates student data, hall configuration, and GA parameters.
"""

import random


def get_input(use_demo=True):
    """
    Returns:
        students       : list of dicts {id, name, branch, roll_no, subject, division}
        hall_config    : dict {rows, cols, total_seats}
        ga_params      : dict {population_size, generations, crossover_rate, mutation_rate, elitism_count}
    """
    if not use_demo:
        raise ValueError("Only demo mode is supported for get_input in the web version.")

    students, hall_config, ga_params = _generate_demo_data()
    _validate(students, hall_config)
    return students, hall_config, ga_params


def _generate_demo_data():
    branches  = ["CS", "IT", "AIML", "ENTC", "MECH"]
    divisions = ["A", "B", "C"]

    branch_subject = {
        "CS"  : "DAA",
        "IT"  : "SE",
        "AIML": "AI",
        "ENTC": "DBMS",
        "MECH": "Thermodynamics"
    }

    students = []
    sid = 1
    for branch in branches:
        for i in range(1, 13):
            division = divisions[(i - 1) % 3]
            students.append({
                "id"      : sid,
                "name"    : f"Student_{sid:03d}",
                "branch"  : branch,
                "roll_no" : f"{branch[:2]}{i:03d}",
                "subject" : branch_subject[branch],
                "division": division
            })
            sid += 1

    random.shuffle(students)

    hall_config = {
        "rows"       : 6,
        "cols"       : 10,
        "total_seats": 60
    }

    ga_params = {
        "population_size": 150,
        "generations"    : 500,
        "crossover_rate" : 0.85,
        "mutation_rate"  : 0.04,
        "elitism_count"  : 8
    }

    print(f"[Demo] {len(students)} students | Hall: {hall_config['rows']}x{hall_config['cols']}")
    print(f"[Demo] Branches : {', '.join(branches)}")
    print(f"[Demo] Subjects : {', '.join(set(branch_subject.values()))}")
    print(f"[Demo] Divisions: {', '.join(divisions)}")
    return students, hall_config, ga_params


def _validate(students, hall_config):
    total_seats = hall_config["rows"] * hall_config["cols"]
    if len(students) > total_seats:
        raise ValueError(
            f"Validation Error: {len(students)} students but only {total_seats} seats."
        )
    ids = [s["id"] for s in students]
    if len(ids) != len(set(ids)):
        raise ValueError("Validation Error: Duplicate student IDs detected.")
    print(f"[✓] Validation passed — {len(students)} students, {total_seats} seats available.")