def clasificacion(gallos):
    """Puntos desc → tiempo de victorias asc (gana más rápido = mejor) → más ganadas."""
    return sorted(gallos, key=lambda g: (-g.puntos, g.seg_victorias if g.ganadas else float("inf"), -g.ganadas))

def clasificacion_cuerdas(cuerdas):
    """Tabla por cuerda (como la imagen del cliente): suma de su frente."""
    filas = []
    for c in cuerdas:
        for f in c.frentes:
            pts = sum(g.puntos for g in f.gallos)
            pg  = sum(g.ganadas for g in f.gallos)
            pe  = sum(g.empatadas for g in f.gallos)
            pp  = sum(g.perdidas for g in f.gallos)
            seg = sum(g.seg_victorias for g in f.gallos)
            filas.append({"cuerda": c.nombre, "frente": f.numero, "puntos": pts,
                          "pg": pg, "pe": pe, "pp": pp,
                          "min": int(seg)//60, "seg": int(seg)%60, "_seg": seg})
    filas.sort(key=lambda x: (-x["puntos"], x["_seg"] if x["pg"] else float("inf")))
    return filas
