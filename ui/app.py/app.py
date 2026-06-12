import customtkinter as ctk
import sys, os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "src"))

from torneo.torneo import Torneo
from torneo.torneo import Torneo


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
        self.entry_equipo = ctk.CTkEntry(form, placeholder_text="Equipo / zona (ej. GIRARDOT)")
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
        for w in (self.entry_nombre, self.entry_equipo, self.entry_gallo,
                  self.entry_peso, self.btn_agregar):
            w.configure(state=estado)

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
        try:
            self.app.torneo.radicar_frente(nombre, equipo, self.gallos_pendientes)
        except ValueError as e:
            self._estado(str(e), "tomato")
            return
        self.gallos_pendientes = []
        self.entry_nombre.delete(0, "end")
        self.entry_equipo.delete(0, "end")
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
#  PANTALLAS PLACEHOLDER (las llenamos después)
# ============================================================

class PantallaPeleas(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        ctk.CTkLabel(self, text="PELEAS", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=40)
        ctk.CTkLabel(self, text="(Aquí irán las peleas con el reloj)").pack()


class PantallaTabla(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        ctk.CTkLabel(self, text="TABLA DE POSICIONES", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=40)
        ctk.CTkLabel(self, text="(Aquí irá la tabla con puntos)").pack()


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

        self.torneo = None   # se crea desde la pantalla de radicación

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

    def _mostrar(self, nombre):
        if self.pantalla_actual:
            self.pantalla_actual.pack_forget()
        self.pantalla_actual = self.pantallas[nombre]
        self.pantalla_actual.pack(fill="both", expand=True)

    def mostrar_radicacion(self): self._mostrar("radicacion")
    def mostrar_peleas(self):     self._mostrar("peleas")
    def mostrar_tabla(self):      self._mostrar("tabla")


if __name__ == "__main__":
    app = App()
    app.mainloop()