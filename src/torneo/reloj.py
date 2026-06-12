import time

class Reloj:
    def __init__(self, duracion_seg):
        self.duracion = duracion_seg
        self._inicio = None
        self._acumulado = 0.0
        self.corriendo = False
    def iniciar(self):
        if not self.corriendo:
            self._inicio = time.monotonic(); self.corriendo = True
    def pausar(self):
        if self.corriendo:
            self._acumulado += time.monotonic() - self._inicio; self.corriendo = False
    def reiniciar(self):
        self._inicio = None; self._acumulado = 0.0; self.corriendo = False
    def transcurrido(self):
        t = self._acumulado
        if self.corriendo: t += time.monotonic() - self._inicio
        return t
    def restante(self):
        return max(0.0, self.duracion - self.transcurrido())
    def termino(self):
        return self.restante() <= 0

def formato_mmss(segundos):
    segundos = int(segundos)
    return f"{segundos // 60:02d}:{segundos % 60:02d}"
