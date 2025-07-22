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
    QTabWidget, QScrollArea, QGridLayout, QFrame, QGroupBox
)
from PySide6.QtCore import Qt
from core.models import Student
from core.genetic import run_ga
from gui.plot import plot_layout
from gui.evolution_plot import plot_evolution
import numpy as np
import sys
import io
import os
import csv

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
        title.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px; color: #2E86AB;")
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

        assignment_frame = QGroupBox("🪑 Asignación de Asientos")
        assignment_layout = QVBoxLayout(assignment_frame)
        
        grid_layout = QGridLayout()
        grid_layout.setSpacing(5)
        students_by_seat = {self.seats[seat_idx]: self.students[i] for i, seat_idx in enumerate(solution)}
        max_row = max(seat[0] for seat in self.seats)
        max_col = max(seat[1] for seat in self.seats)
        
        board_label = QLabel("📋 PIZARRÓN")
        board_label.setAlignment(Qt.AlignCenter)
        board_label.setStyleSheet("background-color: #2E7D32; color: white; padding: 8px; font-weight: bold; border-radius: 4px;")
        grid_layout.addWidget(board_label, 0, 0, 1, max_col)
        
        for row in range(1, max_row + 1):
            for col in range(1, max_col + 1):
                seat_pos = (row, col)
                student = students_by_seat.get(seat_pos)
                if student:
                    if student.vision == "no_far": bg_color, icon, border_color = "#ffcdd2", "👓", "#d32f2f"
                    elif student.vision == "no_near": bg_color, icon, border_color = "#bbdefb", "🔍", "#1976d2"
                    else: bg_color, icon, border_color = "#e8f5e9", "👀", "#388e3c"
                    seat_label = QLabel(f"{icon}\n{student.name}")
                    seat_label.setStyleSheet(f"background-color: {bg_color}; border: 1px solid {border_color}; border-radius: 4px; padding: 5px; font-size: 10px; min-width: 80px; min-height: 40px;")
                else:
                    seat_label = QLabel("🪑\nVacío")
                    seat_label.setStyleSheet("background-color: #fafafa; border: 1px dashed #ccc; border-radius: 4px; padding: 5px; font-size: 10px; color: #999; min-width: 80px; min-height: 40px;")
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
        self.window.setMinimumSize(550, 700)
        self.students = []
        self.compat_matrix = None
        self.setup_styles()
        self.setup_ui()

    def _create_group_box(self, title):
        box = QGroupBox(title)
        layout = QVBoxLayout(box)
        return box, layout

    def setup_ui(self):
        self.main_layout = QVBoxLayout(self.window)
        
        title = QLabel("🧬 SeatPlan - Optimizador de Asientos")
        title.setAlignment(Qt.AlignCenter)
        title.setObjectName("mainTitle")
        self.main_layout.addWidget(title)
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        self.main_layout.addWidget(scroll_area)
        
        content_widget = QWidget()
        scroll_area.setWidget(content_widget)
        content_layout = QVBoxLayout(content_widget)

        aula_box, aula_layout = self._create_group_box("🏫 Configuración del Aula")
        grid_layout = QGridLayout()
        grid_layout.addWidget(QLabel("Filas:"), 0, 0)
        self.rows_input = QSpinBox()
        self.rows_input.setMinimum(1); self.rows_input.setMaximum(20); self.rows_input.setValue(5)
        grid_layout.addWidget(self.rows_input, 0, 1)
        grid_layout.addWidget(QLabel("Columnas:"), 0, 2)
        self.cols_input = QSpinBox()
        self.cols_input.setMinimum(1); self.cols_input.setMaximum(20); self.cols_input.setValue(6)
        grid_layout.addWidget(self.cols_input, 0, 3)
        grid_layout.setColumnStretch(1, 1)
        grid_layout.setColumnStretch(3, 1)
        aula_layout.addLayout(grid_layout)
        content_layout.addWidget(aula_box)

        students_box, students_layout = self._create_group_box("👥 Gestión de Estudiantes")
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
        
        add_buttons_layout = QHBoxLayout()
        self.add_button = QPushButton("➕ Agregar Estudiante")
        self.add_button.clicked.connect(self.add_student)
        add_buttons_layout.addWidget(self.add_button)
        self.load_dataset_button = QPushButton("📂 Cargar Dataset")
        self.load_dataset_button.clicked.connect(self.load_dataset)
        add_buttons_layout.addWidget(self.load_dataset_button)
        students_layout.addLayout(add_buttons_layout)
        
        self.students_list = QListWidget()
        self.students_list.setMaximumHeight(150)
        students_layout.addWidget(QLabel("Lista de Estudiantes:"))
        students_layout.addWidget(self.students_list)
        buttons_layout = QHBoxLayout()
        self.remove_button = QPushButton("❌ Eliminar Seleccionado")
        self.remove_button.clicked.connect(self.remove_student)
        buttons_layout.addWidget(self.remove_button)
        self.clear_button = QPushButton("🗑️ Limpiar Todo")
        
        # === INICIO DE LA MODIFICACIÓN 1 ===
        # Se usa una lambda para llamar a clear_students con un argumento.
        self.clear_button.clicked.connect(lambda: self.clear_students(ask_confirmation=True))
        # === FIN DE LA MODIFICACIÓN 1 ===
        
        buttons_layout.addWidget(self.clear_button)
        students_layout.addLayout(buttons_layout)
        content_layout.addWidget(students_box)

        compat_box, compat_layout = self._create_group_box("🤝 Configuración de Compatibilidades")
        compat_info = QLabel("Marca a los estudiantes que se distraen entre sí.")
        compat_layout.addWidget(compat_info)
        self.comp_button = QPushButton("⚙️ Definir Compatibilidades")
        self.comp_button.clicked.connect(self.define_compatibilities)
        compat_layout.addWidget(self.comp_button)
        self.compat_status = QLabel("❌ Compatibilidades no definidas")
        self.compat_status.setAlignment(Qt.AlignCenter)
        compat_layout.addWidget(self.compat_status)
        content_layout.addWidget(compat_box)

        optim_box, optim_layout = self._create_group_box("🚀 Optimización")
        self.run_button = QPushButton("🧬 Ejecutar Algoritmo Genético")
        self.run_button.setObjectName("runButton")
        self.run_button.clicked.connect(self.optimize_seats)
        optim_layout.addWidget(self.run_button)
        self.progress_label = QLabel("")
        self.progress_label.setAlignment(Qt.AlignCenter)
        optim_layout.addWidget(self.progress_label)
        content_layout.addWidget(optim_box)

        content_layout.addStretch()
        self.name_input.returnPressed.connect(self.add_student)

    def setup_styles(self):
        self.window.setStyleSheet("""
            QWidget {
                background-color: #eef2f5;
                color: #333;
                font-family: Segoe UI, sans-serif;
            }
            QGroupBox {
                background-color: #ffffff;
                border: 1px solid #dcdcdc;
                border-radius: 8px;
                padding-top: 20px;
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 5px 10px;
                background-color: #2E86AB;
                color: white;
                border-radius: 4px;
                font-weight: bold;
            }
            QLabel {
                color: #333;
                background-color: transparent;
            }
            QLabel#mainTitle {
                font-size: 18px;
                font-weight: bold;
                color: #2E86AB;
                padding: 10px;
            }
            QPushButton {
                padding: 8px 12px;
                border-radius: 4px;
                border: 1px solid #ccc;
                background-color: #f0f0f0;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
                border-color: #bbb;
            }
            QPushButton#runButton {
                background-color: #2E7D32;
                color: white;
                font-size: 14px;
            }
            QPushButton#runButton:hover {
                background-color: #388E3C;
            }
            QLineEdit, QComboBox, QSpinBox {
                padding: 6px;
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: #ffffff;
                color: #333;
            }
            QListWidget {
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: white;
                padding: 5px;
            }
            QScrollArea {
                border: none;
            }
        """)

    def run(self):
        self.window.show()
        self.app.exec()

    def add_student(self):
        name = self.name_input.text().strip()
        vision_text = self.vision_input.currentText()
        vision_data = self.vision_input.itemData(self.vision_input.currentIndex())
        if not name:
            QMessageBox.warning(self.window, "Entrada Inválida", "Por favor, ingresa un nombre para el estudiante.")
            return
        if any(s.name.lower() == name.lower() for s in self.students):
            QMessageBox.warning(self.window, "Estudiante Duplicado", "Ya existe un estudiante con ese nombre.")
            return
        
        self.students.append(Student(name, vision_data, len(self.students)))
        display_text = f"{vision_text} - {name}"
        self.students_list.addItem(display_text)
        self.name_input.clear()
        self.name_input.setFocus()
        self.compat_matrix = None
        self.compat_status.setText("❌ Compatibilidades no definidas")
        self.compat_status.setStyleSheet("color: #d32f2f; font-weight: bold;")

    def remove_student(self):
        current_row = self.students_list.currentRow()
        if current_row >= 0:
            self.students_list.takeItem(current_row)
            self.students.pop(current_row)
            for i, student in enumerate(self.students): student.index = i
            self.compat_matrix = None
            self.compat_status.setText("❌ Compatibilidades no definidas")
            self.compat_status.setStyleSheet("color: #d32f2f; font-weight: bold;")

    # === INICIO DE LA MODIFICACIÓN 2 ===
    # Se cambia la firma de la función y se usa el nuevo parámetro.
    def clear_students(self, ask_confirmation=False):
        if ask_confirmation:
            reply = QMessageBox.question(self.window, "Confirmar Limpieza",
                                         "¿Estás seguro de que quieres eliminar a todos los estudiantes de la lista?",
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.No:
                return

        self.students.clear()
        self.students_list.clear()
        self.compat_matrix = None
        self.compat_status.setText("❌ Compatibilidades no definidas")
        self.compat_status.setStyleSheet("color: #d32f2f; font-weight: bold;")
    # === FIN DE LA MODIFICACIÓN 2 ===
    
    def load_dataset(self):
        reply = QMessageBox.question(self.window, "Confirmar Carga",
                                     "¿Deseas cargar el dataset predefinido?\nSe borrarán todos los estudiantes actuales.",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.No:
            return

        # Limpia los datos existentes sin pedir confirmación.
        self.clear_students(ask_confirmation=False)

        try:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            students_file = os.path.join(base_dir, 'datasets', 'students_dataset.csv')
            compat_file = os.path.join(base_dir, 'datasets', 'compatibility_dataset.csv')
            
            vision_text_map = {"normal": "👀 Normal", "no_far": "👓 No ve bien de lejos", "no_near": "🔍 No ve bien de cerca"}
            
            name_to_index = {}
            with open(students_file, mode='r', encoding='utf-8') as infile:
                reader = csv.DictReader(infile)
                for row in reader:
                    name = row['name'].strip()
                    vision = row['vision'].strip()
                    student_index = len(self.students)
                    self.students.append(Student(name, vision, student_index))
                    name_to_index[name] = student_index
                    
                    display_text = f"{vision_text_map.get(vision, vision)} - {name}"
                    self.students_list.addItem(display_text)

            num_students = len(self.students)
            self.compat_matrix = np.zeros((num_students, num_students))
            compat_pairs_count = 0
            with open(compat_file, mode='r', encoding='utf-8') as infile:
                reader = csv.DictReader(infile)
                for row in reader:
                    s1_name = row['student1_name'].strip()
                    s2_name = row['student2_name'].strip()
                    if s1_name in name_to_index and s2_name in name_to_index:
                        idx1 = name_to_index[s1_name]
                        idx2 = name_to_index[s2_name]
                        self.compat_matrix[idx1, idx2] = 1
                        self.compat_matrix[idx2, idx1] = 1
                        compat_pairs_count += 1
            
            self.rows_input.setValue(4)
            self.cols_input.setValue(5)
            self.compat_status.setText(f"✅ {compat_pairs_count} parejas conflictivas cargadas")
            self.compat_status.setStyleSheet("color: #2E7D32; font-weight: bold;")
            QMessageBox.information(self.window, "Éxito", f"Se cargaron {num_students} estudiantes y {compat_pairs_count} compatibilidades.")

        except FileNotFoundError as e:
            QMessageBox.critical(self.window, "Error de Archivo",
                                 f"No se pudo encontrar un archivo del dataset.\nAsegúrate de que la carpeta 'datasets' y sus archivos .csv existen.\n\nError: {e}")
        except Exception as e:
            QMessageBox.critical(self.window, "Error Inesperado", f"Ocurrió un error al cargar el dataset:\n{e}")

    def define_compatibilities(self):
        n = len(self.students)
        if n < 2:
            QMessageBox.information(self.window, "Información", "Necesitas al menos 2 estudiantes para definir compatibilidades.")
            return

        dialog = QDialog(self.window)
        dialog.setWindowTitle("Definir Compatibilidades"); dialog.setMinimumSize(400, 300)
        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel("Marca las <b>PAREJAS</b> que se <b>DISTRAEN</b> entre sí:"))
        
        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        scroll_widget = QWidget(); scroll_layout = QVBoxLayout(scroll_widget)
        
        checkboxes = []
        if self.compat_matrix is None:
            self.compat_matrix = np.zeros((n, n))

        for i in range(n):
            for j in range(i + 1, n):
                cb = QCheckBox(f"{self.students[i].name} ↔️ {self.students[j].name}")
                if self.compat_matrix[i, j] == 1:
                    cb.setChecked(True)
                scroll_layout.addWidget(cb)
                checkboxes.append((i, j, cb))
        
        scroll_widget.setLayout(scroll_layout)
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
            self.compat_status.setText(f"✅ {compatible_pairs} parejas conflictivas definidas")
            self.compat_status.setStyleSheet("color: #2E7D32; font-weight: bold;")

    def optimize_seats(self):
        if not self.students:
            QMessageBox.warning(self.window, "Error", "No hay estudiantes agregados en la lista.")
            return
        total_seats = self.rows_input.value() * self.cols_input.value()
        if total_seats < len(self.students):
            QMessageBox.critical(self.window, "Error de Capacidad", "No hay suficientes asientos en el aula para todos los estudiantes.")
            return
        if self.compat_matrix is None:
            reply = QMessageBox.question(self.window, "Aviso de Compatibilidad", 
                                         "No has definido las compatibilidades. ¿Deseas continuar asumiendo que ningún estudiante se distrae con otro?",
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.No:
                return
            self.compat_matrix = np.zeros((len(self.students), len(self.students)))

        seats = [(r + 1, c + 1) for r in range(self.rows_input.value()) for c in range(self.cols_input.value())]
        seat_distances = {seat: seat[0] for seat in seats}

        self.progress_label.setText("🔄 Ejecutando algoritmo genético, por favor espera...")
        self.run_button.setEnabled(False)
        self.app.processEvents()

        old_stdout = sys.stdout
        sys.stdout = captured_output = io.StringIO()
        
        solutions = None
        logbook = None

        try:
            solutions, logbook = run_ga(self.students, seats, self.compat_matrix, seat_distances, [1])
        finally:
            sys.stdout = old_stdout
            print(captured_output.getvalue())
            self.run_button.setEnabled(True)
            self.progress_label.setText("✅ ¡Optimización completada!")

        if solutions:
            SolutionDialog(solutions, self.students, seats, self.compat_matrix, self.window).exec()
            if logbook:
                plot_evolution(logbook)
        else:
            QMessageBox.warning(self.window, "Sin Resultados", "El algoritmo no pudo encontrar una solución válida. Intenta de nuevo o ajusta los parámetros.")