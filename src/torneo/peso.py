"""Conversión de peso. El cliente escribe '3-2.0' o '3,4' (libras, onzas).
Internamente TODO se maneja en onzas (1 libra = 16 onzas)."""

def a_onzas(texto) -> float:
    """'3-2.0' -> 50.0 | '3,4' -> 52.0 | '3.5' (ya en lb decimales NO: error) | 52 -> 52.0"""
    if isinstance(texto, (int, float)):
        return float(texto)            # ya viene en onzas
    t = str(texto).strip().replace(",", "-")
    if "-" in t:
        lb, oz = t.split("-", 1)
        return int(lb) * 16 + float(oz)
    return float(t)                    # solo onzas

def formato_lb_oz(onzas: float) -> str:
    lb = int(onzas) // 16
    oz = onzas - lb * 16
    oz_txt = f"{oz:.1f}".rstrip("0").rstrip(".")
    return f"{lb}-{oz_txt}"
