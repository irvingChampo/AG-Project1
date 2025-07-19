import random
import numpy as np
from deap import base, creator, tools, algorithms
import math

def score_vista(individual, students, seats, seat_distances, d_max):
    """
    Puntaje de vista mejorado con mejor diferenciación entre tipos de visión
    """
    v_total = 0
    for i, seat_idx in enumerate(individual):
        student = students[i]
        seat = seats[seat_idx]
        d = seat_distances[seat]
        
        if student.vision == "no_far":  # No ve bien de lejos (necesita estar cerca)
            # Puntaje alto para asientos cerca del pizarrón
            v_i = max(0, 1.0 - (d / d_max)) * 2.0  # Multiplicador para dar más peso
        elif student.vision == "no_near":  # No ve bien de cerca (mejor atrás)
            # Puntaje alto para asientos lejos del pizarrón
            v_i = (d / d_max) * 1.5
        else:  # Visión normal
            v_i = 0.8  # Puntaje base moderado
        
        v_total += v_i
    
    return v_total / len(students)

def penalizacion_compatibilidad(individual, students, seats, compatibility_matrix):
    """
    Penalización mejorada por proximidad entre estudiantes compatibles
    VALORES ALTOS = MALA FORMACIÓN (más penalización)
    """
    total_penalty = 0
    penalty_count = 0
    n = len(individual)
    
    for i in range(n):
        for j in range(i+1, n):
            # Si son compatibles (se distraen mutuamente)
            if compatibility_matrix[i][j] == 1:
                seat_i = seats[individual[i]]
                seat_j = seats[individual[j]]
                
                # Calcular distancia euclidiana
                dist_euc = math.sqrt((seat_i[0] - seat_j[0]) ** 2 + (seat_i[1] - seat_j[1]) ** 2)
                
                # Penalización progresiva basada en distancia
                if dist_euc == 0:  # Mismo asiento (imposible, pero por seguridad)
                    penalty = 100.0
                elif dist_euc <= 1.0:  # Adyacentes directos
                    penalty = 50.0
                elif dist_euc <= 1.41:  # Diagonales adyacentes
                    penalty = 25.0
                elif dist_euc <= 2.0:  # Segunda fila de proximidad
                    penalty = 10.0
                elif dist_euc <= 2.83:  # Diagonales de segunda fila
                    penalty = 5.0
                elif dist_euc <= 3.0:  # Tercera proximidad
                    penalty = 2.0
                else:  # Suficientemente separados
                    penalty = 0.0
                
                total_penalty += penalty
                penalty_count += 1
    
    # Normalizar por el número de pares compatibles
    return total_penalty / max(penalty_count, 1)

