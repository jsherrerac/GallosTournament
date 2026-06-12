from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
import uuid

def _nuevo_id()->str:
    return str(uuid.uuid4())[:8]

@dataclass
class Gallo:
    nombre: str
    peso: float #onzas
    frente: str
    equipo: str
    id: str = field (default_factory=_nuevo_id)
    ganadas: int=0
    empatadas: int = 0
    perdidas: int = 0
    
    @property
    def puntos(self)->int:
        return self.ganadas*3+ self.empatadas
    @property
    def peleas(self)->int:
        return self.ganadas+ self.empatadas+ self.perdidas

@dataclass
class Frente:
    nombre: str
    equipo: str
    radicado: str = ""
    gallos: list[Gallo]= field(default_factory=list)
    id: str= field(default_factory=_nuevo_id)

    def inscribir(self, nombre:str, peso:float)->Gallo:
        g= Gallo(nombre=nombre,peso=peso, frente=self.nombre, equipo=self.equipo)
        self.gallos.append(g)
        return g

@dataclass
class Pelea:
    gallo_a: Gallo
    gallo_b: Gallo
    ronda: int=1
    ganador: Gallo | None = None
    finalizada: bool=False
    id: str=field(default_factory=_nuevo_id)
    
    def resolver(self, ganador:Gallo| None)->None:
        self.finalizada=True
        self.ganador= ganador
        if ganador is None:
            self.gallo_a.empatadas+=1
            self.gallo_b.empatadas+=1
        elif ganador is self.gallo_a:
            self.gallo_a.ganadas += 1; self.gallo_b.perdidas += 1
        else:
            self.gallo_b.ganadas += 1; self.gallo_a.perdidas += 1
            
        