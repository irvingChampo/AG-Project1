from PySide6.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QLabel,
    QSpinBox, QLineEdit, QListWidget, QComboBox, QMessageBox,
    QDialog, QCheckBox, QDialogButtonBox, QFormLayout, QTextEdit,
    QTabWidget, QScrollArea, QGridLayout, QFrame
)
from PySide6.QtCore import Qt, QThread, QObject, Signal
from core.models import Student
from core.genetic import run_ga, print_detailed_analysis
from gui.plot import plot_layout
import numpy as np

class OptimizationWorker(QObject):
    """Worker thread para ejecutar el algoritmo genético sin bloquear la UI"""
    finished = Signal(list)
    progress = Signal(str)
    
    def __init__(self, students, seats, compatibility_matrix, seat_distances, front_rows):
        super().__init__()
        self.students = students
        self.seats = seats
        self.compatibility_matrix = compatibility_matrix
        self.seat_distances = seat_distances
        self.front_rows = front_rows
    
    def run_optimization(self):
        try:
            self.progress.emit("Iniciando optimización...")
            solutions = run_ga(
                self.students, 
                self.seats, 
                self.compatibility_matrix, 
                self.seat_distances, 
                self.front_rows,
                ngen=150,
                pop_size=200
            )
            self.progress.emit("Optimización completada!")
            self.finished.emit(solutions)
        except Exception as e:
            self.progress.emit(f"Error: {str(e)}")
            self.finished.emit([])

