import customtkinter as ctk
import sys, os

# Para que Python encuentre src/torneo desde ui/app.py
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "src"))

from torneo.torneo import Torneo
from torneo.reloj import Reloj, formato_mmss
from torneo import municipios
import customtkinter as ctk
import sys, os
from torneo.torneo import Torneo
from torneo.reloj import Reloj, formato_mmss
from torneo import municipios
from torneo.tabla import tabla_posiciones
from torneo.persistencia import conectar, guardar, cargar



# ============================================================
#  WIDGET: ENTRADA DE MUNICIPIO CON AUTOCOMPLETADO
# ============================================================

class EntradaMunicipio(ctk.CTkFrame):
    """Campo de texto que sugiere municipios reales mientras escribís."""
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self.entry = ctk.CTkEntry(self, placeholder_text="Equipo / municipio (ej. Nilo)")
        self.entry.pack(fill="x")
        self.entry.bind("<KeyRelease>", self._al_escribir)
        self.sugerencias = ctk.CTkScrollableFrame(self, height=130)
        self._visible = False

    def _al_escribir(self, evento):
        texto = self.entry.get().strip()
        for w in self.sugerencias.winfo_children():
            w.destroy()
        matches = municipios.buscar(texto) if texto else []
        if matches:
            for m in matches:
                ctk.CTkButton(self.sugerencias, text=m, anchor="w", height=26,
                              fg_color="transparent", hover_color=("gray70", "gray30"),
                              command=lambda mm=m: self._elegir(mm)).pack(fill="x", padx=2, pady=1)
            self._mostrar()
        else:
            self._ocultar()

    def _elegir(self, m):
        self.entry.delete(0, "end")
        self.entry.insert(0, m)
        self._ocultar()

    def _mostrar(self):
        if not self._visible:
            self.sugerencias.pack(fill="x", pady=(2, 0))
            self._visible = True

    def _ocultar(self):
        if self._visible:
            self.sugerencias.pack_forget()
            self._visible = False

    # API para que la pantalla la use como si fuera un Entry
    def get(self):
        return self.entry.get()

    def clear(self):
        self.entry.delete(0, "end")
        self._ocultar()

    def set_enabled(self, enabled):
        self.entry.configure(state="normal" if enabled else "disabled")
        if not enabled:
            self._ocultar()


# ============================================================
#  PANTALLA: RADICACIÓN
# ============================================================

