# ================================================
# FILE: core/genetic.py
# ================================================
# Este archivo contiene el "cerebro" del proyecto: la implementación del algoritmo genético.
# Aquí se define cómo se evalúa una solución, cómo se cruzan, mutan y seleccionan los individuos.

import random
import numpy as np
from deap import base, creator, tools, algorithms
import math

# =============================================================================
# === SECCIÓN 1: FUNCIONES DE EVALUACIÓN (CÁLCULO DE LA APTITUD) ================
# =============================================================================
# Estas funciones calculan qué "tan buena" es una solución (un individuo).
# La aptitud se compone de dos partes: el puntaje por visión y la penalización por compatibilidad.

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
            # El puntaje es más alto cuanto menor es la distancia 'd'.
            # El multiplicador 2.0 da más importancia a este tipo de estudiante.
            v_i = max(0, 1.0 - (d / d_max)) * 2.0
        elif student.vision == "no_near":  # No ve bien de cerca (mejor atrás)
            # El puntaje es más alto cuanto mayor es la distancia 'd'.
            v_i = (d / d_max) * 1.5
        else:  # Visión normal
            v_i = 0.8  # Puntaje base para no penalizar ubicaciones intermedias.

        v_total += v_i

    return v_total / len(students) # Se normaliza por el número de estudiantes.

def penalizacion_compatibilidad(individual, students, seats, compatibility_matrix):
    """
    FÓRMULA 2: PENALIZACIÓN POR COMPATIBILIDAD
    Calcula una penalización si los estudiantes que se distraen mutuamente están sentados cerca.
    - La penalización es MÁS ALTA cuanto más cerca están.
    - Una solución ideal tendría una penalización de 0.
    - VALORES ALTOS = MALA DISTRIBUCIÓN (más penalización).
    """
    total_penalty = 0
    penalty_count = 0
    n = len(individual)

    for i in range(n):
        for j in range(i + 1, n):
            # Si son compatibles (se distraen, compatibility_matrix[i][j] == 1)
            if compatibility_matrix[i][j] == 1:
                seat_i = seats[individual[i]]
                seat_j = seats[individual[j]]

                # Calcular distancia euclidiana entre los asientos
                dist_euc = math.sqrt((seat_i[0] - seat_j[0]) ** 2 + (seat_i[1] - seat_j[1]) ** 2)

                # Penalización progresiva: más alta para distancias más cortas.
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
    
    # Se normaliza por el número de pares conflictivos para no depender del total de incompatibilidades.
    return total_penalty / max(penalty_count, 1)

def evaluate(individual, students, seats, compatibility_matrix, seat_distances, d_max, w1=0.4, w2=0.6):
    """
    FUNCIÓN DE APTITUD (FITNESS) PRINCIPAL
    Esta función combina el puntaje de visión y la penalización de compatibilidad en un único valor de "aptitud".
    El algoritmo genético intentará MAXIMIZAR este valor.

    Fórmula: fitness = (w1 * puntaje_vision) - (w2 * penalizacion_compatibilidad)

    - w1 y w2 son los pesos que determinan qué criterio es más importante.
      Aquí se da más peso (0.6) a separar a los estudiantes conflictivos.
    """
    v_score = score_vista(individual, students, seats, seat_distances, d_max)
    c_penalty = penalizacion_compatibilidad(individual, students, seats, compatibility_matrix)

    # Normalización para que ambos términos de la fórmula estén en una escala similar.
    v_normalized = v_score / 2.0
    p_normalized = c_penalty / 50.0

    # Función objetivo: maximizar vista, minimizar penalización.
    fitness = (w1 * v_normalized) - (w2 * p_normalized)

    return (fitness,) # DEAP requiere que el fitness se devuelva como una tupla.


# =============================================================================
# === SECCIÓN 2: OPERADORES AUXILIARES (REPARACIÓN Y CREACIÓN INTELIGENTE) ======
# =============================================================================

def feasible(individual):
    """Verifica que un individuo sea válido (que no haya asientos duplicados)."""
    return len(set(individual)) == len(individual)

def repair(individual, seats_count):
    """Repara un individuo inválido reemplazando los asientos duplicados por otros disponibles."""
    used_seats = set()
    duplicates = []
    
    # Encuentra los asientos usados y los duplicados
    for i, seat in enumerate(individual):
        if seat in used_seats:
            duplicates.append(i)
        else:
            used_seats.add(seat)
            
    # Encuentra los asientos que no se usaron
    available_seats = [s for s in range(seats_count) if s not in used_seats]
    random.shuffle(available_seats)
    
    # Asigna asientos disponibles a las posiciones duplicadas
    for i in duplicates:
        if available_seats:
            individual[i] = available_seats.pop()
            
    return individual

