import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle, FancyBboxPatch
import matplotlib.patches as mpatches

def plot_layout(seats, assignment, students, title="Distribución Optimizada de Asientos"):
    
    fig, ax = plt.subplots(figsize=(12, 8))
    
    fig.patch.set_facecolor('#f8f9fa')
    ax.set_facecolor('#ffffff')
    
    max_row = max(r for r, c in seats)
    max_col = max(c for r, c in seats)
    
    board_width = max_col + 0.5
    board_height = 0.6
    board_x = 0.25
    board_y = 0.5
    
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
    
    student_by_seat = {}
    for i, seat_idx in enumerate(assignment):
        seat = seats[seat_idx]
        student_by_seat[seat] = students[i]
    
    seat_size = 0.8
    margin = 0.1
    
    for row in range(1, max_row + 1):
        for col in range(1, max_col + 1):
            seat_pos = (row, col)
            
            x = col - 1 + margin
            y = -(row - 1) - 0.5
            
            if seat_pos in student_by_seat:
                student = student_by_seat[seat_pos]
                
                # === INICIO DE LA MODIFICACIÓN: Lógica de visualización actualizada ===
                dist_opt = student.distancia_optima
                if dist_opt > 0 and dist_opt <= 4.0:
                    color = '#ffcdd2'
                    edge_color = '#d32f2f'
                    symbol = '👓'
                    vision_text = f'D.Opt: {dist_opt}m'
                elif dist_opt > 4.0:
                    color = '#bbdefb'
                    edge_color = '#1976d2'
                    symbol = '🔍'
                    vision_text = f'D.Opt: {dist_opt}m'
                else:
                    color = '#e8f5e8'
                    edge_color = '#388e3c'
                    symbol = '👀'
                    vision_text = 'Visión Normal'
                # === FIN DE LA MODIFICACIÓN ===

                shadow_chair = Rectangle((x + 0.02, y - 0.02), seat_size, seat_size, facecolor='gray', alpha=0.3)
                ax.add_patch(shadow_chair)
                
                chair = FancyBboxPatch(
                    (x, y), seat_size, seat_size,
                    boxstyle="round,pad=0.05", 
                    facecolor=color, edgecolor=edge_color, linewidth=2
                )
                ax.add_patch(chair)
                
                ax.text(x + seat_size/2, y + seat_size/2 + 0.1, 
                       f"{symbol}\n{student.name}", 
                       ha='center', va='center', 
                       fontsize=9, fontweight='bold', color='black')
                
                ax.text(x + seat_size/2, y + seat_size/2 - 0.2, 
                       vision_text, ha='center', va='center', 
                       fontsize=7, style='italic', color='#666')
                
            else:
                chair = Rectangle((x, y), seat_size, seat_size, 
                                facecolor='#f5f5f5', edgecolor='#ccc', 
                                linewidth=1, linestyle='--')
                ax.add_patch(chair)
                
                ax.text(x + seat_size/2, y + seat_size/2, 
                       '🪑\nVacío', ha='center', va='center', 
                       fontsize=8, color='#999', style='italic')
    
    ax.set_xlim(-0.2, max_col + 0.3)
    ax.set_ylim(-max_row - 0.3, 1.5)
    
    ax.set_xticks(range(max_col + 1))
    ax.set_yticks([])
    ax.grid(True, alpha=0.1)
    ax.set_axisbelow(True)
    
    for col in range(1, max_col + 1):
        ax.text(col - 1 + seat_size/2, -max_row - 0.15, f'Col {col}', 
               ha='center', va='center', fontsize=10, fontweight='bold')
    
    for row in range(1, max_row + 1):
        ax.text(-0.15, -(row - 1) - 0.5 + seat_size/2, f'F{row}', 
               ha='center', va='center', fontsize=10, fontweight='bold', 
               rotation=90)
    
    plt.title(title, fontsize=16, fontweight='bold', pad=20, color='#2E86AB')
    
    legend_elements = [
        mpatches.Patch(color='#ffcdd2', label='👓 Necesita estar cerca (<= 4m)'),
        mpatches.Patch(color='#bbdefb', label='🔍 Necesita estar lejos (> 4m)'),
        mpatches.Patch(color='#e8f5e8', label='👀 Visión Normal'),
        mpatches.Patch(color='#f5f5f5', label='🪑 Asiento vacío')
    ]
    
    ax.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(1.02, 1), 
             borderaxespad=0, frameon=True, fancybox=True, shadow=True)
    
    info_text = f"Total estudiantes: {len(students)}\n"
    info_text += f"Asientos totales: {len(seats)}\n"
    info_text += f"Asientos libres: {len(seats) - len(students)}"

    ax.text(1.02, 0.4, info_text, transform=ax.transAxes, fontsize=10,
            verticalalignment='bottom', bbox=dict(boxstyle='round', facecolor='aliceblue'))
    
    plt.tight_layout(rect=[0, 0, 0.85, 1])
    plt.show()