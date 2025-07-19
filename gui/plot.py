import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle, FancyBboxPatch
import matplotlib.patches as mpatches

def plot_layout(seats, assignment, students, title="Distribución Optimizada de Asientos"):
    """
    Visualización mejorada del plano del aula con estudiantes asignados
    """
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Configurar el fondo
    fig.patch.set_facecolor('#f8f9fa')
    ax.set_facecolor('#ffffff')
    
    # Obtener dimensiones del aula
    max_row = max(r for r, c in seats)
    max_col = max(c for r, c in seats)
    
    # --- Dibujar pizarrón ---
    board_width = max_col + 0.5
    board_height = 0.6
    board_x = 0.25
    board_y = 0.5
    
    # Pizarrón con sombra
    shadow = FancyBboxPatch(
        (board_x + 0.05, board_y - 0.05), board_width, board_height,
        boxstyle="round,pad=0.1", facecolor='gray', alpha=0.3
    )
    ax.add_patch(shadow)
    
    board = FancyBboxPatch(
        (board_x, board_y), board_width, board_height,
        boxstyle="round,pad=0.1", facecolor='#2E7D32', edgecolor='#1B5E20', linewidth=2
    )
    ax.add_patch(board)
    
    ax.text(board_x + board_width/2, board_y + board_height/2, 
            "📋 PIZARRÓN", ha='center', va='center', 
            fontsize=14, fontweight='bold', color='white')
    
    # --- Crear mapeo de estudiantes por asiento ---
    student_by_seat = {}
    for i, seat_idx in enumerate(assignment):
        seat = seats[seat_idx]
        student_by_seat[seat] = students[i]
    
    # --- Dibujar asientos ---
    seat_size = 0.8
    margin = 0.1
    
    for row in range(1, max_row + 1):
        for col in range(1, max_col + 1):
            seat_pos = (row, col)
            
            # Posición en el gráfico (invertir fila para que 1 esté arriba)
            x = col - 1 + margin
            y = -(row - 1) - 0.5  # Negativo para que fila 1 esté cerca del pizarrón
            
            if seat_pos in student_by_seat:
                student = student_by_seat[seat_pos]
                
                # Colores y símbolos por tipo de visión
                if student.vision == "no_far":
                    color = '#ffcdd2'  # Rojo suave
                    edge_color = '#d32f2f'
                    symbol = '👓'
                    vision_text = 'No ve lejos'
                elif student.vision == "no_near":
                    color = '#bbdefb'  # Azul suave
                    edge_color = '#1976d2'
                    symbol = '🔍'
                    vision_text = 'No ve cerca'
                else:
                    color = '#e8f5e8'  # Verde suave
                    edge_color = '#388e3c'
                    symbol = '👀'
                    vision_text = 'Visión normal'
                
                # Dibujar silla con sombra
                shadow_chair = Rectangle((x + 0.02, y - 0.02), seat_size, seat_size, 
                                       facecolor='gray', alpha=0.3)
                ax.add_patch(shadow_chair)
                
                # Silla principal
                chair = FancyBboxPatch(
                    (x, y), seat_size, seat_size,
                    boxstyle="round,pad=0.05", 
                    facecolor=color, edgecolor=edge_color, linewidth=2
                )
                ax.add_patch(chair)
                
                # Texto del estudiante
                ax.text(x + seat_size/2, y + seat_size/2 + 0.1, 
                       f"{symbol}\n{student.name}", 
                       ha='center', va='center', 
                       fontsize=9, fontweight='bold', color='black')
                
                # Información de visión (más pequeña)
                ax.text(x + seat_size/2, y + seat_size/2 - 0.2, 
                       vision_text, ha='center', va='center', 
                       fontsize=7, style='italic', color='#666')
                
            else:
                # Asiento vacío
                chair = Rectangle((x, y), seat_size, seat_size, 
                                facecolor='#f5f5f5', edgecolor='#ccc', 
                                linewidth=1, linestyle='--')
                ax.add_patch(chair)
                
                ax.text(x + seat_size/2, y + seat_size/2, 
                       '🪑\nVacío', ha='center', va='center', 
                       fontsize=8, color='#999', style='italic')
    
    # --- Configurar ejes ---
    ax.set_xlim(-0.2, max_col + 0.3)
    ax.set_ylim(-max_row - 0.3, 1.5)
    
    # Ocultar ejes pero mantener el grid sutil
    ax.set_xticks(range(max_col + 1))
    ax.set_yticks([])
    ax.grid(True, alpha=0.1)
    ax.set_axisbelow(True)
    
    # Etiquetas de columnas
    for col in range(1, max_col + 1):
        ax.text(col - 1 + seat_size/2, -max_row - 0.15, f'Col {col}', 
               ha='center', va='center', fontsize=10, fontweight='bold')
    
    # Etiquetas de filas
    for row in range(1, max_row + 1):
        ax.text(-0.15, -(row - 1) - 0.5 + seat_size/2, f'F{row}', 
               ha='center', va='center', fontsize=10, fontweight='bold', 
               rotation=90)
    
    # --- Título y leyenda ---
    plt.title(title, fontsize=16, fontweight='bold', pad=20, color='#2E86AB')
    
    # Crear leyenda
    legend_elements = [
        mpatches.Patch(color='#ffcdd2', label='👓 No ve bien de lejos'),
        mpatches.Patch(color='#bbdefb', label='🔍 No ve bien de cerca'),
        mpatches.Patch(color='#e8f5e8', label='👀 Visión normal'),
        mpatches.Patch(color='#f5f5f5', label='🪑 Asiento vacío')
    ]
    
    ax.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(1.02, 1), 
             borderaxespad=0, frameon=True, fancybox=True, shadow=True)
    
    # --- Información adicional ---
    info_text = f"Total estudiantes: {len(students)}\n"
    info_text += f"Asientos totales: {len(seats)}\n"
    info_text += f"Asientos libres: {len(seats) - len