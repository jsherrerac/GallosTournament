def tabla_posiciones(gallos):
    return sorted(gallos, key=lambda g: (-g.puntos, -g.ganadas, g.perdidas))

def imprimir_tabla(gallos):
    print(f"{'#':<3}{'Gallo':<10}{'Frente':<18}{'PJ':>3}{'G':>3}{'E':>3}{'P':>3}{'Pts':>5}")
    print("-" * 52)
    for i, g in enumerate(tabla_posiciones(gallos), start=1):
        print(f"{i:<3}{g.nombre:<10}{g.frente:<18}{g.peleas:>3}{g.ganadas:>3}{g.empatadas:>3}{g.perdidas:>3}{g.puntos:>5}")
        
        
