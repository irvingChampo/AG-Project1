import random
import numpy as np
from deap import base, creator, tools, algorithms
import math

def score_vista(individual, students, seats, seat_distances, d_max):
    v_total = 0
    for i, seat_idx in enumerate(individual):
        student = students[i]
        seat = seats[seat_idx]
        d = seat_distances[seat]
        if student.vision == "cerca":
            v_i = 1.0 - (d / d_max)
        else:
            v_i = 0.5
        v_total += v_i
    return v_total / len(students)

def penalizacion_compatibilidad(individual, students, seats, compatibility_matrix):
    """
    Penaliza estudiantes compatibles que están cerca.
    VALORES ALTOS = MALA FORMACIÓN (más penalización)
    """
    P = []
    n = len(individual)
    for i in range(n):
        for j in range(i+1, n):
            if compatibility_matrix[i][j] == 1:  # Son compatibles (se distraen)
                P.append((i, j))

    if not P:
        return 0

    suma_penalizacion = 0
    for (i, j) in P:
        seat_i = seats[individual[i]]
        seat_j = seats[individual[j]]
        
        # Calcular distancia euclidiana
        dist_euc = math.sqrt((seat_i[0] - seat_j[0]) ** 2 + (seat_i[1] - seat_j[1]) ** 2)
        
        # PENALIZACIÓN EXPONENCIAL: mientras más cerca, mayor penalización
        if dist_euc == 0:  # Mismo asiento (no debería pasar)
            penalizacion = 10.0
        elif dist_euc <= 1.0:  # Adyacentes (muy cerca)
            penalizacion = 5.0
        elif dist_euc <= 1.41:  # Diagonales (cerca)
            penalizacion = 3.0
        elif dist_euc <= 2.0:  # Relativamente cerca
            penalizacion = 1.0
        else:  # Suficientemente separados
            penalizacion = 0.0
        
        suma_penalizacion += penalizacion

    return suma_penalizacion / len(P)

def evaluate(individual, students, seats, compatibility_matrix, seat_distances, d_max, w1=0.6, w2=0.4):
    """
    Función de evaluación mejorada con mayor peso a la separación
    """
    v_score = score_vista(individual, students, seats, seat_distances, d_max)
    c_penalty = penalizacion_compatibilidad(individual, students, seats, compatibility_matrix)
    
    # Aumentar el peso de la penalización para forzar mayor separación
    fx = w1 * v_score - w2 * c_penalty
    return (fx,)

def feasible(individual):
    """Verifica que no haya asientos duplicados"""
    return len(set(individual)) == len(individual)

def repair(individual, seats_count):
    """Repara individuos con asientos duplicados"""
    available_seats = list(range(seats_count))
    used_seats = set()
    
    for i in range(len(individual)):
        if individual[i] in used_seats:
            # Buscar un asiento disponible
            for seat in available_seats:
                if seat not in used_seats:
                    individual[i] = seat
                    used_seats.add(seat)
                    break
        else:
            used_seats.add(individual[i])
    
    return individual

def create_smart_individual(students, seats, compatibility_matrix, seat_distances):
    """
    Crea un individuo inicial inteligente que separa estudiantes compatibles
    """
    num_students = len(students)
    num_seats = len(seats)
    
    # Crear lista de estudiantes con problemas de vista
    students_cerca = [i for i, s in enumerate(students) if s.vision == "cerca"]
    students_lejos = [i for i, s in enumerate(students) if s.vision == "lejos"]
    
    # Ordenar asientos por proximidad al pizarrón
    seats_ordenados = sorted(range(num_seats), key=lambda x: seat_distances[seats[x]])
    
    # Inicializar asignación
    individual = [-1] * num_students
    seats_usados = set()
    
    # Paso 1: Asignar estudiantes "cerca" a las primeras filas
    for i, student_idx in enumerate(students_cerca):
        if i < len(seats_ordenados):
            seat_idx = seats_ordenados[i]
            individual[student_idx] = seat_idx
            seats_usados.add(seat_idx)
    
    # Paso 2: Asignar estudiantes "lejos" evitando compatibilidades
    available_seats = [s for s in seats_ordenados if s not in seats_usados]
    
    for student_idx in students_lejos:
        mejor_seat = None
        menor_conflicto = float('inf')
        
        for seat_idx in available_seats:
            conflicto = 0
            seat_pos = seats[seat_idx]
            
            # Calcular conflicto con estudiantes ya asignados
            for other_student, other_seat_idx in enumerate(individual):
                if other_seat_idx != -1 and compatibility_matrix[student_idx][other_student] == 1:
                    other_seat_pos = seats[other_seat_idx]
                    dist = math.sqrt((seat_pos[0] - other_seat_pos[0])**2 + 
                                   (seat_pos[1] - other_seat_pos[1])**2)
                    if dist <= 2.0:  # Demasiado cerca
                        conflicto += (3.0 - dist)
            
            if conflicto < menor_conflicto:
                menor_conflicto = conflicto
                mejor_seat = seat_idx
        
        if mejor_seat is not None:
            individual[student_idx] = mejor_seat
            available_seats.remove(mejor_seat)
            seats_usados.add(mejor_seat)
    
    # Paso 3: Asignar asientos restantes aleatoriamente
    for i in range(num_students):
        if individual[i] == -1:
            if available_seats:
                seat_idx = random.choice(available_seats)
                individual[i] = seat_idx
                available_seats.remove(seat_idx)
    
    return individual

