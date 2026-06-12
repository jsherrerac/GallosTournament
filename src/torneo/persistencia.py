import sqlite3
from .models import Gallo, Frente
from .torneo import Torneo


def conectar(ruta="torneo.db"):
    con= sqlite3.connect(ruta)
    con.execute("PRAGMA foreign_keys = ON")
    return con
def crear_esquema(con):
    con.executescript("""
            CREATE TABLE IF NOT EXISTS frentes(
                radicado TEXT PRIMARY KEY,
                nombre TEXT NOT NULL,
                equipo TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS gallos(
                id TEXT PRIMARY KEY,
                nombre TEXT NOT NULL,
                peso REAL NOT NULL,
                frente TEXT NOT NULL,
                ganadas INTEGER NOT NULL DEFAULT 0, 
                empatadas INTEGER NOT NULL DEFAULT 0,
                perdidas INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY (frente) REFERENCES frentes(radicado)
            );
            """)
    con.commit()
    
def guardar(con, torneo):
    crear_esquema(con)
    for f in torneo.frentes:
        con.execute(
            "INSERT OR REPLACE INTO frentes (radicado, nombre, equipo) VALUES (?, ?, ?)",
            (f.radicado, f.nombre, f.equipo),
        )
        for g in f.gallos:
            con.execute(
                """INSERT OR REPLACE INTO gallos
                   (id, nombre, peso, frente, ganadas, empatadas, perdidas)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (g.id, g.nombre, g.peso, f.radicado,
                 g.ganadas, g.empatadas, g.perdidas),)
    con.commit()
    
def cargar(con, gallos_por_frente):
    torneo= Torneo(gallos_por_frente)
    for radicado, nombre, equipo in con.execute("SELECT radicado, nombre, equipo FROM frentes"):
        frente= Frente(nombre=nombre, equipo=equipo, radicado=radicado)
        for gid, gn, peso, gan, emp, per in con.execute("""SELECT id, nombre, peso, ganadas, empatadas, perdidas FROM gallos 
                                                        WHERE frente =?""", (radicado, )):
            frente.gallos.append(Gallo(nombre=gn, peso=peso, frente=nombre, equipo=equipo, 
                                       id= gid, ganadas=gan, empatadas=emp, perdidas=per))
        torneo.frentes.append(frente)
    if torneo.frentes:
        torneo._siguiente_radicado= max(int(f.radicado.split("-")[1]) for f in torneo.frentes)+1
    return torneo