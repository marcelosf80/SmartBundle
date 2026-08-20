# sb_cli.py
import argparse
import os
import sys
import time
import zipfile
import py7zr
import tarfile
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn
from rich.panel import Panel

from sb_core import SBArchiver, CompressionMode, AlgorithmID

console = Console()

def format_bytes(size: float) -> str:
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} PB"

def cmd_compress(args):
    source = args.source
    if not os.path.exists(source):
        console.print(f"[bold red]Error:[/bold red] La ruta '{source}' no existe.")
        sys.exit(1)

    output = args.output
    if not output:
        base_name = os.path.basename(os.path.normpath(source))
        output = f"{base_name}.sb"
    elif not output.endswith(".sb"):
        output = f"{output}.sb"

    mode_map = {
        "fast": CompressionMode.FAST,
        "balanced": CompressionMode.BALANCED,
        "extreme": CompressionMode.EXTREME,
    }
    mode = mode_map[args.mode.lower()]

    console.print(Panel(
        f"[bold cyan]Compresor Super Binary (.sb) v1.0[/bold cyan]\n"
        f"Origen: [yellow]{source}[/yellow]\n"
        f"Destino: [green]{output}[/green]\n"
        f"Modo: [magenta]{args.mode.upper()}[/magenta] (Optimización competitiva multihilo SOTA)",
        border_style="cyan"
    ))

    archiver = SBArchiver(mode=mode)
    start_time = time.time()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console
    ) as progress:
        task = progress.add_task("Procesando...", total=100)

        def progress_callback(phase, current, total, extra):
            denom = max(1, total)
            if phase == "scanned":
                progress.update(task, description=f"[cyan]Escaneando:[/cyan] {extra[:30]}", completed=(current / denom) * 30)
            elif phase == "compressed_block":
                pct = min(95.0, 30.0 + ((current / denom) * 65.0))
                progress.update(task, description=f"[green]Bloque {current} -> {extra}[/green]", completed=pct)

        stats = archiver.compress(source, output, progress_cb=progress_callback)
        progress.update(task, completed=100, description="[bold green]Finalizado con éxito[/bold green]")

    elapsed = time.time() - start_time
    
    table = Table(title="Resultados de Compresión (.sb)", style="cyan")
    table.add_column("Métrica", style="bold")
    table.add_column("Valor", style="green")
    
    table.add_row("Archivos empaquetados", str(stats["files_count"]))
    table.add_row("Bloques generados", str(stats["blocks_count"]))
    table.add_row("Tamaño original", format_bytes(stats["uncompressed_size"]))
    table.add_row("Tamaño comprimido (.sb)", format_bytes(stats["compressed_size"]))
    table.add_row("Ratio de compresión", f"{stats['ratio_percent']:.2f}%")
    table.add_row("Espacio ahorrado", f"{stats['savings_percent']:.2f}%")
    table.add_row("Tiempo transcurrido", f"{elapsed:.2f} segundos")
    
    console.print(table)

def cmd_decompress(args):
    source = args.source
    if not os.path.exists(source):
        console.print(f"[bold red]Error:[/bold red] El archivo '{source}' no existe.")
        sys.exit(1)

    dest = args.output
    if not dest:
        base_name = os.path.splitext(os.path.basename(source))[0]
        dest = f"{base_name}_extracted"

    console.print(Panel(
        f"[bold cyan]Descompresor Super Binary (.sb)[/bold cyan]\n"
        f"Archivo: [yellow]{source}[/yellow]\n"
        f"Destino: [green]{dest}[/green]",
        border_style="cyan"
    ))

    archiver = SBArchiver()
    start_time = time.time()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TimeElapsedColumn(),
        console=console
    ) as progress:
        task = progress.add_task("Descomprimiendo y verificando...", total=100)

        def progress_callback(phase, current, total, extra):
            if phase == "decompressed_block":
                pct = (current / total) * 70
                progress.update(task, description=f"[cyan]Descomprimiendo {extra}...[/cyan]", completed=pct)
            elif phase == "extracted":
                pct = 70 + ((current / total) * 30)
                progress.update(task, description=f"[green]Extrayendo:[/green] {extra[:30]}", completed=pct)

        manifest = archiver.decompress(source, dest, progress_cb=progress_callback)
        progress.update(task, completed=100, description="[bold green]Extracción e integridad verificadas al 100%[/bold green]")

    elapsed = time.time() - start_time
    console.print(f"[bold green][OK][/bold green] Extraidos {len(manifest.files)} archivos ({format_bytes(manifest.total_uncompressed_size)}) en {elapsed:.2f}s en '{dest}'")

def cmd_list(args):
    source = args.source
    archiver = SBArchiver()
    manifest = archiver.inspect(source)

    table = Table(title=f"Contenido del archivo: {os.path.basename(source)} (.sb)", style="cyan")
    table.add_column("Ruta", style="yellow")
    table.add_column("Tamaño Original", justify="right", style="green")
    table.add_column("CRC32", style="magenta")

    for f in manifest.files:
        table.add_row(f.path, format_bytes(f.size), f"{f.crc32:08X}")

    console.print(table)
    console.print(f"[bold]Total:[/bold] {len(manifest.files)} archivos, {format_bytes(manifest.total_uncompressed_size)}")

