# Este archivo define las estructuras de datos básicas del proyecto.

from dataclasses import dataclass

@dataclass
class Student:
    name: str
    distancia_optima: float  # Distancia ideal en metros. 0 significa visión normal (ignorar).
    index: int   # La posición del estudiante en la lista original, útil para la matriz de compatibilidad.