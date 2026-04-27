from collections import Counter
from data_representation import seat_to_position

# Neighbour offsets
ADJACENT_OFFSETS = [(-1, 0), (1, 0), (0, -1), (0, 1)]
DIAGONAL_OFFSETS = [(-1,-1), (-1, 1), (1,-1),  (1, 1)]
ALL_OFFSETS      = ADJACENT_OFFSETS + DIAGONAL_OFFSETS

# Penalty weights
ADJACENT_PENALTY       = 20
DIAGONAL_PENALTY       = 15
SAME_ROW_PENALTY       = 5
SAME_COL_PENALTY       = 5
CLUSTER_PENALTY        = 10
FRONT_BACK_PENALTY     = 8
ROLL_PROXIMITY_PENALTY = 6

SAME_SUBJECT_ADJ_PENALTY   = 18
SAME_SUBJECT_DIAG_PENALTY  = 12
SAME_SUBJECT_ROW_PENALTY   = 4

SAME_DIVISION_ADJ_PENALTY  = 12
SAME_DIVISION_DIAG_PENALTY = 8
SAME_DIVISION_ROW_PENALTY  = 3


def evaluate_fitness(chromosome, hall_config, use_diagonals=True):
    rows  = hall_config["rows"]
    cols  = hall_config["cols"]
    total = hall_config["total_seats"]
    penalty = 0

    grid = [[None] * cols for _ in range(rows)]
    for seat_idx in range(total):
        if chromosome[seat_idx] is not None:
            r, c = divmod(seat_idx, cols)
            grid[r][c] = chromosome[seat_idx]

    offsets = ALL_OFFSETS if use_diagonals else ADJACENT_OFFSETS

    # Pass 1: pairwise neighbour checks
    for seat_idx in range(total):
        student = chromosome[seat_idx]
        if student is None:
            continue
        r, c = divmod(seat_idx, cols)

        for (dr, dc) in offsets:
            nr, nc = r + dr, c + dc
            if not (0 <= nr < rows and 0 <= nc < cols):
                continue
            neighbour = grid[nr][nc]
            if neighbour is None:
                continue

            is_adjacent = (dr, dc) in ADJACENT_OFFSETS

            # Constraint 1 & 2: Same branch
            if neighbour["branch"] == student["branch"]:
                penalty += ADJACENT_PENALTY if is_adjacent else DIAGONAL_PENALTY

            # Constraint 8: Same subject
            if neighbour["subject"] == student["subject"]:
                penalty += SAME_SUBJECT_ADJ_PENALTY if is_adjacent else SAME_SUBJECT_DIAG_PENALTY

            # Constraint 9: Same division within same branch
            if neighbour["branch"] == student["branch"] and neighbour["division"] == student["division"]:
                penalty += SAME_DIVISION_ADJ_PENALTY if is_adjacent else SAME_DIVISION_DIAG_PENALTY

    penalty //= 2

    # Pass 2: row-level checks
    for r in range(rows):
        row_students = [grid[r][c] for c in range(cols) if grid[r][c] is not None]

        branch_counts = Counter(s["branch"] for s in row_students)
        for count in branch_counts.values():
            if count > 1:
                penalty += SAME_ROW_PENALTY * (count - 1)

        subject_counts = Counter(s["subject"] for s in row_students)
        for count in subject_counts.values():
            if count > 1:
                penalty += SAME_SUBJECT_ROW_PENALTY * (count - 1)

        division_counts = Counter((s["branch"], s["division"]) for s in row_students)
        for count in division_counts.values():
            if count > 1:
                penalty += SAME_DIVISION_ROW_PENALTY * (count - 1)

    # Pass 3: column-level checks
    for c in range(cols):
        col_students = [grid[r][c] for r in range(rows) if grid[r][c] is not None]
        branch_counts = Counter(s["branch"] for s in col_students)
        for count in branch_counts.values():
            if count > 1:
                penalty += SAME_COL_PENALTY * (count - 1)

    # Pass 4: 3x3 cluster check
    for r in range(rows - 2):
        for c in range(cols - 2):
            block = []
            for br in range(r, r + 3):
                for bc in range(c, c + 3):
                    if grid[br][bc] is not None:
                        block.append(grid[br][bc])
            branch_counts = Counter(s["branch"] for s in block)
            for count in branch_counts.values():
                if count >= 3:
                    penalty += CLUSTER_PENALTY * (count - 2)

    # Pass 5: front-back same column consecutive rows
    for c in range(cols):
        for r in range(rows - 1):
            s1 = grid[r][c]
            s2 = grid[r + 1][c]
            if s1 and s2 and s1["branch"] == s2["branch"]:
                penalty += FRONT_BACK_PENALTY

    # Pass 6: roll-number proximity
    for seat_idx in range(total):
        student = chromosome[seat_idx]
        if student is None:
            continue
        r, c = divmod(seat_idx, cols)
        for (dr, dc) in ADJACENT_OFFSETS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols:
                neighbour = grid[nr][nc]
                if neighbour and neighbour["branch"] == student["branch"]:
                    try:
                        roll1 = int(''.join(filter(str.isdigit, student["roll_no"])))
                        roll2 = int(''.join(filter(str.isdigit, neighbour["roll_no"])))
                        if abs(roll1 - roll2) == 1:
                            penalty += ROLL_PROXIMITY_PENALTY
                    except ValueError:
                        pass

    fitness = 1.0 / (1.0 + penalty)
    return fitness


def rank_population(population, hall_config):
    scored = [(chrom, evaluate_fitness(chrom, hall_config)) for chrom in population]
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored