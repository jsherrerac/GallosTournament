# src/torneo/main.py
from .torneo import Torneo
from .persistencia import conectar, guardar, cargar
from .tabla import imprimir_tabla

t = Torneo(gallos_por_frente=2)
t.radicar_frente("GIRARDOT SEBAS", "GIRARDOT", [("Rayo", 3), ("Trueno", 4)])

peleas = t.generar_ronda(1)
for p in peleas:
    p.resolver(p.gallo_a)   

imprimir_tabla(t.todos_los_gallos())

con = conectar()
guardar(con, t)
con.close()