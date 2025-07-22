# ================================================
# FILE: core/genetic.py
# ================================================
# Este archivo contiene el "cerebro" del proyecto: la implementación del algoritmo genético.
# Aquí se define cómo se evalúa una solución, cómo se cruzan, mutan y seleccionan los individuos.

import random
import numpy as np
from deap import base, creator, tools, algorithms
import math

# Definición de tipos de DEAP fuera de la función para evitar advertencias y recreaciones.
# Se crea una función de Fitness que se busca maximizar (weights=(1.0,))
creator.create("FitnessMax", base.Fitness, weights=(1.0,))
# Se crea un tipo de Individuo que es una lista y tiene el atributo de fitness definido arriba.
creator.create("Individual", list, fitness=creator.FitnessMax)


# =============================================================================
# === SECCIÓN 1: FUNCIONES DE EVALUACIÓN (CÁLCULO DE LA APTITUD) ================
# =============================================================================

def score_vista(individual, students, seats, seat_distances, d_max):
    """
    FÓRMULA 1: PUNTAJE DE VISTA
    Calcula un puntaje basado en la correcta ubicación de los estudiantes según su visión.
    - Maximiza el puntaje si los estudiantes que 'no ven de lejos' están cerca del pizarrón.
    - Maximiza el puntaje si los estudiantes que 'no ven de cerca' están lejos.
    """
    v_total = 0
    for i, seat_idx in enumerate(individual):
        student = students[i]
        seat = seats[seat_idx]
        d = seat_distances[seat]  # Distancia del asiento al pizarrón (número de fila)

        if student.vision == "no_far":  # No ve bien de lejos (necesita estar cerca)
            v_i = max(0, 1.0 - (d / d_max)) * 2.0
        elif student.vision == "no_near":  # No ve bien de cerca (mejor atrás)
            v_i = (d / d_max) * 1.5
        else:  # Visión normal
            v_i = 0.8  # Puntaje base

        v_total += v_i

    return v_total / len(students) # Se normaliza por el número de estudiantes.

def penalizacion_compatibilidad(individual, students, seats, compatibility_matrix):
    """
    FÓRMULA 2: PENALIZACIÓN POR COMPATIBILIDAD
    Calcula una penalización si los estudiantes que se distraen mutuamente están sentados cerca.
    """
    total_penalty = 0
    penalty_count = 0
    n = len(individual)

    for i in range(n):
        for j in range(i + 1, n):
            # Si son incompatibles (se distraen, compatibility_matrix[i][j] == 1)
            if compatibility_matrix[i][j] == 1:
                seat_i = seats[individual[i]]
                seat_j = seats[individual[j]]

                # Calcular distancia euclidiana entre los asientos
                dist_euc = math.sqrt((seat_i[0] - seat_j[0]) ** 2 + (seat_i[1] - seat_j[1]) ** 2)

                # Penalización progresiva
                if dist_euc <= 1.0:    # Adyacentes directos
                    penalty = 50.0
                elif dist_euc <= 1.42: # Diagonales cercanos (sqrt(2))
                    penalty = 25.0
                elif dist_euc <= 2.0:  # Un asiento de por medio
                    penalty = 10.0
                else:                  # Suficientemente separados
                    penalty = 0.0
                
                total_penalty += penalty
                penalty_count += 1
    
    return total_penalty / max(penalty_count, 1)

def evaluate(individual, students, seats, compatibility_matrix, seat_distances, d_max, w1=0.4, w2=0.6):
    """
    FUNCIÓN DE APTITUD (FITNESS) PRINCIPAL
    Combina el puntaje de visión y la penalización de compatibilidad.
    """
    v_score = score_vista(individual, students, seats, seat_distances, d_max)
    c_penalty = penalizacion_compatibilidad(individual, students, seats, compatibility_matrix)

    v_normalized = v_score / 2.0
    p_normalized = c_penalty / 50.0

    fitness = (w1 * v_normalized) - (w2 * p_normalized)

    return (fitness,) # DEAP requiere que el fitness se devuelva como una tupla.


# =============================================================================
# === SECCIÓN 2: OPERADORES AUXILIARES (REPARACIÓN) ============================
# =============================================================================

def feasible(individual):
    """Verifica que un individuo sea válido (que no haya asientos duplicados)."""
    return len(set(individual)) == len(individual)

