"""Exportar resultados a PDF (formato como el reporte del cliente)."""
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from datetime import date
from .tabla import clasificacion_cuerdas, clasificacion

def exportar_resultados(torneo, ruta, titulo="RESULTADO DEL TORNEO"):
    doc = SimpleDocTemplate(ruta, pagesize=letter,
                            topMargin=1.5*cm, bottomMargin=1.5*cm)
    estilos = getSampleStyleSheet()
    centrado = ParagraphStyle("c", parent=estilos["Title"], alignment=1)
    elems = [Paragraph(titulo, centrado),
             Paragraph(date.today().strftime("%A %d de %B de %Y").capitalize(),
                       ParagraphStyle("f", parent=estilos["Normal"], alignment=1)),
             Spacer(1, 18)]

    # --- tabla por cuerda/frente ---
    datos = [["#", "CUERDA", "FRENTE", "PUNTOS", "PG", "PE", "PP", "MIN", "SEG"]]
    for i, fila in enumerate(clasificacion_cuerdas(torneo.cuerdas), 1):
        datos.append([i, fila["cuerda"], fila["frente"], fila["puntos"],
                      fila["pg"], fila["pe"], fila["pp"], fila["min"], fila["seg"]])
    t = Table(datos, repeatRows=1)
    t.setStyle(TableStyle([
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("LINEBELOW", (0,0), (-1,0), 1, colors.black),
        ("LINEBELOW", (0,1), (-1,-1), 0.4, colors.grey),
        ("ALIGN", (2,0), (-1,-1), "CENTER"),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.Color(0.95,0.95,0.95)]),
    ]))
    elems.append(t)
    doc.build(elems)
    return ruta
