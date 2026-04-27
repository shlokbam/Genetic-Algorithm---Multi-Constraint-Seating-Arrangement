import random
import copy
from data_representation import encode
from fitness_module       import rank_population, evaluate_fitness
from genetic_operators    import (
    tournament_selection, order_crossover,
    swap_mutation, scramble_mutation
)

class GeneticAlgorithm:
    def __init__(self, students, hall_config, ga_params):
        self.students    = students
        self.hall_config = hall_config
        self.params      = ga_params

        # Unpack GA hyper-parameters
        self.pop_size    = ga_params["population_size"]
        self.generations = ga_params["generations"]
        self.cx_rate     = ga_params["crossover_rate"]
        self.mut_rate    = ga_params["mutation_rate"]
        self.elitism_n   = ga_params["elitism_count"]


    def _init_population(self):
        """Generate an initial population of random chromosomes."""
        population = []
        for _ in range(self.pop_size):
            chrom = encode(self.students, self.hall_config)
            population.append(chrom)
        return population


    def _evolve(self, population):
        """Produce the next generation from the current population."""
        scored = rank_population(population, self.hall_config)

        new_population = []

        # Elitism: carry the best chromosomes unchanged
        for i in range(self.elitism_n):
            new_population.append(copy.deepcopy(scored[i][0]))

        # Fill the rest with offspring
        while len(new_population) < self.pop_size:
            # Selection
            parent1 = tournament_selection(scored)
            parent2 = tournament_selection(scored)

            # Crossover
            if random.random() < self.cx_rate:
                child = order_crossover(parent1, parent2)
            else:
                child = copy.deepcopy(parent1)

            # Mutation
            child = swap_mutation(child, self.mut_rate)
            child = scramble_mutation(child, self.mut_rate * 0.5)

            new_population.append(child)

        return new_population
