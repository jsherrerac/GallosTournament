import customtkinter as ctk
from tkinter import filedialog
import sys, os
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "src"))

from torneo.torneo import Torneo, Config
from torneo.reloj import Reloj, formato_mmss
from torneo.peso import formato_lb_oz
from torneo.tabla import clasificacion, clasificacion_cuerdas
from torneo.importar import importar, crear_plantilla
from torneo.exportar import exportar_resultados
from torneo.persistencia import conectar, guardar, cargar

DB = "torneo.db"


class Pantalla(ctk.CTkFrame):
    """Base: todas las pantallas tienen app y un label de estado."""
    def __init__(self, parent, app, titulo):
        super().__init__(parent)
        self.app = app
        head = ctk.CTkFrame(self, fg_color="transparent")
        head.pack(fill="x", padx=20, pady=(15, 5))
        ctk.CTkLabel(head, text=titulo,
                     font=ctk.CTkFont(size=22, weight="bold")).pack(side="left")
        self.header = head
        self.lbl_estado = ctk.CTkLabel(self, text="")

    def estado(self, txt, color="gray"):
        self.lbl_estado.configure(text=txt, text_color=color)

    def al_mostrar(self):
        pass


# ============================================================
#  CONFIGURACIÓN
# ============================================================
class PantallaConfig(Pantalla):
    def __init__(self, parent, app):
        super().__init__(parent, app, "Configuración del torneo")
        form = ctk.CTkFrame(self)
        form.pack(padx=20, pady=10, fill="x")
        self.entries = {}
        campos = [("Gallos por frente", "gallos_por_frente", "3"),
                  ("Frentes por cuerda", "frentes_por_cuerda", "1"),
                  ("Tolerancia máx. de peso (oz)", "tolerancia_max", "2"),
                  ("Duración de pelea (minutos)", "duracion_min", "10"),
                  ("Número de rondas (vacío = sin límite)", "num_rondas", "")]
        for i, (lbl, clave, defecto) in enumerate(campos):
            ctk.CTkLabel(form, text=lbl, anchor="w").grid(row=i, column=0,
                         sticky="w", padx=15, pady=8)
            e = ctk.CTkEntry(form, width=120)
            e.insert(0, defecto)
            e.grid(row=i, column=1, padx=15, pady=8)
            self.entries[clave] = e
        self.btn = ctk.CTkButton(self, text="Crear torneo", command=self.crear)
        self.btn.pack(pady=10)
        self.lbl_estado.pack()
        self.lbl_info = ctk.CTkLabel(self, text="", text_color="gray")
        self.lbl_info.pack(pady=5)

    def crear(self):
        try:
            gpf = int(self.entries["gallos_por_frente"].get())
            fpc = int(self.entries["frentes_por_cuerda"].get())
            tol = float(self.entries["tolerancia_max"].get())
            dur = int(self.entries["duracion_min"].get()) * 60
            nr_txt = self.entries["num_rondas"].get().strip()
            nr = int(nr_txt) if nr_txt else None
            if gpf <= 0 or fpc <= 0 or dur <= 0 or tol not in (0, 1, 2) \
               or (nr is not None and nr <= 0):
                raise ValueError
        except ValueError:
            self.estado("Valores inválidos (tolerancia debe ser 0, 1 o 2).", "tomato")
            return
        self.app.torneo = Torneo(Config(gpf, fpc, tol, dur, nr))
        self.bloquear()
        self.estado("Torneo creado. Pasá a Registro de cuerdas.", "lightgreen")

    def bloquear(self):
        for e in self.entries.values():
            e.configure(state="disabled")
        self.btn.configure(state="disabled")
        c = self.app.torneo.config
        self.lbl_info.configure(text=f"Torneo activo · {c.gallos_por_frente} gallos/frente · "
            f"{c.frentes_por_cuerda} frente(s)/cuerda · ±{c.tolerancia_max:.0f} oz · "
            f"{c.duracion_pelea_seg//60} min/pelea · "
            f"rondas: {c.num_rondas if c.num_rondas else 'sin límite'}")

    def al_mostrar(self):
        if self.app.torneo:
            for clave, valor in [("gallos_por_frente", self.app.torneo.config.gallos_por_frente),
                                 ("frentes_por_cuerda", self.app.torneo.config.frentes_por_cuerda),
                                 ("tolerancia_max", int(self.app.torneo.config.tolerancia_max)),
                                 ("duracion_min", self.app.torneo.config.duracion_pelea_seg // 60),
                                 ("num_rondas", self.app.torneo.config.num_rondas or "")]:
                e = self.entries[clave]
                e.configure(state="normal"); e.delete(0, "end"); e.insert(0, str(valor))
            self.bloquear()


# ============================================================
#  REGISTRO DE CUERDAS
# ============================================================
class PantallaRegistro(Pantalla):
    def __init__(self, parent, app):
        super().__init__(parent, app, "Registro de cuerdas y gallos")
        ctk.CTkButton(self.header, text="📄 Generar plantilla Excel", width=180,
                      fg_color="gray30", hover_color="gray40",
                      command=self.plantilla).pack(side="right", padx=5)
        ctk.CTkButton(self.header, text="📥 Importar Excel", width=150,
                      command=self.importar_excel).pack(side="right", padx=5)

        cols = ctk.CTkFrame(self, fg_color="transparent")
        cols.pack(fill="both", expand=True, padx=20, pady=10)

        # --- izquierda: formularios ---
        izq = ctk.CTkFrame(cols)
        izq.pack(side="left", fill="both", expand=True, padx=(0, 10))

        ctk.CTkLabel(izq, text="Nueva cuerda",
                     font=ctk.CTkFont(size=15, weight="bold")).pack(pady=(12, 5))
        self.e_cuerda = ctk.CTkEntry(izq, placeholder_text="Nombre de la cuerda (ej. GUALCALA)")
        self.e_cuerda.pack(fill="x", padx=15, pady=3)
        self.e_alianzas = ctk.CTkEntry(izq, placeholder_text="Alianzas, separadas por coma (opcional)")
        self.e_alianzas.pack(fill="x", padx=15, pady=3)
        self.e_ciudad = ctk.CTkEntry(izq, placeholder_text="Ciudad (opcional)")
        self.e_ciudad.pack(fill="x", padx=15, pady=3)
        ctk.CTkButton(izq, text="Registrar cuerda", command=self.reg_cuerda).pack(pady=6)

        ctk.CTkLabel(izq, text="Registrar ave",
                     font=ctk.CTkFont(size=15, weight="bold")).pack(pady=(12, 5))
        f1 = ctk.CTkFrame(izq, fg_color="transparent"); f1.pack(fill="x", padx=15)
        self.cb_cuerda = ctk.CTkComboBox(f1, values=[""], width=200)
        self.cb_cuerda.pack(side="left", padx=(0, 5))
        self.cb_frente = ctk.CTkComboBox(f1, values=["F1"], width=80)
        self.cb_frente.pack(side="left", padx=5)
        f2 = ctk.CTkFrame(izq, fg_color="transparent"); f2.pack(fill="x", padx=15, pady=5)
        self.e_placa = ctk.CTkEntry(f2, placeholder_text="Placa *", width=110)
        self.e_placa.pack(side="left", padx=(0, 5))
        self.e_peso = ctk.CTkEntry(f2, placeholder_text="Peso lb-oz *", width=110)
        self.e_peso.pack(side="left", padx=5)
        self.cb_tipo = ctk.CTkComboBox(f2, values=["GALLO", "POLLO"], width=100)
        self.cb_tipo.pack(side="left", padx=5)
        f3 = ctk.CTkFrame(izq, fg_color="transparent"); f3.pack(fill="x", padx=15)
        self.e_color = ctk.CTkEntry(f3, placeholder_text="Color", width=110)
        self.e_color.pack(side="left", padx=(0, 5))
        self.e_marca = ctk.CTkEntry(f3, placeholder_text="Marca", width=80)
        self.e_marca.pack(side="left", padx=5)
        self.e_anillo = ctk.CTkEntry(f3, placeholder_text="Anillo", width=80)
        self.e_anillo.pack(side="left", padx=5)
        ctk.CTkButton(izq, text="+ Agregar ave", command=self.reg_gallo).pack(pady=8)
        self.lbl_estado.pack(in_=izq, pady=(0, 8))

        # --- derecha: cuerdas registradas ---
        der = ctk.CTkFrame(cols)
        der.pack(side="right", fill="both", expand=True, padx=(10, 0))
        self.lbl_resumen = ctk.CTkLabel(der, text="Cuerdas: 0 · Aves: 0 · Frentes completos: 0/0",
                                        font=ctk.CTkFont(size=13, weight="bold"))
        self.lbl_resumen.pack(pady=(12, 5))
        self.lista = ctk.CTkScrollableFrame(der)
        self.lista.pack(fill="both", expand=True, padx=12, pady=8)

    def _check(self):
        if not self.app.torneo:
            self.estado("Primero creá el torneo en Configuración.", "tomato")
            return False
        return True

    def reg_cuerda(self):
        if not self._check(): return
        try:
            self.app.torneo.registrar_cuerda(self.e_cuerda.get(),
                                             self.e_alianzas.get(), self.e_ciudad.get())
        except ValueError as e:
            self.estado(str(e), "tomato"); return
        for e in (self.e_cuerda, self.e_alianzas, self.e_ciudad):
            e.delete(0, "end")
        self.refrescar()
        self.estado("Cuerda registrada.", "lightgreen")

    def reg_gallo(self):
        if not self._check(): return
        try:
            num = int(self.cb_frente.get().replace("F", ""))
            self.app.torneo.registrar_gallo(
                self.cb_cuerda.get(), num, self.e_placa.get(), self.e_peso.get(),
                color=self.e_color.get(), tipo=self.cb_tipo.get(),
                marca=self.e_marca.get(), anillo=self.e_anillo.get())
        except ValueError as e:
            self.estado(str(e), "tomato"); return
        for e in (self.e_placa, self.e_peso, self.e_color, self.e_marca, self.e_anillo):
            e.delete(0, "end")
        self.refrescar()
        self.estado("Ave registrada.", "lightgreen")

    def importar_excel(self):
        if not self._check(): return
        ruta = filedialog.askopenfilename(filetypes=[("Excel", "*.xlsx")])
        if not ruta: return
        n, errores = importar(self.app.torneo, ruta)
        self.refrescar()
        msg = f"{n} aves importadas." + (f" {len(errores)} errores." if errores else "")
        self.estado(msg, "orange" if errores else "lightgreen")
        for e in errores[:5]:
            print("Import:", e)

    def plantilla(self):
        ruta = filedialog.asksaveasfilename(defaultextension=".xlsx",
                                            initialfile="plantilla_inscripcion.xlsx")
        if ruta:
            crear_plantilla(ruta)
            self.estado("Plantilla generada.", "lightgreen")

    def refrescar(self):
        t = self.app.torneo
        for w in self.lista.winfo_children():
            w.destroy()
        if not t: return
        self.cb_cuerda.configure(values=[c.nombre for c in t.cuerdas] or [""])
        self.cb_frente.configure(values=[f"F{i}" for i in range(1, t.config.frentes_por_cuerda + 1)])
        total_f = sum(len(c.frentes) for c in t.cuerdas)
        comp = total_f - len(t.frentes_incompletos())
        self.lbl_resumen.configure(text=f"Cuerdas: {len(t.cuerdas)} · "
            f"Aves: {len(t.todos_los_gallos())} · Frentes completos: {comp}/{total_f}")
        for c in t.cuerdas:
            alz = f"  [alianza: {', '.join(sorted(c.alianzas))}]" if c.alianzas else ""
            ctk.CTkLabel(self.lista, text=f"▸ {c.nombre}{alz}",
                         font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=5, pady=(6, 0))
            for f in c.frentes:
                falta = t.config.gallos_por_frente - len(f.gallos)
                tag = "✔" if falta == 0 else f"faltan {falta}"
                ctk.CTkLabel(self.lista, text=f"    {f.etiqueta} ({tag}): " +
                             ", ".join(f"{g.placa} {formato_lb_oz(g.peso_oz)}" for g in f.gallos)
                             ).pack(anchor="w", padx=5)

    def al_mostrar(self):
        self.refrescar()


# ============================================================
#  REALIZAR SORTEO
# ============================================================
class PantallaSorteo(Pantalla):
    def __init__(self, parent, app):
        super().__init__(parent, app, "Realizar sorteo")
        self.lbl_ronda = ctk.CTkLabel(self.header, text="", text_color="gray")
        self.lbl_ronda.pack(side="left", padx=15)
        ctk.CTkButton(self.header, text="🎲 Sortear ronda",
                      command=self.sortear).pack(side="right")
        self.lista = ctk.CTkScrollableFrame(self)
        self.lista.pack(fill="both", expand=True, padx=20, pady=10)
        self.lbl_estado.pack(pady=(0, 10))

    def sortear(self):
        if not self.app.torneo:
            self.estado("Primero creá el torneo en Configuración.", "tomato"); return
        try:
            peleas = self.app.torneo.generar_ronda()
        except ValueError as e:
            self.estado(str(e), "tomato"); return
        self.refrescar()
        sin = self.app.torneo.gallos_sin_rival()
        extra = f" · {len(sin)} sin rival (requieren comodín)" if sin else ""
        self.estado(f"Ronda {self.app.torneo.ronda_actual}: {len(peleas)} peleas{extra}.",
                    "orange" if sin else "lightgreen")

    def refrescar(self):
        for w in self.lista.winfo_children():
            w.destroy()
        t = self.app.torneo
        if not t: return
        self.lbl_ronda.configure(text=f"Ronda actual: {t.ronda_actual}" if t.ronda_actual else "")
        niveles = {0: "peso exacto", 1: "±1 oz", 2: "±2 oz ⚠ consentida"}
        for p in t.peleas_de_ronda():
            fila = ctk.CTkFrame(self.lista)
            fila.pack(fill="x", padx=5, pady=3)
            txt = (f"{p.gallo_a.placa} {p.gallo_a.cuerda} ({formato_lb_oz(p.gallo_a.peso_oz)})"
                   f"  vs  {p.gallo_b.placa} {p.gallo_b.cuerda} ({formato_lb_oz(p.gallo_b.peso_oz)})"
                   f"   ·   {niveles[p.nivel_peso]}")
            ctk.CTkLabel(fila, text=txt, anchor="w").pack(side="left", padx=10, pady=4)
            if p.finalizada:
                res = "Empate" if p.ganador is None else f"Ganó {p.ganador.placa}"
                ctk.CTkLabel(fila, text=res, text_color="lightgreen").pack(side="right", padx=10)
        sin = t.gallos_sin_rival()
        if sin and t.ronda_actual:
            ctk.CTkLabel(self.lista, text="— Sin rival (comodín del organizador): " +
                         ", ".join(f"{g.placa} ({g.cuerda}, {formato_lb_oz(g.peso_oz)})" for g in sin),
                         text_color="orange").pack(anchor="w", padx=8, pady=8)

    def al_mostrar(self):
        self.refrescar()


# ============================================================
#  CONTROL DE PELEAS
# ============================================================
class PantallaPeleas(Pantalla):
    def __init__(self, parent, app):
        super().__init__(parent, app, "Control de peleas")
        self.pelea = None
        self.reloj = None
        self._tick_id = None

        self.panel = ctk.CTkFrame(self)
        self.panel.pack(fill="x", padx=20, pady=8)
        self.lbl_pelea = ctk.CTkLabel(self.panel, text="Seleccioná una pelea",
                                      font=ctk.CTkFont(size=16, weight="bold"))
        self.lbl_pelea.pack(pady=(12, 4))
        self.lbl_reloj = ctk.CTkLabel(self.panel, text="--:--",
                                      font=ctk.CTkFont(size=42, weight="bold"))
        self.lbl_reloj.pack()
        ctrl = ctk.CTkFrame(self.panel, fg_color="transparent"); ctrl.pack(pady=6)
        self.b_play = ctk.CTkButton(ctrl, text="Iniciar", width=100,
                                    command=self.toggle, state="disabled")
        self.b_play.pack(side="left", padx=4)
        self.b_reset = ctk.CTkButton(ctrl, text="Reiniciar", width=100,
                                     command=self.reset, state="disabled")
        self.b_reset.pack(side="left", padx=4)
        res = ctk.CTkFrame(self.panel, fg_color="transparent"); res.pack(pady=(4, 12))
        self.b_a = ctk.CTkButton(res, text="Gana A", width=140, state="disabled",
                                 command=lambda: self.resolver("a"))
        self.b_a.pack(side="left", padx=4)
        self.b_e = ctk.CTkButton(res, text="Empate (tablas)", width=140, state="disabled",
                                 fg_color="gray", command=lambda: self.resolver("e"))
        self.b_e.pack(side="left", padx=4)
        self.b_b = ctk.CTkButton(res, text="Gana B", width=140, state="disabled",
                                 command=lambda: self.resolver("b"))
        self.b_b.pack(side="left", padx=4)

        self.lista = ctk.CTkScrollableFrame(self)
        self.lista.pack(fill="both", expand=True, padx=20, pady=8)
        self.lbl_estado.pack(pady=(0, 10))

    def seleccionar(self, p):
        self.pelea = p
        self.reloj = Reloj(self.app.torneo.config.duracion_pelea_seg)
        self.lbl_pelea.configure(text=f"{p.gallo_a.placa} {p.gallo_a.cuerda}  vs  "
                                      f"{p.gallo_b.placa} {p.gallo_b.cuerda}")
        self.b_a.configure(text=f"Gana {p.gallo_a.placa}", state="normal")
        self.b_b.configure(text=f"Gana {p.gallo_b.placa}", state="normal")
        self.b_e.configure(state="normal")
        self.b_play.configure(state="normal", text="Iniciar")
        self.b_reset.configure(state="normal")
        self.lbl_reloj.configure(text=formato_mmss(self.reloj.restante()))

    def toggle(self):
        if not self.reloj: return
        if self.reloj.corriendo:
            self.reloj.pausar(); self.b_play.configure(text="Iniciar")
        else:
            self.reloj.iniciar(); self.b_play.configure(text="Pausar"); self._tick()

    def _tick(self):
        if not self.reloj: return
        self.lbl_reloj.configure(text=formato_mmss(self.reloj.restante()))
        if self.reloj.termino():
            self.reloj.pausar(); self.b_play.configure(text="Iniciar")
            self.estado("¡Tiempo cumplido! Registrá el resultado (empate si no hubo ganador).",
                        "orange")
            return
        if self.reloj.corriendo:
            self._tick_id = self.after(200, self._tick)

    def reset(self):
        if self.reloj:
            self.reloj.reiniciar()
            if self._tick_id: self.after_cancel(self._tick_id); self._tick_id = None
            self.b_play.configure(text="Iniciar")
            self.lbl_reloj.configure(text=formato_mmss(self.reloj.duracion))

    def resolver(self, cual):
        p, r = self.pelea, self.reloj
        if not p: return
        if r and r.corriendo: r.pausar()
        if self._tick_id: self.after_cancel(self._tick_id); self._tick_id = None
        dur = r.transcurrido() if r else 0.0
        ganador = {"a": p.gallo_a, "b": p.gallo_b, "e": None}[cual]
        p.resolver(ganador, dur)
        self.pelea = None; self.reloj = None
        self.lbl_pelea.configure(text="Seleccioná una pelea")
        self.lbl_reloj.configure(text="--:--")
        for b in (self.b_a, self.b_b, self.b_e, self.b_play, self.b_reset):
            b.configure(state="disabled")
        self.b_a.configure(text="Gana A"); self.b_b.configure(text="Gana B")
        self.refrescar()
        m, s = int(dur) // 60, int(dur) % 60
        self.estado(f"Resultado registrado ({m} min {s} seg).", "lightgreen")

    def refrescar(self):
        for w in self.lista.winfo_children():
            w.destroy()
        t = self.app.torneo
        if not t or not t.ronda_actual: return
        for p in t.peleas_de_ronda():
            fila = ctk.CTkFrame(self.lista); fila.pack(fill="x", padx=5, pady=3)
            txt = (f"{p.gallo_a.placa} {p.gallo_a.cuerda} ({formato_lb_oz(p.gallo_a.peso_oz)})"
                   f"  vs  {p.gallo_b.placa} {p.gallo_b.cuerda} ({formato_lb_oz(p.gallo_b.peso_oz)})")
            ctk.CTkLabel(fila, text=txt, anchor="w").pack(side="left", padx=10, pady=4)
            if p.finalizada:
                m, s = int(p.duracion_seg) // 60, int(p.duracion_seg) % 60
                res = "Tablas" if p.ganador is None else f"Ganó {p.ganador.placa}"
                ctk.CTkLabel(fila, text=f"{res} · {m}:{s:02d}",
                             text_color="lightgreen").pack(side="right", padx=10)
            else:
                ctk.CTkButton(fila, text="Al ruedo", width=90,
                              command=lambda pe=p: self.seleccionar(pe)).pack(side="right", padx=8)

    def al_mostrar(self):
        self.refrescar()


# ============================================================
#  ESTADÍSTICAS
# ============================================================
class PantallaStats(Pantalla):
    def __init__(self, parent, app):
        super().__init__(parent, app, "Estadísticas")
        ctk.CTkButton(self.header, text="📑 Exportar PDF", width=140,
                      command=self.pdf).pack(side="right", padx=5)
        self.modo = ctk.CTkSegmentedButton(self.header, values=["Por cuerda", "Por gallo"],
                                           command=lambda _: self.refrescar())
        self.modo.set("Por cuerda")
        self.modo.pack(side="right", padx=10)
        self.cab = ctk.CTkFrame(self)
        self.cab.pack(fill="x", padx=20, pady=(8, 0))
        self.lista = ctk.CTkScrollableFrame(self)
        self.lista.pack(fill="both", expand=True, padx=20, pady=8)
        self.lbl_estado.pack(pady=(0, 8))

    def _fila(self, parent, valores, anchos, bold=False, zebra=False):
        f = ctk.CTkFrame(parent, fg_color=("gray85", "gray20") if zebra else "transparent")
        f.pack(fill="x", pady=1)
        font = ctk.CTkFont(weight="bold") if bold else None
        for v, a in zip(valores, anchos):
            ctk.CTkLabel(f, text=str(v), width=a, font=font).pack(side="left", padx=2, pady=3)

    def refrescar(self):
        for w in list(self.cab.winfo_children()) + list(self.lista.winfo_children()):
            w.destroy()
        t = self.app.torneo
        if not t: return
        if self.modo.get() == "Por cuerda":
            anchos = [40, 220, 70, 80, 50, 50, 50, 60, 60]
            self._fila(self.cab, ["#", "CUERDA", "FRENTE", "PUNTOS", "PG", "PE", "PP", "MIN", "SEG"],
                       anchos, bold=True)
            for i, fl in enumerate(clasificacion_cuerdas(t.cuerdas), 1):
                self._fila(self.lista, [i, fl["cuerda"], fl["frente"], fl["puntos"],
                                        fl["pg"], fl["pe"], fl["pp"], fl["min"], fl["seg"]],
                           anchos, zebra=i % 2 == 1)
        else:
            anchos = [40, 90, 180, 80, 50, 50, 50, 50, 60, 80]
            self._fila(self.cab, ["#", "PLACA", "CUERDA", "PESO", "PJ", "G", "E", "P", "PTS", "T.VICT"],
                       anchos, bold=True)
            for i, g in enumerate(clasificacion(t.todos_los_gallos()), 1):
                m, s = int(g.seg_victorias) // 60, int(g.seg_victorias) % 60
                self._fila(self.lista, [i, g.placa, g.cuerda, formato_lb_oz(g.peso_oz),
                                        g.peleas, g.ganadas, g.empatadas, g.perdidas,
                                        g.puntos, f"{m}:{s:02d}"],
                           anchos, zebra=i % 2 == 1)

    def pdf(self):
        if not self.app.torneo:
            self.estado("No hay torneo activo.", "tomato"); return
        ruta = filedialog.asksaveasfilename(defaultextension=".pdf",
                                            initialfile="resultado_torneo.pdf")
        if ruta:
            exportar_resultados(self.app.torneo, ruta, "RESULTADO DEL TORNEO")
            self.estado("PDF exportado.", "lightgreen")

    def al_mostrar(self):
        self.refrescar()


# ============================================================
#  APP
# ============================================================
class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Torneo Gallístico")
        self.geometry("1150x700")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("green")
        self.torneo = None
        self._cargar()

        self.nav = ctk.CTkFrame(self, width=200)
        self.nav.pack(side="left", fill="y", padx=5, pady=5)
        self.nav.pack_propagate(False)
        ctk.CTkLabel(self.nav, text="🐓 TORNEO\nGALLÍSTICO",
                     font=ctk.CTkFont(size=17, weight="bold")).pack(pady=(20, 25))

        self.contenido = ctk.CTkFrame(self)
        self.contenido.pack(side="right", fill="both", expand=True, padx=5, pady=5)
        self.pantallas = {
            "config":   PantallaConfig(self.contenido, self),
            "registro": PantallaRegistro(self.contenido, self),
            "sorteo":   PantallaSorteo(self.contenido, self),
            "peleas":   PantallaPeleas(self.contenido, self),
            "stats":    PantallaStats(self.contenido, self),
        }
        botones = [("⚙ Configuración", "config"), ("📋 Registro de cuerdas", "registro"),
                   ("🎲 Realizar sorteo", "sorteo"), ("⏱ Control de peleas", "peleas"),
                   ("📊 Estadísticas", "stats")]
        for txt, clave in botones:
            ctk.CTkButton(self.nav, text=txt, height=42, anchor="w",
                          command=lambda c=clave: self.mostrar(c)).pack(fill="x", padx=10, pady=4)
        ctk.CTkButton(self.nav, text="💾 Guardar", height=38, fg_color="gray30",
                      hover_color="gray40", command=self.guardar_ahora
                      ).pack(side="bottom", fill="x", padx=10, pady=10)

        self.actual = None
        self.mostrar("config" if not self.torneo else "registro")
        self.protocol("WM_DELETE_WINDOW", self.al_cerrar)

    def mostrar(self, clave):
        if self.actual:
            self.actual.pack_forget()
        self.actual = self.pantallas[clave]
        self.actual.pack(fill="both", expand=True)
        self.actual.al_mostrar()

    # ---- persistencia ----
    def _cargar(self):
        if os.path.exists(DB):
            try:
                con = conectar(DB)
                self.torneo = cargar(con)
                con.close()
            except Exception as e:
                print("No se pudo cargar:", e)

    def guardar_ahora(self):
        if not self.torneo: return False
        try:
            con = conectar(DB); guardar(con, self.torneo); con.close()
            return True
        except Exception as e:
            print("Error guardando:", e); return False

    def al_cerrar(self):
        self.guardar_ahora()
        self.destroy()


if __name__ == "__main__":
    App().mainloop()
