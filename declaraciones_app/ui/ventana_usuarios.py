# ventana_usuarios.py
import customtkinter as ctk
from tkinter import messagebox
from config import COLOR_PRIMARY, COLOR_SUCCESS, COLOR_WARNING


class VentanaGestionUsuarios:
    def __init__(self, parent, db):
        self.db = db
        self.parent = parent
        self.usuario_seleccionado_id = None

        self.frame = ctk.CTkFrame(parent)
        self.frame.pack(fill="both", expand=True)

        self.crear_interfaz()
        self.cargar_usuarios()

    def crear_interfaz(self):
        # Configuración de grid principal
        self.frame.grid_rowconfigure(1, weight=1)
        self.frame.grid_columnconfigure(0, weight=1)

        # Encabezado
        header = ctk.CTkFrame(self.frame, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))

        titulo = ctk.CTkLabel(
            header,
            text="👥 Gestión de Usuarios",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        titulo.pack(anchor="w")

        subtitulo = ctk.CTkLabel(
            header,
            text="Administre cuentas, roles y estado de acceso al sistema.",
            font=ctk.CTkFont(size=12),
            text_color="gray70",
        )
        subtitulo.pack(anchor="w", pady=(2, 0))

        # Línea separadora
        linea = ctk.CTkFrame(self.frame, fg_color="gray25", height=1)
        linea.grid(row=0, column=0, sticky="ew", padx=10, pady=(0, 5))

        # Panel central (lista + formulario)
        panel_central = ctk.CTkFrame(self.frame)
        panel_central.grid(row=1, column=0, sticky="nsew", padx=10, pady=(5, 10))

        panel_central.grid_columnconfigure(0, weight=1, uniform="col")
        panel_central.grid_columnconfigure(1, weight=1, uniform="col")
        panel_central.grid_rowconfigure(0, weight=1)

        # ==================== LADO IZQUIERDO: LISTA ====================

        frame_lista = ctk.CTkFrame(panel_central)
        frame_lista.grid(row=0, column=0, sticky="nsew", padx=(0, 5), pady=5)

        encabezado_lista = ctk.CTkLabel(
            frame_lista,
            text="Usuarios registrados",
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        encabezado_lista.pack(anchor="w", padx=8, pady=(8, 0))

        descripcion_lista = ctk.CTkLabel(
            frame_lista,
            text="Seleccione un usuario para editar sus datos.",
            font=ctk.CTkFont(size=11),
            text_color="gray70",
        )
        descripcion_lista.pack(anchor="w", padx=8, pady=(0, 5))

        self.scroll_usuarios = ctk.CTkScrollableFrame(frame_lista)
        self.scroll_usuarios.pack(fill="both", expand=True, padx=8, pady=(5, 8))

        # ==================== LADO DERECHO: FORMULARIO ====================

        frame_form = ctk.CTkFrame(panel_central)
        frame_form.grid(row=0, column=1, sticky="nsew", padx=(5, 0), pady=5)

        frame_form.grid_columnconfigure(0, weight=0)
        frame_form.grid_columnconfigure(1, weight=1)

        # Título formulario
        ctk.CTkLabel(
            frame_form,
            text="✏️ Datos del usuario",
            font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=0, column=0, columnspan=2, pady=(10, 0), padx=10, sticky="w")

        ctk.CTkLabel(
            frame_form,
            text="Complete la información y guarde para crear o actualizar.",
            font=ctk.CTkFont(size=11),
            text_color="gray70",
        ).grid(row=1, column=0, columnspan=2, pady=(0, 5), padx=10, sticky="w")

        # Pequeña línea separadora en el formulario
        sep_form = ctk.CTkFrame(frame_form, fg_color="gray25", height=1)
        sep_form.grid(row=2, column=0, columnspan=2, sticky="ew", padx=10, pady=(5, 10))

        row = 3

        # Usuario
        ctk.CTkLabel(frame_form, text="Usuario:").grid(
            row=row, column=0, sticky="w", padx=10, pady=4
        )
        self.entry_username = ctk.CTkEntry(
            frame_form,
            placeholder_text="usuario123",
        )
        self.entry_username.grid(row=row, column=1, sticky="ew", padx=10, pady=4)
        row += 1

        # Nombre
        ctk.CTkLabel(frame_form, text="Nombre completo:").grid(
            row=row, column=0, sticky="w", padx=10, pady=4
        )
        self.entry_nombre = ctk.CTkEntry(
            frame_form,
            placeholder_text="Nombre Apellido",
        )
        self.entry_nombre.grid(row=row, column=1, sticky="ew", padx=10, pady=4)
        row += 1

        # Rol (admin / usuario)
        ctk.CTkLabel(frame_form, text="Rol:").grid(
            row=row, column=0, sticky="w", padx=10, pady=4
        )
        self.combo_rol = ctk.CTkComboBox(
            frame_form,
            values=["admin", "usuario"],
            state="readonly",
        )
        self.combo_rol.set("usuario")
        self.combo_rol.grid(row=row, column=1, sticky="ew", padx=10, pady=4)
        row += 1

        # Activo
        ctk.CTkLabel(frame_form, text="Estado:").grid(
            row=row, column=0, sticky="w", padx=10, pady=4
        )
        self.switch_activo = ctk.CTkSwitch(
            frame_form,
            text="Usuario activo",
            onvalue=1,
            offvalue=0,
        )
        self.switch_activo.select()
        self.switch_activo.grid(row=row, column=1, sticky="w", padx=10, pady=4)
        row += 1

        # Contraseña
        ctk.CTkLabel(frame_form, text="Contraseña:").grid(
            row=row, column=0, sticky="w", padx=10, pady=4
        )
        self.entry_password = ctk.CTkEntry(
            frame_form,
            placeholder_text="(nueva o cambio de contraseña)",
            show="*",
        )
        self.entry_password.grid(row=row, column=1, sticky="ew", padx=10, pady=4)
        row += 1

        # Nota sobre contraseña
        ctk.CTkLabel(
            frame_form,
            text="Deje la contraseña vacía para mantener la actual\n(al actualizar un usuario).",
            font=ctk.CTkFont(size=10),
            text_color="gray70",
            justify="left",
        ).grid(row=row, column=0, columnspan=2, padx=10, pady=(0, 10), sticky="w")
        row += 1

        # Botones
        frame_botones = ctk.CTkFrame(frame_form, fg_color="transparent")
        frame_botones.grid(row=row, column=0, columnspan=2, pady=(5, 15), padx=10, sticky="ew")

        frame_botones.grid_columnconfigure(0, weight=1, uniform="btn")
        frame_botones.grid_columnconfigure(1, weight=1, uniform="btn")
        frame_botones.grid_columnconfigure(2, weight=1, uniform="btn")

        btn_nuevo = ctk.CTkButton(
            frame_botones,
            text="➕ Nuevo",
            fg_color=COLOR_PRIMARY,
            command=self.nuevo_usuario,
        )
        btn_nuevo.grid(row=0, column=0, padx=4, sticky="ew")

        btn_guardar = ctk.CTkButton(
            frame_botones,
            text="💾 Guardar",
            fg_color=COLOR_SUCCESS,
            command=self.guardar_usuario,
        )
        btn_guardar.grid(row=0, column=1, padx=4, sticky="ew")

        btn_eliminar = ctk.CTkButton(
            frame_botones,
            text="🗑️ Eliminar",
            fg_color=COLOR_WARNING,
            hover_color="#e67e22",
            command=self.eliminar_usuario,
        )
        btn_eliminar.grid(row=0, column=2, padx=4, sticky="ew")

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
                font=ctk.CTkFont(size=12),
                text_color="gray70",
            ).pack(pady=10)
            return

        for user in usuarios:
            user_id, username, nombre_completo, rol, activo, creado_en, ultimo_login = user

            # Primera línea: usuario (rol)
            linea_superior = f"{username}  •  {rol.upper() if rol else 'USUARIO'}"
            # Segunda línea: nombre completo (si existe)
            linea_inferior = nombre_completo if nombre_completo else ""

            # Estado
            if activo == 1:
                estado = "ACTIVO"
                estado_icono = "✅"
            else:
                estado = "INACTIVO"
                estado_icono = "🚫"

            texto = f"{estado_icono} {linea_superior}\n   {linea_inferior}   [{estado}]"

            btn = ctk.CTkButton(
                self.scroll_usuarios,
                text=texto,
                anchor="w",
                command=lambda u=user: self.seleccionar_usuario(u),
                height=52,
                fg_color="gray23",
                hover_color="gray30",
                text_color="white",
            )
            btn.pack(fill="x", padx=4, pady=3)

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

        self.entry_password.delete(0, "end")

    def nuevo_usuario(self):
        """Limpia el formulario para registrar un nuevo usuario (rol usuario por defecto)."""
        self.usuario_seleccionado_id = None
        self.entry_username.delete(0, "end")
        self.entry_nombre.delete(0, "end")
        self.combo_rol.set("usuario")
        self.switch_activo.select()
        self.entry_password.delete(0, "end")

    def guardar_usuario(self):
        """Crea o actualiza un usuario, guardando también el rol (admin/usuario)."""
        username = self.entry_username.get().strip()
        nombre = self.entry_nombre.get().strip()
        rol = self.combo_rol.get().strip()
        activo = bool(self.switch_activo.get())
        password = self.entry_password.get().strip()

        if not username:
            messagebox.showwarning("Advertencia", "El campo 'Usuario' es obligatorio.")
            return

        # Validar rol por si acaso
        if rol not in ("admin", "usuario"):
            messagebox.showwarning("Advertencia", "Rol inválido. Debe ser 'admin' o 'usuario'.")
            return

        try:
            if self.usuario_seleccionado_id is None:
                # Crear
                if not password:
                    messagebox.showwarning(
                        "Advertencia",
                        "Debe indicar una contraseña para el nuevo usuario.",
                    )
                    return

                self.db.crear_usuario(username, password, nombre, rol, activo)
                messagebox.showinfo("Éxito", "Usuario creado correctamente.")
            else:
                # Actualizar
                self.db.actualizar_usuario(
                    self.usuario_seleccionado_id,
                    username,
                    nombre,
                    rol,
                    activo,
                )
                if password:
                    self.db.cambiar_password_usuario(self.usuario_seleccionado_id, password)
                messagebox.showinfo("Éxito", "Usuario actualizado correctamente.")

            self.cargar_usuarios()
            self.nuevo_usuario()

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar el usuario:\n{str(e)}")

    def eliminar_usuario(self):
        """Elimina el usuario seleccionado."""
        if self.usuario_seleccionado_id is None:
            messagebox.showwarning("Advertencia", "Seleccione un usuario para eliminar.")
            return

        resp = messagebox.askyesno(
            "Confirmar eliminación",
            "¿Seguro que desea eliminar este usuario?\nEsta acción no se puede deshacer.",
        )
        if not resp:
            return

        try:
            self.db.eliminar_usuario(self.usuario_seleccionado_id)
            messagebox.showinfo("Éxito", "Usuario eliminado correctamente.")
            self.cargar_usuarios()
            self.nuevo_usuario()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo eliminar el usuario:\n{str(e)}")