class SolutionDialog(QDialog):
    """Diálogo para mostrar las 3 mejores soluciones"""
    
    def __init__(self, solutions, students, seats, compatibility_matrix, parent=None):
        super().__init__(parent)
        self.solutions = solutions
        self.students = students
        self.seats = seats
        self.compatibility_matrix = compatibility_matrix
        
        self.setWindowTitle("Mejores Soluciones Encontradas")
        self.setMinimumSize(800, 600)
        
        self.setup_ui()
        self.analyze_solutions()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Título
        title = QLabel("🧬 Algoritmo Genético - Mejores Soluciones")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px;")
        layout.addWidget(title)
        
        # Tabs para cada solución
        self.tab_widget = QTabWidget()
        
        for i, solution in enumerate(self.solutions):
            tab = self.create_solution_tab(solution, i + 1)
            self.tab_widget.addTab(tab, f"Solución {i + 1}")
        
        layout.addWidget(self.tab_widget)
        
        # Botones
        button_layout = QHBoxLayout()
        
        plot_button = QPushButton("📊 Ver Plano Visual")
        plot_button.clicked.connect(self.plot_current_solution)
        button_layout.addWidget(plot_button)
        
        export_button = QPushButton("💾 Exportar Análisis")
        export_button.clicked.connect(self.export_analysis)
        button_layout.addWidget(export_button)
        
        close_button = QPushButton("✅ Cerrar")
        close_button.clicked.connect(self.accept)
        button_layout.addWidget(close_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def create_solution_tab(self, solution, solution_num):
        """Crear una pestaña para mostrar una solución específica"""
        
        # Widget principal con scroll
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        
        main_widget = QWidget()
        layout = QVBoxLayout()
        
        # Métricas de la solución
        metrics_frame = QFrame()
        metrics_frame.setFrameStyle(QFrame.Box)
        metrics_layout = QVBoxLayout()
        
        metrics_title = QLabel(f"📈 Métricas de Solución {solution_num}")
        metrics_title.setStyleSheet("font-weight: bold; color: #2E86AB;")
        metrics_layout.addWidget(metrics_title)
        
        # Calcular métricas
        conflicts, total_pairs, vision_analysis = self.calculate_metrics(solution)
        
        metrics_text = f"""
        🎯 Conflictos de Compatibilidad: {conflicts}/{total_pairs} pares
        📊 Porcentaje de Separación: {((total_pairs-conflicts)/total_pairs*100):.1f}%
        👁️ Análisis por Visión:
        """
        
        for vision_type, avg_row in vision_analysis.items():
            icon = "👓" if vision_type == "no_far" else "🔍" if vision_type == "no_near" else "👀"
            metrics_text += f"   {icon} {vision_type}: Fila promedio {avg_row:.1f}\n"
        
        metrics_label = QLabel(metrics_text)
        metrics_label.setStyleSheet("font-family: monospace; background-color: #f0f8ff; padding: 10px; border-radius: 5px;")
        metrics_layout.addWidget(metrics_label)
        
        metrics_frame.setLayout(metrics_layout)
        layout.addWidget(metrics_frame)
        
        # Asignación de asientos
        assignment_frame = QFrame()
        assignment_frame.setFrameStyle(QFrame.Box)
        assignment_layout = QVBoxLayout()
        
        assignment_title = QLabel("🪑 Asignación de Asientos")
        assignment_title.setStyleSheet("font-weight: bold; color: #2E86AB;")
        assignment_layout.addWidget(assignment_title)
        
        # Crear grid para asientos
        grid_layout = QGridLayout()
        
        # Organizar por filas
        students_by_seat = {}
        for i, seat_idx in enumerate(solution):
            seat = self.seats[seat_idx]
            students_by_seat[seat] = self.students[i]
        
        max_row = max(seat[0] for seat in self.seats)
        max_col = max(seat[1] for seat in self.seats)
        
        # Añadir indicador de pizarrón
        board_label = QLabel("📋 PIZARRÓN")
        board_label.setAlignment(Qt.AlignCenter)
        board_label.setStyleSheet("background-color: #4CAF50; color: white; padding: 5px; font-weight: bold;")
        grid_layout.addWidget(board_label, 0, 0, 1, max_col)
        
        # Añadir estudiantes en sus asientos
        for row in range(1, max_row + 1):
            for col in range(1, max_col + 1):
                seat = (row, col)
                if seat in students_by_seat:
                    student = students_by_seat[seat]
                    
                    # Color según tipo de visión
                    if student.vision == "no_far":
                        bg_color = "#ffebee"  # Rojo suave
                        icon = "👓"
                    elif student.vision == "no_near":
                        bg_color = "#e3f2fd"  # Azul suave
                        icon = "🔍"
                    else:
                        bg_color = "#f5f5f5"  # Gris suave
                        icon = "👀"
                    
                    seat_label = QLabel(f"{icon}\n{student.name}")
                    seat_label.setAlignment(Qt.AlignCenter)
                    seat_label.setStyleSheet(f"""
                        background-color: {bg_color}; 
                        border: 2px solid #ddd; 
                        padding: 5px; 
                        font-size: 10px;
                        min-width: 80px;
                        min-height: 50px;
                    """)
                else:
                    seat_label = QLabel("🪑\nVacío")
                    seat_label.setAlignment(Qt.AlignCenter)
                    seat_label.setStyleSheet("""
                        background-color: #fafafa; 
                        border: 1px solid #ccc; 
                        padding: 5px; 
                        font-size: 10px;
                        min-width: 80px;
                        min-height: 50px;
                    """)
                
                grid_layout.addWidget(seat_label, row, col - 1)
        
        assignment_layout.addLayout(grid_layout)
        assignment_frame.setLayout(assignment_layout)
        layout.addWidget(assignment_frame)
        
        # Detalles de conflictos
        conflicts_frame = QFrame()
        conflicts_frame.setFrameStyle(QFrame.Box)
        conflicts_layout = QVBoxLayout()
        
        conflicts_title = QLabel("⚠️ Análisis de Conflictos")
        conflicts_title.setStyleSheet("font-weight: bold; color: #d32f2f;")
        conflicts_layout.addWidget(conflicts_title)
        
        conflicts_text = self.get_conflicts_analysis(solution)
        conflicts_display = QTextEdit()
        conflicts_display.setPlainText(conflicts_text)
        conflicts_display.setMaximumHeight(200)
        conflicts_display.setStyleSheet("font-family: monospace; font-size: 12px;")
        conflicts_layout.addWidget(conflicts_display)
        
        conflicts_frame.setLayout(conflicts_layout)
        layout.addWidget(conflicts_frame)
        
        main_widget.setLayout(layout)
        scroll.setWidget(main_widget)
        
        return scroll
    
    def calculate_metrics(self, solution):
        """Calcular métricas de una solución"""
        conflicts = 0
        total_pairs = 0
        
        # Análisis de conflictos
        for i in range(len(solution)):
            for j in range(i+1, len(solution)):
                if self.compatibility_matrix[i][j] == 1:
                    total_pairs += 1
                    seat_i = self.seats[solution[i]]
                    seat_j = self.seats[solution[j]]
                    dist = np.sqrt((seat_i[0] - seat_j[0])**2 + (seat_i[1] - seat_j[1])**2)
                    if dist <= 2.0:
                        conflicts += 1
        
        # Análisis por visión
        vision_analysis = {}
        for vision_type in ["no_far", "no_near", "normal"]:
            students_type = [i for i, s in enumerate(self.students) if s.vision == vision_type]
            if students_type:
                rows = [self.seats[solution[i]][0] for i in students_type]
                avg_row = sum(rows) / len(rows)
                vision_analysis[vision_type] = avg_row
        
        return conflicts, total_pairs, vision_analysis
    
    def get_conflicts_analysis(self, solution):
        """Obtener análisis detallado de conflictos"""
        conflicts_text = ""
        conflicts_found = False
        
        for i in range(len(solution)):
            for j in range(i+1, len(solution)):
                if self.compatibility_matrix[i][j] == 1:
                    seat_i = self.seats[solution[i]]
                    seat_j = self.seats[solution[j]]
                    dist = np.sqrt((seat_i[0] - seat_j[0])**2 + (seat_i[1] - seat_j[1])**2)
                    
                    if dist <= 2.0:
                        status = "❌ CONFLICTO"
                        conflicts_found = True
                    elif dist <= 3.0:
                        status = "⚠️  CERCA"
                    else:
                        status = "✅ SEPARADOS"
                    
                    conflicts_text += f"{self.students[i].name} - {self.students[j].name}: distancia {dist:.2f} {status}\n"
        
        if not conflicts_found:
            conflicts_text = "🎉 ¡Excelente! No se encontraron conflictos de proximidad.\n" + conflicts_text
        else:
            conflicts_text = "⚠️ Se encontraron algunos conflictos que requieren atención:\n\n" + conflicts_text
        
        return conflicts_text
    
    def analyze_solutions(self):
        """Analizar y rankear las soluciones"""
        self.solution_scores = []
        
        for i, solution in enumerate(self.solutions):
            conflicts, total_pairs, vision_analysis = self.calculate_metrics(solution)
            
            # Calcular score general
            separation_score = (total_pairs - conflicts) / total_pairs if total_pairs > 0 else 1.0
            
            # Score de ubicación por visión
            vision_score = 0
            if "no_far" in vision_analysis:
                vision_score += max(0, (5 - vision_analysis["no_far"]) / 5)  # Mejor si están adelante
            if "no_near" in vision_analysis:
                vision_score += max(0, (vision_analysis["no_near"] - 1) / 5)  # Mejor si están atrás
            
            total_score = (separation_score * 0.7) + (vision_score * 0.3)
            self.solution_scores.append(total_score)
        
        # Actualizar títulos de tabs con scores
        for i, score in enumerate(self.solution_scores):
            current_text = self.tab_widget.tabText(i)
            self.tab_widget.setTabText(i, f"{current_text} (Score: {score:.2f})")
    
    def plot_current_solution(self):
        """Mostrar el plano visual de la solución actual"""
        current_index = self.tab_widget.currentIndex()
        if current_index < len(self.solutions):
            try:
                plot_layout(self.seats, self.solutions[current_index], self.students)
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Error al mostrar el plano: {str(e)}")
    
    def export_analysis(self):
        """Exportar análisis detallado a archivo de texto"""
        try:
            with open("analisis_soluciones.txt", "w", encoding="utf-8") as f:
                f.write("=" * 60 + "\n")
                f.write("ANÁLISIS DETALLADO DE SOLUCIONES - ALGORITMO GENÉTICO\n")
                f.write("=" * 60 + "\n\n")
                
                for i, solution in enumerate(self.solutions):
                    f.write(f"SOLUCIÓN {i + 1} (Score: {self.solution_scores[i]:.3f})\n")
                    f.write("-" * 40 + "\n\n")
                    
                    # Asignación
                    f.write("ASIGNACIÓN DE ASIENTOS:\n")
                    for j, seat_idx in enumerate(solution):
                        seat = self.seats[seat_idx]
                        f.write(f"{self.students[j].name:20} -> Fila {seat[0]:2}, Columna {seat[1]:2} (Visión: {self.students[j].vision})\n")
                    
                    # Conflictos
                    f.write(f"\nANÁLISIS DE CONFLICTOS:\n")
                    f.write(self.get_conflicts_analysis(solution))
                    
                    f.write("\n" + "=" * 60 + "\n\n")
            
            QMessageBox.information(self, "Éxito", "Análisis exportado a 'analisis_soluciones.txt'")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error al exportar: {str(e)}")

class SeatPlanApp:
    def __init__(self):
        self.app = QApplication([])
        self.window = QWidget()
        self.window.setWindowTitle("🧬 SeatPlan - Algoritmo Genético")
        self.window.setMinimumSize(500, 700)

        # Datos principales
        self.students = []
        self.compat_matrix = None
        
        self.setup_ui()
        self.setup_styles()

    def setup_ui(self):
        self.layout = QVBoxLayout()

        # Título principal
        title = QLabel("🧬 SeatPlan - Optimizador de Asientos")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #2E86AB; padding: 15px;")
        self.layout.addWidget(title)

        # Configuración del aula
        aula_frame = QFrame()
        aula_frame.setFrameStyle(QFrame.Box)
        aula_layout = QVBoxLayout()
        
        aula_title = QLabel("🏫 Configuración del Aula")
        aula_title.setStyleSheet("font-weight: bold; color: #2E86AB; padding: 5px;")
        aula_layout.addWidget(aula_title)
        
        # Grid para filas y columnas
        grid_layout = QGridLayout()
        
        grid_layout.addWidget(QLabel("Filas:"), 0, 0)
        self.rows_input = QSpinBox()
        self.rows_input.setMinimum(1)
        self.rows_input.setMaximum(20)
        self.rows_input.setValue(5)
        grid_layout.addWidget(self.rows_input, 0, 1)
        
        grid_layout.addWidget(QLabel("Columnas:"), 0, 2)
        self.cols_input = QSpinBox()
        self.cols_input.setMinimum(1)
        self.cols_input.setMaximum(20)
        self.cols_input.setValue(6)
        grid_layout.addWidget(self.cols_input, 0, 3)
        
        aula_layout.addLayout(grid_layout)
        aula_frame.setLayout(aula_layout)
        self.layout.addWidget(aula_frame)

        # Gestión de estudiantes
        students_frame = QFrame()
        students_frame.setFrameStyle(QFrame.Box)
        students_layout = QVBoxLayout()
        
        students_title = QLabel("👥 Gestión de Estudiantes")
        students_title.setStyleSheet("font-weight: bold; color: #2E86AB; padding: 5px;")
        students_layout.addWidget(students_title)
        
        # Formulario para agregar estudiantes
        form_layout = QGridLayout()
        
        form_layout.addWidget(QLabel("Nombre:"), 0, 0)
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Nombre del estudiante")
        form_layout.addWidget(self.name_input, 0, 1)
        
        form_layout.addWidget(QLabel("Tipo de Visión:"), 1, 0)
        self.vision_input = QComboBox()
        self.vision_input.addItems([
            ("normal", "👀 Normal"), 
            ("no_far", "👓 No ve bien de lejos"), 
            ("no_near", "🔍 No ve bien de cerca")
        ])
        self.vision_input.setItemData(0, "normal")
        self.vision_input.setItemData(1, "no_far") 
        self.vision_input.setItemData(2, "no_near")
        form_layout.addWidget(self.vision_input, 1, 1)

        students_layout.addLayout(form_layout)
        
        self.add_button = QPushButton("➕ Agregar Estudiante")
        self.add_button.clicked.connect(self.add_student)
        students_layout.addWidget(self.add_button)

        # Lista de estudiantes
        self.students_list = QListWidget()
        self.students_list.setMaximumHeight(150)
        students_layout.addWidget(self.students_list)
        
        # Botones de gestión
        buttons_layout = QHBoxLayout()
        
        self.remove_button = QPushButton("❌ Eliminar Seleccionado")
        self.remove_button.clicked.connect(self.remove_student)
        buttons_layout.addWidget(self.remove_button)
        
        self.clear_button = QPushButton("🗑️ Limpiar Todo")
        self.clear_button.clicked.connect(self.clear_students)
        buttons_layout.addWidget(self.clear_button)
        
        students_layout.addLayout(buttons_layout)
        students_frame.setLayout(students_layout)
        self.layout.addWidget(students_frame)

        # Compatibilidades
        compat_frame = QFrame()
        compat_frame.setFrameStyle(QFrame.Box)
        compat_layout = QVBoxLayout()
        
        compat_title = QLabel("🤝 Configuración de Compatibilidades")
        compat_title.setStyleSheet("font-weight: bold; color: #2E86AB; padding: 5px;")
        compat_layout.addWidget(compat_title)
        
        compat_info = QLabel("Marca a los estudiantes que se distraen entre sí (compatibles)")
        compat_info.setStyleSheet("color: #666; font-style: italic;")
        compat_layout.addWidget(compat_info)
        
        self.comp_button = QPushButton("⚙️ Definir Compatibilidades")
        self.comp_button.clicked.connect(self.define_compatibilities)
        compat_layout.addWidget(self.comp_button)
        
        self.compat_status = QLabel("❌ Compatibilidades no definidas")
        self.compat_status.setStyleSheet("color: #d32f2f;")
        compat_layout.addWidget(self.compat_status)
        
        compat_frame.setLayout(compat_layout)
        self.layout.addWidget(compat_frame)

        # Optimización
        optim_frame = QFrame()
        optim_frame.setFrameStyle(QFrame.Box)
        optim_layout = QVBoxLayout()
        
        optim_title = QLabel("🚀 Optimización")
        optim_title.setStyleSheet("font-weight: bold; color: #2E86AB; padding: 5px;")
        optim_layout.addWidget(optim_title)
        
        self.run_button = QPushButton("🧬 Ejecutar Algoritmo Genético")
        self.run_button.clicked.connect(self.optimize_seats)
        self.run_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 10px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        optim_layout.addWidget(self.run_button)
        
        self.progress_label = QLabel("")
        optim_layout.addWidget(self.progress_label)
        
        optim_frame.setLayout(optim_layout)
        self.layout.addWidget(optim_frame)

        self.window.setLayout(self.layout)
        
        # Conectar Enter key para agregar estudiante
        self.name_input.returnPressed.connect(self.add_student)

    def setup_styles(self):
        """Configurar estilos generales de la aplicación"""
        self.window.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border-radius: 8px;
                padding: 10px;
                margin: 5px;
            }
            QLabel {
                color: #333;
            }
            QPushButton {
                padding: 8px;
                border-radius: 4px;
                border: 1px solid #ddd;
                background-color: #fff;
            }
            QPushButton:hover {
                background-color: #e9ecef;
            }
            QLineEdit, QComboBox, QSpinBox {
                padding: 5px;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
            QListWidget {
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: white;
            }
        """)

    def run(self):
        self.window.show()
        self.app.exec()

    def add_student(self):
        name = self.name_input.text().strip()
        vision = self.vision_input.itemData(self.vision_input.currentIndex())
        
        if not name:
            QMessageBox.warning(self.window, "Error", "Por favor ingresa un nombre válido.")
            return
        
        # Verificar que no existe el nombre
        if any(s.name.lower() == name.lower() for s in self.students):
            QMessageBox.warning(self.window, "Error", "Ya existe un estudiante con ese nombre.")
            return

        idx = len(self.students)
        self.students.append(Student(name, vision, idx))
        
        # Mostrar con íconos
        vision_icons = {"normal": "👀", "no_far": "👓", "no_near": "🔍"}
        vision_labels = {"normal": "Normal", "no_far": "No ve lejos", "no_near": "No ve cerca"}
        
        display_text = f"{vision_icons[vision]} {name} ({vision_labels[vision]})"
        self.students_list.addItem(display_text)
        
        self.name_input.clear()
        self.name_input.setFocus()
        
        # Resetear compatibilidades si cambia la lista
        if self.compat_matrix is not None:
            self.compat_matrix = None
            self.compat_status.setText("❌ Compatibilidades no definidas")
            self.compat_status.setStyleSheet("color: #d32f2f;")

    def remove_student(self):
        current_row = self.students_list.currentRow()
        if current_row >= 0:
            self.students_list.takeItem(current_row)
            self.students.pop(current_row)
            
            # Actualizar índices
            for i, student in enumerate(self.students):
                student.index = i
            
            # Resetear compatibilidades
            if self.compat_matrix is not None:
                self.compat_matrix = None
                self.compat_status.setText("❌ Compatibilidades no definidas")
                self.compat_status.setStyleSheet("color: #d32f2f;")

    def clear_students(self):
        reply = QMessageBox.question(self.window, "Confirmar", 
                                   "¿Estás seguro de que quieres eliminar todos los estudiantes?")
        if reply == QMessageBox.Yes:
            self.students.clear()
            self.students_list.clear()
            self.compat_matrix = None
            self.compat_status.setText("❌ Compatibilidades no definidas")
            self.compat_status.setStyleSheet("color: #d32f2f;")

    def define_compatibilities(self):
        n = len(self.students)
        if n < 2:
            QMessageBox.warning(self.window, "Error", "Necesitas al menos 2 estudiantes para definir compatibilidades.")
            return

        # Inicializar matriz (0 = no compatibles, 1 = compatibles)
        self.compat_matrix = np.zeros((n, n))
        
        dialog = QDialog(self.window)
        dialog.setWindowTitle("Definir Compatibilidades")
        dialog.setMinimumSize(600, 400)
        
        layout = QVBoxLayout()
        
        info_label = QLabel("Selecciona las PAREJAS que se DISTRAEN entre sí:")
        info_label.setStyleSheet("font-weight: bold; color: #d32f2f; padding: 10px;")
        layout.addWidget(info_label)
        
        # Scroll area para las compatibilidades
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout()
        
        checkboxes = []
        
        for i in range(n):
            for j in range(i + 1, n):
                cb = QCheckBox(f"{self.students[i].name} ↔️ {self.students[j].name}")
                scroll_layout.addWidget(cb)
                checkboxes.append((i, j, cb))
        
        scroll_widget.setLayout(scroll_layout)
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)
        
        # Botones
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layout.addWidget(buttons)
        
        dialog.setLayout(layout)
        
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        
        if dialog.exec() == QDialog.Accepted:
            # Procesar selecciones
            compatible_pairs = 0
            for i, j, cb in checkboxes:
                if cb.isChecked():
                    self.compat_matrix[i][j] = 1
                    self.compat_matrix[j][i] = 1  # Matriz simétrica
                    compatible_pairs += 1
            
            self.compat_status.setText(f"✅ {compatible_pairs} parejas compatibles definidas")
            self.compat_status.setStyleSheet("color: #2E7D32;")
        else:
            # Si se cancela, mantener matriz anterior o crear una por defecto
            if self.compat_matrix is None:
                self.compat_matrix = np.zeros((n, n))

    def optimize_seats(self):
        rows = self.rows_input.value()
        cols = self.cols_input.value()
        total_seats = rows * cols

        if len(self.students) == 0:
            QMessageBox.warning(self.window, "Error", "No hay estudiantes agregados.")
            return

        if total_seats < len(self.students):
            QMessageBox.warning(self.window, "Error", 
                              f"No hay suficientes asientos. Tienes {len(self.students)} estudiantes pero solo {total_seats} asientos.")
            return

        if self.compat_matrix is None:
            reply = QMessageBox.question(self.window, "Compatibilidades no definidas", 
                                       "No has definido compatibilidades. ¿Quieres continuar asumiendo que ningún estudiante es compatible?")
            if reply == QMessageBox.Yes:
                n = len(self.students)
                self.compat_matrix = np.zeros((n, n))
            else:
                return

        # Crear estructura de asientos
        seats = [(r + 1, c + 1) for r in range(rows) for c in range(cols)]
        seat_distances = {seat: seat[0] for seat in seats}  # Distancia = número de fila
        front_rows = [1]

        try:
            # Mostrar progreso
            self.progress_label.setText("🔄 Ejecutando algoritmo genético...")
            self.run_button.setEnabled(False)
            self.app.processEvents()

            # Ejecutar algoritmo genético
            solutions = run_ga(
                self.students, 
                seats, 
                self.compat_matrix, 
                seat_distances, 
                front_rows,
                ngen=150,  # Más generaciones para mejor calidad
                pop_size=200  # Población más grande
            )
            
            self.progress_label.setText("✅ ¡Optimización completada!")
            
            if solutions:
                # Mostrar diálogo con las 3 mejores soluciones
                solution_dialog = SolutionDialog(solutions, self.students, seats, self.compat_matrix, self.window)
                solution_dialog.exec()
            else:
                QMessageBox.warning(self.window, "Error", "No se pudieron generar soluciones válidas.")
            
        except Exception as e:
            QMessageBox.critical(self.window, "Error", f"Error durante la optimización: {str(e)}")
            
        finally:
            self.run_button.setEnabled(True)
            self.progress_label.setText("")