def evaluate(individual, students, seats, compatibility_matrix, seat_distances, d_max, w1=0.4, w2=0.6):
    """
    Función de evaluación balanceada con mayor peso en separación de compatibles
    """
    v_score = score_vista(individual, students, seats, seat_distances, d_max)
    c_penalty = penalizacion_compatibilidad(individual, students, seats, compatibility_matrix)
    
    # Normalizar el puntaje de vista para que esté en escala similar
    v_normalized = v_score / 2.0  # Asumiendo que el máximo es ~2.0
    
    # Función objetivo: maximizar vista, minimizar penalización
    fitness = w1 * v_normalized - w2 * (c_penalty / 50.0)  # Normalizar penalización
    
    return (fitness,)

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
    Crea un individuo inicial inteligente que considera ambos criterios
    """
    num_students = len(students)
    num_seats = len(seats)
    
    # Clasificar estudiantes por tipo de visión
    students_no_far = [(i, s) for i, s in enumerate(students) if s.vision == "no_far"]
    students_no_near = [(i, s) for i, s in enumerate(students) if s.vision == "no_near"]
    students_normal = [(i, s) for i, s in enumerate(students) if s.vision == "normal"]
    
    # Ordenar asientos por distancia al pizarrón
    seats_by_distance = sorted(range(num_seats), key=lambda x: seat_distances[seats[x]])
    
    # Inicializar asignación
    individual = [-1] * num_students
    seats_disponibles = set(range(num_seats))
    
    # Paso 1: Asignar estudiantes que no ven bien de lejos a primeras filas
    for idx, (student_idx, student) in enumerate(students_no_far):
        if seats_by_distance and seats_by_distance[0] in seats_disponibles:
            best_seat = find_best_seat_avoiding_conflicts(
                student_idx, seats_disponibles, individual, students, 
                seats, compatibility_matrix, prefer_front=True
            )
            if best_seat is not None:
                individual[student_idx] = best_seat
                seats_disponibles.remove(best_seat)
    
    # Paso 2: Asignar estudiantes que no ven bien de cerca a filas posteriores
    seats_back = [s for s in seats_by_distance if s in seats_disponibles]
    seats_back.reverse()  # Empezar por atrás
    
    for student_idx, student in students_no_near:
        best_seat = find_best_seat_avoiding_conflicts(
            student_idx, seats_disponibles, individual, students,
            seats, compatibility_matrix, prefer_front=False
        )
        if best_seat is not None:
            individual[student_idx] = best_seat
            seats_disponibles.remove(best_seat)
    
    # Paso 3: Asignar estudiantes con visión normal
    for student_idx, student in students_normal:
        best_seat = find_best_seat_avoiding_conflicts(
            student_idx, seats_disponibles, individual, students,
            seats, compatibility_matrix, prefer_front=None
        )
        if best_seat is not None:
            individual[student_idx] = best_seat
            seats_disponibles.remove(best_seat)
    
    # Paso 4: Asignar asientos restantes aleatoriamente
    remaining_students = [i for i in range(num_students) if individual[i] == -1]
    remaining_seats = list(seats_disponibles)
    
    for student_idx in remaining_students:
        if remaining_seats:
            seat_idx = random.choice(remaining_seats)
            individual[student_idx] = seat_idx
            remaining_seats.remove(seat_idx)
    
    return individual

def find_best_seat_avoiding_conflicts(student_idx, available_seats, current_assignment, 
                                    students, seats, compatibility_matrix, prefer_front=None):
    """
    Encuentra el mejor asiento evitando conflictos con estudiantes ya asignados
    """
    if not available_seats:
        return None
    
    best_seat = None
    best_score = float('-inf')
    
    for seat_idx in available_seats:
        score = 0
        seat_pos = seats[seat_idx]
        
        # Bonificación por preferencia de ubicación
        if prefer_front is True:
            score += (10 - seat_pos[0])  # Menor número de fila = más cerca
        elif prefer_front is False:
            score += seat_pos[0]  # Mayor número de fila = más lejos
        
        # Penalización por compatibilidades conflictivas
        for other_student_idx, other_seat_idx in enumerate(current_assignment):
            if (other_seat_idx != -1 and 
                compatibility_matrix[student_idx][other_student_idx] == 1):
                
                other_seat_pos = seats[other_seat_idx]
                dist = math.sqrt((seat_pos[0] - other_seat_pos[0])**2 + 
                               (seat_pos[1] - other_seat_pos[1])**2)
                
                # Bonificar distancias mayores
                if dist > 3.0:
                    score += 10
                elif dist > 2.0:
                    score += 5
                elif dist > 1.41:
                    score += 2
                else:
                    score -= 20  # Penalizar mucho la proximidad
        
        if score > best_score:
            best_score = score
            best_seat = seat_idx
    
    return best_seat

def mutate_smart(individual, students, seats, compatibility_matrix, indpb=0.2):
    """
    Mutación inteligente que considera el impacto en el fitness
    """
    if random.random() < indpb:
        n = len(individual)
        
        # Calcular fitness antes de la mutación
        fitness_antes = calcular_fitness_rapido(individual, students, seats, compatibility_matrix)
        
        # Seleccionar estudiantes para intercambiar
        i, j = random.sample(range(n), 2)
        
        # Realizar intercambio
        individual[i], individual[j] = individual[j], individual[i]
        
        # Calcular fitness después
        fitness_despues = calcular_fitness_rapido(individual, students, seats, compatibility_matrix)
        
        # Si el intercambio empeora significativamente, revertir
        if fitness_despues < fitness_antes - 0.1:  # Tolerancia pequeña
            individual[i], individual[j] = individual[j], individual[i]
    
    return individual,

def calcular_fitness_rapido(individual, students, seats, compatibility_matrix):
    """
    Cálculo rápido de fitness para mutación
    """
    # Penalización por compatibilidades cercanas
    penalty = 0
    n = len(individual)
    
    for i in range(n):
        for j in range(i+1, n):
            if compatibility_matrix[i][j] == 1:
                seat_i = seats[individual[i]]
                seat_j = seats[individual[j]]
                dist = math.sqrt((seat_i[0] - seat_j[0])**2 + (seat_i[1] - seat_j[1])**2)
                if dist <= 2.0:
                    penalty += (3.0 - dist)
    
    return -penalty  # Negativo porque queremos minimizar conflictos

def run_ga(students, seats, compatibility_matrix, seat_distances, front_rows, 
           ngen=150, pop_size=200, w1=0.4, w2=0.6):
    """
    Algoritmo genético mejorado que devuelve las 3 mejores soluciones
    """
    num_students = len(students)
    d_max = max(seat_distances.values())

    # Limpiar creadores previos si existen
    if hasattr(creator, "FitnessMax"):
        del creator.FitnessMax
    if hasattr(creator, "Individual"):
        del creator.Individual

    creator.create("FitnessMax", base.Fitness, weights=(1.0,))
    creator.create("Individual", list, fitness=creator.FitnessMax)

    toolbox = base.Toolbox()
    
    # Registrar operadores
    toolbox.register("individual", lambda: create_smart_individual(
        students, seats, compatibility_matrix, seat_distances))
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)
    toolbox.register("evaluate", lambda ind: evaluate(
        ind, students, seats, compatibility_matrix, seat_distances, d_max, w1, w2))
    toolbox.register("mate", tools.cxPartialyMatched)
    toolbox.register("mutate", lambda ind: mutate_smart(
        ind, students, seats, compatibility_matrix, indpb=0.15))
    toolbox.register("select", tools.selTournament, tournsize=7)

    # Crear población inicial
    pop = toolbox.population(n=pop_size)

    # Estadísticas
    stats = tools.Statistics(lambda ind: ind.fitness.values)
    stats.register("avg", np.mean)
    stats.register("max", np.max)
    stats.register("min", np.min)
    
    print("=== INICIANDO ALGORITMO GENÉTICO ===")
    print(f"Población: {pop_size}, Generaciones: {ngen}")
    print(f"Estudiantes: {num_students}, Asientos: {len(seats)}")
    
    # Evaluar población inicial
    fitnesses = list(map(toolbox.evaluate, pop))
    for ind, fit in zip(pop, fitnesses):
        ind.fitness.values = fit

    # Evolución
    for gen in range(ngen):
        # Selección y variación
        offspring = toolbox.select(pop, len(pop))
        offspring = list(map(toolbox.clone, offspring))
        
        # Cruzamiento
        for child1, child2 in zip(offspring[::2], offspring[1::2]):
            if random.random() < 0.8:  # Probabilidad de cruzamiento
                toolbox.mate(child1, child2)
                del child1.fitness.values
                del child2.fitness.values

        # Mutación
        for mutant in offspring:
            if random.random() < 0.25:  # Probabilidad de mutación
                toolbox.mutate(mutant)
                del mutant.fitness.values

        # Reparar individuos inválidos
        for ind in offspring:
            if not feasible(ind):
                repair(ind, len(seats))

        # Evaluar descendencia nueva
        invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
        fitnesses = map(toolbox.evaluate, invalid_ind)
        for ind, fit in zip(invalid_ind, fitnesses):
            ind.fitness.values = fit
        
        # Reemplazar población
        pop[:] = offspring
        
        # Estadísticas cada 20 generaciones
        if gen % 20 == 0 or gen == ngen - 1:
            fits = [ind.fitness.values[0] for ind in pop]
            length = len(pop)
            mean = sum(fits) / length
            sum2 = sum(x*x for x in fits)
            std = abs(sum2 / length - mean**2)**0.5
            print(f"Gen {gen:3d}: Max={max(fits):6.3f}, Avg={mean:6.3f}, Std={std:6.3f}")

    # Obtener las 3 mejores soluciones únicas
    pop.sort(key=lambda x: x.fitness.values[0], reverse=True)
    
    # Asegurar que las soluciones sean diferentes
    top_solutions = []
    for ind in pop:
        is_different = True
        for existing in top_solutions:
            if ind == existing:
                is_different = False
                break
        if is_different:
            top_solutions.append(list(ind))  # Crear copia
        if len(top_solutions) >= 3:
            break
    
    print(f"\n=== ALGORITMO COMPLETADO ===")
    print(f"Mejores fitness: {[pop[i].fitness.values[0] for i in range(min(3, len(pop)))]}")
    
    return top_solutions

def print_detailed_analysis(solutions, students, seats, compatibility_matrix):
    """
    Análisis detallado de las soluciones encontradas
    """
    for idx, solution in enumerate(solutions):
        print(f"\n{'='*50}")
        print(f"SOLUCIÓN {idx + 1}")
        print(f"{'='*50}")
        
        print("\n--- ASIGNACIÓN DE ASIENTOS ---")
        for i, seat_idx in enumerate(solution):
            seat = seats[seat_idx]
            print(f"{students[i].name:15} -> Fila {seat[0]:2}, Columna {seat[1]:2} (Visión: {students[i].vision})")
        
        print("\n--- ANÁLISIS DE COMPATIBILIDADES ---")
        conflicts = 0
        total_pairs = 0
        
        for i in range(len(solution)):
            for j in range(i+1, len(solution)):
                if compatibility_matrix[i][j] == 1:  # Son compatibles (se distraen)
                    total_pairs += 1
                    seat_i = seats[solution[i]]
                    seat_j = seats[solution[j]]
                    dist = math.sqrt((seat_i[0] - seat_j[0])**2 + (seat_i[1] - seat_j[1])**2)
                    
                    if dist <= 2.0:
                        conflicts += 1
                        status = "❌ CONFLICTO"
                    elif dist <= 3.0:
                        status = "⚠️  CERCA"
                    else:
                        status = "✅ SEPARADOS"
                    
                    print(f"{students[i].name} - {students[j].name}: distancia {dist:.2f} {status}")
        
        print(f"\nRESUMEN: {conflicts}/{total_pairs} pares compatibles en conflicto")
        
        # Análisis de visión
        print("\n--- ANÁLISIS DE UBICACIÓN POR VISIÓN ---")
        for vision_type in ["no_far", "no_near", "normal"]:
            students_type = [i for i, s in enumerate(students) if s.vision == vision_type]
            if students_type:
                rows = [seats[solution[i]][0] for i in students_type]
                avg_row = sum(rows) / len(rows)
                print(f"Visión {vision_type}: Fila promedio {avg_row:.1f}")