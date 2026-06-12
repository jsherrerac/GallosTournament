from .models import Gallo, Pelea
import networkx as nx
def son_compatibles(a: Gallo, b: Gallo, tolerancia: float = 1.0) -> bool:
    """True si pueden pelear:
       - distinto gallo, distinto frente, distinto equipo
       - |peso_a - peso_b| <= tolerancia
    """
    return (
        a.id != b.id
        and a.equipo != b.equipo            # mismo equipo ⟹ mismo frente, así que esto ya cubre el frente
        and abs(a.peso - b.peso) <= tolerancia
    )
    

def emparejar_ronda(gallos: list[Gallo], ronda: int,
                    cubrir_todos_los_frentes: bool = False) -> list[Pelea]:
    """Genera las peleas de una ronda. Cada gallo pelea máx 1 vez.
       Si cubrir_todos_los_frentes=True (ronda 1), garantiza que
       al menos un gallo de cada frente quede emparejado.
    """
    peleas, usados = [], set()   # usados = ids que ya pelean esta ronda

    def buscar_rival(a):
        if a.id in usados:
            return False
        for b in gallos:
            if b.id in usados or not son_compatibles(a, b):
                continue
            peleas.append(Pelea(a, b, ronda))
            usados.update({a.id, b.id})   # <-- consumimos ambos
            return True
        return False

    # Fase 1 (ronda 1): garantizar 1 gallo por frente
    if cubrir_todos_los_frentes:
        por_frente = {}
        for g in gallos:
            por_frente.setdefault(g.frente, []).append(g)
        for sus in por_frente.values():
            if not any(g.id in usados for g in sus):   # ¿este frente ya quedó cubierto?
                for g in sus:
                    if buscar_rival(g):
                        break

    # Fase 2: greedy con el resto
    for a in gallos:
        buscar_rival(a)

    return peleas
def emparejar_optimo(gallos, ronda):
    G= nx.Graph()
    G.add_nodes_from(g.id for g in gallos)
    for i, a in enumerate(gallos):
        for b in gallos[i+1]:
            if son_compatibles(a,b):
                G.add_edge(a.id, b.id)
    por_id = {g.id: g for g in gallos}
    return [Pelea(por_id[x], por_id[y], ronda) for x, y in nx.max_weight_matching(G, maxcardinality=True)] 
