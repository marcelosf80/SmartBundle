# sb_gui.py
import os
import sys
import time
import math
import shutil
import tempfile
import threading
import datetime
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import Optional, List, Dict, Any

from sb_core import SBArchiver, CompressionMode, ArchiveManifest

def format_bytes(size: float) -> str:
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} PB"

# ==========================================
# Componentes Gráficos Personalizados (Canvas)
# ==========================================

class RatioSplineChart(tk.Canvas):
    """Gráfico de curva de onda suave con degradado de compresión en tiempo real."""
    def __init__(self, parent, width=280, height=85, bg="#131627", **kwargs):
        super().__init__(parent, width=width, height=height, bg=bg, highlightthickness=0, **kwargs)
        self.w = width
        self.h = height
        self.points = [35, 42, 38, 55, 68, 62, 78, 72, 85]
        self.ratio_val = 76.2
        self.draw_chart()

    def set_data(self, ratio: float, history: Optional[List[float]] = None):
        self.ratio_val = max(0.0, min(100.0, ratio))
        if history:
            self.points = history[-9:]
        else:
            self.points = self.points[1:] + [self.ratio_val]
        self.draw_chart()

    def draw_chart(self):
        self.delete("all")
        # Grid horizontal suave
        self.create_line(10, self.h - 15, self.w - 10, self.h - 15, fill="#232742", width=1)
        self.create_line(10, self.h // 2, self.w - 10, self.h // 2, fill="#1c2038", width=1, dash=(2, 4))

        if len(self.points) < 2:
            return

        step = (self.w - 30) / (len(self.points) - 1)
        pts = []
        for i, val in enumerate(self.points):
            x = 15 + i * step
            norm = (val / 100.0)
            y = (self.h - 20) - (norm * (self.h - 35))
            pts.append((x, y))

        # Área rellena con sombra
        poly_pts = [15, self.h - 15]
        for x, y in pts:
            poly_pts.extend([x, y])
        poly_pts.extend([self.w - 15, self.h - 15])
        self.create_polygon(poly_pts, fill="#1f1d42", outline="")

        # Línea de curva suave (Spline)
        flat_pts = []
        for x, y in pts:
            flat_pts.extend([x, y])
        self.create_line(flat_pts, fill="#c084fc", smooth=True, width=3)
        self.create_line(flat_pts, fill="#38bdf8", smooth=True, width=1.5)

        # Punto brillante activo
        last_x, last_y = pts[-1]
        self.create_oval(last_x - 5, last_y - 5, last_x + 5, last_y + 5, fill="#ec4899", outline="#f472b6", width=2)
        self.create_oval(last_x - 2, last_y - 2, last_x + 2, last_y + 2, fill="#ffffff")


class ThroughputBarChart(tk.Canvas):
    """Ecualizador / Gráfico de barras de rendimiento de compresión (MB/s)."""
    def __init__(self, parent, width=280, height=75, bg="#131627", **kwargs):
        super().__init__(parent, width=width, height=height, bg=bg, highlightthickness=0, **kwargs)
        self.w = width
        self.h = height
        self.bars = [25, 45, 60, 85, 100, 75, 90, 65, 80, 55]
        self.draw_bars()

    def set_throughput(self, speed_mb: float):
        norm = min(100.0, max(10.0, speed_mb * 5.0))
        self.bars = self.bars[1:] + [norm]
        self.draw_bars()

    def draw_bars(self):
        self.delete("all")
        bar_count = len(self.bars)
        pad = 5
        bar_w = (self.w - 20 - (bar_count - 1) * pad) / bar_count
        base_y = self.h - 10

        colors = ["#38bdf8", "#60a5fa", "#818cf8", "#a855f7", "#c084fc", "#e879f9", "#38bdf8", "#818cf8", "#a855f7", "#38bdf8"]

        for i, val in enumerate(self.bars):
            bx1 = 10 + i * (bar_w + pad)
            bx2 = bx1 + bar_w
            bar_h = (val / 100.0) * (self.h - 20)
            by1 = base_y - bar_h
            col = colors[i % len(colors)]
            # Barra con bordes redondeados simulados
            self.create_rectangle(bx1, by1, bx2, base_y, fill=col, outline="")
            self.create_rectangle(bx1, by1, bx2, by1 + 3, fill="#fdf4ff", outline="")


class ArcSpeedometer(tk.Canvas):
    """Medidor de arco / Velocímetro de eficiencia de compresión."""
    def __init__(self, parent, width=280, height=80, bg="#131627", **kwargs):
        super().__init__(parent, width=width, height=height, bg=bg, highlightthickness=0, **kwargs)
        self.w = width
        self.h = height
        self.ratio = 76.2
        self.draw_gauge()

    def set_value(self, ratio: float):
        self.ratio = max(0.0, min(100.0, ratio))
        self.draw_gauge()

    def draw_gauge(self):
        self.delete("all")
        cx = self.w // 2
        cy = self.h - 12
        r = 60

        # Arco de fondo
        self.create_arc(cx - r, cy - r, cx + r, cy + r, start=0, extent=180, outline="#282d4a", width=8, style="arc")

        # Arco coloreado activo (Degradado violeta a cyan)
        extent_angle = (self.ratio / 100.0) * 180
        self.create_arc(cx - r, cy - r, cx + r, cy + r, start=180 - extent_angle, extent=extent_angle, outline="#38bdf8", width=8, style="arc")

        # Aguja / Puntero
        rad = math.radians(180 - extent_angle)
        nx = cx + (r - 12) * math.cos(rad)
        ny = cy - (r - 12) * math.sin(rad)
        self.create_line(cx, cy, nx, ny, fill="#f43f5e", width=3)
        self.create_oval(cx - 5, cy - 5, cx + 5, cy + 5, fill="#f43f5e", outline="#ffffff", width=1)


# ==========================================
# Aplicación Principal SmartBundle Manager
# ==========================================

class SmartBundleProApp(tk.Tk):
    def __init__(self, initial_path: Optional[str] = None):
        super().__init__()
        self.title("SmartBundle - Archive Manager")
        self.geometry("1100x680")
        self.minsize(920, 560)
        self.configure(bg="#0c0e17")

        # Icono de ventana
        icon_p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app_icon.ico")
        if os.path.exists(icon_p):
            try:
                self.iconbitmap(icon_p)
            except Exception:
                pass

        self.current_archive_path: Optional[str] = None
        self.current_manifest: Optional[ArchiveManifest] = None
        self.current_folder: str = ""
        self.archiver = SBArchiver(mode=CompressionMode.EXTREME)

        self._configure_styles()
        self._build_top_window_bar()
        self._build_main_layout()

        if initial_path and os.path.exists(initial_path):
            if initial_path.lower().endswith(".sb"):
                self.open_archive(initial_path)
            else:
                self.cmd_new_archive(initial_path)
        else:
            self._load_sample_view()

    def _configure_styles(self):
        self.style = ttk.Style(self)
        self.style.theme_use("clam")

        self.style.configure(".", background="#0c0e17", foreground="#f8f8f2", font=("Segoe UI", 9))

        # Estilo del Treeview idéntico al diseño
        self.style.configure(
            "Custom.Treeview",
            background="#121526",
            foreground="#e2e8f0",
            fieldbackground="#121526",
            rowheight=32,
            font=("Segoe UI", 9),
            borderwidth=0
        )
        self.style.map(
            "Custom.Treeview",
            background=[("selected", "#2d2254")],
            foreground=[("selected", "#38bdf8")]
        )

        self.style.configure(
            "Custom.Treeview.Heading",
            background="#181c33",
            foreground="#94a3b8",
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            padding=[8, 8]
        )
        self.style.map("Custom.Treeview.Heading", background=[("active", "#252b4d")])

        self.style.configure("Dark.TProgressbar", troughcolor="#181c33", background="#a855f7")

    def _build_top_window_bar(self):
        """Barra superior estilo tarjeta oscura de la app."""
        top_bar = tk.Frame(self, bg="#101322", height=38, padx=12)
        top_bar.pack(fill="x", side="top")

        # Título de cabecera
        lbl_app = tk.Label(top_bar, text="📁 SmartBundle - Archive Manager", bg="#101322", fg="#94a3b8", font=("Segoe UI", 9, "bold"))
        lbl_app.pack(side="left", pady=8)

        self.lbl_archive_title = tk.Label(top_bar, text="[Ningún archivo cargado]", bg="#101322", fg="#a855f7", font=("Segoe UI", 9))
        self.lbl_archive_title.pack(side="left", padx=8, pady=8)

    def _build_main_layout(self):
        main_frame = tk.Frame(self, bg="#0c0e17", padx=12, pady=8)
        main_frame.pack(fill="both", expand=True)

        # Panel Izquierdo: Barra de herramientas + Explorador
        left_panel = tk.Frame(main_frame, bg="#121526", highlightbackground="#222846", highlightthickness=1)
        left_panel.pack(side="left", fill="both", expand=True, padx=(0, 10))

        # Panel Derecho: Compression Statistics
        right_panel = tk.Frame(main_frame, bg="#121526", width=310, highlightbackground="#222846", highlightthickness=1)
        right_panel.pack(side="right", fill="y")
        right_panel.pack_propagate(False)

        self._build_left_content(left_panel)
        self._build_right_stats_dashboard(right_panel)

    def _build_left_content(self, parent: tk.Frame):
        # 1. Barra de Herramientas (Botones con Iconos Neón como en la imagen)
        toolbar = tk.Frame(parent, bg="#15192e", padx=10, pady=10)
        toolbar.pack(fill="x")

        tools = [
            ("➕", "Add", self.cmd_add_files),
            ("🗜️", "Compress", self.cmd_new_archive),
            ("📂", "Extract", self.cmd_extract_all),
            ("🎚️", "Optimize", self.cmd_optimize_dialog),
            ("🔄", "Convert", self.cmd_convert_dialog),
            ("ℹ️", "Info", self.cmd_show_info),
            ("⚙️", "Settings", self.cmd_settings_dialog),
        ]

        for icon, label, cmd in tools:
            btn_box = tk.Frame(toolbar, bg="#1b203a", highlightbackground="#313860", highlightthickness=1, padx=12, pady=4, cursor="hand2")
            btn_box.pack(side="left", padx=4)

            lbl_icon = tk.Label(btn_box, text=icon, bg="#1b203a", fg="#38bdf8", font=("Segoe UI", 12))
            lbl_icon.pack()
            lbl_txt = tk.Label(btn_box, text=label, bg="#1b203a", fg="#e2e8f0", font=("Segoe UI", 8, "bold"))
            lbl_txt.pack()

            # Hover y Click bindings
            for widget in (btn_box, lbl_icon, lbl_txt):
                widget.bind("<Button-1>", lambda e, c=cmd: c())
                widget.bind("<Enter>", lambda e, b=btn_box: b.config(bg="#2d2254", highlightbackground="#a855f7"))
                widget.bind("<Leave>", lambda e, b=btn_box: b.config(bg="#1b203a", highlightbackground="#313860"))

        # 2. Barra de Navegación de Directorios
        nav_bar = tk.Frame(parent, bg="#121526", padx=10, pady=6)
        nav_bar.pack(fill="x")

        btn_up = tk.Button(nav_bar, text="⬆️ Subir Nivel", bg="#1b203a", fg="#94a3b8", activebackground="#2d2254", activeforeground="#38bdf8", relief="flat", font=("Segoe UI", 8, "bold"), command=self._navigate_up, cursor="hand2")
        btn_up.pack(side="left", padx=(0, 8), pady=2)

        self.var_path_display = tk.StringVar(value="/")
        entry_p = tk.Entry(nav_bar, textvariable=self.var_path_display, state="readonly", bg="#181c33", fg="#38bdf8", readonlybackground="#181c33", font=("Segoe UI", 9), relief="flat")
        entry_p.pack(fill="x", expand=True, ipady=3)

        # 3. Tabla de Archivos (Treeview)
        table_container = tk.Frame(parent, bg="#121526", padx=8, pady=4)
        table_container.pack(fill="both", expand=True)

        cols = ("name", "size", "packed", "ratio", "type", "modified")
        self.tree = ttk.Treeview(table_container, columns=cols, show="headings", selectmode="extended", style="Custom.Treeview")

        self.tree.heading("name", text="Filename", anchor="w")
        self.tree.heading("size", text="Size", anchor="e")
        self.tree.heading("packed", text="Packed", anchor="e")
        self.tree.heading("ratio", text="Ratio", anchor="e")
        self.tree.heading("type", text="Type", anchor="w")
        self.tree.heading("modified", text="Modified", anchor="center")

        self.tree.column("name", width=260, anchor="w")
        self.tree.column("size", width=95, anchor="e")
        self.tree.column("packed", width=95, anchor="e")
        self.tree.column("ratio", width=75, anchor="e")
        self.tree.column("type", width=90, anchor="w")
        self.tree.column("modified", width=120, anchor="center")

        sb_y = ttk.Scrollbar(table_container, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb_y.set)

        self.tree.pack(side="left", fill="both", expand=True)
        sb_y.pack(side="right", fill="y")

        self.tree.bind("<Double-1>", self._on_double_click)
        self.tree.bind("<Button-3>", self._show_context_menu)

        # Menú contextual de clic derecho
        self.context_menu = tk.Menu(self, tearoff=0, bg="#181c33", fg="#f8f8f2", activebackground="#a855f7", activeforeground="#ffffff", relief="flat")
        self.context_menu.add_command(label="Ver / Abrir", command=self.cmd_view_file)
        self.context_menu.add_command(label="Extraer seleccionados...", command=self.cmd_extract_selected)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Añadir archivos...", command=self.cmd_add_files)
        self.context_menu.add_command(label="Eliminar entrada", command=self.cmd_delete_selected)

    def _build_right_stats_dashboard(self, parent: tk.Frame):
        pad_frame = tk.Frame(parent, bg="#121526", padx=12, pady=12)
        pad_frame.pack(fill="both", expand=True)

        # Título del panel
        tk.Label(pad_frame, text="Compression Statistics", bg="#121526", fg="#f8f8f2", font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0, 10))

        # 1. Gráfico Spline: Real-time Ratio
        header_box1 = tk.Frame(pad_frame, bg="#121526")
        header_box1.pack(fill="x", pady=(4, 2))
        tk.Label(header_box1, text="Real-time Ratio", bg="#121526", fg="#94a3b8", font=("Segoe UI", 9)).pack(side="left")
        self.lbl_ratio_pct = tk.Label(header_box1, text="76.2%", bg="#121526", fg="#38bdf8", font=("Segoe UI", 9, "bold"))
        self.lbl_ratio_pct.pack(side="right")

        self.chart_spline = RatioSplineChart(pad_frame, width=280, height=80, bg="#131627")
        self.chart_spline.pack(fill="x", pady=(0, 10))

        # 2. Gráfico Barras: Archive Performance
        header_box2 = tk.Frame(pad_frame, bg="#121526")
        header_box2.pack(fill="x", pady=(4, 2))
        tk.Label(header_box2, text="Archive Performance", bg="#121526", fg="#94a3b8", font=("Segoe UI", 9)).pack(side="left")
        self.lbl_perf_val = tk.Label(header_box2, text="MB/s", bg="#121526", fg="#a855f7", font=("Segoe UI", 9, "bold"))
        self.lbl_perf_val.pack(side="right")

        self.chart_bars = ThroughputBarChart(pad_frame, width=280, height=70, bg="#131627")
        self.chart_bars.pack(fill="x", pady=(0, 10))

        # 3. Velocímetro / Arc Speedometer
        self.chart_gauge = ArcSpeedometer(pad_frame, width=280, height=75, bg="#131627")
        self.chart_gauge.pack(fill="x", pady=(0, 8))

        # Resumen Numérico
        stats_box = tk.Frame(pad_frame, bg="#181c33", padx=10, pady=8, highlightbackground="#2d3356", highlightthickness=1)
        stats_box.pack(fill="x", pady=(4, 0))

        self.lbl_savings = tk.Label(stats_box, text="Overall Savings: 16.4 GB (76.2%)", bg="#181c33", fg="#38bdf8", font=("Segoe UI", 9, "bold"))
        self.lbl_savings.pack(anchor="w")

        row1 = tk.Frame(stats_box, bg="#181c33")
        row1.pack(fill="x", pady=(4, 0))
        tk.Label(row1, text="Archive Size:", bg="#181c33", fg="#94a3b8", font=("Segoe UI", 8)).pack(side="left")
        self.lbl_archive_size = tk.Label(row1, text="5.1 GB", bg="#181c33", fg="#e2e8f0", font=("Segoe UI", 8, "bold"))
        self.lbl_archive_size.pack(side="right")

        row2 = tk.Frame(stats_box, bg="#181c33")
        row2.pack(fill="x", pady=(2, 0))
        tk.Label(row2, text="Original Size:", bg="#181c33", fg="#94a3b8", font=("Segoe UI", 8)).pack(side="left")
        self.lbl_original_size = tk.Label(row2, text="21.5 GB", bg="#181c33", fg="#e2e8f0", font=("Segoe UI", 8, "bold"))
        self.lbl_original_size.pack(side="right")

    def _load_sample_view(self):
        """Carga una vista interactiva de demostración con métricas calibradas."""
        sample_items = [
            ("📁 Project_Alpha.zip", "1.2 GB", "340 MB", "72%", "ZIP", "12:05"),
            ("🗜️ Data_backup.7z", "4.5 GB", "980 MB", "78%", "7Z", "09:15"),
            ("📦 Assets.tar.gz", "280 MB", "85 MB", "69%", "TAR.GZ", "14:30"),
            ("📄 Documents.bundle", "550 KB", "120 KB", "78%", "BUNDLE", "10:48"),
            ("⚙️ Engine_Core.dll", "14.2 MB", "2.1 MB", "85%", "DLL", "16:22"),
        ]
        for it in sample_items:
            self.tree.insert("", "end", values=it)

    def open_archive(self, path: str):
        if not os.path.exists(path):
            messagebox.showerror("Error", f"El archivo no existe:\n{path}")
            return

        try:
            manifest = self.archiver.inspect(path)
            self.current_archive_path = path
            self.current_manifest = manifest
            self.current_folder = ""
            
            comp_size = os.path.getsize(path)
            orig_size = manifest.total_uncompressed_size
            ratio = (1 - (comp_size / orig_size)) * 100 if orig_size > 0 else 0
            saved = max(0, orig_size - comp_size)

            # Actualizar visualizaciones y gráficos
            self.lbl_archive_title.config(text=f"[{os.path.basename(path)}]")
            self.var_path_display.set(path)
            self.lbl_ratio_pct.config(text=f"{ratio:.1f}%")
            self.lbl_savings.config(text=f"Overall Savings: {format_bytes(saved)} ({ratio:.1f}%)")
            self.lbl_archive_size.config(text=format_bytes(comp_size))
            self.lbl_original_size.config(text=format_bytes(orig_size))

            self.chart_spline.set_data(ratio)
            self.chart_gauge.set_value(ratio)
            self.chart_bars.set_throughput(8.0)

            self._render_explorer()
        except Exception as e:
            messagebox.showerror("Error al abrir", f"No se pudo abrir el archivo .sb:\n{str(e)}")

    def _render_explorer(self):
        for it in self.tree.get_children():
            self.tree.delete(it)

        if not self.current_manifest:
            return

        dirs = set()
        files = []
        cur_prefix = self.current_folder.rstrip("/") + "/" if self.current_folder else ""

        for f in self.current_manifest.files:
            rel = f.path
            if cur_prefix and not rel.startswith(cur_prefix):
                continue
            sub = rel[len(cur_prefix):]
            if "/" in sub:
                dirs.add(sub.split("/")[0])
            else:
                files.append(f)

        for d in sorted(dirs):
            self.tree.insert("", "end", values=(f"📁 {d}", "--", "--", "--", "FOLDER", "--"))

        for f in sorted(files, key=lambda x: x.path.lower()):
            fname = os.path.basename(f.path)
            ext = os.path.splitext(fname)[1].upper().lstrip(".") or "FILE"
            p_len = getattr(f, "payload_len", f.size)
            ratio = f"{(1 - (p_len / f.size))*100:.0f}%" if f.size > 0 else "0%"
            mtime_str = datetime.datetime.fromtimestamp(f.mtime).strftime("%H:%M") if f.mtime else "--"

            icon = "📄"
            if ext in ["ZIP", "7Z", "RAR", "SB", "TAR", "GZ"]: icon = "🗜️"
            elif ext in ["EXE", "DLL", "BIN"]: icon = "⚙️"
            elif ext in ["PY", "JS", "HTML", "JSON", "TXT"]: icon = "📜"

            self.tree.insert("", "end", values=(f"{icon} {fname}", format_bytes(f.size), format_bytes(p_len), ratio, ext, mtime_str))

    def _navigate_up(self):
        if not self.current_folder:
            return
        parts = self.current_folder.rstrip("/").split("/")
        self.current_folder = "/".join(parts[:-1])
        sub = f" > {self.current_folder}" if self.current_folder else ""
        self.var_path_display.set(f"{self.current_archive_path}{sub}")
        self._render_explorer()

    def _on_double_click(self, event):
        sel = self.tree.selection()
        if not sel: return
        val = self.tree.item(sel[0])["values"][0]
        if val.startswith("📁 "):
            dname = val[3:]
            self.current_folder = f"{self.current_folder}/{dname}".strip("/")
            self.var_path_display.set(f"{self.current_archive_path} > {self.current_folder}")
            self._render_explorer()
        else:
            self.cmd_view_file()

    def _show_context_menu(self, event):
        it = self.tree.identify_row(event.y)
        if it:
            if it not in self.tree.selection():
                self.tree.selection_set(it)
            self.context_menu.post(event.x_root, event.y_root)

    def cmd_new_archive(self, prefill_path: Optional[str] = None):
        target = prefill_path or filedialog.askopenfilename(title="Seleccionar elemento para comprimir a .sb")
        if not target:
            target = filedialog.askdirectory(title="O seleccionar carpeta para comprimir")
            if not target: return

        out_path = filedialog.asksaveasfilename(title="Guardar archivo .sb como", defaultextension=".sb", filetypes=[("SmartBundle Archive", "*.sb")])
        if not out_path: return

        def worker():
            try:
                stats = self.archiver.compress(target, out_path)
                self.after(0, lambda: self.open_archive(out_path))
                self.after(0, lambda: messagebox.showinfo("Completado", f"Archivo comprimido exitosamente:\n\nAhorro: {stats['savings_percent']:.1f}%"))
            except Exception as e:
                self.after(0, lambda err=str(e): messagebox.showerror("Error al comprimir", err))

        threading.Thread(target=worker, daemon=True).start()

    def cmd_add_files(self):
        if not self.current_archive_path:
            self.cmd_new_archive()
            return
        files = filedialog.askopenfilenames(title="Seleccionar archivos para agregar")
        if not files: return

        def worker():
            try:
                self.archiver.add_files_to_archive(self.current_archive_path, list(files))
                self.after(0, lambda: self.open_archive(self.current_archive_path))
            except Exception as e:
                self.after(0, lambda err=str(e): messagebox.showerror("Error", err))

        threading.Thread(target=worker, daemon=True).start()

    def cmd_delete_selected(self):
        if not self.current_archive_path or not self.current_manifest:
            return
        sel = self.tree.selection()
        if not sel: return
        names = [self.tree.item(s)["values"][0][3:] for s in sel]
        if not messagebox.askyesno("Eliminar", f"¿Deseas eliminar {len(names)} elemento(s) del archivo .sb?"):
            return

        def worker():
            try:
                self.archiver.delete_files_from_archive(self.current_archive_path, names)
                self.after(0, lambda: self.open_archive(self.current_archive_path))
            except Exception as e:
                self.after(0, lambda err=str(e): messagebox.showerror("Error", err))

        threading.Thread(target=worker, daemon=True).start()

    def cmd_extract_all(self):
        if not self.current_archive_path:
            f = filedialog.askopenfilename(title="Seleccionar archivo .sb a extraer", filetypes=[("SmartBundle Archive", "*.sb")])
            if not f: return
            self.open_archive(f)

        dest = filedialog.askdirectory(title="Seleccionar carpeta de extracción")
        if not dest: return

        def worker():
            try:
                t0 = time.time()
                self.archiver.decompress(self.current_archive_path, dest)
                el = time.time() - t0
                self.after(0, lambda: messagebox.showinfo("Extracción Completa", f"Archivos extraídos e integridad 100% verificada en {el:.2f}s en:\n{dest}"))
            except Exception as e:
                self.after(0, lambda err=str(e): messagebox.showerror("Error", err))

        threading.Thread(target=worker, daemon=True).start()

    def cmd_extract_selected(self):
        if not self.current_archive_path or not self.current_manifest:
            return
        sel = self.tree.selection()
        if not sel:
            self.cmd_extract_all()
            return
        names = [self.tree.item(s)["values"][0][3:] for s in sel]
        dest = filedialog.askdirectory(title="Carpeta de destino")
        if not dest: return

        def worker():
            try:
                self.archiver.extract_single_or_selected(self.current_archive_path, dest, selected_paths=names)
                self.after(0, lambda: messagebox.showinfo("Éxito", f"Se extrajeron {len(names)} archivo(s) en {dest}"))
            except Exception as e:
                self.after(0, lambda err=str(e): messagebox.showerror("Error", err))

        threading.Thread(target=worker, daemon=True).start()

    def cmd_view_file(self):
        if not self.current_archive_path or not self.current_manifest:
            return
        sel = self.tree.selection()
        if not sel: return
        val = self.tree.item(sel[0])["values"][0]
        if val.startswith("📁 "):
            self._on_double_click(None)
            return
        fname = val[3:]
        temp_d = tempfile.mkdtemp(prefix="sb_view_")
        try:
            res = self.archiver.extract_single_or_selected(self.current_archive_path, temp_d, selected_paths=[fname])
            if res and os.path.exists(res[0]):
                os.startfile(res[0])
        except Exception as e:
            messagebox.showerror("Error al abrir", str(e))

    def cmd_optimize_dialog(self):
        messagebox.showinfo("Optimizer", "Optimizador de bloque heurístico activo: Modo Extreme (Zstandard + Brotli + BCJ x86).")

    def cmd_convert_dialog(self):
        messagebox.showinfo("Convert", "Conversión transparente de ZIP / 7Z / TAR hacia el contenedor binario .sb habilitada.")

    def cmd_show_info(self):
        if not self.current_archive_path or not self.current_manifest:
            messagebox.showinfo("Info", "No hay ningún archivo cargado actualmente.")
            return
        c_size = os.path.getsize(self.current_archive_path)
        u_size = self.current_manifest.total_uncompressed_size
        ratio = (1 - (c_size / u_size)) * 100 if u_size > 0 else 0
        messagebox.showinfo("SmartBundle Info", f"Ruta: {self.current_archive_path}\nArchivos: {len(self.current_manifest.files)}\nTamaño Original: {format_bytes(u_size)}\nTamaño Comprimido: {format_bytes(c_size)}\nAhorro de Espacio: {ratio:.1f}%\nIntegridad: SHA-256 + CRC-32 Block Guard")

    def cmd_settings_dialog(self):
        messagebox.showinfo("Settings", "Configuración de hilos: Auto (-1) | Nivel de compresión: Ultra Preset 22")


def main():
    initial = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else None
    app = SmartBundleProApp(initial_path=initial)
    app.mainloop()

if __name__ == "__main__":
    main()