def cmd_benchmark(args):
    target = args.source
    if not os.path.exists(target):
        console.print(f"[bold red]Error:[/bold red] La ruta '{target}' no existe.")
        sys.exit(1)

    console.print(Panel(
        f"[bold cyan]BENCHMARK COMPARATIVO DE COMPRESIÓN[/bold cyan]\n"
        f"Objetivo de prueba: [yellow]{target}[/yellow]\n"
        f"Formatos a evaluar: [bold]ZIP (Deflate)[/bold], [bold]TAR.GZ (Gzip)[/bold], [bold]7Z (LZMA2 Ultra)[/bold], [bold].SB (Super Binary)[/bold]",
        border_style="magenta"
    ))

    # 1. Preparar archivos
    test_zip = "temp_bench.zip"
    test_targz = "temp_bench.tar.gz"
    test_7z = "temp_bench.7z"
    test_sb = "temp_bench.sb"

    results = []

    # Recolectar tamaño original
    from sb_core.manifest import scan_target
    files = scan_target(target)
    orig_size = sum(os.path.getsize(f) for f in files)

    # A) ZIP (Deflate estándar)
    t0 = time.time()
    with zipfile.ZipFile(test_zip, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        base = os.path.dirname(target) if os.path.isfile(target) else target
        for f in files:
            zf.write(f, os.path.relpath(f, base))
    t_zip = time.time() - t0
    s_zip = os.path.getsize(test_zip)
    results.append(("ZIP (Deflate Max)", s_zip, t_zip))

    # B) TAR.GZ
    t0 = time.time()
    with tarfile.open(test_targz, "w:gz", compresslevel=9) as tf:
        base = os.path.dirname(target) if os.path.isfile(target) else target
        for f in files:
            tf.add(f, arcname=os.path.relpath(f, base))
    t_tar = time.time() - t0
    s_tar = os.path.getsize(test_targz)
    results.append(("TAR.GZ (Gzip)", s_tar, t_tar))

    # C) 7-ZIP (LZMA2 Preset 9)
    t0 = time.time()
    with py7zr.SevenZipFile(test_7z, "w", filters=[{"id": py7zr.FILTER_LZMA2, "preset": 9}]) as sz:
        base = os.path.dirname(target) if os.path.isfile(target) else target
        for f in files:
            sz.write(f, os.path.relpath(f, base))
    t_7z = time.time() - t0
    s_7z = os.path.getsize(test_7z)
    results.append(("7-Zip (LZMA2 Ultra)", s_7z, t_7z))

    # D) .SB (Super Binary EXTREME)
    t0 = time.time()
    archiver = SBArchiver(mode=CompressionMode.EXTREME)
    stats_sb = archiver.compress(target, test_sb)
    t_sb = time.time() - t0
    s_sb = os.path.getsize(test_sb)
    results.append(("[bold cyan].SB (Super Binary)[/bold cyan]", s_sb, t_sb))

    # Limpiar archivos temporales de prueba
    for tmp in [test_zip, test_targz, test_7z, test_sb]:
        if os.path.exists(tmp):
            os.remove(tmp)

    table = Table(title="Resultado del Benchmark de Compresión", style="cyan")
    table.add_column("Formato / Algoritmo", style="bold")
    table.add_column("Tamaño Final", justify="right")
    table.add_column("Ratio (%)", justify="right")
    table.add_column("Ahorro vs Original", justify="right")
    table.add_column("Tiempo (s)", justify="right")

    for name, size, t in sorted(results, key=lambda x: x[1]):
        ratio = (size / orig_size * 100) if orig_size > 0 else 0
        savings = 100 - ratio
        table.add_row(
            name,
            format_bytes(size),
            f"{ratio:.2f}%",
            f"[bold green]{savings:.2f}%[/bold green]",
            f"{t:.2f}s"
        )

    console.print(table)

def main():
    parser = argparse.ArgumentParser(description="Super Binary (.sb) SOTA Compressor CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Compress
    p_comp = subparsers.add_parser("compress", aliases=["c"], help="Comprimir archivos o carpetas a formato .sb")
    p_comp.add_argument("source", help="Ruta del archivo o carpeta a comprimir")
    p_comp.add_argument("-o", "--output", help="Ruta del archivo .sb de salida")
    p_comp.add_argument("-m", "--mode", choices=["fast", "balanced", "extreme"], default="extreme", help="Modo de compresión (default: extreme)")
    p_comp.set_defaults(func=cmd_compress)

    # Decompress
    p_decomp = subparsers.add_parser("decompress", aliases=["x", "d"], help="Descomprimir y verificar archivo .sb")
    p_decomp.add_argument("source", help="Ruta del archivo .sb")
    p_decomp.add_argument("-o", "--output", help="Directorio de destino para la extracción")
    p_decomp.set_defaults(func=cmd_decompress)

    # List
    p_list = subparsers.add_parser("list", aliases=["l"], help="Listar contenido de archivo .sb")
    p_list.add_argument("source", help="Ruta del archivo .sb")
    p_list.add_argument("-o", "--output", help="Directorio de destino opcional")
    p_list.set_defaults(func=cmd_list)

    # Benchmark
    p_bench = subparsers.add_parser("benchmark", aliases=["b"], help="Comparar ratio de compresión contra ZIP, GZ y 7Z")
    p_bench.add_argument("source", help="Archivo o carpeta a comparar")
    p_bench.add_argument("-o", "--output", help="Directorio de destino opcional")
    p_bench.set_defaults(func=cmd_benchmark)

    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
