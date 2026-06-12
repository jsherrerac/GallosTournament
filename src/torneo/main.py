from .models import Gallo, Pelea
from .emparejador import *

def generar_ronda(gallos, ronda):
    if ronda==1:
        return emparejar_ronda(gallos, ronda, cubrir_todos_los_frentes=True)
    return emparejar_optimo(gallos, ronda)
