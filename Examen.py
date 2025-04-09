import tkinter as tk
from tkinter import ttk, messagebox
import json
from datetime import datetime
import os
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from docx import Document
from docx.shared import Inches
from PIL import Image
from io import BytesIO
from tkinter import filedialog
from PIL import Image, ImageTk
from reportlab.platypus import Image as RLImage
from PIL import Image as PILImage
from docx import Document
from docx.shared import Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH

class GoogleFormsClone:
    def __init__(self, root):
        self.root = root
        self.root.title("Google Forms Clone")
        self.root.geometry("1000x800")

        # Variables para almacenar datos del formulario
        self.form_data = {
            "title": "",
            "description": "",
            "questions": []
        }

        self.current_question = {
            "type": "text",
            "question": "",
            "options": [],
            "required": False
        }
        
        # Configurar expansión de la ventana
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        self.editing_index = None
        self.create_gui()

    def create_gui(self):
        # Frame principal con scrollbar y márgenes
        main_container = ttk.Frame(self.root, padding="20")  # Padding general
        main_container.grid(row=0, column=0, sticky="nsew")
        main_container.grid_columnconfigure(0, weight=1)

        canvas = tk.Canvas(main_container)
        scrollbar = ttk.Scrollbar(main_container, orient="vertical", command=canvas.yview)
        self.main_frame = ttk.Frame(canvas, padding="20")  # Padding interno

        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        canvas_frame = canvas.create_window((0, 0), window=self.main_frame, anchor="nw")

        # Hacer que el contenido se expanda al ancho del canvas
        def configure_frame(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.itemconfig(canvas_frame, width=canvas.winfo_width())

        canvas.bind('<Configure>', configure_frame)
        self.main_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        # Configurar columnas para centrado y expansión
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(1, weight=1)

        # Título y descripción con más espacio
        title_frame = ttk.Frame(self.main_frame)
        title_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 20))
        title_frame.grid_columnconfigure(0, weight=1)

        ttk.Label(title_frame, text="Título del formulario:", font=('Arial', 12)).grid(
            row=0, column=0, sticky=tk.W, pady=(0, 5), padx=(20, 0))
        self.title_entry = ttk.Entry(title_frame, width=70, font=('Arial', 11))
        self.title_entry.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 10))

        ttk.Label(title_frame, text="Descripción:", font=('Arial', 12)).grid(
            row=2, column=0, sticky=tk.W, pady=(10, 5), padx=(20, 0))
        self.description_entry = ttk.Entry(title_frame, width=70, font=('Arial', 11))
        self.description_entry.grid(row=3, column=0, sticky="ew", padx=20, pady=(0, 10))

        # Frame para preguntas existentes
        self.questions_frame = ttk.LabelFrame(self.main_frame, text="Preguntas", padding="20")
        self.questions_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=20, pady=20)
        self.questions_frame.grid_columnconfigure(0, weight=1)

        # Frame para nueva pregunta
        self.question_frame = ttk.LabelFrame(self.main_frame, text="Nueva Pregunta", padding="20")
        self.question_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=20, pady=20)
        self.question_frame.grid_columnconfigure(1, weight=1)

        # Tipo de pregunta con más espacio
        ttk.Label(self.question_frame, text="Tipo:", font=('Arial', 11)).grid(
            row=0, column=0, sticky=tk.W, pady=(0, 10))
        self.question_type = ttk.Combobox(self.question_frame,
                                        values=["Texto", "Párrafo", "Opción múltiple", "Casillas", "Imágenes múltiples"],
                                        state="readonly", width=30, font=('Arial', 11))
        self.question_type.set("Texto")
        self.question_type.grid(row=0, column=1, sticky="ew", pady=(0, 10), padx=(10, 0))
        self.question_type.bind('<<ComboboxSelected>>', self.on_type_change)

        # Pregunta con más espacio
        ttk.Label(self.question_frame, text="Pregunta:", font=('Arial', 11)).grid(
            row=1, column=0, sticky=tk.W, pady=10)
        self.question_entry = ttk.Entry(self.question_frame, width=50, font=('Arial', 11))
        self.question_entry.grid(row=1, column=1, sticky="ew", pady=10, padx=(10, 0))

        # Frame para opciones
        self.options_frame = ttk.Frame(self.question_frame)
        self.options_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=10)
        self.options_frame.grid_columnconfigure(0, weight=1)

        # Obligatorio con más espacio
        self.required_var = tk.BooleanVar()
        self.required_check = ttk.Checkbutton(self.question_frame, text="Obligatorio",
                                            variable=self.required_var, padding=(20, 10))
        self.required_check.grid(row=3, column=0, sticky=tk.W, pady=10)

        # Botones con mejor espaciado
        button_frame = ttk.Frame(self.question_frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=(20, 0))

        self.add_button = ttk.Button(button_frame, text="Agregar Pregunta",
                                   command=self.add_question, padding=(20, 5))
        self.add_button.grid(row=0, column=0, padx=10)

        self.update_button = ttk.Button(button_frame, text="Actualizar Pregunta",
                                      command=self.update_question, state='disabled', padding=(20, 5))
        self.update_button.grid(row=0, column=1, padx=10)

        # Botones de formulario con mejor espaciado
        form_button_frame = ttk.Frame(self.main_frame)
        form_button_frame.grid(row=3, column=0, columnspan=2, pady=30)

        buttons = [
            ("Guardar Formulario", self.save_form),
            ("Cargar Formulario", self.load_form),
            ("Exportar a PDF", self.export_to_pdf),
            ("Exportar a Word", self.export_to_word)
        ]

        for i, (text, command) in enumerate(buttons):
            ttk.Button(form_button_frame, text=text, command=command, padding=(20, 5)).grid(
                row=0, column=i, padx=10)

    def load_images(self):
        filenames = filedialog.askopenfilenames(
            title="Seleccionar imágenes",
            filetypes=[("Imágenes", "*.png *.jpg *.jpeg *.gif *.bmp")]
        )
        return list(filenames) if filenames else []
    
    def update_questions_display(self):
        # Limpiar el frame de preguntas
        for widget in self.questions_frame.winfo_children():
            widget.destroy()

        # Mostrar cada pregunta
        for i, question in enumerate(self.form_data["questions"]):
            question_frame = ttk.Frame(self.questions_frame)
            question_frame.grid(row=i, column=0, sticky="ew", pady=(0, 10), padx=20)
            question_frame.grid_columnconfigure(0, weight=1)

            # Número y texto de la pregunta
            question_text = f"{i+1}. {question['question']}"
            if question['required']:
                question_text += " *"
            ttk.Label(question_frame, text=question_text, font=('Arial', 11)).grid(
                row=0, column=0, sticky=tk.W)

            # Mostrar miniaturas de imágenes si es tipo "Imágenes múltiples"
            if question['type'] == "Imágenes múltiples" and 'image_paths' in question:
                image_frame = ttk.Frame(question_frame)
                image_frame.grid(row=1, column=0, sticky="w", padx=40, pady=(5, 0))

                for j, path in enumerate(question['image_paths']):
                    if path and os.path.exists(path):
                        try:
                            with Image.open(path) as img:
                                img.thumbnail((50, 50))  # Tamaño más pequeño para las miniaturas
                                photo = ImageTk.PhotoImage(img)
                                label = ttk.Label(image_frame, image=photo)
                                label.image = photo  # Mantener referencia
                                label.grid(row=0, column=j, padx=5)
                                ttk.Label(image_frame, text=f"{j+1}").grid(row=1, column=j)
                        except Exception:
                            pass

            # Mostrar opciones si las hay (para otros tipos de preguntas)
            elif question['options']:
                options_text = "\n".join(f"  • {opt}" for opt in question['options'])
                ttk.Label(question_frame, text=options_text, font=('Arial', 10)).grid(
                    row=1, column=0, sticky=tk.W, padx=40, pady=(5, 0))

            # Botones de editar y eliminar
            button_frame = ttk.Frame(question_frame)
            button_frame.grid(row=0, column=1, padx=(0, 20))

            ttk.Button(button_frame, text="Editar",
                    command=lambda q=question, idx=i: self.edit_question(idx),
                    padding=(10, 2)).grid(row=0, column=0, padx=5)
            ttk.Button(button_frame, text="Eliminar",
                    command=lambda idx=i: self.delete_question(idx),
                    padding=(10, 2)).grid(row=0, column=1, padx=5)

    def edit_question(self, index):
        question = self.form_data["questions"][index]
        self.editing_index = index

        # Llenar los campos con los datos de la pregunta
        self.question_type.set(question["type"])
        self.question_entry.delete(0, tk.END)
        self.question_entry.insert(0, question["question"])
        self.required_var.set(question["required"])

        # Actualizar opciones si existen
        self.on_type_change()
        if question["type"] in ["Opción múltiple", "Casillas"] and hasattr(self, 'options_text'):
            self.options_text.delete("1.0", tk.END)
            self.options_text.insert("1.0", "\n".join(question["options"]))

        # Cambiar estado de los botones
        self.add_button.config(state='disabled')
        self.update_button.config(state='normal')

    def update_question(self):
        if self.editing_index is None:
            return

        question_text = self.question_entry.get()
        if not question_text:
            messagebox.showwarning("Advertencia", "Por favor ingresa una pregunta")
            return

        question_type = self.question_type.get()
        options = []
        if question_type in ["Opción múltiple", "Casillas"] and hasattr(self, 'options_text'):
            options = self.options_text.get("1.0", tk.END).strip().split('\n')
            options = [opt for opt in options if opt.strip()]

        # Actualizar la pregunta
        self.form_data["questions"][self.editing_index] = {
            "type": question_type,
            "question": question_text,
            "options": options,
            "required": self.required_var.get()
        }

        # Restablecer el estado de edición
        self.editing_index = None
        self.add_button.config(state='normal')
        self.update_button.config(state='disabled')
        self.clear_question_fields()
        self.update_questions_display()

    def delete_question(self, index):
        if messagebox.askyesno("Confirmar eliminación",
                             "¿Estás seguro de que quieres eliminar esta pregunta?"):
            del self.form_data["questions"][index]
            self.update_questions_display()

    def add_question(self):
        question_text = self.question_entry.get()
        if not question_text:
            messagebox.showwarning("Advertencia", "Por favor ingresa una pregunta")
            return

        question_type = self.question_type.get()
        options = []
        image_paths = []

        if question_type in ["Opción múltiple", "Casillas"] and hasattr(self, 'options_text'):
            options = self.options_text.get("1.0", tk.END).strip().split('\n')
            options = [opt for opt in options if opt.strip()]
        elif question_type == "Imágenes múltiples":
            try:
                if hasattr(self, 'image_references') and hasattr(self, '_image_paths'):
                    image_paths = self._image_paths  # Usar las rutas guardadas
                num_images = len(image_paths) if image_paths else int(self.num_images.get())
                options = [f"Imagen {i+1}" for i in range(num_images)]
            except ValueError:
                messagebox.showwarning("Advertencia", "Por favor ingresa un número válido de imágenes")
                return

        question = {
            "type": question_type,
            "question": question_text,
            "options": options,
            "image_paths": image_paths,
            "required": self.required_var.get()
        }

        self.form_data["questions"].append(question)
        self.clear_question_fields()
        self.update_questions_display()

    def export_to_pdf(self):
        if not self.form_data["questions"]:
            messagebox.showwarning("Advertencia", "No hay preguntas para exportar")
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"form_{timestamp}.pdf"

        doc = SimpleDocTemplate(filename, pagesize=letter)
        styles = getSampleStyleSheet()
        elements = []

        # Título
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Title'],
            fontSize=16,
            spaceAfter=30
        )
        elements.append(Paragraph(self.title_entry.get(), title_style))

        # Descripción
        if self.description_entry.get():
            elements.append(Paragraph(self.description_entry.get(), styles['Normal']))
            elements.append(Spacer(1, 20))

        for i, question in enumerate(self.form_data["questions"], 1):
            question_text = f"{i}. {question['question']}"
            if question['required']:
                question_text += " *"
            elements.append(Paragraph(question_text, styles['Heading2']))
            elements.append(Spacer(1, 10))

            if question['type'] == "Imágenes múltiples":
                image_data = []
                current_row = []

                for j, path in enumerate(question.get('image_paths', []), 1):
                    try:
                        if path and os.path.exists(path):
                            # Abrir y procesar la imagen usando PIL
                            img = PILImage.open(path)
                            img.thumbnail((200, 200))

                            # Convertir la imagen a bytes
                            img_buffer = BytesIO()
                            img.save(img_buffer, format='PNG')
                            img_buffer.seek(0)

                            # Crear celda con imagen y número
                            cell_content = [
                                [Paragraph(f"{j}.", styles['Normal'])],
                                [RLImage(img_buffer, width=150, height=150)],
                                [Paragraph("_" * 20, styles['Normal'])]
                            ]

                            cell = Table(cell_content, colWidths=[200])
                            cell.setStyle(TableStyle([
                                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                            ]))
                            current_row.append(cell)
                        else:
                            cell = Table([[Paragraph(f"{j}.\n[Imagen no disponible]\n{'_' * 20}", styles['Normal'])]], colWidths=[200])
                            current_row.append(cell)

                        if len(current_row) == 2 or j == len(question.get('image_paths', [])):
                            while len(current_row) < 2:
                                current_row.append(Table([['']], colWidths=[200]))
                            image_data.append(current_row)
                            current_row = []

                    except Exception as e:
                        print(f"Error procesando imagen {j}: {str(e)}")
                        import traceback
                        traceback.print_exc()
                        cell = Table([[Paragraph(f"{j}.\n[Error al cargar imagen]\n{'_' * 20}", styles['Normal'])]], colWidths=[200])
                        current_row.append(cell)

                if image_data:
                    table = Table(image_data, colWidths=[250, 250])
                    table.setStyle(TableStyle([
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                        ('PADDING', (0, 0), (-1, -1), 10),
                    ]))
                    elements.append(table)
                    elements.append(Spacer(1, 20))

            elif question['type'] in ["Opción múltiple", "Casillas"]:
                for option in question['options']:
                    bullet = "○ " if question['type'] == "Opción múltiple" else "□ "
                    elements.append(Paragraph(f"{bullet}{option}", styles['Normal']))
                    elements.append(Spacer(1, 5))
            else:
                if question['type'] == "Texto":
                    t = Table([["_" * 80]], colWidths=[450])
                    t.setStyle(TableStyle([
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                    ]))
                    elements.append(t)
                else:  # Párrafo
                    for _ in range(6):
                        t = Table([["_" * 80]], colWidths=[450])
                        t.setStyle(TableStyle([
                            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                        ]))
                        elements.append(t)
                        elements.append(Spacer(1, 10))

            elements.append(Spacer(1, 20))

        try:
            doc.build(elements)
            messagebox.showinfo("Éxito", f"Formulario exportado como {filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Error al exportar a PDF: {str(e)}")
            import traceback
            traceback.print_exc()

    def export_to_word(self):
        if not self.form_data["questions"]:
            messagebox.showwarning("Advertencia", "No hay preguntas para exportar")
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"form_{timestamp}.docx"

        doc = Document()

        # Configurar el documento para páginas A4
        section = doc.sections[0]
        section.page_height = Inches(11.69)
        section.page_width = Inches(8.27)
        section.left_margin = Inches(1)
        section.right_margin = Inches(1)
        section.top_margin = Inches(1)
        section.bottom_margin = Inches(1)

        # Título
        doc.add_heading(self.title_entry.get(), 0)

        # Descripción
        if self.description_entry.get():
            doc.add_paragraph(self.description_entry.get())
            doc.add_paragraph()

        def resize_image(image_path, max_size=(800, 800)):
            """Redimensiona la imagen si es necesario"""
            try:
                with PILImage.open(image_path) as img:
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                    width, height = img.size
                    if width > max_size[0] or height > max_size[1]:
                        ratio = min(max_size[0]/width, max_size[1]/height)
                        new_size = (int(width * ratio), int(height * ratio))
                        img = img.resize(new_size, PILImage.LANCZOS)
                    temp_path = f"temp_{os.path.basename(image_path)}"
                    img.save(temp_path, 'JPEG', quality=85)
                    return temp_path
            except Exception as e:
                print(f"Error al redimensionar imagen: {str(e)}")
                return image_path

        temp_files = []

        for i, question in enumerate(self.form_data["questions"], 1):
            question_text = f"{i}. {question['question']}"
            if question['required']:
                question_text += " *"

            if question['type'] == "Imágenes múltiples":
                # Agregar salto de página antes de la pregunta con imágenes
                doc.add_page_break()

            doc.add_paragraph(question_text, style='Heading 2')

            if question['type'] == "Imágenes múltiples":
                image_paths = question.get('image_paths', [])
                if not image_paths:
                    continue

                num_rows = (len(image_paths) + 1) // 2
                table = doc.add_table(rows=num_rows, cols=2)
                table.style = 'Table Grid'
                table.autofit = False

                for col in table.columns:
                    for cell in col.cells:
                        cell.width = Inches(3)

                for idx, path in enumerate(image_paths):
                    if not path or not os.path.exists(path):
                        continue

                    row = idx // 2
                    col = idx % 2

                    try:
                        temp_path = resize_image(path)
                        if temp_path != path:
                            temp_files.append(temp_path)

                        cell = table.cell(row, col)
                        cell.text = ""
                        paragraph = cell.paragraphs[0]

                        number_run = paragraph.add_run(f"{idx + 1}.")
                        number_run.bold = True
                        paragraph.add_run("\n")

                        try:
                            run = paragraph.add_run()
                            run.add_picture(temp_path, width=Inches(2.5))
                            paragraph.add_run("\n" + "_" * 20)
                        except Exception as img_error:
                            print(f"Error al agregar imagen {idx + 1}: {str(img_error)}")
                            paragraph.add_run("[Error al cargar imagen]\n" + "_" * 20)

                        paragraph.alignment = 1

                    except Exception as e:
                        print(f"Error procesando imagen {idx + 1}: {str(e)}")
                        if cell:
                            cell.text = f"{idx + 1}.\n[Error]\n{'_' * 20}"

                doc.add_paragraph()  # Espacio después de la tabla

            elif question['type'] in ["Opción múltiple", "Casillas"]:
                for option in question['options']:
                    bullet = "○ " if question['type'] == "Opción múltiple" else "□ "
                    doc.add_paragraph(bullet + option)
            else:
                if question['type'] == "Texto":
                    doc.add_paragraph("_" * 80)
                else:  # Párrafo
                    for _ in range(6):
                        doc.add_paragraph("_" * 80)

            doc.add_paragraph()

        try:
            doc.save(filename)
            messagebox.showinfo("Éxito", f"Formulario exportado como {filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Error al exportar a Word: {str(e)}")
        finally:
            for temp_file in temp_files:
                try:
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                except Exception as e:
                    print(f"Error al eliminar archivo temporal {temp_file}: {str(e)}")
        
    def on_type_change(self, event=None):
        question_type = self.question_type.get()

        # Limpiar frame de opciones
        for widget in self.options_frame.winfo_children():
            widget.destroy()

        if question_type in ["Opción múltiple", "Casillas"]:
            # [Código existente para opciones múltiples y casillas]
            pass
        elif question_type == "Imágenes múltiples":
            ttk.Label(self.options_frame, text="Número de imágenes:").grid(row=0, column=0, sticky=tk.W)
            self.num_images = ttk.Spinbox(self.options_frame, from_=1, to=10, width=5)
            self.num_images.set("4")
            self.num_images.grid(row=0, column=1, sticky=tk.W, padx=5)

            # Agregar botón para cargar imágenes
            ttk.Button(self.options_frame, text="Cargar imágenes",
                    command=self.handle_image_load).grid(row=0, column=2, padx=10)

            # Frame para mostrar las imágenes seleccionadas
            self.images_preview_frame = ttk.Frame(self.options_frame)
            self.images_preview_frame.grid(row=1, column=0, columnspan=3, pady=10)

    def handle_image_load(self):
        image_paths = self.load_images()
        if not image_paths:
            return

        # Guardar las rutas de las imágenes
        self._image_paths = [os.path.abspath(path) for path in image_paths]

        # Limpiar el frame de vista previa
        for widget in self.images_preview_frame.winfo_children():
            widget.destroy()

        # Mostrar miniaturas de las imágenes seleccionadas
        self.image_references = []  # Mantener referencia a las imágenes
        for i, path in enumerate(image_paths):
            try:
                with Image.open(path) as img:
                    img.thumbnail((100, 100))
                    photo = ImageTk.PhotoImage(img)
                    self.image_references.append(photo)

                    # Mostrar miniatura con número
                    frame = ttk.Frame(self.images_preview_frame)
                    frame.grid(row=i//3, column=i%3, padx=5, pady=5)

                    label = ttk.Label(frame, image=photo)
                    label.grid(row=0, column=0)

                    ttk.Label(frame, text=f"{i+1}").grid(row=1, column=0)

            except Exception as e:
                messagebox.showerror("Error", f"Error al cargar la imagen {path}: {str(e)}")

        # Actualizar el número de imágenes en el Spinbox
        self.num_images.set(str(len(image_paths)))

    def add_question(self):
        question_text = self.question_entry.get()
        if not question_text:
            messagebox.showwarning("Advertencia", "Por favor ingresa una pregunta")
            return

        question_type = self.question_type.get()
        options = []
        image_paths = []

        if question_type in ["Opción múltiple", "Casillas"] and hasattr(self, 'options_text'):
            options = self.options_text.get("1.0", tk.END).strip().split('\n')
            options = [opt for opt in options if opt.strip()]
        elif question_type == "Imágenes múltiples":
            if hasattr(self, '_image_paths'):
                image_paths = self._image_paths
                options = [f"Imagen {i+1}" for i in range(len(image_paths))]
            else:
                messagebox.showwarning("Advertencia", "Por favor carga las imágenes primero")
                return

        question = {
            "type": question_type,
            "question": question_text,
            "options": options,
            "image_paths": image_paths,
            "required": self.required_var.get()
        }

        if self.editing_index is not None:
            self.form_data["questions"][self.editing_index] = question
            self.editing_index = None
            self.add_button.config(state='normal')
            self.update_button.config(state='disabled')
        else:
            self.form_data["questions"].append(question)

        self.clear_question_fields()
        self.update_questions_display()

    def clear_question_fields(self):
        self.question_entry.delete(0, tk.END)
        self.question_type.set("Texto")
        self.required_var.set(False)
        self.on_type_change()

    def save_form(self):
        self.form_data["title"] = self.title_entry.get()
        self.form_data["description"] = self.description_entry.get()

        # Convertir todas las rutas de imágenes a rutas absolutas
        for question in self.form_data["questions"]:
            if question["type"] == "Imágenes múltiples":
                question["image_paths"] = [os.path.abspath(path) for path in question.get("image_paths", [])]

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"form_{timestamp}.json"

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.form_data, f, ensure_ascii=False, indent=2)

        messagebox.showinfo("Éxito", f"Formulario guardado como {filename}")

    def load_form(self):
        filename = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json")],
            title="Selecciona un formulario para cargar"
        )

        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    self.form_data = json.load(f)

                # Verificar y actualizar rutas de imágenes
                for question in self.form_data["questions"]:
                    if question["type"] == "Imágenes múltiples":
                        valid_paths = []
                        for path in question.get("image_paths", []):
                            if os.path.exists(path):
                                valid_paths.append(path)
                            else:
                                print(f"Advertencia: No se encontró la imagen {path}")
                        question["image_paths"] = valid_paths

                self.title_entry.delete(0, tk.END)
                self.title_entry.insert(0, self.form_data.get("title", ""))

                self.description_entry.delete(0, tk.END)
                self.description_entry.insert(0, self.form_data.get("description", ""))

                self.update_questions_display()
                messagebox.showinfo("Éxito", "Formulario cargado correctamente")
            except Exception as e:
                messagebox.showerror("Error", f"Error al cargar el formulario: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = GoogleFormsClone(root)
    root.mainloop()