from PySide6.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout, QLabel,
    QSpinBox, QLineEdit, QListWidget, QComboBox, QMessageBox,
    QDialog, QCheckBox, QDialogButtonBox, QFormLayout
)
from core.models import Student
from core.genetic import run_ga
from gui.plot import plot_layout
import numpy as np

class SeatPlanApp:
    def __init__(self):
        self.app = QApplication([])
        self.window = QWidget()
        self.window.setWindowTitle("SeatPlan - Configuración")

        self.layout = QVBoxLayout()

        self.rows_input = QSpinBox()
        self.rows_input.setMinimum(1)
        self.rows_input.setPrefix("Filas: ")
        self.layout.addWidget(self.rows_input)

        self.cols_input = QSpinBox()
        self.cols_input.setMinimum(1)
        self.cols_input.setPrefix("Columnas: ")
        self.layout.addWidget(self.cols_input)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Nombre del estudiante")
        self.layout.addWidget(self.name_input)

        self.vision_input = QComboBox()
        self.vision_input.addItems(["normal", "no_far", "no_near"])
        self.layout.addWidget(self.vision_input)

        self.add_button = QPushButton("Agregar estudiante")
        self.add_button.clicked.connect(self.add_student)
        self.layout.addWidget(self.add_button)

        self.students_list = QListWidget()
        self.layout.addWidget(self.students_list)

        self.comp_button = QPushButton("Definir compatibilidades")
        self.comp_button.clicked.connect(self.define_compatibilities)
        self.layout.addWidget(self.comp_button)

        self.run_button = QPushButton("Optimizar asientos")
        self.run_button.clicked.connect(self.optimize_seats)
        self.layout.addWidget(self.run_button)

        self.students = []
        self.compat_matrix = None

        self.window.setLayout(self.layout)

    def run(self):
        self.window.show()
        self.app.exec()

    def add_student(self):
        name = self.name_input.text().strip()
        vision = self.vision_input.currentText()

        if not name:
            QMessageBox.critical(self.window, "Error", "Nombre vacío.")
            return

        idx = len(self.students)
        self.students.append(Student(name, vision, idx))
        self.students_list.addItem(f"{name} ({vision})")
        self.name_input.clear()

    def define_compatibilities(self):
        n = len(self.students)
        if n < 2:
            QMessageBox.critical(self.window, "Error", "Necesitas al menos 2 estudiantes.")
            return

        self.compat_matrix = np.ones((n, n))
        for i in range(n):
            dialog = QDialog(self.window)
            dialog.setWindowTitle(f"Compatibilidad para {self.students[i].name}")
            layout = QFormLayout()

            checkboxes = []
            for j in range(n):
                if i != j:
                    cb = QCheckBox(self.students[j].name)
                    layout.addRow(cb)
                    checkboxes.append((j, cb))

            buttons = QDialogButtonBox(QDialogButtonBox.Ok)
            layout.addWidget(buttons)
            dialog.setLayout(layout)

            buttons.accepted.connect(dialog.accept)
            dialog.exec()

            for j, cb in checkboxes:
                if cb.isChecked():
                    self.compat_matrix[i][j] = 0  # NO compatible

        QMessageBox.information(self.window, "Compatibilidad", "Compatibilidades definidas correctamente.")

    def optimize_seats(self):
        rows = self.rows_input.value()
        cols = self.cols_input.value()
        total_seats = rows * cols

        if total_seats < len(self.students):
            QMessageBox.critical(self.window, "Error", "No hay suficientes asientos.")
            return

        seats = [(r + 1, c + 1) for r in range(rows) for c in range(cols)]
        seat_distances = {seat: seat[0] for seat in seats}
        front_rows = [1]

        if self.compat_matrix is None or self.compat_matrix.shape != (len(self.students), len(self.students)):
            QMessageBox.critical(self.window, "Error", "Define compatibilidades primero.")
            return

        assignment = run_ga(self.students, seats, self.compat_matrix, seat_distances, front_rows)
        plot_layout(seats, assignment, self.students)
