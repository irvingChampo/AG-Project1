# Este archivo define las estructuras de datos básicas del proyecto.

from dataclasses import dataclass

@dataclass
class Student:
    """
    Representa a un estudiante.
    Usar un dataclass es una forma moderna y limpia de crear clases
    que principalmente almacenan datos.
    """
    name: str
    vision: str  # 'normal', 'no_far' (no ve de lejos), 'no_near' (no ve de cerca)
    index: int   # La posición del estudiante en la lista original, útil para la matriz de compatibilidad.