def repair(individual, seats_count):
    """Repara un individuo inválido reemplazando los asientos duplicados por otros disponibles."""
    if feasible(individual):
        return individual # Si ya es válido, no hacer nada

    used_seats = set()
    duplicates_indices = []
    
    for i, seat in enumerate(individual):
        if seat in used_seats:
            duplicates_indices.append(i)
        else:
            used_seats.add(seat)
            
    available_seats = [s for s in range(seats_count) if s not in used_seats]
    random.shuffle(available_seats)
    
    for i in duplicates_indices:
        if available_seats:
            individual[i] = available_seats.pop()
            
    return individual

# =============================================================================
# === SECCIÓN 3: FUNCIÓN PRINCIPAL DEL ALGORITMO GENÉTICO (run_ga) =============
# =============================================================================

def run_ga(students, seats, compatibility_matrix, seat_distances, front_rows,
           ngen=150, pop_size=200, w1=0.4, w2=0.6, cxpb=0.8, mutpb=0.2):
    """
    Configura y ejecuta el Algoritmo Genético con los operadores y bucle correctos.
    """
    num_students = len(students)
    seats_count = len(seats)
    d_max = max(seat_distances.values()) if seat_distances else 1

    toolbox = base.Toolbox()

    # --- REGISTRO DE OPERADORES GENÉTICOS ---
    toolbox.register("attr_seat", random.randint, 0, seats_count - 1)
    toolbox.register("individual", tools.initRepeat, creator.Individual, toolbox.attr_seat, num_students)
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)
    toolbox.register("mate", tools.cxUniform, indpb=0.5)
    toolbox.register("mutate", tools.mutUniformInt, low=0, up=seats_count - 1, indpb=0.05)
    toolbox.register("select", tools.selTournament, tournsize=3)
    toolbox.register("evaluate", evaluate, students=students, seats=seats,
                     compatibility_matrix=compatibility_matrix, seat_distances=seat_distances,
                     d_max=d_max, w1=w1, w2=w2)

    # --- EJECUCIÓN DEL ALGORITMO ---
    
    pop = toolbox.population(n=pop_size)
    hof = tools.HallOfFame(3)
    stats = tools.Statistics(lambda ind: ind.fitness.values)
    stats.register("avg", np.mean)
    stats.register("max", np.max)
    stats.register("min", np.min)
    
    # Se crea un 'logbook' para guardar el historial de estadísticas
    logbook = []
    
    print("=== INICIANDO ALGORITMO GENÉTICO ===")
    
    # 1. Reparar y evaluar la población inicial
    for ind in pop:
        repair(ind, seats_count)
    
    fitnesses = [toolbox.evaluate(ind) for ind in pop]
    for ind, fit in zip(pop, fitnesses):
        ind.fitness.values = fit

    # 2. Iniciar el ciclo de generaciones
    for gen in range(1, ngen + 1):
        offspring = toolbox.select(pop, len(pop))
        offspring = [toolbox.clone(ind) for ind in offspring]

        for i in range(1, len(offspring), 2):
            if random.random() < cxpb:
                toolbox.mate(offspring[i-1], offspring[i])
                del offspring[i-1].fitness.values, offspring[i].fitness.values
        
        for i in range(len(offspring)):
            if random.random() < mutpb:
                toolbox.mutate(offspring[i])
                del offspring[i].fitness.values

        invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
        for ind in invalid_ind:
            repair(ind, seats_count) # Reparación ANTES de evaluar
        
        fitnesses = [toolbox.evaluate(ind) for ind in invalid_ind]
        for ind, fit in zip(invalid_ind, fitnesses):
            ind.fitness.values = fit
            
        pop[:] = offspring
        
        hof.update(pop)
        record = stats.compile(pop)
        
        # Se añade la generación actual al registro y se guarda en el logbook
        record['gen'] = gen
        logbook.append(record)
        
        print(f"gen {gen:<4} nevals {len(invalid_ind):<4} avg {record['avg']:.6f} max {record['max']:.6f} min {record['min']:.6f}")

    print("=== ALGORITMO COMPLETADO ===")
    
    top_solutions = []
    for ind in hof:
        if list(ind) not in top_solutions:
            top_solutions.append(list(ind))
            
    # Se devuelve tanto las soluciones como el logbook con el historial
    return top_solutions, logbook