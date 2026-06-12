from .models import Cuerda, Frente, Gallo
from .alianzas import parsear
from .emparejador import emparejar_ronda, sin_rival
from .peso import a_onzas

class Config:
    def __init__(self, gallos_por_frente=3, frentes_por_cuerda=1,
                 tolerancia_max=2.0, duracion_pelea_seg=600, num_rondas=None):
        self.gallos_por_frente = gallos_por_frente
        self.frentes_por_cuerda = frentes_por_cuerda
        self.tolerancia_max = tolerancia_max
        self.duracion_pelea_seg = duracion_pelea_seg
        self.num_rondas = num_rondas      # None = sin límite

class Torneo:
    def __init__(self, config: Config):
        self.config = config
        self.cuerdas = []           # list[Cuerda]
        self.ronda_actual = 0
        self.peleas = []            # historial de TODAS las peleas

    # ---------- registro ----------
    def registrar_cuerda(self, nombre, alianzas_texto="", ciudad=""):
        nombre = nombre.strip()
        if not nombre:
            raise ValueError("La cuerda necesita nombre.")
        if any(c.nombre.lower() == nombre.lower() for c in self.cuerdas):
            raise ValueError(f"Ya existe la cuerda '{nombre}'.")
        c = Cuerda(nombre=nombre, alianzas=parsear(alianzas_texto), ciudad=ciudad)
        for i in range(1, self.config.frentes_por_cuerda + 1):
            c.frentes.append(Frente(numero=i, cuerda=nombre))
        self.cuerdas.append(c)
        return c

    def registrar_gallo(self, cuerda_nombre, num_frente, placa, peso_texto, **extra):
        c = self.buscar_cuerda(cuerda_nombre)
        if c is None:
            raise ValueError(f"No existe la cuerda '{cuerda_nombre}'.")
        if not str(placa).strip():
            raise ValueError("La placa es obligatoria.")
        placa = str(placa).strip()
        if any(g.placa == placa for g in self.todos_los_gallos()):
            raise ValueError(f"Ya existe un gallo con placa {placa}.")
        f = next((f for f in c.frentes if f.numero == int(num_frente)), None)
        if f is None:
            raise ValueError(f"La cuerda '{cuerda_nombre}' no tiene frente F{num_frente}.")
        if len(f.gallos) >= self.config.gallos_por_frente:
            raise ValueError(f"El frente F{num_frente} de '{cuerda_nombre}' ya está completo "
                             f"({self.config.gallos_por_frente} gallos).")
        g = Gallo(placa=placa, peso_oz=a_onzas(peso_texto),
                  cuerda=c.nombre, frente=f.etiqueta,
                  color=extra.get("color",""), tipo=extra.get("tipo","GALLO"),
                  marca=str(extra.get("marca","")), anillo=str(extra.get("anillo","")),
                  ciudad=extra.get("ciudad",""))
        f.gallos.append(g)
        return g

    # ---------- consultas ----------
    def buscar_cuerda(self, nombre):
        return next((c for c in self.cuerdas if c.nombre.lower() == nombre.lower().strip()), None)

    def todos_los_gallos(self):
        return [g for c in self.cuerdas for g in c.todos_los_gallos()]

    def frentes_incompletos(self):
        n = self.config.gallos_por_frente
        return [(c.nombre, f.etiqueta, len(f.gallos))
                for c in self.cuerdas for f in c.frentes if len(f.gallos) != n]

    def alianzas_por_cuerda(self):
        return {c.nombre: c.alianzas for c in self.cuerdas}

    def rivales_previos(self):
        """Pares (id,id) que ya pelearon — un gallo no repite rival en el torneo."""
        return {frozenset((p.gallo_a.id, p.gallo_b.id)) for p in self.peleas}

    # ---------- sorteo ----------
    def generar_ronda(self):
        if self.frentes_incompletos():
            raise ValueError("Hay frentes incompletos. Completá la inscripción primero.")
        if self.config.num_rondas and self.ronda_actual >= self.config.num_rondas:
            raise ValueError("El torneo ya alcanzó su número de rondas.")
        if any(not p.finalizada for p in self.peleas):
            raise ValueError("Hay peleas sin resolver de la ronda anterior.")
        self.ronda_actual += 1
        previos = self.rivales_previos()
        nuevas = emparejar_ronda(
            self.todos_los_gallos(), self.ronda_actual,
            self.alianzas_por_cuerda(), self.config.tolerancia_max,
            garantizar_frentes=(self.ronda_actual == 1))
        # filtrar repetición de rival a lo largo del torneo
        nuevas = [p for p in nuevas
                  if frozenset((p.gallo_a.id, p.gallo_b.id)) not in previos]
        self.peleas.extend(nuevas)
        return nuevas

    def peleas_de_ronda(self, ronda=None):
        r = ronda or self.ronda_actual
        return [p for p in self.peleas if p.ronda == r]

    def gallos_sin_rival(self, ronda=None):
        return sin_rival(self.todos_los_gallos(), self.peleas_de_ronda(ronda))

    @property
    def terminado(self):
        return (self.config.num_rondas is not None
                and self.ronda_actual >= self.config.num_rondas
                and all(p.finalizada for p in self.peleas))
