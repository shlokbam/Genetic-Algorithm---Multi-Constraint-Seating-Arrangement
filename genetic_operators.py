import random

def tournament_selection(scored_population, tournament_size=5):
    """
    Selects the best individual from a random subset of the population.
    """
    contestants = random.sample(scored_population, min(tournament_size, len(scored_population)))
    winner = max(contestants, key=lambda x: x[1])
    return winner[0] # Returns a reference to the chromosome (list)


def order_crossover(parent1, parent2):
    """
    Preserves relative ordering of students from parent1 and fills remaining from parent2.
    """
    size = len(parent1)
    child = [None] * size

    # Step 1: pick a random segment
    start = random.randint(0, size - 1)
    end   = random.randint(start, size - 1)

    # Step 2: copy segment from parent1
    placed_ids = set()
    for i in range(start, end + 1):
        child[i] = parent1[i]
        if parent1[i] is not None:
            placed_ids.add(parent1[i]["id"])

    # Step 3: fill from parent2 in order, skipping duplicates
    p2_idx = 0
    for i in list(range(0, start)) + list(range(end + 1, size)):
        while p2_idx < size:
            gene = parent2[p2_idx]
            p2_idx += 1
            if gene is None or gene["id"] in placed_ids:
                continue
            child[i] = gene
            placed_ids.add(gene["id"])
            break

    # Step 4: repair missing students from parent1 if any positions are still empty
    missing = [g for g in parent1 if g is not None and g["id"] not in placed_ids]
    for i in range(size):
        if child[i] is None and missing:
            child[i] = missing.pop(0)

    return child


def swap_mutation(chromosome, mutation_rate=0.05):
    """
    Randomly swaps two students' positions.
    """
    chrom = chromosome[:] # Fast shallow copy of the list
    size  = len(chrom)
    for i in range(size):
        if random.random() < mutation_rate:
            j = random.randint(0, size - 1)
            chrom[i], chrom[j] = chrom[j], chrom[i]
    return chrom


def scramble_mutation(chromosome, mutation_rate=0.05):
    """
    Randomly shuffles a sub-segment of the chromosome.
    """
    chrom = chromosome[:] # Fast shallow copy of the list
    if random.random() < mutation_rate:
        size  = len(chrom)
        start = random.randint(0, size - 2)
        end   = random.randint(start + 1, size - 1)
        sub   = chrom[start:end + 1]
        random.shuffle(sub)
        chrom[start:end + 1] = sub
    return chrom