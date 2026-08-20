# sb_gui.py
import os
import sys
import threading
import time
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from sb_core import SBArchiver, CompressionMode

def format_bytes(size: float) -> str:
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} PB"

class SuperBinaryApp(tk.Tk):
    def __init__(self, initial_path: str = None):
        super().__init__()
        self.title("SmartBundle Pro (.sb) - Archivador & Compresor")
        self.geometry("760x600")
        self.minsize(640, 480)
        self.configure(bg="#1e1e2e")
        
        # Cargar icono de la aplicación si existe
        icon_p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app_icon.ico")
        if os.path.exists(icon_p):
            try:
                self.iconbitmap(icon_p)
            except Exception:
                pass

        self._configure_styles()
        self._build_ui()
        
        if initial_path and os.path.exists(initial_path):
            if initial_path.lower().endswith(".sb"):
                self.notebook.select(self.tab_decompress)
                self.var_decomp_src.set(initial_path)
                base = os.path.splitext(os.path.basename(initial_path))[0]
                self.var_decomp_dst.set(os.path.join(os.path.dirname(initial_path), base))
            else:
                self.notebook.select(self.tab_compress)
                self.var_source.set(initial_path)
                out = f"{initial_path}.sb" if not initial_path.endswith(".sb") else initial_path
                self.var_dest.set(out)

    def _configure_styles(self):
        style = ttk.Style(self)
        style.theme_use("clam")

        bg_color = "#1e1e2e"
        card_bg = "#282a36"
        fg_color = "#f8f8f2"
        accent_color = "#bd93f9"
        accent_hover = "#ff79c6"

        style.configure(".", background=bg_color, foreground=fg_color, font=("Segoe UI", 10))
        style.configure("TNotebook", background=bg_color, borderwidth=0)
        style.configure("TNotebook.Tab", background="#44475a", foreground=fg_color, padding=[16, 8], font=("Segoe UI", 10, "bold"))
        style.map("TNotebook.Tab", background=[("selected", accent_color)], foreground=[("selected", "#282a36")])

        style.configure("Card.TFrame", background=card_bg, relief="flat")
        style.configure("Action.TButton", background=accent_color, foreground="#282a36", font=("Segoe UI", 10, "bold"), padding=[12, 6])
        style.map("Action.TButton", background=[("active", accent_hover)])
        style.configure("Secondary.TButton", background="#44475a", foreground=fg_color, padding=[10, 5])
        style.map("Secondary.TButton", background=[("active", "#6272a4")])

        style.configure("Horizontal.TProgressbar", troughcolor="#44475a", background=accent_color)

    def _build_ui(self):
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=16, pady=16)

        self.tab_compress = ttk.Frame(self.notebook)
        self.tab_decompress = ttk.Frame(self.notebook)

        self.notebook.add(self.tab_compress, text="  Comprimir (.sb)  ")
        self.notebook.add(self.tab_decompress, text="  Descomprimir  ")

        self._build_compress_tab()
        self._build_decompress_tab()

    def _build_compress_tab(self):
        frame = ttk.Frame(self.tab_compress, style="Card.TFrame", padding=20)
        frame.pack(fill="both", expand=True)

        lbl_source = tk.Label(frame, text="Elemento a comprimir (Carpeta o Archivo / Programa):", bg="#282a36", fg="#f8f8f2", font=("Segoe UI", 10, "bold"))
        lbl_source.pack(anchor="w")

        src_box = tk.Frame(frame, bg="#282a36")
        src_box.pack(fill="x", pady=(4, 12))

        self.var_source = tk.StringVar()
        self.entry_source = tk.Entry(src_box, textvariable=self.var_source, bg="#44475a", fg="#ffffff", insertbackground="#ffffff", font=("Segoe UI", 10), relief="flat")
        self.entry_source.pack(side="left", fill="x", expand=True, ipady=6, padx=(0, 8))

        btn_folder = ttk.Button(src_box, text="Carpeta...", style="Secondary.TButton", command=self._select_folder)
        btn_folder.pack(side="left", padx=2)
        btn_file = ttk.Button(src_box, text="Archivo/Exe...", style="Secondary.TButton", command=self._select_file)
        btn_file.pack(side="left", padx=2)

        lbl_dest = tk.Label(frame, text="Ruta de destino (.sb):", bg="#282a36", fg="#f8f8f2", font=("Segoe UI", 10, "bold"))
        lbl_dest.pack(anchor="w")

        dst_box = tk.Frame(frame, bg="#282a36")
        dst_box.pack(fill="x", pady=(4, 12))

        self.var_dest = tk.StringVar()
        self.entry_dest = tk.Entry(dst_box, textvariable=self.var_dest, bg="#44475a", fg="#ffffff", insertbackground="#ffffff", font=("Segoe UI", 10), relief="flat")
        self.entry_dest.pack(side="left", fill="x", expand=True, ipady=6, padx=(0, 8))

        btn_save = ttk.Button(dst_box, text="Examinar...", style="Secondary.TButton", command=self._select_save_path)
        btn_save.pack(side="left")

        mode_box = tk.Frame(frame, bg="#282a36")
        mode_box.pack(fill="x", pady=(0, 16))

        tk.Label(mode_box, text="Modo de compresión:", bg="#282a36", fg="#f8f8f2", font=("Segoe UI", 10, "bold")).pack(side="left", padx=(0, 12))
        self.var_mode = tk.StringVar(value="extreme")
        
        r1 = tk.Radiobutton(mode_box, text="Extreme (Máximo Ratio SOTA)", variable=self.var_mode, value="extreme", bg="#282a36", fg="#f8f8f2", selectcolor="#44475a", activebackground="#282a36", activeforeground="#ff79c6")
        r1.pack(side="left", padx=8)
        r2 = tk.Radiobutton(mode_box, text="Balanced (Heurístico)", variable=self.var_mode, value="balanced", bg="#282a36", fg="#f8f8f2", selectcolor="#44475a", activebackground="#282a36", activeforeground="#ff79c6")
        r2.pack(side="left", padx=8)
        r3 = tk.Radiobutton(mode_box, text="Fast (Ultra Rápido)", variable=self.var_mode, value="fast", bg="#282a36", fg="#f8f8f2", selectcolor="#44475a", activebackground="#282a36", activeforeground="#ff79c6")
        r3.pack(side="left", padx=8)

        self.btn_compress = ttk.Button(frame, text="COMPRIMIR AHORA (.sb)", style="Action.TButton", command=self._start_compress)
        self.btn_compress.pack(fill="x", pady=(0, 12))

        self.progress_bar = ttk.Progressbar(frame, mode="determinate", style="Horizontal.TProgressbar")
        self.progress_bar.pack(fill="x", pady=(0, 8))

        self.lbl_status = tk.Label(frame, text="Listo para comprimir.", bg="#282a36", fg="#8be9fd", font=("Segoe UI", 9))
        self.lbl_status.pack(anchor="w")

        self.txt_results = tk.Text(frame, height=7, bg="#1e1e2e", fg="#50fa7b", font=("Consolas", 9), relief="flat", padx=8, pady=8)
        self.txt_results.pack(fill="both", expand=True, pady=(8, 0))

    def _build_decompress_tab(self):
        frame = ttk.Frame(self.tab_decompress, style="Card.TFrame", padding=20)
        frame.pack(fill="both", expand=True)

        lbl_sb = tk.Label(frame, text="Archivo Super Binary (.sb) a extraer:", bg="#282a36", fg="#f8f8f2", font=("Segoe UI", 10, "bold"))
        lbl_sb.pack(anchor="w")

        sb_box = tk.Frame(frame, bg="#282a36")
        sb_box.pack(fill="x", pady=(4, 12))

        self.var_decomp_src = tk.StringVar()
        self.entry_decomp_src = tk.Entry(sb_box, textvariable=self.var_decomp_src, bg="#44475a", fg="#ffffff", insertbackground="#ffffff", font=("Segoe UI", 10), relief="flat")
        self.entry_decomp_src.pack(side="left", fill="x", expand=True, ipady=6, padx=(0, 8))

        btn_sb = ttk.Button(sb_box, text="Seleccionar .sb...", style="Secondary.TButton", command=self._select_decomp_file)
        btn_sb.pack(side="left")

        lbl_out = tk.Label(frame, text="Carpeta de extracción:", bg="#282a36", fg="#f8f8f2", font=("Segoe UI", 10, "bold"))
        lbl_out.pack(anchor="w")

        out_box = tk.Frame(frame, bg="#282a36")
        out_box.pack(fill="x", pady=(4, 16))

        self.var_decomp_dst = tk.StringVar()
        self.entry_decomp_dst = tk.Entry(out_box, textvariable=self.var_decomp_dst, bg="#44475a", fg="#ffffff", insertbackground="#ffffff", font=("Segoe UI", 10), relief="flat")
        self.entry_decomp_dst.pack(side="left", fill="x", expand=True, ipady=6, padx=(0, 8))

        btn_out = ttk.Button(out_box, text="Carpeta...", style="Secondary.TButton", command=self._select_decomp_folder)
        btn_out.pack(side="left")

        self.btn_decompress = ttk.Button(frame, text="DESCOMPRIMIR Y VERIFICAR INTEGRIDAD", style="Action.TButton", command=self._start_decompress)
        self.btn_decompress.pack(fill="x", pady=(0, 12))

        self.decomp_progress = ttk.Progressbar(frame, mode="determinate", style="Horizontal.TProgressbar")
        self.decomp_progress.pack(fill="x", pady=(0, 8))

        self.lbl_decomp_status = tk.Label(frame, text="Listo para extraer.", bg="#282a36", fg="#8be9fd", font=("Segoe UI", 9))
        self.lbl_decomp_status.pack(anchor="w")

        self.txt_decomp_results = tk.Text(frame, height=7, bg="#1e1e2e", fg="#50fa7b", font=("Consolas", 9), relief="flat", padx=8, pady=8)
        self.txt_decomp_results.pack(fill="both", expand=True, pady=(8, 0))

    def _select_folder(self):
        path = filedialog.askdirectory(title="Seleccionar Carpeta a Comprimir")
        if path:
            self.var_source.set(path)
            self.var_dest.set(f"{path}.sb")

    def _select_file(self):
        path = filedialog.askopenfilename(title="Seleccionar Archivo o Programa")
        if path:
            self.var_source.set(path)
            base = os.path.splitext(path)[0]
            self.var_dest.set(f"{base}.sb")

    def _select_save_path(self):
        path = filedialog.asksaveasfilename(title="Guardar como archivo .sb", defaultextension=".sb", filetypes=[("Super Binary", "*.sb")])
        if path:
            self.var_dest.set(path)

    def _select_decomp_file(self):
        path = filedialog.askopenfilename(title="Seleccionar archivo .sb", filetypes=[("Super Binary", "*.sb")])
        if path:
            self.var_decomp_src.set(path)
            base = os.path.splitext(path)[0]
            self.var_decomp_dst.set(f"{base}_extraido")

    def _select_decomp_folder(self):
        path = filedialog.askdirectory(title="Seleccionar Carpeta de Destino")
        if path:
            self.var_decomp_dst.set(path)

    def _start_compress(self):
        src = self.var_source.get().strip()
        dst = self.var_dest.get().strip()

        if not src or not os.path.exists(src):
            messagebox.showerror("Error", "Debe seleccionar un archivo o carpeta válido.")
            return

        if not dst:
            dst = f"{src}.sb"
            self.var_dest.set(dst)

        mode_map = {
            "fast": CompressionMode.FAST,
            "balanced": CompressionMode.BALANCED,
            "extreme": CompressionMode.EXTREME,
        }
        mode = mode_map[self.var_mode.get()]

        self.btn_compress.config(state="disabled")
        self.txt_results.delete("1.0", tk.END)
        self.progress_bar["value"] = 0

        def worker():
            t0 = time.time()
            archiver = SBArchiver(mode=mode)
            try:
                def on_progress(phase, current, total, extra):
                    denom = max(1, total)
                    if phase == "scanned":
                        pct = min(95.0, (current / denom) * 95.0)
                        msg = f"Escaneando y procesando ({current}/{total}): {extra[:45]}"
                        self.after(0, lambda p=pct, m=msg: self._update_comp_progress(p, m))
                    elif phase == "compressed_block":
                        msg = f"Bloques generados: {current} | Ultimo algoritmo: {extra}"
                        self.after(0, lambda m=msg: self._update_comp_status_msg(m))

                stats = archiver.compress(src, dst, progress_cb=on_progress)
                elapsed = time.time() - t0

                res_text = (
                    f"[OK] Compresion Finalizada con Exito en {elapsed:.2f}s\n"
                    f"--------------------------------------------------\n"
                    f"Archivos:            {stats['files_count']}\n"
                    f"Tamano Original:     {format_bytes(stats['uncompressed_size'])}\n"
                    f"Tamano Comprimido:   {format_bytes(stats['compressed_size'])} (.sb)\n"
                    f"Ratio de Compresion: {stats['ratio_percent']:.2f}%\n"
                    f"Ahorro de Espacio:   {stats['savings_percent']:.2f}%\n"
                )
                self.after(0, lambda r=res_text: self._finish_compress(r))
            except Exception as e:
                err_msg = f"{type(e).__name__}: {str(e)}" if str(e) else f"Error: {type(e).__name__}"
                self.after(0, lambda err=err_msg: self._error_compress(err))

        threading.Thread(target=worker, daemon=True).start()

    def _update_comp_progress(self, val, msg):
        self.progress_bar["value"] = val
        self.lbl_status.config(text=msg)

    def _update_comp_status_msg(self, msg):
        self.lbl_status.config(text=msg)

    def _finish_compress(self, report):
        self.progress_bar["value"] = 100
        self.lbl_status.config(text="Compresión completada con éxito.")
        self.txt_results.insert(tk.END, report)
        self.btn_compress.config(state="normal")
        messagebox.showinfo("Completado", "El archivo .sb ha sido creado satisfactoriamente.")

    def _error_compress(self, err):
        self.lbl_status.config(text="Error durante la compresión.")
        self.txt_results.insert(tk.END, f"[ERROR] {err}\n")
        self.btn_compress.config(state="normal")
        messagebox.showerror("Fallo de compresión", err)

    def _start_decompress(self):
        src = self.var_decomp_src.get().strip()
        dst = self.var_decomp_dst.get().strip()

        if not src or not os.path.exists(src):
            messagebox.showerror("Error", "Debe seleccionar un archivo .sb existente.")
            return

        if not dst:
            dst = os.path.splitext(src)[0] + "_extraido"
            self.var_decomp_dst.set(dst)

        self.btn_decompress.config(state="disabled")
        self.txt_decomp_results.delete("1.0", tk.END)
        self.decomp_progress["value"] = 0

        def worker():
            t0 = time.time()
            archiver = SBArchiver()
            try:
                def on_progress(phase, current, total, extra):
                    denom = max(1, total)
                    if phase == "decompressed_block":
                        pct = min(70.0, (current / denom) * 70.0)
                        msg = f"Descomprimiendo flujo ({format_bytes(current)} / {format_bytes(total)}) [{extra}]"
                        self.after(0, lambda p=pct, m=msg: self._update_decomp_progress(p, m))
                    elif phase == "extracted":
                        pct = min(100.0, 70.0 + ((current / denom) * 30.0))
                        msg = f"Extrayendo archivo ({current}/{total}): {extra[:45]}"
                        self.after(0, lambda p=pct, m=msg: self._update_decomp_progress(p, m))

                manifest = archiver.decompress(src, dst, progress_cb=on_progress)
                elapsed = time.time() - t0

                res_text = (
                    f"[OK] Extraccion Completa e Integridad Verificada (SHA256+CRC32)\n"
                    f"--------------------------------------------------------------\n"
                    f"Archivos extraidos:  {len(manifest.files)}\n"
                    f"Tamano Total:        {format_bytes(manifest.total_uncompressed_size)}\n"
                    f"Tiempo:              {elapsed:.2f}s\n"
                    f"Destino:             {dst}\n"
                )
                self.after(0, lambda r=res_text: self._finish_decompress(r))
            except Exception as e:
                err_msg = f"{type(e).__name__}: {str(e)}" if str(e) else f"Error: {type(e).__name__}"
                self.after(0, lambda err=err_msg: self._error_decompress(err))

        threading.Thread(target=worker, daemon=True).start()

    def _update_decomp_progress(self, val, msg):
        self.decomp_progress["value"] = val
        self.lbl_decomp_status.config(text=msg)

    def _finish_decompress(self, report):
        self.decomp_progress["value"] = 100
        self.lbl_decomp_status.config(text="Extracción finalizada.")
        self.txt_decomp_results.insert(tk.END, report)
        self.btn_decompress.config(state="normal")
        messagebox.showinfo("Completado", "Archivos extraídos y verificados exitosamente.")

    def _error_decompress(self, err):
        self.lbl_decomp_status.config(text="Error durante la extracción.")
        self.txt_decomp_results.insert(tk.END, f"[ERROR] {err}\n")
        self.btn_decompress.config(state="normal")
        messagebox.showerror("Fallo de descompresión", err)

def main():
    initial = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else None
    app = SuperBinaryApp(initial_path=initial)
    app.mainloop()

if __name__ == "__main__":
    main()
