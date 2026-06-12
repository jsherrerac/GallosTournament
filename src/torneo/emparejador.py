import random
import networkx as nx
from .models import Pelea
from .alianzas import comparten

def restriccion_ok(a, b, alianzas_por_cuerda) -> bool:
    """No pelean: mismo gallo, misma cuerda, o cuerdas con alianza compartida."""
    if a.id == b.id or a.cuerda == b.cuerda:
        return False
    if comparten(alianzas_por_cuerda.get(a.cuerda, set()),
                 alianzas_por_cuerda.get(b.cuerda, set())):
        return False
    return True

def nivel_peso(a, b, tolerancia_max=2.0):
    """0 = peso exacto, 1 = ±1oz, 2 = ±2oz. None = incompatibles."""
    d = abs(a.peso_oz - b.peso_oz)
    if d == 0: return 0
    if d <= 1: return 1
    if d <= 2 and tolerancia_max >= 2: return 2
    return None

def emparejar_ronda(gallos, ronda, alianzas_por_cuerda, tolerancia_max=2.0,
                    garantizar_frentes=False, semilla=None):
    """Matching con prioridad: exacto > ±1oz > ±2oz. Aleatorio entre iguales.
       Si garantizar_frentes: cada (cuerda,frente) mete al menos un gallo si es posible."""
    rng = random.Random(semilla)
    gallos = list(gallos)
    rng.shuffle(gallos)                      # aleatoriedad que pide el cliente
    usados, peleas = set(), []

    def candidatos(a, pool):
        """rivales válidos de a, ordenados por nivel de peso (mejor primero)."""
        cs = []
        for b in pool:
            if b.id in usados or a.id == b.id: continue
            if not restriccion_ok(a, b, alianzas_por_cuerda): continue
            nv = nivel_peso(a, b, tolerancia_max)
            if nv is not None:
                cs.append((nv, rng.random(), b))
        cs.sort(key=lambda t: (t[0], t[1]))  # nivel asc, azar entre iguales
        return cs

    def emparejar(a):
        if a.id in usados: return False
        cs = candidatos(a, gallos)
        if not cs: return False
        nv, _, b = cs[0]
        p = Pelea(a, b, ronda); p.nivel_peso = nv
        peleas.append(p); usados.update({a.id, b.id})
        return True

    if garantizar_frentes:
        por_frente = {}
        for g in gallos:
            por_frente.setdefault((g.cuerda, g.frente), []).append(g)
        claves = list(por_frente.keys()); rng.shuffle(claves)
        for k in claves:
            sus = por_frente[k]
            if not any(g.id in usados for g in sus):
                for g in sus:
                    if emparejar(g): break

    for a in gallos:
        emparejar(a)
    return peleas

def sin_rival(gallos, peleas):
    """Gallos que quedaron libres (candidatos a comodín)."""
    en_pelea = {g.id for p in peleas for g in (p.gallo_a, p.gallo_b)}
    return [g for g in gallos if g.id not in en_pelea]
