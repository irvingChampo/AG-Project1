# ================================================
# FILE: gui/window.py
# ================================================
# Este archivo define toda la interfaz gráfica de usuario (GUI) utilizando PySide6.
# Contiene la ventana principal, los diálogos, los botones y la lógica para
# interactuar con el algoritmo genético.

from PySide6.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QLabel,
    QSpinBox, QLineEdit, QListWidget, QComboBox, QMessageBox,
    QDialog, QCheckBox, QDialogButtonBox, QTextEdit,
    QTabWidget, QScrollArea, QGridLayout, QFrame
)
from PySide6.QtCore import Qt
from core.models import Student
from core.genetic import run_ga
from gui.plot import plot_layout
import numpy as np
import sys
import io

class SolutionDialog(QDialog):
    """Diálogo para mostrar las 3 mejores soluciones encontradas."""
    
    def __init__(self, solutions, students, seats, compatibility_matrix, parent=None):
        super().__init__(parent)
        self.solutions = solutions
        self.students = students
        self.seats = seats
        self.compatibility_matrix = compatibility_matrix
        
        self.setWindowTitle("Mejores Soluciones Encontradas")
        self.setMinimumSize(800, 600)
        
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        title = QLabel("🧬 Algoritmo Genético - Mejores Soluciones")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px;")
        layout.addWidget(title)
        
        self.tab_widget = QTabWidget()
        for i, solution in enumerate(self.solutions):
            tab = self.create_solution_tab(solution, i + 1)
            self.tab_widget.addTab(tab, f"Solución {i + 1}")
        layout.addWidget(self.tab_widget)
        
        button_layout = QHBoxLayout()
        plot_button = QPushButton("📊 Ver Plano Visual")
        plot_button.clicked.connect(self.plot_current_solution)
        button_layout.addWidget(plot_button)
        
        close_button = QPushButton("✅ Cerrar")
        close_button.clicked.connect(self.accept)
        button_layout.addWidget(close_button)
        layout.addLayout(button_layout)
    
    def create_solution_tab(self, solution, solution_num):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        main_widget = QWidget()
        layout = QVBoxLayout(main_widget)

        # Asignación de asientos
        assignment_frame = QFrame()
        assignment_frame.setFrameStyle(QFrame.Box)
        assignment_layout = QVBoxLayout(assignment_frame)
        assignment_title = QLabel("🪑 Asignación de Asientos")
        assignment_title.setStyleSheet("font-weight: bold; color: #2E86AB;")
        assignment_layout.addWidget(assignment_title)
        
        grid_layout = QGridLayout()
        students_by_seat = {self.seats[seat_idx]: self.students[i] for i, seat_idx in enumerate(solution)}
        max_row = max(seat[0] for seat in self.seats)
        max_col = max(seat[1] for seat in self.seats)
        
        board_label = QLabel("📋 PIZARRÓN")
        board_label.setAlignment(Qt.AlignCenter)
        board_label.setStyleSheet("background-color: #4CAF50; color: white; padding: 5px; font-weight: bold;")
        grid_layout.addWidget(board_label, 0, 0, 1, max_col)
        
        for row in range(1, max_row + 1):
            for col in range(1, max_col + 1):
                seat_pos = (row, col)
                if seat_pos in students_by_seat:
                    student = students_by_seat[seat_pos]
                    if student.vision == "no_far": bg_color, icon = "#ffebee", "👓"
                    elif student.vision == "no_near": bg_color, icon = "#e3f2fd", "🔍"
                    else: bg_color, icon = "#f0f0f0", "👀"
                    seat_label = QLabel(f"{icon}\n{student.name}")
                    seat_label.setStyleSheet(f"background-color: {bg_color}; border: 2px solid #ddd; padding: 5px; font-size: 10px; min-width: 80px; min-height: 50px;")
                else:
                    seat_label = QLabel("🪑\nVacío")
                    seat_label.setStyleSheet("background-color: #fafafa; border: 1px solid #ccc; padding: 5px; font-size: 10px; min-width: 80px; min-height: 50px;")
                seat_label.setAlignment(Qt.AlignCenter)
                grid_layout.addWidget(seat_label, row, col - 1)
        
        assignment_layout.addLayout(grid_layout)
        layout.addWidget(assignment_frame)
        scroll.setWidget(main_widget)
        return scroll

    def plot_current_solution(self):
        current_index = self.tab_widget.currentIndex()
        if current_index < len(self.solutions):
            try:
                plot_layout(self.seats, self.solutions[current_index], self.students, f"Plano de Solución {current_index + 1}")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Error al mostrar el plano: {str(e)}")

class SeatPlanApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.window = QWidget()
        self.window.setWindowTitle("🧬 SeatPlan - Algoritmo Genético")
        self.window.setMinimumSize(500, 700)
        self.students = []
        self.compat_matrix = None
        self.setup_ui()
        self.setup_styles()

    def setup_ui(self):
        self.layout = QVBoxLayout(self.window)
        # ... (El resto del código de UI es largo pero no necesita cambios funcionales) ...
        # Se incluye completo para que sea copiable.
        title = QLabel("🧬 SeatPlan - Optimizador de Asientos")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2E86AB; padding: 15px;")
        self.layout.addWidget(title)

        aula_frame = QFrame()
        aula_frame.setFrameStyle(QFrame.Box)
        aula_layout = QVBoxLayout(aula_frame)
        aula_title = QLabel("🏫 Configuración del Aula")
        aula_title.setStyleSheet("font-weight: bold; color: #2E86AB; padding: 5px;")
        aula_layout.addWidget(aula_title)
        grid_layout = QGridLayout()
        grid_layout.addWidget(QLabel("Filas:"), 0, 0)
        self.rows_input = QSpinBox()
        self.rows_input.setMinimum(1); self.rows_input.setMaximum(20); self.rows_input.setValue(5)
        grid_layout.addWidget(self.rows_input, 0, 1)
        grid_layout.addWidget(QLabel("Columnas:"), 0, 2)
        self.cols_input = QSpinBox()
        self.cols_input.setMinimum(1); self.cols_input.setMaximum(20); self.cols_input.setValue(6)
        grid_layout.addWidget(self.cols_input, 0, 3)
        aula_layout.addLayout(grid_layout)
        self.layout.addWidget(aula_frame)

        students_frame = QFrame()
        students_frame.setFrameStyle(QFrame.Box)
        students_layout = QVBoxLayout(students_frame)
        students_title = QLabel("👥 Gestión de Estudiantes")
        students_title.setStyleSheet("font-weight: bold; color: #2E86AB; padding: 5px;")
        students_layout.addWidget(students_title)
        form_layout = QGridLayout()
        form_layout.addWidget(QLabel("Nombre:"), 0, 0)
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Nombre del estudiante")
        form_layout.addWidget(self.name_input, 0, 1)
        form_layout.addWidget(QLabel("Tipo de Visión:"), 1, 0)
        self.vision_input = QComboBox()
        self.vision_input.addItems(["👀 Normal", "👓 No ve bien de lejos", "🔍 No ve bien de cerca"])
        self.vision_input.setItemData(0, "normal")
        self.vision_input.setItemData(1, "no_far")
        self.vision_input.setItemData(2, "no_near")
        form_layout.addWidget(self.vision_input, 1, 1)
        students_layout.addLayout(form_layout)
        self.add_button = QPushButton("➕ Agregar Estudiante")
        self.add_button.clicked.connect(self.add_student)
        students_layout.addWidget(self.add_button)
        self.students_list = QListWidget()
        self.students_list.setMaximumHeight(150)
        students_layout.addWidget(self.students_list)
        buttons_layout = QHBoxLayout()
        self.remove_button = QPushButton("❌ Eliminar Seleccionado")
        self.remove_button.clicked.connect(self.remove_student)
        buttons_layout.addWidget(self.remove_button)
        self.clear_button = QPushButton("🗑️ Limpiar Todo")
        self.clear_button.clicked.connect(self.clear_students)
        buttons_layout.addWidget(self.clear_button)
        students_layout.addLayout(buttons_layout)
        self.layout.addWidget(students_frame)

        compat_frame = QFrame()
        compat_frame.setFrameStyle(QFrame.Box)
        compat_layout = QVBoxLayout(compat_frame)
        compat_title = QLabel("🤝 Configuración de Compatibilidades")
        compat_title.setStyleSheet("font-weight: bold; color: #2E86AB; padding: 5px;")
        compat_layout.addWidget(compat_title)
        compat_info = QLabel("Marca a los estudiantes que se distraen entre sí.")
        compat_layout.addWidget(compat_info)
        self.comp_button = QPushButton("⚙️ Definir Compatibilidades")
        self.comp_button.clicked.connect(self.define_compatibilities)
        compat_layout.addWidget(self.comp_button)
        self.compat_status = QLabel("❌ Compatibilidades no definidas")
        self.compat_status.setStyleSheet("color: #d32f2f;")
        compat_layout.addWidget(self.compat_status)
        self.layout.addWidget(compat_frame)

        optim_frame = QFrame()
        optim_frame.setFrameStyle(QFrame.Box)
        optim_layout = QVBoxLayout(optim_frame)
        optim_title = QLabel("🚀 Optimización")
        optim_title.setStyleSheet("font-weight: bold; color: #2E86AB; padding: 5px;")
        optim_layout.addWidget(optim_title)
        self.run_button = QPushButton("🧬 Ejecutar Algoritmo Genético")
        self.run_button.clicked.connect(self.optimize_seats)
        optim_layout.addWidget(self.run_button)
        self.progress_label = QLabel("")
        optim_layout.addWidget(self.progress_label)
        self.layout.addWidget(optim_frame)
        self.name_input.returnPressed.connect(self.add_student)

    def setup_styles(self):
        self.window.setStyleSheet("""
            QWidget { background-color: #eef2f5; }
            QFrame { background-color: #f8f9fa; border-radius: 8px; padding: 10px; margin: 5px; }
            QLabel { color: #333; }
            QPushButton { padding: 8px; border-radius: 4px; border: 1px solid #ccc; background-color: #fff; }
            QPushButton:hover { background-color: #e9ecef; }
            QLineEdit, QComboBox, QSpinBox { padding: 5px; border: 1px solid #ddd; border-radius: 4px; }
            QListWidget { border: 1px solid #ddd; border-radius: 4px; background-color: white; }
            #run_button { background-color: #4CAF50; color: white; font-weight: bold; }
            #run_button:hover { background-color: #45a049; }
        """)
        self.run_button.setObjectName("run_button")

    def run(self):
        self.window.show()
        self.app.exec()

    def add_student(self):
        name = self.name_input.text().strip()
        vision = self.vision_input.itemData(self.vision_input.currentIndex())
        if not name:
            QMessageBox.warning(self.window, "Error", "Por favor ingresa un nombre.")
            return
        if any(s.name.lower() == name.lower() for s in self.students):
            QMessageBox.warning(self.window, "Error", "Ya existe un estudiante con ese nombre.")
            return
        self.students.append(Student(name, vision, len(self.students)))
        display_text = f"{self.vision_input.itemText(self.vision_input.currentIndex())} - {name}"
        self.students_list.addItem(display_text)
        self.name_input.clear()
        self.name_input.setFocus()
        self.compat_matrix = None
        self.compat_status.setText("❌ Compatibilidades no definidas")
        self.compat_status.setStyleSheet("color: #d32f2f;")

    def remove_student(self):
        current_row = self.students_list.currentRow()
        if current_row >= 0:
            self.students_list.takeItem(current_row)
            self.students.pop(current_row)
            for i, student in enumerate(self.students): student.index = i
            self.compat_matrix = None
            self.compat_status.setText("❌ Compatibilidades no definidas")
            self.compat_status.setStyleSheet("color: #d32f2f;")

    def clear_students(self):
        if QMessageBox.question(self.window, "Confirmar", "¿Eliminar todos los estudiantes?") == QMessageBox.Yes:
            self.students.clear()
            self.students_list.clear()
            self.compat_matrix = None
            self.compat_status.setText("❌ Compatibilidades no definidas")
            self.compat_status.setStyleSheet("color: #d32f2f;")

    def define_compatibilities(self):
        n = len(self.students)
        if n < 2:
            QMessageBox.warning(self.window, "Error", "Necesitas al menos 2 estudiantes.")
            return

        dialog = QDialog(self.window)
        dialog.setWindowTitle("Definir Compatibilidades"); dialog.setMinimumSize(400, 300)
        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel("Marca las PAREJAS que se DISTRAEN entre sí:"))
        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        scroll_widget = QWidget(); scroll_layout = QVBoxLayout(scroll_widget)
        checkboxes = []
        for i in range(n):
            for j in range(i + 1, n):
                cb = QCheckBox(f"{self.students[i].name} ↔️ {self.students[j].name}")
                scroll_layout.addWidget(cb)
                checkboxes.append((i, j, cb))
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept); buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        if dialog.exec() == QDialog.Accepted:
            self.compat_matrix = np.zeros((n, n))
            compatible_pairs = 0
            for i, j, cb in checkboxes:
                if cb.isChecked():
                    self.compat_matrix[i, j] = self.compat_matrix[j, i] = 1
                    compatible_pairs += 1
            self.compat_status.setText(f"✅ {compatible_pairs} parejas definidas")
            self.compat_status.setStyleSheet("color: #2E7D32;")

    def optimize_seats(self):
        if not self.students:
            QMessageBox.warning(self.window, "Error", "No hay estudiantes agregados.")
            return
        total_seats = self.rows_input.value() * self.cols_input.value()
        if total_seats < len(self.students):
            QMessageBox.warning(self.window, "Error", "No hay suficientes asientos.")
            return
        if self.compat_matrix is None:
            if QMessageBox.question(self.window, "Aviso", "No has definido compatibilidades. ¿Continuar asumiendo que nadie se distrae?") == QMessageBox.No:
                return
            self.compat_matrix = np.zeros((len(self.students), len(self.students)))

        seats = [(r + 1, c + 1) for r in range(self.rows_input.value()) for c in range(self.cols_input.value())]
        seat_distances = {seat: seat[0] for seat in seats}

        self.progress_label.setText("🔄 Ejecutando algoritmo genético..."); self.run_button.setEnabled(False)
        self.app.processEvents()

        # Redirigir stdout para capturar logs de DEAP
        old_stdout = sys.stdout
        sys.stdout = captured_output = io.StringIO()
        
        solutions = run_ga(self.students, seats, self.compat_matrix, seat_distances, [1])
        
        sys.stdout = old_stdout # Restaurar stdout
        print(captured_output.getvalue()) # Imprimir logs a la consola real
        
        self.run_button.setEnabled(True); self.progress_label.setText("✅ ¡Optimización completada!")

        if solutions:
            SolutionDialog(solutions, self.students, seats, self.compat_matrix, self.window).exec()
        else:
            QMessageBox.warning(self.window, "Sin resultados", "El algoritmo no encontró soluciones válidas.")