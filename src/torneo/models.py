from __future__ import annotations
from dataclasses import dataclass, field
import uuid

def _nuevo_id() -> str:
    return str(uuid.uuid4())[:8]

@dataclass
class Gallo:
    placa: str                  # obligatoria, identificador real
    peso_oz: float              # SIEMPRE en onzas internamente
    cuerda: str                 # nombre de la gallera dueña
    frente: str                 # "F1", "F2"... dentro de la cuerda
    color: str = ""
    tipo: str = "GALLO"         # GALLO | POLLO
    marca: str = ""
    anillo: str = ""
    ciudad: str = ""
    id: str = field(default_factory=_nuevo_id)
    ganadas: int = 0
    empatadas: int = 0
    perdidas: int = 0
    seg_victorias: float = 0.0  # tiempo acumulado de sus peleas GANADAS (desempate)

    @property
    def puntos(self) -> int:
        return self.ganadas * 3 + self.empatadas

    @property
    def peleas(self) -> int:
        return self.ganadas + self.empatadas + self.perdidas

@dataclass
class Frente:
    numero: int                 # 1, 2, 3...
    cuerda: str
    gallos: list = field(default_factory=list)

    @property
    def etiqueta(self) -> str:
        return f"F{self.numero}"

@dataclass
class Cuerda:
    nombre: str
    alianzas: set = field(default_factory=set)   # palabras clave (normalizadas)
    ciudad: str = ""
    frentes: list = field(default_factory=list)  # list[Frente]
    id: str = field(default_factory=_nuevo_id)

    def todos_los_gallos(self):
        return [g for f in self.frentes for g in f.gallos]

@dataclass
class Pelea:
    gallo_a: Gallo
    gallo_b: Gallo
    ronda: int = 1
    ganador: object = None
    finalizada: bool = False
    duracion_seg: float = 0.0   # cuánto duró la pelea (desempate por tiempo)
    nivel_peso: int = 0         # 0=exacto, 1=±1oz, 2=±2oz (consentida)
    id: str = field(default_factory=_nuevo_id)

    def resolver(self, ganador, duracion_seg: float = 0.0):
        self.finalizada = True
        self.ganador = ganador
        self.duracion_seg = duracion_seg
        if ganador is None:
            self.gallo_a.empatadas += 1; self.gallo_b.empatadas += 1
        elif ganador is self.gallo_a:
            self.gallo_a.ganadas += 1; self.gallo_b.perdidas += 1
            self.gallo_a.seg_victorias += duracion_seg
        else:
            self.gallo_b.ganadas += 1; self.gallo_a.perdidas += 1
            self.gallo_b.seg_victorias += duracion_seg
