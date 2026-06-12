import customtkinter as ctk
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

class PantallaRadicacion(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        ctk.CTkLabel(self, text="RADICACIÓN DE FRENTES",
        font=ctk.CTkFont(size=24, weight="bold")).pack(pady=40)
        
        ctk.CTkLabel(self, text="Formulario Inscripción", font=ctk.CTkFont(size=14)).pack()
        
class PantallaPeleas(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        ctk.CTkLabel(self, text="PELEAS", font= ctk.CTkFont(size=24, weight="bold")).pack(pady=40)
        
        ctk.CTkLabel(self, text= "Peleas con reloj", font=ctk.CTkFont(size=14)).pack()
        
class PantallaTabla(ctk.CTkFrame):
    """Pantalla con la tabla de posiciones."""
    def __init__(self, parent):
        super().__init__(parent)
 
        ctk.CTkLabel(
            self, text="TABLA DE POSICIONES",
            font=ctk.CTkFont(size=24, weight="bold")
        ).pack(pady=40)
 
        ctk.CTkLabel(
            self, text="(Aquí irá la tabla con puntos)",
            font=ctk.CTkFont(size=14)
        ).pack()
         
class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Torneo de Gallos")
        self.geometry("1000x650")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("green")
        
        self.nav= ctk.CTkFrame(self, width=180)
        self.nav.pack(side="left", fill= "y", padx=5, pady=5)
        self.nav.pack_propagate(False)
        
        ctk.CTkLabel(self.nav, text= "🐓 TORNEO", font= ctk.CTkFont(size=18, weight="bold")).pack(pady=(20,30))
        
        botones=[
            ("Radicación", self.mostrar_radicacion),
            ("Peleas", self.mostrar_peleas), 
            ("Tabla", self.mostrar_tabla),
        ]
        for texto, comando in botones:
            ctk.CTkButton(
                self.nav, text= texto, command=comando, height=40, font=ctk.CTkFont(size=14)
            ).pack(fill="x", padx=10, pady=5)
        self.contenido=ctk.CTkFrame(self)
        self.contenido.pack(side="right", fill= "both", expand=True, padx=5, pady=5)
        
        self.pantallas={
            "radicacion": PantallaRadicacion(self.contenido),
            "peleas": PantallaPeleas(self.contenido),
            "tabla": PantallaTabla(self.contenido),
        }
        
        self.pantalla_actual=None
        self.mostrar_radicacion()
        
    
    def _mostrar(self, nombre):
        """Oculta la pantalla actual y muestra la nueva."""
        if self.pantalla_actual:
            self.pantalla_actual.pack_forget()   # ocultar la vieja
        self.pantalla_actual = self.pantallas[nombre]
        self.pantalla_actual.pack(fill="both", expand=True)

    def mostrar_radicacion(self):
        self._mostrar("radicacion")

    def mostrar_peleas(self):
        self._mostrar("peleas")

    def mostrar_tabla(self):
        self._mostrar("tabla")


if __name__ == "__main__":
    app=App()
    
    app.mainloop()