class PantallaRadicacion(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.gallos_pendientes = []   # [(nombre, peso), ...] del frente en construcción

        ctk.CTkLabel(self, text="Radicación de frentes",
                     font=ctk.CTkFont(size=22, weight="bold")).pack(pady=(15, 10))

        # ---- Configuración del torneo ----
        config = ctk.CTkFrame(self)
        config.pack(fill="x", padx=20, pady=5)
        ctk.CTkLabel(config, text="Gallos por frente:").pack(side="left", padx=(10, 5), pady=10)
        self.entry_gpf = ctk.CTkEntry(config, width=70, placeholder_text="ej. 3")
        self.entry_gpf.pack(side="left", padx=5, pady=10)
        self.btn_crear = ctk.CTkButton(config, text="Crear torneo", command=self.crear_torneo)
        self.btn_crear.pack(side="left", padx=10, pady=10)
        self.lbl_torneo = ctk.CTkLabel(config, text="Sin torneo creado", text_color="gray")
        self.lbl_torneo.pack(side="left", padx=10)

        # ---- Dos columnas ----
        cols = ctk.CTkFrame(self, fg_color="transparent")
        cols.pack(fill="both", expand=True, padx=20, pady=10)

        # === Izquierda: formulario ===
        form = ctk.CTkFrame(cols)
        form.pack(side="left", fill="both", expand=True, padx=(0, 10))

        ctk.CTkLabel(form, text="Nuevo frente",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(15, 10))
        self.entry_nombre = ctk.CTkEntry(form, placeholder_text="Nombre del frente (ej. GIRARDOT SEBAS)")
        self.entry_nombre.pack(fill="x", padx=15, pady=5)
        self.entry_equipo = EntradaMunicipio(form)
        self.entry_equipo.pack(fill="x", padx=15, pady=5)

        ctk.CTkLabel(form, text="Agregar gallos").pack(pady=(15, 5))
        fila = ctk.CTkFrame(form, fg_color="transparent")
        fila.pack(fill="x", padx=15)
        self.entry_gallo = ctk.CTkEntry(fila, placeholder_text="Nombre del gallo")
        self.entry_gallo.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.entry_peso = ctk.CTkEntry(fila, width=90, placeholder_text="Peso oz")
        self.entry_peso.pack(side="left", padx=5)
        self.btn_agregar = ctk.CTkButton(fila, text="+", width=40, command=self.agregar_gallo)
        self.btn_agregar.pack(side="left")

        self.lbl_contador = ctk.CTkLabel(form, text="Gallos: 0 / 0")
        self.lbl_contador.pack(pady=(10, 5))
        self.lista_gallos = ctk.CTkScrollableFrame(form, height=110)
        self.lista_gallos.pack(fill="both", expand=True, padx=15, pady=5)

        self.btn_radicar = ctk.CTkButton(form, text="Radicar frente",
                                         command=self.radicar_frente, state="disabled")
        self.btn_radicar.pack(fill="x", padx=15, pady=10)
        self.lbl_estado = ctk.CTkLabel(form, text="")
        self.lbl_estado.pack(pady=(0, 10))

        # === Derecha: frentes radicados ===
        derecha = ctk.CTkFrame(cols)
        derecha.pack(side="right", fill="both", expand=True, padx=(10, 0))
        ctk.CTkLabel(derecha, text="Frentes radicados",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(15, 10))
        self.lista_frentes = ctk.CTkScrollableFrame(derecha)
        self.lista_frentes.pack(fill="both", expand=True, padx=15, pady=10)

        self._set_form_enabled(False)

    # -------- helpers --------
    def _set_form_enabled(self, enabled):
        estado = "normal" if enabled else "disabled"
        for w in (self.entry_nombre, self.entry_gallo,
                  self.entry_peso, self.btn_agregar):
            w.configure(state=estado)
        self.entry_equipo.set_enabled(enabled)

    def _estado(self, texto, color="gray"):
        self.lbl_estado.configure(text=texto, text_color=color)

    # -------- handlers --------
    def crear_torneo(self):
        try:
            n = int(self.entry_gpf.get())
            if n <= 0:
                raise ValueError
        except ValueError:
            self._estado("Gallos por frente debe ser un entero positivo.", "tomato")
            return
        self.app.torneo = Torneo(gallos_por_frente=n)
        self.lbl_torneo.configure(text=f"Torneo activo · {n} gallos por frente", text_color="white")
        self.entry_gpf.configure(state="disabled")
        self.btn_crear.configure(state="disabled")
        self._set_form_enabled(True)
        self._actualizar_contador()
        self._estado("Torneo creado. Ya podés radicar frentes.", "lightgreen")

    def agregar_gallo(self):
        n = self.app.torneo.gallos_por_frente
        if len(self.gallos_pendientes) >= n:
            self._estado(f"Este frente ya tiene {n} gallos.", "tomato")
            return
        nombre = self.entry_gallo.get().strip()
        if not nombre:
            self._estado("El gallo necesita un nombre.", "tomato")
            return
        try:
            peso = float(self.entry_peso.get())
            if peso <= 0:
                raise ValueError
        except ValueError:
            self._estado("El peso debe ser un número positivo.", "tomato")
            return
        self.gallos_pendientes.append((nombre, peso))
        self.entry_gallo.delete(0, "end")
        self.entry_peso.delete(0, "end")
        self._refrescar_pendientes()
        self._estado("")

    def radicar_frente(self):
        nombre = self.entry_nombre.get().strip()
        equipo = self.entry_equipo.get().strip()
        if not nombre or not equipo:
            self._estado("Nombre y equipo son obligatorios.", "tomato")
            return
        equipo_oficial = municipios.canonico(equipo)
        if equipo_oficial is None:
            self._estado(f"'{equipo}' no es un municipio válido. Elegí uno de la lista.", "tomato")
            return
        try:
            self.app.torneo.radicar_frente(nombre, equipo_oficial, self.gallos_pendientes)
        except ValueError as e:
            self._estado(str(e), "tomato")
            return
        self.gallos_pendientes = []
        self.entry_nombre.delete(0, "end")
        self.entry_equipo.clear()
        self._refrescar_pendientes()
        self._refrescar_frentes()
        self._estado(f"Frente '{nombre}' radicado.", "lightgreen")

    # -------- refrescos --------
    def _actualizar_contador(self):
        n = self.app.torneo.gallos_por_frente if self.app.torneo else 0
        self.lbl_contador.configure(text=f"Gallos: {len(self.gallos_pendientes)} / {n}")
        completo = bool(self.app.torneo) and len(self.gallos_pendientes) == n
        self.btn_radicar.configure(state="normal" if completo else "disabled")

    def _refrescar_pendientes(self):
        for w in self.lista_gallos.winfo_children():
            w.destroy()
        for i, (nombre, peso) in enumerate(self.gallos_pendientes, 1):
            ctk.CTkLabel(self.lista_gallos, text=f"{i}. {nombre} — {peso} oz").pack(anchor="w", padx=5)
        self._actualizar_contador()

    def _refrescar_frentes(self):
        for w in self.lista_frentes.winfo_children():
            w.destroy()
        for f in self.app.torneo.frentes:
            texto = f"{f.radicado}  ·  {f.nombre}  ·  {f.equipo}  ·  {len(f.gallos)} gallos"
            ctk.CTkLabel(self.lista_frentes, text=texto).pack(anchor="w", padx=5, pady=2)


# ============================================================
#  PANTALLA: PELEAS
# ============================================================

class PantallaPeleas(ctk.CTkFrame):
    DURACION = 600  # segundos por pelea (configurable después)

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.ronda_actual = 0
        self.peleas_ronda = []
        self.pelea_activa = None
        self.reloj = Reloj(self.DURACION)
        self._tick_id = None

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(15, 5))
        ctk.CTkLabel(header, text="Peleas",
                     font=ctk.CTkFont(size=22, weight="bold")).pack(side="left")
        self.lbl_ronda = ctk.CTkLabel(header, text="Sin rondas generadas", text_color="gray")
        self.lbl_ronda.pack(side="left", padx=20)
        self.btn_generar = ctk.CTkButton(header, text="Generar ronda", command=self.generar_ronda)
        self.btn_generar.pack(side="right")

        self.panel = ctk.CTkFrame(self)
        self.panel.pack(fill="x", padx=20, pady=10)
        self.lbl_activa = ctk.CTkLabel(self.panel, text="Seleccioná una pelea de la lista",
                                       font=ctk.CTkFont(size=16, weight="bold"))
        self.lbl_activa.pack(pady=(15, 5))
        self.lbl_reloj = ctk.CTkLabel(self.panel, text=formato_mmss(self.DURACION),
                                      font=ctk.CTkFont(size=42, weight="bold"))
        self.lbl_reloj.pack(pady=5)

        controles = ctk.CTkFrame(self.panel, fg_color="transparent")
        controles.pack(pady=10)
        self.btn_reloj = ctk.CTkButton(controles, text="Iniciar", width=110,
                                       command=self.toggle_reloj, state="disabled")
        self.btn_reloj.pack(side="left", padx=5)
        self.btn_reset = ctk.CTkButton(controles, text="Reiniciar", width=110,
                                       command=self.reiniciar_reloj, state="disabled")
        self.btn_reset.pack(side="left", padx=5)

        resultados = ctk.CTkFrame(self.panel, fg_color="transparent")
        resultados.pack(pady=(5, 15))
        self.btn_gana_a = ctk.CTkButton(resultados, text="Gana A", width=130,
                                        command=lambda: self.resolver("a"), state="disabled")
        self.btn_gana_a.pack(side="left", padx=5)
        self.btn_empate = ctk.CTkButton(resultados, text="Empate", width=130, fg_color="gray",
                                        command=lambda: self.resolver("empate"), state="disabled")
        self.btn_empate.pack(side="left", padx=5)
        self.btn_gana_b = ctk.CTkButton(resultados, text="Gana B", width=130,
                                        command=lambda: self.resolver("b"), state="disabled")
        self.btn_gana_b.pack(side="left", padx=5)

        ctk.CTkLabel(self, text="Peleas de la ronda",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(5, 0))
        self.lista = ctk.CTkScrollableFrame(self)
        self.lista.pack(fill="both", expand=True, padx=20, pady=10)
        self.lbl_estado = ctk.CTkLabel(self, text="")
        self.lbl_estado.pack(pady=(0, 10))

    def _estado(self, texto, color="gray"):
        self.lbl_estado.configure(text=texto, text_color=color)

    def generar_ronda(self):
        if not self.app.torneo or not self.app.torneo.frentes:
            self._estado("Primero radicá frentes en la pantalla de Radicación.", "tomato")
            return
        if self.peleas_ronda and any(not p.finalizada for p in self.peleas_ronda):
            self._estado("Resolvé todas las peleas antes de generar otra ronda.", "tomato")
            return
        self.ronda_actual += 1
        self.peleas_ronda = self.app.torneo.generar_ronda(self.ronda_actual)
        if not self.peleas_ronda:
            self.ronda_actual -= 1
            self._estado("No se pudieron armar peleas (revisá pesos/equipos).", "tomato")
            return
        self.lbl_ronda.configure(
            text=f"Ronda {self.ronda_actual} · {len(self.peleas_ronda)} peleas", text_color="white")
        self._limpiar_activa()
        self._refrescar_lista()
        self._estado(f"Ronda {self.ronda_actual} generada.", "lightgreen")

    def seleccionar(self, pelea):
        if pelea.finalizada:
            return
        self.pelea_activa = pelea
        self.lbl_activa.configure(
            text=f"{pelea.gallo_a.nombre} ({pelea.gallo_a.peso}oz)   vs   "
                 f"{pelea.gallo_b.nombre} ({pelea.gallo_b.peso}oz)")
        self.btn_gana_a.configure(text=f"Gana {pelea.gallo_a.nombre}", state="normal")
        self.btn_gana_b.configure(text=f"Gana {pelea.gallo_b.nombre}", state="normal")
        self.btn_empate.configure(state="normal")
        self.btn_reloj.configure(state="normal")
        self.btn_reset.configure(state="normal")
        self.reiniciar_reloj()

    def toggle_reloj(self):
        if self.reloj.corriendo:
            self.reloj.pausar()
            self.btn_reloj.configure(text="Iniciar")
        else:
            self.reloj.iniciar()
            self.btn_reloj.configure(text="Pausar")
            self._tick()

    def _tick(self):
        self.lbl_reloj.configure(text=formato_mmss(self.reloj.restante()))
        if self.reloj.termino():
            self.reloj.pausar()
            self.btn_reloj.configure(text="Iniciar")
            self._estado("¡Tiempo! Definí el resultado.", "orange")
            return
        if self.reloj.corriendo:
            self._tick_id = self.after(200, self._tick)

    def reiniciar_reloj(self):
        self.reloj.reiniciar()
        if self._tick_id:
            self.after_cancel(self._tick_id)
            self._tick_id = None
        self.btn_reloj.configure(text="Iniciar")
        self.lbl_reloj.configure(text=formato_mmss(self.reloj.duracion))

    def resolver(self, cual):
        p = self.pelea_activa
        if not p:
            return
        ganador = {"a": p.gallo_a, "b": p.gallo_b, "empate": None}[cual]
        p.resolver(ganador)
        self.reloj.pausar()
        if self._tick_id:
            self.after_cancel(self._tick_id)
            self._tick_id = None
        self._refrescar_lista()
        self._limpiar_activa()
        self._estado("Resultado registrado.", "lightgreen")

    def _limpiar_activa(self):
        self.pelea_activa = None
        self.lbl_activa.configure(text="Seleccioná una pelea de la lista")
        for b in (self.btn_gana_a, self.btn_gana_b, self.btn_empate,
                  self.btn_reloj, self.btn_reset):
            b.configure(state="disabled")
        self.btn_gana_a.configure(text="Gana A")
        self.btn_gana_b.configure(text="Gana B")
        self.lbl_reloj.configure(text=formato_mmss(self.DURACION))

    def _refrescar_lista(self):
        for w in self.lista.winfo_children():
            w.destroy()
        for p in self.peleas_ronda:
            fila = ctk.CTkFrame(self.lista)
            fila.pack(fill="x", padx=5, pady=3)
            texto = (f"{p.gallo_a.nombre} ({p.gallo_a.peso}oz)   vs   "
                     f"{p.gallo_b.nombre} ({p.gallo_b.peso}oz)")
            ctk.CTkLabel(fila, text=texto, anchor="w", width=340).pack(side="left", padx=10, pady=5)
            if p.finalizada:
                res = "Empate" if p.ganador is None else f"Ganó {p.ganador.nombre}"
                ctk.CTkLabel(fila, text=res, text_color="lightgreen").pack(side="right", padx=10)
            else:
                ctk.CTkButton(fila, text="Pelear", width=80,
                              command=lambda pel=p: self.seleccionar(pel)).pack(side="right", padx=10)


