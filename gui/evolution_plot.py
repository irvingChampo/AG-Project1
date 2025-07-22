# ================================================
# FILE: gui/evolution_plot.py
# ================================================
# Este archivo contiene la lógica para graficar la evolución del fitness
# del algoritmo genético a lo largo de las generaciones.

import matplotlib.pyplot as plt

def plot_evolution(logbook):
    """
    Genera un gráfico que muestra la evolución del fitness máximo, promedio y mínimo.
    
    Args:
        logbook (list): Una lista de diccionarios, donde cada diccionario contiene
                        las estadísticas ('max', 'avg', 'min') para una generación.
    """
    if not logbook:
        print("El logbook está vacío, no se puede generar el gráfico de evolución.")
        return

    # Extraer los datos del logbook
    gen = [record['gen'] for record in logbook]
    max_fitness = [record['max'] for record in logbook]
    avg_fitness = [record['avg'] for record in logbook]
    min_fitness = [record['min'] for record in logbook]

    # Crear el gráfico
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Trazar las líneas de fitness
    ax.plot(gen, max_fitness, 'g-', label='Fitness Máximo (Mejor Individuo)', linewidth=2)
    ax.plot(gen, avg_fitness, 'b-', label='Fitness Promedio (Población)', linewidth=2)
    ax.plot(gen, min_fitness, 'r--', label='Fitness Mínimo (Peor Individuo)', alpha=0.7)

    # Configurar etiquetas, título y leyenda
    ax.set_xlabel("Generación")
    ax.set_ylabel("Valor de Fitness")
    ax.set_title("Evolución del Fitness por Generación")
    ax.legend(loc="best")
    ax.grid(True, linestyle='--', alpha=0.6)

    # Mostrar el gráfico
    plt.tight_layout()
    plt.show()

