import customtkinter as ctk
from tkinter import messagebox
from config import (
    # Constantes de fuente
    FONT_SIZE_TITLE,
    FONT_SIZE_SUBTITLE,
    FONT_SIZE_NORMAL,
    FONT_SIZE_SMALL,
    FONT_SIZE_BUTTON,
    # Constantes de padding
    PADDING_LARGE,
    PADDING_MEDIUM,
    PADDING_SMALL,
    PADDING_TINY,
    # Constantes de altura
    BUTTON_HEIGHT_SMALL,
    INPUT_HEIGHT,
    # Función de escalado
    escalar
)

class VentanaGestionUsuarios:
    def __init__(self, parent, db):
        self.db = db
        self.parent = parent
        self.usuario_seleccionado_id = None

        self.frame = ctk.CTkFrame(parent, fg_color="#001a33")
        self.frame.pack(fill="both", expand=True)

        self.crear_interfaz()
        self.cargar_usuarios()

    def crear_interfaz(self):
        # Configuración de grid principal
        self.frame.grid_rowconfigure(1, weight=1)
        self.frame.grid_columnconfigure(0, weight=1)

        # Encabezado
        header = ctk.CTkFrame(self.frame, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=PADDING_MEDIUM, pady=(PADDING_MEDIUM, PADDING_SMALL))

        titulo = ctk.CTkLabel(
            header,
            text="👥 Gestión de Usuarios",
            font=ctk.CTkFont(size=FONT_SIZE_TITLE, weight="bold"),
            text_color="white"
        )
        titulo.pack(anchor="w")

        subtitulo = ctk.CTkLabel(
            header,
            text="Administre cuentas, roles y estado de acceso al sistema.",
            font=ctk.CTkFont(size=FONT_SIZE_NORMAL),
            text_color="#c4dafa",
        )
        subtitulo.pack(anchor="w", pady=(escalar(2), 0))

        # ✅ CORRECCIÓN: ELIMINAR COMPLETAMENTE LA LÍNEA SEPARADORA PROBLEMÁTICA
        # La línea causaba superposición con el título/subtítulo
        # No es necesaria ya que hay suficiente espacio visual

        # Panel central (lista + formulario)
        panel_central = ctk.CTkFrame(self.frame, fg_color="#001a33")
        panel_central.grid(row=1, column=0, sticky="nsew", padx=PADDING_MEDIUM, pady=(PADDING_SMALL, PADDING_MEDIUM))

        panel_central.grid_columnconfigure(0, weight=1, uniform="col")
        panel_central.grid_columnconfigure(1, weight=1, uniform="col")
        panel_central.grid_rowconfigure(0, weight=1)

        # ==================== LADO IZQUIERDO: LISTA ====================

        frame_lista = ctk.CTkFrame(panel_central, fg_color="#003d66")
        frame_lista.grid(row=0, column=0, sticky="nsew", padx=(0, PADDING_SMALL), pady=PADDING_SMALL)

        encabezado_lista = ctk.CTkLabel(
            frame_lista,
            text="📋 Usuarios registrados",
            font=ctk.CTkFont(size=FONT_SIZE_SUBTITLE, weight="bold"),
            text_color="white"
        )
        encabezado_lista.pack(anchor="w", padx=PADDING_SMALL, pady=(PADDING_SMALL, 0))

        descripcion_lista = ctk.CTkLabel(
            frame_lista,
            text="Seleccione un usuario para editar sus datos.",
            font=ctk.CTkFont(size=FONT_SIZE_SMALL),
            text_color="#c4dafa",
        )
        descripcion_lista.pack(anchor="w", padx=PADDING_SMALL, pady=(0, PADDING_SMALL))

        self.scroll_usuarios = ctk.CTkScrollableFrame(frame_lista, fg_color="#001a33")
        self.scroll_usuarios.pack(fill="both", expand=True, padx=PADDING_SMALL, pady=(PADDING_SMALL, PADDING_SMALL))

        # ==================== LADO DERECHO: FORMULARIO ====================

        frame_form = ctk.CTkFrame(panel_central, fg_color="#003d66")
        frame_form.grid(row=0, column=1, sticky="nsew", padx=(PADDING_SMALL, 0), pady=PADDING_SMALL)

        frame_form.grid_columnconfigure(0, weight=0)
        frame_form.grid_columnconfigure(1, weight=1)

        # Título formulario
        ctk.CTkLabel(
            frame_form,
            text="✏️ Datos del usuario",
            font=ctk.CTkFont(size=FONT_SIZE_SUBTITLE, weight="bold"),
            text_color="white"
        ).grid(row=0, column=0, columnspan=2, pady=(PADDING_MEDIUM, 0), padx=PADDING_MEDIUM, sticky="w")

        ctk.CTkLabel(
            frame_form,
            text="Complete la información y guarde para crear o actualizar.",
            font=ctk.CTkFont(size=FONT_SIZE_SMALL),
            text_color="#c4dafa",
        ).grid(row=1, column=0, columnspan=2, pady=(0, PADDING_SMALL), padx=PADDING_MEDIUM, sticky="w")

        # Pequeña línea separadora en el formulario
        sep_form = ctk.CTkFrame(frame_form, fg_color="#005187", height=escalar(1))
        sep_form.grid(row=2, column=0, columnspan=2, sticky="ew", padx=PADDING_MEDIUM, pady=(PADDING_SMALL, PADDING_MEDIUM))

        row = 3

        # Usuario
        ctk.CTkLabel(
            frame_form, 
            text="Usuario:", 
            text_color="white",
            font=ctk.CTkFont(size=FONT_SIZE_SMALL)
        ).grid(row=row, column=0, sticky="w", padx=PADDING_MEDIUM, pady=PADDING_TINY)
        
        self.entry_username = ctk.CTkEntry(
            frame_form,
            placeholder_text="usuario123",
            fg_color="#001a33",
            text_color="white",
            placeholder_text_color="#84b6f4",
            height=INPUT_HEIGHT,
            font=ctk.CTkFont(size=FONT_SIZE_SMALL)
        )
        self.entry_username.grid(row=row, column=1, sticky="ew", padx=PADDING_MEDIUM, pady=PADDING_TINY)
        row += 1

        # Nombre
        ctk.CTkLabel(
            frame_form, 
            text="Nombre completo:", 
            text_color="white",
            font=ctk.CTkFont(size=FONT_SIZE_SMALL)
        ).grid(row=row, column=0, sticky="w", padx=PADDING_MEDIUM, pady=PADDING_TINY)
        
        self.entry_nombre = ctk.CTkEntry(
            frame_form,
            placeholder_text="Nombre Apellido",
            fg_color="#001a33",
            text_color="white",
            placeholder_text_color="#84b6f4",
            height=INPUT_HEIGHT,
            font=ctk.CTkFont(size=FONT_SIZE_SMALL)
        )
        self.entry_nombre.grid(row=row, column=1, sticky="ew", padx=PADDING_MEDIUM, pady=PADDING_TINY)
        row += 1

        # Rol (admin / usuario)
        ctk.CTkLabel(
            frame_form, 
            text="Rol:", 
            text_color="white",
            font=ctk.CTkFont(size=FONT_SIZE_SMALL)
        ).grid(row=row, column=0, sticky="w", padx=PADDING_MEDIUM, pady=PADDING_TINY)
        
        self.combo_rol = ctk.CTkComboBox(
            frame_form,
            values=["admin", "usuario"],
            state="readonly",
            fg_color="#001a33",
            button_color="#003d66",
            text_color="white",
            dropdown_fg_color="#001a33",
            dropdown_hover_color="#2d5f8d",
            height=INPUT_HEIGHT,
            font=ctk.CTkFont(size=FONT_SIZE_SMALL)
        )
        self.combo_rol.set("usuario")
        self.combo_rol.grid(row=row, column=1, sticky="ew", padx=PADDING_MEDIUM, pady=PADDING_TINY)
        row += 1

        # Activo
        ctk.CTkLabel(
            frame_form, 
            text="Estado:", 
            text_color="white",
            font=ctk.CTkFont(size=FONT_SIZE_SMALL)
        ).grid(row=row, column=0, sticky="w", padx=PADDING_MEDIUM, pady=PADDING_TINY)
        
        self.switch_activo = ctk.CTkSwitch(
            frame_form,
            text="Usuario activo",
            onvalue=1,
            offvalue=0,
            fg_color="#001a33",
            button_color="#003d66",
            progress_color="#005187",
            text_color="white",
            font=ctk.CTkFont(size=FONT_SIZE_SMALL)
        )
        self.switch_activo.select()
        self.switch_activo.grid(row=row, column=1, sticky="w", padx=PADDING_MEDIUM, pady=PADDING_TINY)
        row += 1

        # Contraseña
        ctk.CTkLabel(
            frame_form, 
            text="Contraseña:", 
            text_color="white",
            font=ctk.CTkFont(size=FONT_SIZE_SMALL)
        ).grid(row=row, column=0, sticky="w", padx=PADDING_MEDIUM, pady=PADDING_TINY)
        
        self.entry_password = ctk.CTkEntry(
            frame_form,
            placeholder_text="Mínimo 4 caracteres",
            show="*",
            fg_color="#001a33",
            text_color="white",
            placeholder_text_color="#84b6f4",
            height=INPUT_HEIGHT,
            font=ctk.CTkFont(size=FONT_SIZE_SMALL)
        )
        self.entry_password.grid(row=row, column=1, sticky="ew", padx=PADDING_MEDIUM, pady=PADDING_TINY)
        row += 1

        # Confirmar contraseña
        ctk.CTkLabel(
            frame_form, 
            text="Confirmar contraseña:", 
            text_color="white",
            font=ctk.CTkFont(size=FONT_SIZE_SMALL)
        ).grid(row=row, column=0, sticky="w", padx=PADDING_MEDIUM, pady=PADDING_TINY)
        
        self.entry_password_confirm = ctk.CTkEntry(
            frame_form,
            placeholder_text="Repita la contraseña",
            show="*",
            fg_color="#001a33",
            text_color="white",
            placeholder_text_color="#84b6f4",
            height=INPUT_HEIGHT,
            font=ctk.CTkFont(size=FONT_SIZE_SMALL)
        )
        self.entry_password_confirm.grid(row=row, column=1, sticky="ew", padx=PADDING_MEDIUM, pady=PADDING_TINY)
        row += 1

        # Nota sobre contraseña
        ctk.CTkLabel(
            frame_form,
            text="ℹ️ Al crear: contraseña es obligatoria.\n"
                 "   Al editar: deje vacío para mantener la actual.\n"
                 "   Los nombres de usuario no distinguen mayúsculas/minúsculas.",
            font=ctk.CTkFont(size=FONT_SIZE_SMALL - 1),
            text_color="#c4dafa",
            justify="left",
        ).grid(row=row, column=0, columnspan=2, padx=PADDING_MEDIUM, pady=(0, PADDING_MEDIUM), sticky="w")
        row += 1

        # Botones
        frame_botones = ctk.CTkFrame(frame_form, fg_color="transparent")
        frame_botones.grid(row=row, column=0, columnspan=2, pady=(PADDING_SMALL, PADDING_LARGE), padx=PADDING_MEDIUM, sticky="ew")

        frame_botones.grid_columnconfigure(0, weight=1, uniform="btn")
        frame_botones.grid_columnconfigure(1, weight=1, uniform="btn")
        frame_botones.grid_columnconfigure(2, weight=1, uniform="btn")

        btn_nuevo = ctk.CTkButton(
            frame_botones,
            text="➕ Nuevo",
            fg_color="#005187",
            hover_color="#2d5f8d",
            command=self.nuevo_usuario,
            height=BUTTON_HEIGHT_SMALL,
            font=ctk.CTkFont(size=FONT_SIZE_BUTTON, weight="bold")
        )
        btn_nuevo.grid(row=0, column=0, padx=PADDING_TINY, sticky="ew")

        btn_guardar = ctk.CTkButton(
            frame_botones,
            text="💾 Guardar",
            fg_color="#2d5f8d",
            hover_color="#005187",
            command=self.guardar_usuario,
            height=BUTTON_HEIGHT_SMALL,
            font=ctk.CTkFont(size=FONT_SIZE_BUTTON, weight="bold")
        )
        btn_guardar.grid(row=0, column=1, padx=PADDING_TINY, sticky="ew")

        btn_eliminar = ctk.CTkButton(
            frame_botones,
            text="🗑️ Eliminar",
            fg_color="#c0392b",
            hover_color="#e74c3c",
            command=self.eliminar_usuario,
            height=BUTTON_HEIGHT_SMALL,
            font=ctk.CTkFont(size=FONT_SIZE_BUTTON, weight="bold"),
            border_width=0
        )
        btn_eliminar.grid(row=0, column=2, padx=PADDING_TINY, sticky="ew")

    # ==================== LÓGICA ====================

    def cargar_usuarios(self):
        """Llena la lista de usuarios (muestra rol y estado)."""
        for widget in self.scroll_usuarios.winfo_children():
            widget.destroy()

        usuarios = self.db.obtener_todos_usuarios()

        if not usuarios:
            ctk.CTkLabel(
                self.scroll_usuarios,
                text="No hay usuarios registrados.",
                font=ctk.CTkFont(size=FONT_SIZE_NORMAL),
                text_color="#c4dafa",
            ).pack(pady=PADDING_MEDIUM)
            return

        for user in usuarios:
            user_id, username, nombre_completo, rol, activo, creado_en, ultimo_login = user

            # Primera línea: usuario (rol)
            linea_superior = f"{username}    {rol.upper() if rol else 'USUARIO'}"
            # Segunda línea: nombre completo (si existe)
            linea_inferior = nombre_completo if nombre_completo else ""

            # Estado
            if activo == 1:
                estado = "ACTIVO"
                estado_icono = "✅"
            else:
                estado = "INACTIVO"
                estado_icono = "❌"

            texto = f"{estado_icono} {linea_superior}\n   {linea_inferior}   [{estado}]"

            btn = ctk.CTkButton(
                self.scroll_usuarios,
                text=texto,
                anchor="w",
                command=lambda u=user: self.seleccionar_usuario(u),
                height=escalar(52),
                fg_color="#003d66",
                hover_color="#2d5f8d",
                text_color="white",
                font=ctk.CTkFont(size=FONT_SIZE_SMALL)
            )
            btn.pack(fill="x", padx=PADDING_TINY, pady=PADDING_TINY)

    def seleccionar_usuario(self, user_data):
        """Rellena el formulario con los datos del usuario seleccionado."""
        user_id, username, nombre_completo, rol, activo, creado_en, ultimo_login = user_data
        self.usuario_seleccionado_id = user_id

        self.entry_username.delete(0, "end")
        self.entry_username.insert(0, username)

        self.entry_nombre.delete(0, "end")
        if nombre_completo:
            self.entry_nombre.insert(0, nombre_completo)

        self.combo_rol.set(rol if rol else "usuario")

        if activo == 1:
            self.switch_activo.select()
        else:
            self.switch_activo.deselect()

        # Limpiar campos de contraseña
        self.entry_password.delete(0, "end")
        self.entry_password_confirm.delete(0, "end")

    def nuevo_usuario(self):
        """Limpia el formulario para registrar un nuevo usuario (rol usuario por defecto)."""
        self.usuario_seleccionado_id = None
        self.entry_username.delete(0, "end")
        self.entry_nombre.delete(0, "end")
        self.combo_rol.set("usuario")
        self.switch_activo.select()
        self.entry_password.delete(0, "end")
        self.entry_password_confirm.delete(0, "end")

    def guardar_usuario(self):
        """Crea o actualiza un usuario con validaciones completas."""
        username = self.entry_username.get().strip()
        nombre = self.entry_nombre.get().strip()
        rol = self.combo_rol.get().strip()
        activo = bool(self.switch_activo.get())
        password = self.entry_password.get().strip()
        password_confirm = self.entry_password_confirm.get().strip()

        # ===== VALIDACIONES =====
        
        # 1. Usuario obligatorio
        if not username:
            messagebox.showwarning("Advertencia", "El campo 'Usuario' es obligatorio.")
            self.entry_username.focus_set()
            return

        # 2. Usuario no debe tener espacios
        if " " in username:
            messagebox.showwarning("Advertencia", "El nombre de usuario no puede contener espacios.")
            self.entry_username.focus_set()
            return

        # 3. Usuario mínimo 3 caracteres
        if len(username) < 3:
            messagebox.showwarning("Advertencia", "El nombre de usuario debe tener al menos 3 caracteres.")
            self.entry_username.focus_set()
            return

        # 4. Validar rol
        if rol not in ("admin", "usuario"):
            messagebox.showwarning("Advertencia", "Rol inválido. Debe ser 'admin' o 'usuario'.")
            return

        # 5. Verificar duplicados (case-insensitive)
        if self.usuario_seleccionado_id is None:
            # Modo CREAR: verificar que no exista (case-insensitive)
            if self.db.verificar_usuario_existe_case_insensitive(username):
                messagebox.showerror(
                    "Error",
                    f"Ya existe un usuario con el nombre '{username}' (sin distinguir mayúsculas/minúsculas).\n\n"
                    "Por favor elija otro nombre."
                )
                self.entry_username.focus_set()
                return
        else:
            # Modo EDITAR: verificar que no exista otro usuario con ese nombre
            if self.db.verificar_usuario_existe_case_insensitive(username, excluir_id=self.usuario_seleccionado_id):
                messagebox.showerror(
                    "Error",
                    f"Ya existe otro usuario con el nombre '{username}' (sin distinguir mayúsculas/minúsculas).\n\n"
                    "Por favor elija otro nombre."
                )
                self.entry_username.focus_set()
                return

        # 6. Validación de contraseña según modo (crear o editar)
        if self.usuario_seleccionado_id is None:
            # MODO CREAR: contraseña obligatoria
            if not password:
                messagebox.showwarning(
                    "Advertencia",
                    "Debe indicar una contraseña para el nuevo usuario.",
                )
                self.entry_password.focus_set()
                return
            
            # Contraseña mínimo 4 caracteres
            if len(password) < 4:
                messagebox.showwarning(
                    "Advertencia",
                    "La contraseña debe tener al menos 4 caracteres.",
                )
                self.entry_password.focus_set()
                return
            
            # Confirmar contraseña
            if password != password_confirm:
                messagebox.showwarning(
                    "Advertencia",
                    "Las contraseñas no coinciden. Por favor verifique.",
                )
                self.entry_password_confirm.focus_set()
                return
        else:
            # MODO EDITAR: contraseña opcional
            if password:  # Si se ingresó contraseña
                # Validar longitud mínima
                if len(password) < 4:
                    messagebox.showwarning(
                        "Advertencia",
                        "La contraseña debe tener al menos 4 caracteres.",
                    )
                    self.entry_password.focus_set()
                    return
                
                # Confirmar contraseña
                if password != password_confirm:
                    messagebox.showwarning(
                        "Advertencia",
                        "Las contraseñas no coinciden. Por favor verifique.",
                    )
                    self.entry_password_confirm.focus_set()
                    return

        # ===== GUARDAR EN BASE DE DATOS =====
        
        try:
            if self.usuario_seleccionado_id is None:
                # === CREAR NUEVO USUARIO ===
                user_id, resultado = self.db.crear_usuario(username, password, nombre, rol, activo)
                messagebox.showinfo("✅ Éxito", f"Usuario '{username}' creado correctamente con contraseña encriptada.")
            else:
                # === ACTUALIZAR USUARIO EXISTENTE ===
                
                # Actualizar datos básicos
                self.db.actualizar_usuario(
                    self.usuario_seleccionado_id,
                    username,
                    nombre,
                    rol,
                    activo,
                )
                
                # Cambiar contraseña solo si se ingresó una nueva
                if password:
                    self.db.cambiar_password_usuario(self.usuario_seleccionado_id, password)
                    messagebox.showinfo("✅ Éxito", f"Usuario '{username}' actualizado correctamente.\nNueva contraseña encriptada guardada.")
                else:
                    messagebox.showinfo("✅ Éxito", f"Usuario '{username}' actualizado correctamente.")

            # Recargar lista y limpiar formulario
            self.cargar_usuarios()
            self.nuevo_usuario()

        except Exception as e:
            messagebox.showerror("❌ Error", f"No se pudo guardar el usuario:\n{str(e)}")

    def eliminar_usuario(self):
        """Elimina el usuario seleccionado con validaciones."""
        if self.usuario_seleccionado_id is None:
            messagebox.showwarning("⚠️ Advertencia", "Seleccione un usuario para eliminar.")
            return

        # Obtener información del usuario
        try:
            usuario = self.db.obtener_usuario_por_id(self.usuario_seleccionado_id)
            if not usuario:
                messagebox.showerror("❌ Error", "No se pudo obtener la información del usuario.")
                return
            
            username = usuario[1]
            rol = usuario[3]
            
            # Verificar que no sea el último admin
            if rol == "admin":
                self.db.cursor.execute("SELECT COUNT(*) FROM usuarios WHERE rol = 'admin' AND activo = 1")
                total_admins = self.db.cursor.fetchone()[0]
                
                if total_admins <= 1:
                    messagebox.showwarning(
                        "⚠️ No se puede eliminar",
                        "No se puede eliminar el último administrador activo del sistema.\n\n"
                        "Debe haber al menos un administrador activo."
                    )
                    return
            
            # Confirmar eliminación
            resp = messagebox.askyesno(
                "⚠️ Confirmar eliminación",
                f"¿Está seguro que desea eliminar el usuario '{username}'?\n\n"
                "Esta acción no se puede deshacer.",
            )
            
            if not resp:
                return

            self.db.eliminar_usuario(self.usuario_seleccionado_id)
            messagebox.showinfo("✅ Éxito", f"Usuario '{username}' eliminado correctamente.")
            
            self.cargar_usuarios()
            self.nuevo_usuario()
            
        except Exception as e:
            messagebox.showerror("❌ Error", f"No se pudo eliminar el usuario:\n{str(e)}")