class PantallaTabla(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(15, 5))
        ctk.CTkLabel(header, text="Tabla de posiciones",
                     font=ctk.CTkFont(size=22, weight="bold")).pack(side="left")
        ctk.CTkButton(header, text="Refrescar", width=110,
                      command=self.refrescar).pack(side="right")

        self.cabecera = ctk.CTkFrame(self)
        self.cabecera.pack(fill="x", padx=20, pady=(10, 0))
        cols = [("#", 40), ("Gallo", 130), ("Frente", 180), ("Equipo", 130),
                ("PJ", 50), ("G", 50), ("E", 50), ("P", 50), ("Pts", 60)]
        for texto, ancho in cols:
            ctk.CTkLabel(self.cabecera, text=texto, width=ancho,
                         font=ctk.CTkFont(weight="bold")).pack(side="left", padx=2)

        self.lista = ctk.CTkScrollableFrame(self)
        self.lista.pack(fill="both", expand=True, padx=20, pady=10)

        self.lbl_vacio = ctk.CTkLabel(
            self, text="Aún no hay gallos. Radicá frentes y jugá rondas.",
            text_color="gray")

    def refrescar(self):
        for w in self.lista.winfo_children():
            w.destroy()
        self.lbl_vacio.pack_forget()

        gallos = self.app.torneo.todos_los_gallos() if self.app.torneo else []
        if not gallos:
            self.lbl_vacio.pack(pady=20)
            return

        anchos = [40, 130, 180, 130, 50, 50, 50, 50, 60]
        for i, g in enumerate(tabla_posiciones(gallos), start=1):
            fila = ctk.CTkFrame(self.lista, fg_color=("gray85", "gray20") if i % 2 else "transparent")
            fila.pack(fill="x", pady=1)
            valores = [str(i), g.nombre, g.frente, g.equipo,
                       str(g.peleas), str(g.ganadas), str(g.empatadas),
                       str(g.perdidas), str(g.puntos)]
            for texto, ancho in zip(valores, anchos):
                ctk.CTkLabel(fila, text=texto, width=ancho).pack(side="left", padx=2, pady=4)


