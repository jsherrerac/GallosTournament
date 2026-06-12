from .models import Frente
from .emparejador import emparejar_ronda, emparejar_optimo

class Torneo:
    def __init__(self, gallos_por_frente):
        self.gallos_por_frente = gallos_por_frente
        self.frentes = []
        self._siguiente_radicado = 1

    def radicar_frente(self, nombre, equipo, gallos_data):
        if len(gallos_data) != self.gallos_por_frente:
            raise ValueError(
                f"'{nombre}' inscribió {len(gallos_data)} gallos, "
                f"pero el torneo exige {self.gallos_por_frente}.")
        if any(f.nombre == nombre for f in self.frentes):
            raise ValueError(f"Ya existe un frente llamado '{nombre}'.")
        radicado = f"R-{self._siguiente_radicado:03d}"
        self._siguiente_radicado += 1
        frente = Frente(nombre=nombre, equipo=equipo, radicado=radicado)
        for gnombre, peso in gallos_data:
            frente.inscribir(gnombre, peso)
        self.frentes.append(frente)
        return frente

    def todos_los_gallos(self):
        return [g for f in self.frentes for g in f.gallos]

    def generar_ronda(self, ronda):
        gallos = self.todos_los_gallos()
        if ronda == 1:
            return emparejar_ronda(gallos, ronda, cubrir_todos_los_frentes=True)
        return emparejar_optimo(gallos, ronda)