def mutate_smart(individual, students, seats, compatibility_matrix, indpb=0.3):
    """
    Mutación inteligente que evita juntar estudiantes compatibles
    """
    if random.random() < indpb:
        # Seleccionar dos estudiantes para intercambiar
        i, j = random.sample(range(len(individual)), 2)
        
        # Calcular conflicto antes del intercambio
        conflicto_antes = calcular_conflicto_individual(individual, students, seats, compatibility_matrix)
        
        # Hacer intercambio temporal
        individual[i], individual[j] = individual[j], individual[i]
        
        # Calcular conflicto después del intercambio
        conflicto_despues = calcular_conflicto_individual(individual, students, seats, compatibility_matrix)
        
        # Si empeora, revertir el intercambio
        if conflicto_despues > conflicto_antes:
            individual[i], individual[j] = individual[j], individual[i]
    
    return individual,

def calcular_conflicto_individual(individual, students, seats, compatibility_matrix):
    """Calcula el conflicto total de un individuo"""
    conflicto = 0
    n = len(individual)
    for i in range(n):
        for j in range(i+1, n):
            if compatibility_matrix[i][j] == 1:
                seat_i = seats[individual[i]]
                seat_j = seats[individual[j]]
                dist = math.sqrt((seat_i[0] - seat_j[0])**2 + (seat_i[1] - seat_j[1])**2)
                if dist <= 2.0:
                    conflicto += (3.0 - dist)
    return conflicto

def run_ga(students, seats, compatibility_matrix, seat_distances, front_rows, ngen=100, pop_size=100, w1=0.6, w2=0.4):
    num_students = len(students)
    d_max = max(seat_distances.values())

    creator.create("FitnessMax", base.Fitness, weights=(1.0,))
    creator.create("Individual", list, fitness=creator.FitnessMax)

    toolbox = base.Toolbox()
    
    # Usar inicialización inteligente
    toolbox.register("individual", lambda: create_smart_individual(students, seats, compatibility_matrix, seat_distances))
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)

    toolbox.register("evaluate", lambda ind: evaluate(ind, students, seats, compatibility_matrix, seat_distances, d_max, w1, w2))
    toolbox.register("mate", tools.cxPartialyMatched)  # Mejor para permutaciones
    toolbox.register("mutate", lambda ind: mutate_smart(ind, students, seats, compatibility_matrix))
    toolbox.register("select", tools.selTournament, tournsize=5)  # Selección más estricta

    pop = toolbox.population(n=pop_size)

    # Estadísticas para monitorear progreso
    stats = tools.Statistics(lambda ind: ind.fitness.values)
    stats.register("avg", np.mean)
    stats.register("max", np.max)
    
    # Ejecutar algoritmo con más generaciones
    for gen in range(ngen):
        offspring = algorithms.varAnd(pop, toolbox, cxpb=0.7, mutpb=0.3)

        # Reparar individuos inválidos
        for ind in offspring:
            if not feasible(ind):
                repair(ind, len(seats))

        # Evaluar descendencia
        fits = toolbox.map(toolbox.evaluate, offspring)
        for fit, ind in zip(fits, offspring):
            ind.fitness.values = fit
        
        pop = toolbox.select(offspring, k=len(pop))
        
        # Mostrar progreso cada 10 generaciones
        if gen % 10 == 0:
            fits = [ind.fitness.values[0] for ind in pop]
            print(f"Gen {gen}: Max={max(fits):.3f}, Avg={np.mean(fits):.3f}")

    # Retornar las 3 mejores soluciones
    top3 = tools.selBest(pop, k=3)
    return top3

# Función para visualizar la asignación
def print_assignment(individual, students, seats, compatibility_matrix):
    print("\n=== ASIGNACIÓN DE ASIENTOS ===")
    for i, seat_idx in enumerate(individual):
        seat = seats[seat_idx]
        print(f"{students[i].name} -> Fila {seat[0]}, Columna {seat[1]} (Vista: {students[i].vision})")
    
    print("\n=== ANÁLISIS DE COMPATIBILIDADES ===")
    for i in range(len(individual)):
        for j in range(i+1, len(individual)):
            if compatibility_matrix[i][j] == 1:
                seat_i = seats[individual[i]]
                seat_j = seats[individual[j]]
                dist = math.sqrt((seat_i[0] - seat_j[0])**2 + (seat_i[1] - seat_j[1])**2)
                status = "❌ MUY CERCA" if dist <= 1.41 else "⚠️ CERCA" if dist <= 2.0 else "✅ SEPARADOS"
                print(f"{students[i].name} - {students[j].name}: distancia {dist:.2f} {status}")