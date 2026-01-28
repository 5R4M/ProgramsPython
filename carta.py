from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

# Crear documento
doc = Document()

# Configurar márgenes
sections = doc.sections
for section in sections:
    section.top_margin = Inches(0.5)
    section.bottom_margin = Inches(0.5)
    section.left_margin = Inches(0.75)
    section.right_margin = Inches(0.75)

# Título y encabezado
title = doc.add_paragraph()
title.alignment = WD_ALIGN_PARAGRAPH.LEFT
run = title.add_run("Industrias Borcelle")
run.font.size = Pt(16)
run.font.bold = True
run.font.color.rgb = RGBColor(41, 98, 255)

# Título principal
main_title = doc.add_paragraph()
run = main_title.add_run("Cotización de Servicios")
run.font.size = Pt(28)
run.font.bold = True
run.font.color.rgb = RGBColor(25, 50, 120)

doc.add_paragraph()

# Crear tabla para datos del cliente y emisor
info_table = doc.add_table(rows=1, cols=2)
info_table.autofit = False
info_table.allow_autofit = False

# Datos del Cliente
cell_cliente = info_table.rows[0].cells[0]
p = cell_cliente.paragraphs[0]
run = p.add_run("Datos del Cliente\n")
run.font.bold = True
run.font.size = Pt(11)
p.add_run("Mateo López\n")
p.add_run("Calle Cualquiera 123, Cualquier Lugar\n")
p.add_run("(55) 1234 5678\n")
p.add_run("hola@sitioincreible.com")

# Datos del Emisor
cell_emisor = info_table.rows[0].cells[1]
p = cell_emisor.paragraphs[0]
run = p.add_run("Datos del Emisor\n")
run.font.bold = True
run.font.size = Pt(11)
p.add_run("Industrias Borcelle\n")
p.add_run("Calle Cualquiera 123, Cualquier Lugar\n")
p.add_run("(55) 1234 5678\n")
p.add_run("hola@sitioincreible.com")

doc.add_paragraph()

# Tabla de productos
products_table = doc.add_table(rows=5, cols=4)
products_table.style = 'Light Grid Accent 1'

# Encabezados
headers = ['Producto', 'Cantidad', 'Precio', 'Subtotal']
header_cells = products_table.rows[0].cells
for i, header in enumerate(headers):
    cell = header_cells[i]
    cell.text = header
    for paragraph in cell.paragraphs:
        for run in paragraph.runs:
            run.font.bold = True
            run.font.color.rgb = RGBColor(255, 255, 255)
    # Color de fondo azul
    shading = cell._element.get_or_add_tcPr()
    shading_elm = OxmlElement('w:shd')
    shading_elm.set(qn('w:fill'), '4472C4')
    shading.append(shading_elm)

# Datos de productos
products_data = [
    ['Descripción', '3', '$120', '$360'],
    ['Descripción', '2', '$100', '$200'],
    ['Descripción', '1', '$300', '$300'],
    ['Descripción', '1', '$200', '$200']
]

for i, product in enumerate(products_data, start=1):
    row_cells = products_table.rows[i].cells
    for j, value in enumerate(product):
        row_cells[j].text = value

doc.add_paragraph()

# Totales
totals = doc.add_paragraph()
totals.alignment = WD_ALIGN_PARAGRAPH.RIGHT
totals.add_run("Subtotal\t\t$1,060\n")
totals.add_run("Impuestos (16%)\t\t$1,060\n")
run = totals.add_run("TOTAL\t\t$1,060")
run.font.bold = True
run.font.size = Pt(14)

doc.add_paragraph()

# Condiciones
conditions = doc.add_paragraph()
run = conditions.add_run("CONDICIONES\n")
run.font.bold = True
run.font.size = Pt(12)
conditions.add_run("Forma de pago: Transferencia bancaria / Depósito\n")
conditions.add_run("Vigencia de la cotización: 7 días naturales\n")
conditions.add_run("Tiempo estimado de entrega: 5 días hábiles a partir del pago\n")
conditions.add_run("Incluye: Número de revisiones, formatos de entrega, garantía")

doc.add_paragraph()

# Información de contacto
contact = doc.add_paragraph()
contact.add_run("● hola@sitioincreible.com\n")
contact.add_run("● www.sitioincreible.com\n")
contact.add_run("● (55) 1234 5678\n")
contact.add_run("● Calle Cualquiera 123, Cualquier Lugar")

# Guardar
doc.save('Cotizacion_Servicios.docx')
print("Documento creado exitosamente")