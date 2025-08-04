from PySide6.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QLabel,
    QSpinBox, QLineEdit, QListWidget, QComboBox, QMessageBox,
    QDialog, QCheckBox, QDialogButtonBox, QDoubleSpinBox,
    QTabWidget, QScrollArea, QGridLayout, QFrame, QGroupBox,
    QTableWidget, QTableWidgetItem, QTextEdit
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont
from core.models import Student
from core.genetic import run_ga, evaluate
import numpy as np
import sys
import io
import os
import csv
import math

class SolutionDialog(QDialog):
    
    def __init__(self, solutions, students, seats, seat_distances, compatibility_matrix, parent=None):
        super().__init__(parent)
        self.solutions = solutions
        self.students = students
        self.seats = seats
        self.seat_distances = seat_distances
        self.compatibility_matrix = compatibility_matrix
        
        self.setWindowTitle("Mejores Soluciones Encontradas")
        self.setMinimumSize(900, 700) # Aumentar tamaño para el resumen
        
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
    
    # === INICIO DE LA MODIFICACIÓN: Restauración y mejora del resumen detallado ===
    def create_solution_tab(self, solution, solution_num):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        main_widget = QWidget()
        layout = QVBoxLayout(main_widget)

        # --- Parte 1: Plano Visual de Asientos ---
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
                    dist_opt = student.distancia_optima
                    if dist_opt > 0 and dist_opt <= 4.0: bg_color, icon, border_color = "#ffcdd2", "👓", "#d32f2f"
                    elif dist_opt > 4.0: bg_color, icon, border_color = "#bbdefb", "🔍", "#1976d2"
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

        # --- Parte 2: Desglose y Análisis Detallado ---
        analysis_frame = QGroupBox("📊 Análisis Detallado de la Solución")
        analysis_layout = QVBoxLayout(analysis_frame)

        # 2.1 Tabla de Métricas por Estudiante
        table = QTableWidget()
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels(["Estudiante", "Asiento (F, C)", "Distancia Real", "Distancia Óptima", "Error Visión", "Dist. a Incompatibles"])
        table.setRowCount(len(self.students))

        student_metrics = {}
        for i, seat_idx in enumerate(solution):
            student = self.students[i]
            seat_pos = self.seats[seat_idx]
            dist_real = self.seat_distances[seat_pos]
            dist_opt = student.distancia_optima
            error_vision = abs(dist_real - dist_opt) if dist_opt > 0 else 0.0
            
            # Calcular distancia promedio a compañeros incompatibles
            incompatible_distances = []
            for j in range(len(self.students)):
                if self.compatibility_matrix[i][j] == 1:
                    other_seat_idx = solution[j]
                    other_seat_pos = self.seats[other_seat_idx]
                    dist_euc = math.sqrt((seat_pos[0] - other_seat_pos[0])**2 + (seat_pos[1] - other_seat_pos[1])**2)
                    incompatible_distances.append(dist_euc)
            
            avg_dist_incompatible = np.mean(incompatible_distances) if incompatible_distances else -1
            student_metrics[student.name] = {
                'seat': f"F{seat_pos[0]}, C{seat_pos[1]}",
                'error_vision': error_vision,
                'avg_dist_incompatible': avg_dist_incompatible,
                'dist_opt': dist_opt
            }

            table.setItem(i, 0, QTableWidgetItem(student.name))
            table.setItem(i, 1, QTableWidgetItem(f"F{seat_pos[0]}, C{seat_pos[1]}"))
            table.setItem(i, 2, QTableWidgetItem(f"{dist_real:.2f} m"))
            table.setItem(i, 3, QTableWidgetItem(f"{dist_opt:.2f} m" if dist_opt > 0 else "N/A"))
            table.setItem(i, 4, QTableWidgetItem(f"{error_vision:.2f} m"))
            dist_incomp_str = f"{avg_dist_incompatible:.2f}" if avg_dist_incompatible != -1 else "N/A"
            table.setItem(i, 5, QTableWidgetItem(dist_incomp_str))

        table.resizeColumnsToContents()
        table.setFixedHeight(300)
        analysis_layout.addWidget(table)
        
        # 2.2 Reporte Interpretativo
        report_text = QTextEdit()
        report_text.setReadOnly(True)
        
        temp_individual = type('Individual', (object,), {'chromosome': solution})()
        fitness_score = evaluate(temp_individual, self.students, self.seats, self.compatibility_matrix, self.seat_distances, max(self.seat_distances.values()))
        
        report_html = f"<h3>Reporte de la Solución</h3>"
        report_html += f"<p><b>Puntuación de Fitness Final: {fitness_score:.4f}</b> (un valor más cercano a 0 es mejor).</p>"
        report_html += "<ul>"
        
        # Generar justificaciones
        for name, metrics in sorted(student_metrics.items()):
            # Justificación de visión
            if metrics['dist_opt'] > 0:
                if metrics['error_vision'] < 0.5: # Umbral de error bajo
                    report_html += f"<li><b>{name}</b> ({metrics['seat']}) está <b>excelentemente ubicado</b> para su visión (error de solo {metrics['error_vision']:.2f} m).</li>"
                elif metrics['error_vision'] < 1.5: # Umbral de error aceptable
                     report_html += f"<li><b>{name}</b> ({metrics['seat']}) tiene una <b>buena ubicación</b> para su visión (error de {metrics['error_vision']:.2f} m).</li>"

            # Justificación de compatibilidad
            if metrics['avg_dist_incompatible'] != -1:
                if metrics['avg_dist_incompatible'] > 2.0: # Umbral de buena separación
                    report_html += f"<li><b>{name}</b> ({metrics['seat']}) está <b>bien separado</b> de sus compañeros incompatibles (distancia promedio {metrics['avg_dist_incompatible']:.2f}).</li>"
                else:
                    report_html += f"<li><font color='orange'>Advertencia:</font> <b>{name}</b> ({metrics['seat']}) está <b>cerca</b> de uno o más compañeros incompatibles. Esto puede ser un compromiso necesario para optimizar otros factores.</li>"

        report_html += "</ul>"
        report_text.setHtml(report_html)
        analysis_layout.addWidget(report_text)
        
        layout.addWidget(analysis_frame)
        
        scroll.setWidget(main_widget)
        return scroll
    # === FIN DE LA MODIFICACIÓN ===

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
        aula_config_layout = QHBoxLayout()
        aula_config_layout.addWidget(QLabel("Selecciona el tamaño del aula:"))
        self.aula_input = QComboBox()
        self.aula_input.addItems([
            "5 Filas x 6 Columnas (30 asientos)",
            "8 Filas x 5 Columnas (40 asientos)"
        ])
        aula_config_layout.addWidget(self.aula_input)
        aula_layout.addLayout(aula_config_layout)
        content_layout.addWidget(aula_box)

        students_box, students_layout = self._create_group_box("👥 Gestión de Estudiantes")
        form_layout = QGridLayout()
        form_layout.addWidget(QLabel("Nombre:"), 0, 0)
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Nombre del estudiante")
        form_layout.addWidget(self.name_input, 0, 1)
        
        form_layout.addWidget(QLabel("Distancia Óptima (metros):"), 1, 0)
        self.distancia_input = QDoubleSpinBox()
        self.distancia_input.setSuffix(" m")
        self.distancia_input.setRange(0, 20)
        self.distancia_input.setSingleStep(0.5)
        self.distancia_input.setDecimals(1)
        self.distancia_input.setToolTip("Ingrese la distancia ideal a la que el estudiante ve bien.\nUse 0.0 m para visión normal (será ignorado).")
        form_layout.addWidget(self.distancia_input, 1, 1)

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
        self.clear_button.clicked.connect(lambda: self.clear_students(ask_confirmation=True))
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
            QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {
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
        distancia_optima = self.distancia_input.value()
        
        if not name:
            QMessageBox.warning(self.window, "Entrada Inválida", "Por favor, ingresa un nombre para el estudiante.")
            return
        if any(s.name.lower() == name.lower() for s in self.students):
            QMessageBox.warning(self.window, "Estudiante Duplicado", "Ya existe un estudiante con ese nombre.")
            return
        
        student_index = len(self.students)
        self.students.append(Student(name, distancia_optima, student_index))
        
        if distancia_optima == 0:
            vision_text = "👀 Visión Normal"
        else:
            vision_text = f"🎯 Dist. Óptima: {distancia_optima} m"
        display_text = f"[ID: {student_index}] {vision_text} - {name}"
        
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
            for i in range(self.students_list.count()):
                student = self.students[i]
                student.index = i
                distancia_optima = student.distancia_optima
                if distancia_optima == 0:
                    vision_text = "👀 Visión Normal"
                else:
                    vision_text = f"🎯 Dist. Óptima: {distancia_optima} m"
                self.students_list.item(i).setText(f"[ID: {i}] {vision_text} - {student.name}")
            self.compat_matrix = None
            self.compat_status.setText("❌ Compatibilidades no definidas")
            self.compat_status.setStyleSheet("color: #d32f2f; font-weight: bold;")

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
    
    def load_dataset(self):
        reply = QMessageBox.question(self.window, "Confirmar Carga",
                                     "¿Deseas cargar el dataset predefinido?\nSe borrarán todos los estudiantes actuales.",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.No:
            return

        self.clear_students(ask_confirmation=False)

        try:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            students_file = os.path.join(base_dir, 'datasets', 'students_dataset.csv')
            compat_file = os.path.join(base_dir, 'datasets', 'compatibility_dataset.csv')
            
            id_from_file_to_index = {}
            with open(students_file, mode='r', encoding='utf-8') as infile:
                reader = csv.DictReader(infile)
                for row in reader:
                    file_id = row['id'].strip()
                    name = row['name'].strip()
                    distancia_optima = float(row['distancia_optima'].strip())
                    
                    student_index = len(self.students)
                    self.students.append(Student(name, distancia_optima, student_index))
                    id_from_file_to_index[file_id] = student_index
                    
                    if distancia_optima == 0:
                        vision_text = "👀 Visión Normal"
                    else:
                        vision_text = f"🎯 Dist. Óptima: {distancia_optima} m"
                    display_text = f"[ID: {student_index}] {vision_text} - {name}"
                    self.students_list.addItem(display_text)

            num_students = len(self.students)
            self.compat_matrix = np.zeros((num_students, num_students))
            compat_pairs_count = 0
            with open(compat_file, mode='r', encoding='utf-8') as infile:
                reader = csv.DictReader(infile)
                for row in reader:
                    s1_id = row['student1_id'].strip()
                    s2_id = row['student2_id'].strip()
                    
                    if s1_id in id_from_file_to_index and s2_id in id_from_file_to_index:
                        idx1 = id_from_file_to_index[s1_id]
                        idx2 = id_from_file_to_index[s2_id]
                        self.compat_matrix[idx1, idx2] = 1
                        self.compat_matrix[idx2, idx1] = 1
                        compat_pairs_count += 1
            
            self.aula_input.setCurrentIndex(0)
            
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
        dialog.setWindowTitle("Definir Compatibilidades"); dialog.setMinimumSize(450, 300)
        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel("Marca las <b>PAREJAS</b> que se <b>DISTRAEN</b> entre sí:"))
        
        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        scroll_widget = QWidget(); scroll_layout = QVBoxLayout(scroll_widget)
        
        checkboxes = []
        if self.compat_matrix is None:
            self.compat_matrix = np.zeros((n, n))

        for i in range(n):
            for j in range(i + 1, n):
                student1_info = f"[ID:{self.students[i].index}] {self.students[i].name}"
                student2_info = f"[ID:{self.students[j].index}] {self.students[j].name}"
                cb = QCheckBox(f"{student1_info} ↔️ {student2_info}")
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

        selected_index = self.aula_input.currentIndex()
        if selected_index == 0:
            rows, cols = 5, 6
        else:
            rows, cols = 8, 5
        
        distancia_inicial = 2.0
        distancia_entre_filas = 1.0

        total_seats = rows * cols
        if total_seats < len(self.students):
            QMessageBox.critical(self.window, "Error de Capacidad", f"El aula seleccionada ({total_seats} asientos) no tiene suficientes lugares para los {len(self.students)} estudiantes.")
            return
            
        seats = [(r + 1, c + 1) for r in range(rows) for c in range(cols)]
        seat_distances = { (r + 1, c + 1): distancia_inicial + (r * distancia_entre_filas) for r in range(rows) for c in range(cols) }

        if self.compat_matrix is None:
            reply = QMessageBox.question(self.window, "Aviso de Compatibilidad", 
                                         "No has definido las compatibilidades. ¿Deseas continuar asumiendo que ningún estudiante se distrae con otro?",
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.No:
                return
            self.compat_matrix = np.zeros((len(self.students), len(self.students)))

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
            SolutionDialog(solutions, self.students, seats, seat_distances, self.compat_matrix, self.window).exec()
            if logbook:
                plot_evolution(logbook)
        else:
            QMessageBox.warning(self.window, "Sin Resultados", "El algoritmo no pudo encontrar una solución válida. Intenta de nuevo o ajusta los parámetros.")