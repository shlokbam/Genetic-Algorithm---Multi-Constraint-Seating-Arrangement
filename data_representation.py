import random

def encode(students, hall_config):
    total_seats = hall_config["total_seats"]
    chromosome  = [None] * total_seats
    indices     = random.sample(range(total_seats), len(students))
    for seat_idx, student in zip(indices, students):
        chromosome[seat_idx] = student
    return chromosome

def decode(chromosome, hall_config):
    cols = hall_config["cols"]
    grid = []
    for i in range(0, len(chromosome), cols):
        grid.append(chromosome[i:i + cols])
    return grid


def seat_to_position(seat_idx, hall_config):
    cols = hall_config["cols"]
    return divmod(seat_idx, cols)


def position_to_seat(row, col, hall_config):
    return row * hall_config["cols"] + col
