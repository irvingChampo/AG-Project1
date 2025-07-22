import random
import numpy as np
import math
import copy

# ESTRUCTURA DEL INDIVIDUO
class Individual:
    def __init__(self, chromosome):
        #lista de índices de asientos.
        self.chromosome = chromosome
        #puntuación de qué tan buena es esta solución.
        self.fitness = 0.0

#FUNCIONES DE EVALUACIÓN (CÁLCULO DE LA APTITUD)

def score_vista(individual_chromosome, students, seats, seat_distances, d_max):
    v_total = 0
    for i, seat_idx in enumerate(individual_chromosome):
        student = students[i]
        seat = seats[seat_idx]
        d = seat_distances[seat]

        if student.vision == "no_far":
            v_i = max(0, 1.0 - (d / d_max)) * 2.0
        elif student.vision == "no_near":
            v_i = (d / d_max) * 1.5
        else:
            v_i = 0.8
        v_total += v_i
    return v_total / len(students)

def penalizacion_compatibilidad(individual_chromosome, students, seats, compatibility_matrix):
    total_penalty = 0
    penalty_count = 0
    n = len(individual_chromosome)
    for i in range(n):
        for j in range(i + 1, n):
            if compatibility_matrix[i][j] == 1:
                seat_i = seats[individual_chromosome[i]]
                seat_j = seats[individual_chromosome[j]]
                dist_euc = math.sqrt((seat_i[0] - seat_j[0]) ** 2 + (seat_i[1] - seat_j[1]) ** 2)
                if dist_euc <= 1.0: penalty = 50.0
                elif dist_euc <= 1.42: penalty = 25.0
                elif dist_euc <= 2.0: penalty = 10.0
                else: penalty = 0.0
                total_penalty += penalty
                penalty_count += 1
    return total_penalty / max(penalty_count, 1)

def evaluate(individual, students, seats, compatibility_matrix, seat_distances, d_max, w1=0.4, w2=0.6):
    v_score = score_vista(individual.chromosome, students, seats, seat_distances, d_max)
    c_penalty = penalizacion_compatibilidad(individual.chromosome, students, seats, compatibility_matrix)
    v_normalized = v_score / 2.0
    p_normalized = c_penalty / 50.0
    fitness = (w1 * v_normalized) - (w2 * p_normalized)
    return fitness

# REPARACIÓN

def feasible(individual_chromosome):
    return len(set(individual_chromosome)) == len(individual_chromosome)

def repair(individual_chromosome, seats_count):
    if feasible(individual_chromosome):
        return individual_chromosome
    used_seats = set()
    duplicates_indices = []
    for i, seat in enumerate(individual_chromosome):
        if seat in used_seats:
            duplicates_indices.append(i)
        else:
            used_seats.add(seat)
    available_seats = [s for s in range(seats_count) if s not in used_seats]
    random.shuffle(available_seats)
    for i in duplicates_indices:
        if available_seats:
            individual_chromosome[i] = available_seats.pop()
    return individual_chromosome

# OPERADORES GENÉTICOS 

def selection_tournament(population, k, tournsize):
    selected = []
    for _ in range(k):
        aspirants = random.sample(population, tournsize)
        winner = max(aspirants, key=lambda ind: ind.fitness)
        selected.append(winner)
    return selected

def crossover_uniform(ind1, ind2, indpb):
    child1_chromo = []
    child2_chromo = []
    for i in range(len(ind1.chromosome)):
        if random.random() < indpb:
            child1_chromo.append(ind2.chromosome[i])
            child2_chromo.append(ind1.chromosome[i])
        else:
            child1_chromo.append(ind1.chromosome[i])
            child2_chromo.append(ind2.chromosome[i])
    return Individual(child1_chromo), Individual(child2_chromo)

def mutate_integer(individual, low, up, indpb):
    for i in range(len(individual.chromosome)):
        if random.random() < indpb:
            individual.chromosome[i] = random.randint(low, up)

# FUNCIÓN PRINCIPAL DEL ALGORITMO GENÉTICO (run_ga) 

def run_ga(students, seats, compatibility_matrix, seat_distances, front_rows,
           ngen=150, pop_size=200, w1=0.4, w2=0.6, cxpb=0.8, mutpb=0.2):
    
    num_students = len(students)
    seats_count = len(seats)
    d_max = max(seat_distances.values()) if seat_distances else 1

    # --- CREACIÓN DE LA POBLACIÓN INICIAL ---
    population = []
    for _ in range(pop_size):
        chromosome = [random.randint(0, seats_count - 1) for _ in range(num_students)]
        population.append(Individual(chromosome))

    # --- REPARACIÓN Y EVALUACIÓN INICIAL ---
    print("=== INICIANDO ALGORITMO GENÉTICO (IMPLEMENTACIÓN MANUAL) ===")
    for ind in population:
        repair(ind.chromosome, seats_count)
        ind.fitness = evaluate(ind, students, seats, compatibility_matrix, seat_distances, d_max, w1, w2)

    # --- PREPARACIÓN PARA EL BUCLE EVOLUTIVO ---
    logbook = []
    hof = sorted(population, key=lambda ind: ind.fitness, reverse=True)[:3]

    # --- BUCLE DE GENERACIONES ---
    for gen in range(1, ngen + 1):
        # 1. SELECCIÓN (EMPAREJAMIENTO)
        parents = selection_tournament(population, k=len(population), tournsize=3)
        offspring = [copy.deepcopy(p) for p in parents]

        # 2. CRUZA (CROSSOVER)
        for i in range(0, len(offspring) - 1, 2):
            if random.random() < cxpb:
                child1, child2 = crossover_uniform(offspring[i], offspring[i+1], indpb=0.5)
                offspring[i] = child1
                offspring[i+1] = child2

        # 3. MUTACIÓN
        for ind in offspring:
            if random.random() < mutpb:
                mutate_integer(ind, low=0, up=seats_count - 1, indpb=0.05)
        
        # 4. REPARACIÓN Y EVALUACIÓN DE LOS NUEVOS HIJOS
        for ind in offspring:
            repair(ind.chromosome, seats_count)
            ind.fitness = evaluate(ind, students, seats, compatibility_matrix, seat_distances, d_max, w1, w2)
        
        # 5. LA NUEVA POBLACIÓN REEMPLAZA A LA ANTIGUA
        population[:] = offspring

        # 6. ACTUALIZACIÓN DE ESTADÍSTICAS Y HALL OF FAME
        hof.extend(population)
        hof = sorted(hof, key=lambda ind: ind.fitness, reverse=True)
        unique_hof_chromosomes = []
        new_hof = []
        for ind in hof:
            if ind.chromosome not in unique_hof_chromosomes:
                unique_hof_chromosomes.append(ind.chromosome)
                new_hof.append(ind)
        hof = new_hof[:3]

        fitness_values = [ind.fitness for ind in population]
        stats_record = {
            'gen': gen,
            'avg': np.mean(fitness_values),
            'max': np.max(fitness_values),
            'min': np.min(fitness_values),
        }
        logbook.append(stats_record)
        
        print(f"gen {gen:<4} avg {stats_record['avg']:.6f} max {stats_record['max']:.6f} min {stats_record['min']:.6f}")

    print("=== ALGORITMO COMPLETADO ===")
    
    top_solutions = [ind.chromosome for ind in hof]
            
    return top_solutions, logbook