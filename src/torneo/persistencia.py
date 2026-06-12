import sqlite3, json
from .models import Cuerda, Frente, Gallo, Pelea
from .torneo import Torneo, Config

def conectar(ruta="torneo.db"):
    con = sqlite3.connect(ruta)
    con.execute("PRAGMA foreign_keys = ON")
    return con

def crear_esquema(con):
    con.executescript("""
        CREATE TABLE IF NOT EXISTS config (
            clave TEXT PRIMARY KEY, valor TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS cuerdas (
            id TEXT PRIMARY KEY, nombre TEXT UNIQUE NOT NULL,
            alianzas TEXT NOT NULL DEFAULT '[]', ciudad TEXT DEFAULT '');
        CREATE TABLE IF NOT EXISTS gallos (
            id TEXT PRIMARY KEY, placa TEXT UNIQUE NOT NULL,
            peso_oz REAL NOT NULL, cuerda TEXT NOT NULL, frente TEXT NOT NULL,
            color TEXT DEFAULT '', tipo TEXT DEFAULT 'GALLO',
            marca TEXT DEFAULT '', anillo TEXT DEFAULT '', ciudad TEXT DEFAULT '',
            ganadas INTEGER DEFAULT 0, empatadas INTEGER DEFAULT 0,
            perdidas INTEGER DEFAULT 0, seg_victorias REAL DEFAULT 0,
            FOREIGN KEY (cuerda) REFERENCES cuerdas(nombre));
        CREATE TABLE IF NOT EXISTS peleas (
            id TEXT PRIMARY KEY, ronda INTEGER NOT NULL,
            gallo_a TEXT NOT NULL, gallo_b TEXT NOT NULL,
            ganador TEXT, finalizada INTEGER DEFAULT 0,
            duracion_seg REAL DEFAULT 0, nivel_peso INTEGER DEFAULT 0,
            FOREIGN KEY (gallo_a) REFERENCES gallos(id),
            FOREIGN KEY (gallo_b) REFERENCES gallos(id));
    """)
    con.commit()

def guardar(con, torneo):
    crear_esquema(con)
    cfg = torneo.config
    pares = {"gallos_por_frente": cfg.gallos_por_frente,
             "frentes_por_cuerda": cfg.frentes_por_cuerda,
             "tolerancia_max": cfg.tolerancia_max,
             "duracion_pelea_seg": cfg.duracion_pelea_seg,
             "num_rondas": cfg.num_rondas if cfg.num_rondas is not None else "",
             "ronda_actual": torneo.ronda_actual}
    for k, v in pares.items():
        con.execute("INSERT OR REPLACE INTO config VALUES (?,?)", (k, str(v)))
    for c in torneo.cuerdas:
        con.execute("INSERT OR REPLACE INTO cuerdas VALUES (?,?,?,?)",
                    (c.id, c.nombre, json.dumps(sorted(c.alianzas)), c.ciudad))
        for g in c.todos_los_gallos():
            con.execute("""INSERT OR REPLACE INTO gallos VALUES
                (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (g.id, g.placa, g.peso_oz, g.cuerda, g.frente, g.color, g.tipo,
                 g.marca, g.anillo, g.ciudad, g.ganadas, g.empatadas,
                 g.perdidas, g.seg_victorias))
    for p in torneo.peleas:
        gid = None if p.ganador is None else p.ganador.id
        con.execute("INSERT OR REPLACE INTO peleas VALUES (?,?,?,?,?,?,?,?)",
                    (p.id, p.ronda, p.gallo_a.id, p.gallo_b.id, gid,
                     int(p.finalizada), p.duracion_seg, p.nivel_peso))
    con.commit()

def cargar(con):
    cfgrows = dict(con.execute("SELECT clave, valor FROM config"))
    if not cfgrows:
        return None
    nr = cfgrows.get("num_rondas", "")
    cfg = Config(int(cfgrows["gallos_por_frente"]), int(cfgrows["frentes_por_cuerda"]),
                 float(cfgrows["tolerancia_max"]), int(float(cfgrows["duracion_pelea_seg"])),
                 int(nr) if nr not in ("", "None") else None)
    t = Torneo(cfg)
    t.ronda_actual = int(cfgrows.get("ronda_actual", 0))
    gallos_por_id = {}
    for cid, nombre, alz, ciudad in con.execute("SELECT * FROM cuerdas"):
        c = Cuerda(nombre=nombre, alianzas=set(json.loads(alz)), ciudad=ciudad, id=cid)
        for i in range(1, cfg.frentes_por_cuerda + 1):
            c.frentes.append(Frente(numero=i, cuerda=nombre))
        for row in con.execute("SELECT * FROM gallos WHERE cuerda=?", (nombre,)):
            (gid, placa, peso, cu, fr, color, tipo, marca, anillo,
             gciudad, gan, emp, per, segv) = row
            g = Gallo(placa=placa, peso_oz=peso, cuerda=cu, frente=fr, color=color,
                      tipo=tipo, marca=marca, anillo=anillo, ciudad=gciudad, id=gid,
                      ganadas=gan, empatadas=emp, perdidas=per, seg_victorias=segv)
            f = next(f for f in c.frentes if f.etiqueta == fr)
            f.gallos.append(g); gallos_por_id[gid] = g
        t.cuerdas.append(c)
    for pid, ronda, ga, gb, gw, fin, dur, nv in con.execute("SELECT * FROM peleas"):
        p = Pelea(gallos_por_id[ga], gallos_por_id[gb], ronda, id=pid)
        p.finalizada = bool(fin); p.duracion_seg = dur; p.nivel_peso = nv
        p.ganador = gallos_por_id.get(gw) if gw else None
        t.peleas.append(p)
    return t
