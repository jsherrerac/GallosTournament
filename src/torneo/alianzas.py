import unicodedata

def normalizar(palabra: str) -> str:
    t = unicodedata.normalize("NFD", str(palabra).lower().strip())
    return "".join(c for c in t if unicodedata.category(c) != "Mn")

def parsear(texto: str) -> set:
    """'Norte, primos' -> {'norte', 'primos'} (separadas por coma o ;)"""
    if not texto:
        return set()
    crudo = str(texto).replace(";", ",")
    return {normalizar(p) for p in crudo.split(",") if p.strip()}

def comparten(al_a: set, al_b: set) -> bool:
    return bool(al_a & al_b)