# ============================================================
#  APP PRINCIPAL
# ============================================================

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Torneo de Gallos")
        self.geometry("1050x680")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("green")

        self.torneo = None
        self.db_path = "torneo.db"
        self._cargar_si_existe()   # se crea desde la pantalla de radicación

        # ---- Navegación ----
        self.nav = ctk.CTkFrame(self, width=180)
        self.nav.pack(side="left", fill="y", padx=5, pady=5)
        self.nav.pack_propagate(False)
        ctk.CTkLabel(self.nav, text="🐓 TORNEO",
                     font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(20, 30))
        for texto, comando in [("Radicación", self.mostrar_radicacion),
                               ("Peleas", self.mostrar_peleas),
                               ("Tabla", self.mostrar_tabla)]:
            ctk.CTkButton(self.nav, text=texto, command=comando, height=40).pack(fill="x", padx=10, pady=5)

        # Botón guardar abajo
        ctk.CTkButton(self.nav, text="💾 Guardar", height=40,
                      command=self.guardar_ahora,
                      fg_color="gray30", hover_color="gray40").pack(side="bottom", fill="x", padx=10, pady=10)

        # Auto-guardar al cerrar la ventana
        self.protocol("WM_DELETE_WINDOW", self.al_cerrar)

        # ---- Contenido ----
        self.contenido = ctk.CTkFrame(self)
        self.contenido.pack(side="right", fill="both", expand=True, padx=5, pady=5)

        self.pantallas = {
            "radicacion": PantallaRadicacion(self.contenido, self),
            "peleas":     PantallaPeleas(self.contenido, self),
            "tabla":      PantallaTabla(self.contenido, self),
        }
        self.pantalla_actual = None
        self.mostrar_radicacion()

        # Si se cargó un torneo desde la base, sincronizar la pantalla
        if self.torneo:
            pr = self.pantallas["radicacion"]
            pr.entry_gpf.insert(0, str(self.torneo.gallos_por_frente))
            pr.entry_gpf.configure(state="disabled")
            pr.btn_crear.configure(state="disabled")
            pr.lbl_torneo.configure(
                text=f"Torneo activo · {self.torneo.gallos_por_frente} gallos por frente",
                text_color="white")
            pr._set_form_enabled(True)
            pr._refrescar_frentes()
            pr._actualizar_contador()

    def _mostrar(self, nombre):
        if self.pantalla_actual:
            self.pantalla_actual.pack_forget()
        self.pantalla_actual = self.pantallas[nombre]
        self.pantalla_actual.pack(fill="both", expand=True)
        if nombre == "tabla":
            self.pantalla_actual.refrescar()

    def mostrar_radicacion(self): self._mostrar("radicacion")
    def mostrar_peleas(self):     self._mostrar("peleas")
    def mostrar_tabla(self):      self._mostrar("tabla")

    # -------- persistencia --------
    def _cargar_si_existe(self):
        if not os.path.exists(self.db_path):
            return
        try:
            con = conectar(self.db_path)
            # leemos gallos_por_frente del 1er frente (todos lo cumplen)
            row = con.execute("SELECT COUNT(*) FROM gallos g "
                              "JOIN frentes f ON g.frente=f.radicado "
                              "GROUP BY f.radicado LIMIT 1").fetchone()
            gpf = row[0] if row else 1
            self.torneo = cargar(con, gpf)
            con.close()
        except Exception as e:
            print("No se pudo cargar:", e)

    def guardar_ahora(self):
        if not self.torneo:
            return False
        try:
            con = conectar(self.db_path)
            guardar(con, self.torneo)
            con.close()
            return True
        except Exception as e:
            print("Error guardando:", e)
            return False

    def al_cerrar(self):
        self.guardar_ahora()
        self.destroy()


if __name__ == "__main__":
    app = App()
    app.mainloop()