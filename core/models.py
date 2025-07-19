from dataclasses import dataclass

@dataclass
class Student:
    name: str
    vision: str  # 'normal', 'no_far', 'no_near'
    index: int   # posición en la lista