def create_smart_individual(students, seats, compatibility_matrix, seat_distances):
    """
    Crea un individuo inicial de forma "inteligente" en lugar de aleatoria.
    Esto ayuda al algoritmo a converger más rápido a una buena solución.
    """
    # Esta es una función heurística que intenta hacer una buena primera asignación.
    num_students = len(students)
    individual = [-1] * num_students
    available_seats = list(range(len(seats)))
    
    # Prioridad 1: Asignar estudiantes con problemas de visión
    # 'no_far' a los asientos de adelante
    no_far_students = [i for i, s in enumerate(students) if s.vision == "no_far"]
    front_seats = sorted(range(len(seats)), key=lambda s: seat_distances[seats[s]])
    for student_idx in no_far_students:
        if front_seats:
            seat_idx = front_seats.pop(0)
            individual[student_idx] = seat_idx
            available_seats.remove(seat_idx)

    # 'no_near' a los asientos de atrás
    no_near_students = [i for i, s in enumerate(students) if s.vision == "no_near"]
    back_seats = sorted([s for s in available_seats], key=lambda s: seat_distances[seats[s]], reverse=True)
    for student_idx in no_near_students:
        if back_seats:
            seat_idx = back_seats.pop(0)
            individual[student_idx] = seat_idx
            available_seats.remove(seat_idx)
            
    # Asignar el resto de estudiantes a los asientos restantes
    remaining_students = [i for i, s in enumerate(students) if individual[i] == -1]
    random.shuffle(available_seats)
    for student_idx in remaining_students:
        if available_seats:
            seat_idx = available_seats.pop(0)
            individual[student_idx] = seat_idx
            
    return individual

# =============================================================================
# === SECCIÓN 3: FUNCIÓN PRINCIPAL DEL ALGORITMO GENÉTICO (run_ga) =============
# =============================================================================
# Esta es la función que configura y ejecuta todo el proceso evolutivo.

def run_ga(students, seats, compatibility_matrix, seat_distances, front_rows,
           ngen=150, pop_size=200, w1=0.4, w2=0.6):
    """
    Configura y ejecuta el Algoritmo Genético.
    """
    num_students = len(students)
    d_max = max(seat_distances.values()) if seat_distances else 1

    # --- CONFIGURACIÓN DE DEAP ---
    # Se crea la estructura básica: una función de fitness que se maximiza
    # y un individuo que es una lista de Python.
    creator.create("FitnessMax", base.Fitness, weights=(1.0,))
    creator.create("Individual", list, fitness=creator.FitnessMax)

    # La 'toolbox' es donde se registran los operadores genéticos.
    toolbox = base.Toolbox()

    # --- REGISTRO DE OPERADORES GENÉTICOS ---

    # Creación de individuos y población
    toolbox.register("individual", tools.initRepeat, creator.Individual, 
                     lambda: random.choice(range(len(seats))), num_students)
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)

    # Función de evaluación (fitness)
    toolbox.register("evaluate", evaluate, students=students, seats=seats,
                     compatibility_matrix=compatibility_matrix, seat_distances=seat_distances,
                     d_max=d_max, w1=w1, w2=w2)

    # OPERADOR DE CRUCE (EMPATEJAMIENTO): tools.cxPartialyMatched (PMX)
    # Combina dos padres para crear dos hijos. Es bueno para problemas de permutación
    # como este, donde cada asiento solo puede usarse una vez.
    toolbox.register("mate", tools.cxPartialyMatched)

    # OPERADOR DE MUTACIÓN: tools.mutShuffleIndexes
    # Cambia aleatoriamente la posición (asiento) de algunos estudiantes.
    # 'indpb' es la probabilidad de que cada gen (asiento) sea mutado.
    toolbox.register("mutate", tools.mutShuffleIndexes, indpb=0.05)

    # OPERADOR DE SELECCIÓN (PODA): tools.selTournament
    # Elige a los 'padres' de la siguiente generación. Se realizan 'tournsize' torneos:
    # en cada uno se elige un grupo aleatorio de individuos y el mejor de ese grupo gana.
    # Esto da a los mejores individuos una mayor probabilidad de ser seleccionados.
    toolbox.register("select", tools.selTournament, tournsize=3)

    # --- EJECUCIÓN DEL ALGORITMO ---
    
    # Crear población inicial y repararla para que sea válida.
    pop = toolbox.population(n=pop_size)
    for ind in pop:
        repair(ind, len(seats))

    # Hall of Fame: objeto que almacena a los mejores individuos encontrados.
    hof = tools.HallOfFame(3)

    # Estadísticas para seguir el progreso del algoritmo.
    stats = tools.Statistics(lambda ind: ind.fitness.values)
    stats.register("avg", np.mean)
    stats.register("max", np.max)
    stats.register("min", np.min)
    
    print("=== INICIANDO ALGORITMO GENÉTICO ===")
    
    # El algoritmo principal de DEAP que ejecuta el ciclo evolutivo.
    algorithms.eaSimple(
        population=pop,
        toolbox=toolbox,
        cxpb=0.8,  # Probabilidad de cruce
        mutpb=0.2, # Probabilidad de mutación
        ngen=ngen, # Número de generaciones
        stats=stats,
        halloffame=hof,
        verbose=True
    )
    
    print("=== ALGORITMO COMPLETADO ===")
    
    # Devuelve los 3 mejores individuos únicos encontrados.
    top_solutions = []
    for ind in hof:
        if list(ind) not in top_solutions:
            top_solutions.append(list(ind))
            
    return top_solutions