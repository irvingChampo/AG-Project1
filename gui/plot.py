import matplotlib.pyplot as plt

def plot_layout(seats, assignment, students):
    fig, ax = plt.subplots(figsize=(8, 6))

    # --- Dibujar pizarrón ---
    max_col = max(c for r, c in seats)
    ax.add_patch(plt.Rectangle((0, 1), max_col + 1, 0.5, facecolor="#b0c4de", edgecolor='black'))
    ax.text((max_col + 1) / 2, 1.25, "Pizarrón", ha='center', va='center', fontsize=12, fontweight='bold')

    # --- Dibujar asientos con colores personalizados ---
    for i, seat_idx in enumerate(assignment):
        seat = seats[seat_idx]
        row, col = seat
        student = students[i]

        # Definir color según visión
        if student.vision == "no_far":
            color = "#ffcccc"  # rojo suave
        elif student.vision == "no_near":
            color = "#cce5ff"  # azul suave
        else:
            color = "#f0f0f0"  # gris claro

        ax.add_patch(plt.Rectangle((col, -row), 1, 1, edgecolor='black', facecolor=color, lw=1.2))
        ax.text(col + 0.5, -row - 0.5, student.name, ha='center', va='center', fontsize=9, fontweight='bold')

    # --- Dibujar contorno de todos los asientos vacíos (por si sobran) ---
    for seat in seats:
        row, col = seat
        ax.add_patch(plt.Rectangle((col, -row), 1, 1, edgecolor='black', facecolor='none', lw=1.2))

    ax.set_xlim(0, max_col + 2)
    ax.set_ylim(-max(r for r, c in seats) - 1.5, 2)
    plt.axis('off')
    plt.show()
