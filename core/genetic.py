import random
import numpy as np
import math
import copy

# ESTRUCTURA DEL INDIVIDUO
class Individual:
    def __init__(self, chromosome):
        self.chromosome = chromosome
        self.fitness = 0.0

# FUNCIONES DE EVALUACIÓN (CÁLCULO DE LA APTITUD)
def penalizacion_vision(individual_chromosome, students, seats, seat_distances):
    total_error = 0
    students_with_needs = 0
    for i, seat_idx in enumerate(individual_chromosome):
        student = students[i]
        if student.distancia_optima > 0:
            distancia_optima_R_estrella = student.distancia_optima
            asiento_asignado = seats[seat_idx]
            distancia_real_R = seat_distances[asiento_asignado]
            error = abs(distancia_real_R - distancia_optima_R_estrella)
            total_error += error
            students_with_needs += 1
    return total_error / max(students_with_needs, 1)

def penalizacion_compatibilidad(individual_chromosome, students, seats, compatibility_matrix):
    total_penalty = 0
    incompatible_pairs_count = 0 
    n = len(individual_chromosome)
    for i in range(n):
        for j in range(i + 1, n):
            if compatibility_matrix[i][j] == 1:
                incompatible_pairs_count += 1
                seat_i_coords = seats[individual_chromosome[i]]
                seat_j_coords = seats[individual_chromosome[j]]
                row_diff = abs(seat_i_coords[0] - seat_j_coords[0])
                col_diff = abs(seat_i_coords[1] - seat_j_coords[1])
                if row_diff <= 1 and col_diff <= 1:
                    total_penalty += 50.0
    return total_penalty / max(incompatible_pairs_count, 1)

def penalizacion_asientos_vacios(individual_chromosome, all_seats, seat_distances, d_max):
    occupied_seats_indices = set(individual_chromosome)
    total_penalty = 0
    empty_seat_count = 0
    for i, seat in enumerate(all_seats):
        if i not in occupied_seats_indices:
            dist = seat_distances[seat]
            penalty = (d_max - dist)
            total_penalty += penalty
            empty_seat_count += 1
    return total_penalty / max(empty_seat_count, 1)

def evaluate(individual, students, seats, compatibility_matrix, seat_distances, d_max, **kwargs):
    """
    Calcula el fitness basado en la fórmula: 1 / ((A+1)*(B+1)*(C+1)).
    El objetivo es MINIMIZAR cada penalización, lo cual se logra MAXIMIZANDO la inversa del producto.
    """
    # 1. Calcular las tres penalizaciones (errores)
    v_penalty = penalizacion_vision(individual.chromosome, students, seats, seat_distances)
    c_penalty = penalizacion_compatibilidad(individual.chromosome, students, seats, compatibility_matrix)
    e_penalty = penalizacion_asientos_vacios(individual.chromosome, seats, seat_distances, d_max)

    # 2. Normalizar cada penalización para que estén en una escala comparable.
    #    Esto es MUY IMPORTANTE cuando se multiplican, para que un criterio no domine a los otros.
    vp_normalized = v_penalty / d_max
    cp_normalized = c_penalty / 50.0 
    ep_normalized = e_penalty / d_max 

    # 3. Aplicar la fórmula del producto de las inversas
    #    Se suma 1 a cada término para evitar que un cero anule todo y para prevenir la división por cero.
    term1 = vp_normalized + 1
    term2 = cp_normalized + 1
    term3 = ep_normalized + 1
    
    # 4. Calcular el fitness final.
    fitness = 1 / (term1 * term2 * term3)
    
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
           ngen=150, pop_size=200, cxpb=0.8, mutpb=0.2, **kwargs): 
    
    num_students = len(students)
    seats_count = len(seats)
    d_max = max(seat_distances.values()) if seat_distances else 1

    population = []
    for _ in range(pop_size):
        chromosome = [random.randint(0, seats_count - 1) for _ in range(num_students)]
        population.append(Individual(chromosome))

    print("=== INICIANDO ALGORITMO GENÉTICO (IMPLEMENTACIÓN MANUAL) ===")
    for ind in population:
        repair(ind.chromosome, seats_count)
        ind.fitness = evaluate(ind, students, seats, compatibility_matrix, seat_distances, d_max)

    logbook = []
    hof = sorted(population, key=lambda ind: ind.fitness, reverse=True)[:3]

    for gen in range(1, ngen + 1):
        parents = selection_tournament(population, k=len(population), tournsize=3)
        offspring = [copy.deepcopy(p) for p in parents]

        for i in range(0, len(offspring) - 1, 2):
            if random.random() < cxpb:
                child1, child2 = crossover_uniform(offspring[i], offspring[i+1], indpb=0.5)
                offspring[i] = child1
                offspring[i+1] = child2

        for ind in offspring:
            if random.random() < mutpb:
                mutate_integer(ind, low=0, up=seats_count - 1, indpb=0.05)
        
        for ind in offspring:
            repair(ind.chromosome, seats_count)
            ind.fitness = evaluate(ind, students, seats, compatibility_matrix, seat_distances, d_max)
        
        population[:] = offspring

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
