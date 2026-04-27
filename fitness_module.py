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

    # Build grid and extract fast-lookup data
    grid = [[None] * cols for _ in range(rows)]
    occupied_indices = []
    
    for seat_idx, student in enumerate(chromosome):
        if student is not None:
            r, c = divmod(seat_idx, cols)
            grid[r][c] = student
            occupied_indices.append((seat_idx, r, c, student))

    offsets = ALL_OFFSETS if use_diagonals else ADJACENT_OFFSETS

    # Pass 1: pairwise neighbour checks + Roll No Proximity
    for seat_idx, r, c, student in occupied_indices:
        s_branch = student["branch"]
        s_subject = student["subject"]
        s_div = student["division"]
        
        # Roll No Parsing (cached if possible, but here we do it once per student per fitness check)
        # Optimized: Only parse if we find a same-branch neighbor
        roll1 = None

        for (dr, dc) in offsets:
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols:
                neighbour = grid[nr][nc]
                if neighbour is None:
                    continue

                is_adjacent = (dr, dc) in ADJACENT_OFFSETS
                n_branch = neighbour["branch"]
                n_subject = neighbour["subject"]
                
                # Branch check
                if n_branch == s_branch:
                    penalty += ADJACENT_PENALTY if is_adjacent else DIAGONAL_PENALTY
                    
                    # Roll proximity (only for adjacent same-branch)
                    if is_adjacent:
                        try:
                            if roll1 is None:
                                roll1 = int(''.join(filter(str.isdigit, student["roll_no"])))
                            roll2 = int(''.join(filter(str.isdigit, neighbour["roll_no"])))
                            if abs(roll1 - roll2) == 1:
                                penalty += ROLL_PROXIMITY_PENALTY
                        except ValueError:
                            pass

                # Subject check
                if n_subject == s_subject:
                    penalty += SAME_SUBJECT_ADJ_PENALTY if is_adjacent else SAME_SUBJECT_DIAG_PENALTY

                # Division check
                if n_branch == s_branch and neighbour["division"] == s_div:
                    penalty += SAME_DIVISION_ADJ_PENALTY if is_adjacent else SAME_DIVISION_DIAG_PENALTY

    # Pairwise penalties are counted twice (A-B and B-A)
    penalty //= 2

    # Pass 2: row-level checks
    for r in range(rows):
        row = grid[r]
        branch_counts = {}
        subj_counts = {}
        div_counts = {}
        
        for student in row:
            if student is None: continue
            
            b = student["branch"]
            s = student["subject"]
            d = (b, student["division"])
            
            branch_counts[b] = branch_counts.get(b, 0) + 1
            subj_counts[s] = subj_counts.get(s, 0) + 1
            div_counts[d] = div_counts.get(d, 0) + 1
            
        for count in branch_counts.values():
            if count > 1: penalty += SAME_ROW_PENALTY * (count - 1)
        for count in subj_counts.values():
            if count > 1: penalty += SAME_SUBJECT_ROW_PENALTY * (count - 1)
        for count in div_counts.values():
            if count > 1: penalty += SAME_DIVISION_ROW_PENALTY * (count - 1)

    # Pass 3: column-level checks + Front-Back
    for c in range(cols):
        prev_branch = None
        col_branch_counts = {}
        
        for r in range(rows):
            student = grid[r][c]
            if student is None:
                prev_branch = None
                continue
            
            b = student["branch"]
            col_branch_counts[b] = col_branch_counts.get(b, 0) + 1
            
            # Front-back check
            if prev_branch == b:
                penalty += FRONT_BACK_PENALTY
            prev_branch = b
            
        for count in col_branch_counts.values():
            if count > 1: penalty += SAME_COL_PENALTY * (count - 1)

    # Pass 4: 3x3 cluster check
    for r in range(rows - 2):
        for c in range(cols - 2):
            counts = {}
            for br in range(r, r + 3):
                row_slice = grid[br][c : c+3]
                for student in row_slice:
                    if student:
                        b = student["branch"]
                        counts[b] = counts.get(b, 0) + 1
            
            for count in counts.values():
                if count >= 3:
                    penalty += CLUSTER_PENALTY * (count - 2)

    return 1.0 / (1.0 + penalty)


def rank_population(population, hall_config):
    scored = [(chrom, evaluate_fitness(chrom, hall_config)) for chrom in population]
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored