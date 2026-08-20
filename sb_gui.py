# sb_gui.py
import os
import sys
import time
import shutil
import tempfile
import threading
import datetime
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import Optional, List

from sb_core import SBArchiver, CompressionMode, ArchiveManifest

def format_bytes(size: float) -> str:
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} PB"

class SmartBundleManagerApp(tk.Tk):
    def __init__(self, initial_path: Optional[str] = None):
        super().__init__()
        self.title("SmartBundle Pro (.sb) - Gestor de Archivos Comprimidos")
        self.geometry("960x640")
        self.minsize(780, 500)
        self.configure(bg="#1e1e2e")

        # Icono
        icon_p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app_icon.ico")
        if os.path.exists(icon_p):
            try:
                self.iconbitmap(icon_p)
            except Exception:
                pass

        self.current_archive_path: Optional[str] = None
        self.current_manifest: Optional[ArchiveManifest] = None
        self.current_folder: str = ""  # Carpeta virtual dentro del archivo
        self.archiver = SBArchiver(mode=CompressionMode.BALANCED)

        self._configure_theme()
        self._build_menu()
        self._build_toolbar()
        self._build_address_bar()
        self._build_explorer_view()
        self._build_status_bar()

        if initial_path and os.path.exists(initial_path):
            if initial_path.lower().endswith(".sb"):
                self.open_archive(initial_path)
            else:
                self._open_new_compression_dialog(initial_path)

    def _configure_theme(self):
        self.style = ttk.Style(self)
        self.style.theme_use("clam")

        bg_color = "#1e1e2e"
        card_bg = "#282a36"
        fg_color = "#f8f8f2"
        accent_color = "#bd93f9"
        accent_hover = "#ff79c6"
        table_select = "#44475a"

        self.style.configure(".", background=bg_color, foreground=fg_color, font=("Segoe UI", 9))
        
        # Toolbar Buttons
        self.style.configure("Tool.TButton", background="#282a36", foreground=fg_color, borderwidth=1, padding=[8, 5], font=("Segoe UI", 9, "bold"))
        self.style.map("Tool.TButton", background=[("active", accent_color), ("pressed", accent_hover)], foreground=[("active", "#1e1e2e")])

        self.style.configure("Accent.TButton", background=accent_color, foreground="#1e1e2e", borderwidth=0, padding=[10, 6], font=("Segoe UI", 9, "bold"))
        self.style.map("Accent.TButton", background=[("active", accent_hover)])

        # Treeview (Explorador)
        self.style.configure(
            "Treeview",
            background="#21222c",
            foreground="#f8f8f2",
            fieldbackground="#21222c",
            rowheight=26,
            font=("Segoe UI", 9),
            borderwidth=0
        )
        self.style.map("Treeview", background=[("selected", table_select)], foreground=[("selected", "#50fa7b")])
        self.style.configure("Treeview.Heading", background="#282a36", foreground=accent_color, font=("Segoe UI", 9, "bold"), relief="flat")
        self.style.map("Treeview.Heading", background=[("active", "#44475a")])

        self.style.configure("Horizontal.TProgressbar", troughcolor="#282a36", background=accent_color)

    def _build_menu(self):
        menubar = tk.Menu(self, bg="#282a36", fg="#f8f8f2", activebackground="#bd93f9", activeforeground="#1e1e2e", relief="flat")
        
        # Menú Archivo
        menu_file = tk.Menu(menubar, tearoff=0, bg="#282a36", fg="#f8f8f2", activebackground="#bd93f9", activeforeground="#1e1e2e")
        menu_file.add_command(label="Nuevo Archivo .sb...", command=self.cmd_new_archive, accelerator="Ctrl+N")
        menu_file.add_command(label="Abrir Archivo...", command=self.cmd_open_archive, accelerator="Ctrl+O")
        menu_file.add_separator()
        menu_file.add_command(label="Cerrar Archivo", command=self.cmd_close_archive)
        menu_file.add_separator()
        menu_file.add_command(label="Salir", command=self.quit, accelerator="Alt+F4")
        menubar.add_cascade(label="Archivo", menu=menu_file)

        # Menú Acciones
        menu_actions = tk.Menu(menubar, tearoff=0, bg="#282a36", fg="#f8f8f2", activebackground="#bd93f9", activeforeground="#1e1e2e")
        menu_actions.add_command(label="Añadir ficheros...", command=self.cmd_add_files, accelerator="Ctrl+A")
        menu_actions.add_command(label="Extraer en carpeta...", command=self.cmd_extract_all, accelerator="Ctrl+E")
        menu_actions.add_command(label="Extraer seleccionados...", command=self.cmd_extract_selected)
        menu_actions.add_command(label="Eliminar ficheros seleccionados", command=self.cmd_delete_selected, accelerator="Supr")
        menu_actions.add_separator()
        menu_actions.add_command(label="Comprobar integridad (SHA256)", command=self.cmd_test_integrity, accelerator="Ctrl+T")
        menu_actions.add_command(label="Información y Estadísticas", command=self.cmd_show_info, accelerator="Ctrl+I")
        menubar.add_cascade(label="Acciones", menu=menu_actions)

        # Menú Opciones
        menu_options = tk.Menu(menubar, tearoff=0, bg="#282a36", fg="#f8f8f2", activebackground="#bd93f9", activeforeground="#1e1e2e")
        self.var_mode = tk.StringVar(value="balanced")
        menu_options.add_radiobutton(label="Compresión Rápida (Zstd)", variable=self.var_mode, value="fast", command=self._update_mode)
        menu_options.add_radiobutton(label="Compresión Equilibrada (Heurística)", variable=self.var_mode, value="balanced", command=self._update_mode)
        menu_options.add_radiobutton(label="Compresión Ultra Extrema (SOTA)", variable=self.var_mode, value="extreme", command=self._update_mode)
        menubar.add_cascade(label="Opciones", menu=menu_options)

        # Menú Ayuda
        menu_help = tk.Menu(menubar, tearoff=0, bg="#282a36", fg="#f8f8f2", activebackground="#bd93f9", activeforeground="#1e1e2e")
        menu_help.add_command(label="Acerca de SmartBundle Pro", command=self._show_about)
        menubar.add_cascade(label="Ayuda", menu=menu_help)

        self.config(menu=menubar)

        # Atajos
        self.bind("<Control-o>", lambda e: self.cmd_open_archive())
        self.bind("<Control-n>", lambda e: self.cmd_new_archive())
        self.bind("<Control-e>", lambda e: self.cmd_extract_all())
        self.bind("<Control-t>", lambda e: self.cmd_test_integrity())
        self.bind("<Control-i>", lambda e: self.cmd_show_info())
        self.bind("<Delete>", lambda e: self.cmd_delete_selected())

    def _build_toolbar(self):
        toolbar = tk.Frame(self, bg="#282a36", padx=8, pady=6)
        toolbar.pack(fill="x", side="top")

        btn_add = ttk.Button(toolbar, text="➕ Añadir", style="Tool.TButton", command=self.cmd_add_files)
        btn_add.pack(side="left", padx=3)

        btn_extract = ttk.Button(toolbar, text="📦 Extraer en", style="Tool.TButton", command=self.cmd_extract_all)
        btn_extract.pack(side="left", padx=3)

        btn_test = ttk.Button(toolbar, text="🔍 Comprobar", style="Tool.TButton", command=self.cmd_test_integrity)
        btn_test.pack(side="left", padx=3)

        btn_view = ttk.Button(toolbar, text="👁️ Ver", style="Tool.TButton", command=self.cmd_view_file)
        btn_view.pack(side="left", padx=3)

        btn_del = ttk.Button(toolbar, text="🗑️ Eliminar", style="Tool.TButton", command=self.cmd_delete_selected)
        btn_del.pack(side="left", padx=3)

        btn_info = ttk.Button(toolbar, text="ℹ️ Información", style="Tool.TButton", command=self.cmd_show_info)
        btn_info.pack(side="left", padx=3)

        sep = tk.Frame(toolbar, width=2, bg="#44475a", height=24)
        sep.pack(side="left", padx=8)

        btn_open = ttk.Button(toolbar, text="📂 Abrir", style="Tool.TButton", command=self.cmd_open_archive)
        btn_open.pack(side="left", padx=3)

        btn_new_zip = ttk.Button(toolbar, text="⚡ Comprimir Nuevo", style="Accent.TButton", command=self.cmd_new_archive)
        btn_new_zip.pack(side="right", padx=3)

    def _build_address_bar(self):
        addr_frame = tk.Frame(self, bg="#1e1e2e", padx=8, pady=4)
        addr_frame.pack(fill="x", side="top")

        btn_up = ttk.Button(addr_frame, text="⬆️ Subir", width=8, style="Tool.TButton", command=self._navigate_up)
        btn_up.pack(side="left", padx=(0, 6))

        self.var_address = tk.StringVar(value="Ningún archivo abierto")
        self.entry_addr = tk.Entry(addr_frame, textvariable=self.var_address, state="readonly", bg="#282a36", fg="#8be9fd", readonlybackground="#282a36", font=("Segoe UI", 9), relief="flat")
        self.entry_addr.pack(fill="x", expand=True, ipady=4)

    def _build_explorer_view(self):
        container = tk.Frame(self, bg="#1e1e2e", padx=8, pady=4)
        container.pack(fill="both", expand=True)

        columns = ("name", "size", "packed_size", "ratio", "type", "modified", "crc")
        self.tree = ttk.Treeview(container, columns=columns, show="headings", selectmode="extended")

        self.tree.heading("name", text="Nombre", anchor="w")
        self.tree.heading("size", text="Tamaño Original", anchor="e")
        self.tree.heading("packed_size", text="Comprimido Est.", anchor="e")
        self.tree.heading("ratio", text="Ratio", anchor="e")
        self.tree.heading("type", text="Tipo", anchor="w")
        self.tree.heading("modified", text="Modificado", anchor="center")
        self.tree.heading("crc", text="CRC32", anchor="center")

        self.tree.column("name", width=280, anchor="w")
        self.tree.column("size", width=110, anchor="e")
        self.tree.column("packed_size", width=110, anchor="e")
        self.tree.column("ratio", width=80, anchor="e")
        self.tree.column("type", width=100, anchor="w")
        self.tree.column("modified", width=140, anchor="center")
        self.tree.column("crc", width=90, anchor="center")

        sb_y = ttk.Scrollbar(container, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb_y.set)

        self.tree.pack(side="left", fill="both", expand=True)
        sb_y.pack(side="right", fill="y")

        # Eventos
        self.tree.bind("<Double-1>", self._on_double_click)
        self.tree.bind("<Button-3>", self._show_context_menu)

        # Context Menu en tabla
        self.tree_menu = tk.Menu(self, tearoff=0, bg="#282a36", fg="#f8f8f2", activebackground="#bd93f9", activeforeground="#1e1e2e")
        self.tree_menu.add_command(label="Ver / Abrir", command=self.cmd_view_file)
        self.tree_menu.add_command(label="Extraer seleccionados...", command=self.cmd_extract_selected)
        self.tree_menu.add_separator()
        self.tree_menu.add_command(label="Añadir archivos...", command=self.cmd_add_files)
        self.tree_menu.add_command(label="Eliminar", command=self.cmd_delete_selected)

    def _build_status_bar(self):
        status_frame = tk.Frame(self, bg="#282a36", padx=8, pady=4)
        status_frame.pack(fill="x", side="bottom")

        self.lbl_status = tk.Label(status_frame, text="Listo. Abre o crea un archivo .sb para comenzar.", bg="#282a36", fg="#8be9fd", font=("Segoe UI", 9))
        self.lbl_status.pack(side="left")

        self.progress = ttk.Progressbar(status_frame, mode="determinate", length=180, style="Horizontal.TProgressbar")
        self.progress.pack(side="right", padx=(8, 0))

        self.lbl_stats = tk.Label(status_frame, text="0 archivos | 0 B", bg="#282a36", fg="#f8f8f2", font=("Segoe UI", 9))
        self.lbl_stats.pack(side="right", padx=8)

    def _update_mode(self):
        m = self.var_mode.get()
        if m == "fast": self.archiver.mode = CompressionMode.FAST
        elif m == "extreme": self.archiver.mode = CompressionMode.EXTREME
        else: self.archiver.mode = CompressionMode.BALANCED

    def open_archive(self, path: str):
        if not os.path.exists(path):
            messagebox.showerror("Error", f"El archivo no existe:\n{path}")
            return

        try:
            self.lbl_status.config(text=f"Cargando {os.path.basename(path)}...")
            self.update_idletasks()
            manifest = self.archiver.inspect(path)
            self.current_archive_path = path
            self.current_manifest = manifest
            self.current_folder = ""
            self._render_explorer()
            
            comp_size = os.path.getsize(path)
            orig_size = manifest.total_uncompressed_size
            ratio = (1 - (comp_size / orig_size)) * 100 if orig_size > 0 else 0
            
            self.var_address.set(f"{path}")
            self.lbl_stats.config(text=f"{len(manifest.files)} archivos | Original: {format_bytes(orig_size)} | Comprimido: {format_bytes(comp_size)} (Ahorro {ratio:.1f}%)")
            self.lbl_status.config(text="Archivo cargado correctamente.")
        except Exception as e:
            messagebox.showerror("Error al abrir", f"No se pudo abrir el archivo .sb:\n{str(e)}")
            self.lbl_status.config(text="Error al abrir archivo.")

    def _render_explorer(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        if not self.current_manifest:
            return

        # Calcular items en la carpeta actual
        dirs_set = set()
        files_in_folder = []

        cur_prefix = self.current_folder.rstrip("/") + "/" if self.current_folder else ""

        for entry in self.current_manifest.files:
            rel = entry.path
            if cur_prefix and not rel.startswith(cur_prefix):
                continue
            
            sub = rel[len(cur_prefix):]
            if "/" in sub:
                dir_name = sub.split("/")[0]
                dirs_set.add(dir_name)
            else:
                files_in_folder.append(entry)

        # Mostrar carpetas
        for d in sorted(dirs_set):
            self.tree.insert("", "end", values=(f"📁 {d}", "--", "--", "--", "Carpeta de archivos", "--", "--"), tags=("dir",))

        # Mostrar archivos
        for f in sorted(files_in_folder, key=lambda x: x.path.lower()):
            fname = os.path.basename(f.path)
            ext = os.path.splitext(fname)[1].lower() or "Archivo"
            mtime_str = datetime.datetime.fromtimestamp(f.mtime).strftime("%Y-%m-%d %H:%M") if f.mtime else "--"
            crc_str = f"{f.crc32:08X}"
            
            # Estimación individual
            p_size = f"{format_bytes(f.payload_len)}" if hasattr(f, "payload_len") and f.payload_len > 0 else "--"
            ratio_str = f"{(1 - (f.payload_len / f.size))*100:.1f}%" if (hasattr(f, "payload_len") and f.size > 0 and f.payload_len > 0) else "--"

            icon_type = "📄"
            if ext in [".py", ".js", ".html", ".css", ".json", ".c", ".cpp", ".rs"]: icon_type = "📜"
            elif ext in [".exe", ".dll", ".bat", ".cmd", ".msi"]: icon_type = "⚙️"
            elif ext in [".png", ".jpg", ".jpeg", ".ico", ".svg"]: icon_type = "🖼️"
            elif ext in [".txt", ".md", ".log", ".ini"]: icon_type = "📝"

            self.tree.insert("", "end", values=(f"{icon_type} {fname}", format_bytes(f.size), p_size, ratio_str, ext.upper(), mtime_str, crc_str), tags=("file",))

    def _navigate_up(self):
        if not self.current_folder:
            return
        parts = self.current_folder.rstrip("/").split("/")
        self.current_folder = "/".join(parts[:-1])
        sub_str = f" > {self.current_folder}" if self.current_folder else ""
        self.var_address.set(f"{self.current_archive_path}{sub_str}")
        self._render_explorer()

    def _on_double_click(self, event):
        sel = self.tree.selection()
        if not sel: return
        item = self.tree.item(sel[0])
        val = item["values"][0]

        if val.startswith("📁 "):
            dir_name = val[3:]
            self.current_folder = f"{self.current_folder}/{dir_name}".strip("/")
            self.var_address.set(f"{self.current_archive_path} > {self.current_folder}")
            self._render_explorer()
        else:
            self.cmd_view_file()

    def _show_context_menu(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            if item not in self.tree.selection():
                self.tree.selection_set(item)
            self.tree_menu.post(event.x_root, event.y_root)

    def cmd_open_archive(self):
        f = filedialog.askopenfilename(title="Abrir archivo comprimido", filetypes=[("SmartBundle Archive", "*.sb"), ("Todos los archivos", "*.*")])
        if f:
            self.open_archive(f)

    def cmd_close_archive(self):
        self.current_archive_path = None
        self.current_manifest = None
        self.current_folder = ""
        self.var_address.set("Ningún archivo abierto")
        self.lbl_stats.config(text="0 archivos | 0 B")
        self.lbl_status.config(text="Archivo cerrado.")
        for item in self.tree.get_children():
            self.tree.delete(item)

    def cmd_new_archive(self):
        self._open_new_compression_dialog()

    def _open_new_compression_dialog(self, prefill_source: Optional[str] = None):
        dlg = tk.Toplevel(self)
        dlg.title("Crear nuevo archivo comprimido (.sb)")
        dlg.geometry("540x360")
        dlg.configure(bg="#282a36")
        dlg.transient(self)
        dlg.grab_set()

        tk.Label(dlg, text="Selecciona el archivo o carpeta a comprimir:", bg="#282a36", fg="#f8f8f2", font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=16, pady=(16, 4))
        
        box1 = tk.Frame(dlg, bg="#282a36")
        box1.pack(fill="x", padx=16, pady=4)
        var_src = tk.StringVar(value=prefill_source or "")
        e_src = tk.Entry(box1, textvariable=var_src, bg="#44475a", fg="#ffffff", font=("Segoe UI", 9), relief="flat")
        e_src.pack(side="left", fill="x", expand=True, ipady=4, padx=(0, 6))
        
        def pick_f():
            p = filedialog.askopenfilename(title="Seleccionar archivo")
            if p: 
                var_src.set(p)
                if not var_dst.get(): var_dst.set(p + ".sb")
        def pick_d():
            p = filedialog.askdirectory(title="Seleccionar carpeta")
            if p: 
                var_src.set(p)
                if not var_dst.get(): var_dst.set(p + ".sb")

        ttk.Button(box1, text="Archivo...", command=pick_f, style="Tool.TButton").pack(side="left", padx=2)
        ttk.Button(box1, text="Carpeta...", command=pick_d, style="Tool.TButton").pack(side="left", padx=2)

        tk.Label(dlg, text="Guardar archivo comprimido como (.sb):", bg="#282a36", fg="#f8f8f2", font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=16, pady=(12, 4))
        
        box2 = tk.Frame(dlg, bg="#282a36")
        box2.pack(fill="x", padx=16, pady=4)
        var_dst = tk.StringVar(value=f"{prefill_source}.sb" if prefill_source else "")
        e_dst = tk.Entry(box2, textvariable=var_dst, bg="#44475a", fg="#ffffff", font=("Segoe UI", 9), relief="flat")
        e_dst.pack(side="left", fill="x", expand=True, ipady=4, padx=(0, 6))

        def pick_out():
            p = filedialog.asksaveasfilename(title="Guardar como", defaultextension=".sb", filetypes=[("SmartBundle Archive", "*.sb")])
            if p: var_dst.set(p)

        ttk.Button(box2, text="Examinar...", command=pick_out, style="Tool.TButton").pack(side="left")

        # Nivel de compresión
        box_m = tk.Frame(dlg, bg="#282a36")
        box_m.pack(fill="x", padx=16, pady=12)
        var_m = tk.StringVar(value="extreme")
        tk.Label(box_m, text="Modo:", bg="#282a36", fg="#f8f8f2", font=("Segoe UI", 9, "bold")).pack(side="left", padx=(0, 8))
        tk.Radiobutton(box_m, text="Ultra Extremo (SOTA)", variable=var_m, value="extreme", bg="#282a36", fg="#f8f8f2", selectcolor="#44475a").pack(side="left", padx=4)
        tk.Radiobutton(box_m, text="Equilibrado", variable=var_m, value="balanced", bg="#282a36", fg="#f8f8f2", selectcolor="#44475a").pack(side="left", padx=4)
        tk.Radiobutton(box_m, text="Rápido", variable=var_m, value="fast", bg="#282a36", fg="#f8f8f2", selectcolor="#44475a").pack(side="left", padx=4)

        def do_comp():
            s = var_src.get().strip()
            d = var_dst.get().strip()
            if not s or not os.path.exists(s):
                messagebox.showerror("Error", "Selecciona un origen válido.", parent=dlg)
                return
            if not d:
                messagebox.showerror("Error", "Especifica la ruta de destino.", parent=dlg)
                return
            dlg.destroy()
            self._start_background_compression(s, d, var_m.get())

        btn_ok = ttk.Button(dlg, text="⚡ COMPRIMIR AHORA", style="Accent.TButton", command=do_comp)
        btn_ok.pack(fill="x", padx=16, pady=16)

    def _start_background_compression(self, source: str, destination: str, mode_str: str):
        self.progress["value"] = 0
        self.lbl_status.config(text=f"Comprimiendo {os.path.basename(source)}...")
        
        mode = CompressionMode.EXTREME if mode_str == "extreme" else (CompressionMode.FAST if mode_str == "fast" else CompressionMode.BALANCED)
        archiver = SBArchiver(mode=mode)

        def worker():
            t0 = time.time()
            try:
                def progress_cb(phase, cur, total, extra):
                    denom = max(1, total)
                    if phase == "scanned":
                        pct = (cur / denom) * 20
                        self.after(0, lambda: self._update_progress(pct, f"Escaneando: {extra}"))
                    elif phase == "compressed_block":
                        pct = min(98.0, 20.0 + (cur * 10))
                        self.after(0, lambda: self._update_progress(pct, f"Comprimiendo bloques ({extra})..."))

                stats = archiver.compress(source, destination, progress_cb=progress_cb)
                elapsed = time.time() - t0
                self.after(0, lambda: self._finish_compression(destination, stats, elapsed))
            except Exception as e:
                self.after(0, lambda err=str(e): messagebox.showerror("Error de compresión", err))
                self.after(0, lambda: self.lbl_status.config(text="Fallo en la compresión."))

        threading.Thread(target=worker, daemon=True).start()

    def _update_progress(self, val: float, msg: str):
        self.progress["value"] = val
        self.lbl_status.config(text=msg)

    def _finish_compression(self, archive_path: str, stats: dict, elapsed: float):
        self.progress["value"] = 100
        self.lbl_status.config(text=f"¡Compresión finalizada en {elapsed:.2f}s!")
        messagebox.showinfo(
            "Compresión Completada",
            f"Archivo .sb generado con éxito:\n\n"
            f"• Archivos: {stats['files_count']}\n"
            f"• Original: {format_bytes(stats['uncompressed_size'])}\n"
            f"• Comprimido: {format_bytes(stats['compressed_size'])}\n"
            f"• Ratio de compresión: {stats['ratio_percent']:.2f}%\n"
            f"• Espacio ahorrado: {stats['savings_percent']:.2f}%\n"
            f"• Tiempo: {elapsed:.2f} segundos"
        )
        self.open_archive(archive_path)

    def cmd_add_files(self):
        if not self.current_archive_path:
            self.cmd_new_archive()
            return

        paths = filedialog.askopenfilenames(title="Seleccionar archivos para agregar al archivo abierto")
        if not paths:
            return

        self.lbl_status.config(text="Agregando archivos y actualizando archivo...")
        self.progress["value"] = 0

        def worker():
            try:
                self.archiver.add_files_to_archive(self.current_archive_path, list(paths))
                self.after(0, lambda: self.open_archive(self.current_archive_path))
                self.after(0, lambda: messagebox.showinfo("Éxito", f"Se agregaron {len(paths)} archivo(s) correctamente."))
            except Exception as e:
                self.after(0, lambda err=str(e): messagebox.showerror("Error al añadir", err))

        threading.Thread(target=worker, daemon=True).start()

    def cmd_delete_selected(self):
        if not self.current_archive_path or not self.current_manifest:
            return

        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showwarning("Eliminar", "Selecciona al menos un archivo o carpeta de la lista.")
            return

        names = []
        for it in selected_items:
            raw_val = self.tree.item(it)["values"][0]
            clean_name = raw_val[3:] if len(raw_val) > 3 else raw_val
            full_p = f"{self.current_folder}/{clean_name}".strip("/") if self.current_folder else clean_name
            names.append(full_p)

        if not messagebox.askyesno("Confirmar eliminación", f"¿Deseas eliminar permanentemente {len(names)} elemento(s) del archivo .sb?"):
            return

        self.lbl_status.config(text="Eliminando elementos del archivo...")
        self.progress["value"] = 0

        def worker():
            try:
                self.archiver.delete_files_from_archive(self.current_archive_path, names)
                self.after(0, lambda: self.open_archive(self.current_archive_path))
                self.after(0, lambda: messagebox.showinfo("Éxito", "Elemento(s) eliminados correctamente."))
            except Exception as e:
                self.after(0, lambda err=str(e): messagebox.showerror("Error al eliminar", err))

        threading.Thread(target=worker, daemon=True).start()

    def cmd_extract_all(self):
        if not self.current_archive_path:
            f = filedialog.askopenfilename(title="Seleccionar archivo .sb a extraer", filetypes=[("SmartBundle Archive", "*.sb")])
            if not f: return
            self.current_archive_path = f

        dest = filedialog.askdirectory(title="Seleccionar carpeta de destino para extracción")
        if not dest: return

        self.lbl_status.config(text=f"Extrayendo en {dest}...")
        self.progress["value"] = 0

        def worker():
            t0 = time.time()
            try:
                def progress_cb(phase, cur, total, extra):
                    denom = max(1, total)
                    if phase == "decompressed_block":
                        pct = (cur / denom) * 60
                        self.after(0, lambda: self._update_progress(pct, f"Descomprimiendo: {extra}"))
                    elif phase == "extracted":
                        pct = 60 + ((cur / denom) * 40)
                        self.after(0, lambda: self._update_progress(pct, f"Extrayendo: {extra}"))

                manifest = self.archiver.decompress(self.current_archive_path, dest, progress_cb=progress_cb)
                elapsed = time.time() - t0
                self.after(0, lambda: self.progress.config(value=100))
                self.after(0, lambda: self.lbl_status.config(text="Extracción finalizada."))
                self.after(0, lambda: messagebox.showinfo("Extracción Completa", f"Se extrajeron {len(manifest.files)} archivos con éxito en:\n{dest}\n\nTiempo: {elapsed:.2f}s\nIntegridad: 100% Verificada (SHA256+CRC32)"))
            except Exception as e:
                self.after(0, lambda err=str(e): messagebox.showerror("Error de extracción", err))

        threading.Thread(target=worker, daemon=True).start()

    def cmd_extract_selected(self):
        if not self.current_archive_path or not self.current_manifest:
            return

        selected_items = self.tree.selection()
        if not selected_items:
            self.cmd_extract_all()
            return

        names = []
        for it in selected_items:
            raw_val = self.tree.item(it)["values"][0]
            clean_name = raw_val[3:] if len(raw_val) > 3 else raw_val
            full_p = f"{self.current_folder}/{clean_name}".strip("/") if self.current_folder else clean_name
            names.append(full_p)

        dest = filedialog.askdirectory(title="Seleccionar carpeta de destino")
        if not dest: return

        self.lbl_status.config(text="Extrayendo selección...")
        
        def worker():
            try:
                res = self.archiver.extract_single_or_selected(self.current_archive_path, dest, selected_paths=names)
                self.after(0, lambda: messagebox.showinfo("Éxito", f"Se extrajeron {len(res)} archivo(s) en:\n{dest}"))
                self.after(0, lambda: self.lbl_status.config(text="Extracción de selección finalizada."))
            except Exception as e:
                self.after(0, lambda err=str(e): messagebox.showerror("Error de extracción", err))

        threading.Thread(target=worker, daemon=True).start()

    def cmd_view_file(self):
        if not self.current_archive_path or not self.current_manifest:
            return

        selected_items = self.tree.selection()
        if not selected_items:
            return

        raw_val = self.tree.item(selected_items[0])["values"][0]
        if raw_val.startswith("📁 "):
            self._on_double_click(None)
            return

        clean_name = raw_val[3:] if len(raw_val) > 3 else raw_val
        full_p = f"{self.current_folder}/{clean_name}".strip("/") if self.current_folder else clean_name

        temp_dir = tempfile.mkdtemp(prefix="sb_view_")
        try:
            extracted = self.archiver.extract_single_or_selected(self.current_archive_path, temp_dir, selected_paths=[full_p])
            if extracted and os.path.exists(extracted[0]):
                os.startfile(extracted[0])
        except Exception as e:
            messagebox.showerror("Error al abrir", f"No se pudo visualizar el archivo:\n{str(e)}")

    def cmd_test_integrity(self):
        if not self.current_archive_path:
            messagebox.showwarning("Comprobar", "Abre primero un archivo .sb.")
            return

        self.lbl_status.config(text="Comprobando integridad bit a bit (SHA256 y CRC32)...")
        self.progress["value"] = 0

        def worker():
            temp_dir = tempfile.mkdtemp(prefix="sb_test_")
            t0 = time.time()
            try:
                manifest = self.archiver.decompress(self.current_archive_path, temp_dir)
                elapsed = time.time() - t0
                self.after(0, lambda: self.progress.config(value=100))
                self.after(0, lambda: self.lbl_status.config(text="Comprobación superada con éxito."))
                self.after(0, lambda: messagebox.showinfo(
                    "Integridad Verificada",
                    f"¡No se encontraron errores en el archivo!\n\n"
                    f"• Archivo: {os.path.basename(self.current_archive_path)}\n"
                    f"• Ficheros analizados: {len(manifest.files)}\n"
                    f"• Total bytes: {format_bytes(manifest.total_uncompressed_size)}\n"
                    f"• Verificación SHA-256: 100% Coincidencia Exacta\n"
                    f"• Verificación CRC-32: Todos los bloques válidos\n"
                    f"• Tiempo de chequeo: {elapsed:.2f}s"
                ))
            except Exception as e:
                self.after(0, lambda err=str(e): messagebox.showerror("Fallo de integridad", f"Se detectó un error en el archivo comprimido:\n{err}"))
            finally:
                shutil.rmtree(temp_dir, ignore_errors=True)

        threading.Thread(target=worker, daemon=True).start()

    def cmd_show_info(self):
        if not self.current_archive_path or not self.current_manifest:
            messagebox.showinfo("Información", "No hay ningún archivo abierto.")
            return

        comp_size = os.path.getsize(self.current_archive_path)
        orig_size = self.current_manifest.total_uncompressed_size
        ratio = (1 - (comp_size / orig_size)) * 100 if orig_size > 0 else 0

        info_text = (
            f"Propiedades del Archivo .sb\n"
            f"--------------------------------------------------\n"
            f"Ruta:                  {self.current_archive_path}\n"
            f"Ficheros totales:      {len(self.current_manifest.files)}\n"
            f"Tamaño sin comprimir:  {format_bytes(orig_size)} ({orig_size:,} bytes)\n"
            f"Tamaño comprimido:     {format_bytes(comp_size)} ({comp_size:,} bytes)\n"
            f"Ahorro de espacio:     {ratio:.2f}%\n"
            f"Algoritmos soportados: Zstd Ultra, Brotli Max, LZMA2, PPMd\n"
            f"Filtros de bytecode:   BCJ x86 / Delta Preprocessor\n"
            f"Integridad:            xxHash64 / SHA-256 Solid Footer\n"
        )
        messagebox.showinfo("Información del Archivo", info_text)

    def _show_about(self):
        messagebox.showinfo(
            "Acerca de SmartBundle Pro",
            "SmartBundle Pro (.sb) v1.0\n\n"
            "Archivador y Compresor Inteligente para Windows.\n"
            "Soporte para exploración interactiva, adición y eliminación de archivos."
        )

def main():
    initial = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else None
    app = SmartBundleManagerApp(initial_path=initial)
    app.mainloop()

if __name__ == "__main__":
    main()
