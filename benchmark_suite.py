# benchmark_suite.py
import os
import sys
import time
import shutil
import tempfile
import hashlib
from typing import Dict, Any, List

from sb_core import SBArchiver, CompressionMode

def generate_test_corpus(base_dir: str) -> Dict[str, int]:
    corpus_info = {}
    
    # 1. Código Fuente y Texto Repetitivo (1.2 MB)
    code_dir = os.path.join(base_dir, "source_code")
    os.makedirs(code_dir, exist_ok=True)
    for i in range(15):
        with open(os.path.join(code_dir, f"module_{i}.py"), "w", encoding="utf-8") as f:
            f.write(f"# Auto-generated module {i}\n" + """
class DataProcessor:
    def __init__(self, identifier: int):
        self.id = identifier
        self.cache = {}
        
    def process_record(self, record: dict) -> dict:
        result = {}
        for k, v in record.items():
            result[f"proc_{k}"] = str(v).upper().strip()
        return result
""" * 300)

    # 2. JSON & Logs Estructurados (2.5 MB)
    logs_dir = os.path.join(base_dir, "logs_and_json")
    os.makedirs(logs_dir, exist_ok=True)
    with open(os.path.join(logs_dir, "server_access.log"), "w", encoding="utf-8") as f:
        for i in range(12000):
            f.write(f"192.168.1.{i % 254} - - [20/Aug/2026:12:00:{i%60:02d} -0300] \"GET /api/v1/resource/{i % 50} HTTP/1.1\" 200 {1024 + (i*17)%4096} \"Mozilla/5.0\"\n")
    
    with open(os.path.join(logs_dir, "dataset.json"), "w", encoding="utf-8") as f:
        f.write('{"records": [' + ", ".join([f'{{"id": {i}, "status": "active", "score": {i*1.5:.2f}}}' for i in range(10000)]) + ']}')

    # 3. Binarios Simulados / X86 Opcodes (1.8 MB)
    bin_dir = os.path.join(base_dir, "binaries")
    os.makedirs(bin_dir, exist_ok=True)
    with open(os.path.join(bin_dir, "core_engine.dll"), "wb") as f:
        # Mezcla de patrones ejecutables (llamadas relativas x86 0xE8/0xE9 y tablas)
        pattern = b"\x55\x89\xe5\x83\xec\x10\xe8\x00\x00\x00\x00\x89\x45\xfc\x8b\x45\xfc\xc9\xc3" * 2000
        f.write(pattern * 20)

    # 4. Estructura anidada con archivos pequeños y vacíos
    nested_dir = os.path.join(base_dir, "nested", "level1", "level2")
    os.makedirs(nested_dir, exist_ok=True)
    for i in range(20):
        with open(os.path.join(nested_dir, f"config_{i}.ini"), "w", encoding="utf-8") as f:
            f.write(f"[Section_{i}]\nkey=value_{i}\nenabled=true\ntimeout=30\n" * 20)
    with open(os.path.join(nested_dir, ".empty"), "wb") as f:
        pass

    # Calcular tamaño total
    total_bytes = 0
    total_files = 0
    for root, _, files in os.walk(base_dir):
        for file in files:
            p = os.path.join(root, file)
            total_bytes += os.path.getsize(p)
            total_files += 1

    return {"total_bytes": total_bytes, "total_files": total_files}

def run_benchmark():
    temp_dir = tempfile.mkdtemp(prefix="sb_bench_")
    corpus_dir = os.path.join(temp_dir, "corpus")
    out_dir = os.path.join(temp_dir, "output")
    os.makedirs(out_dir, exist_ok=True)

    print("=== GENERANDO CORPUS DE PRUEBA ===")
    info = generate_test_corpus(corpus_dir)
    orig_mb = info["total_bytes"] / (1024 * 1024)
    print(f"Archivos: {info['total_files']} | Tamano total: {orig_mb:.2f} MB ({info['total_bytes']:,} bytes)")

    modes = [
        ("FAST", CompressionMode.FAST),
        ("BALANCED", CompressionMode.BALANCED),
        ("EXTREME", CompressionMode.EXTREME)
    ]

    results = []

    for name, mode in modes:
        print(f"\n--- Probando Modo: {name} ---")
        sb_path = os.path.join(out_dir, f"archive_{name.lower()}.sb")
        extract_dir = os.path.join(out_dir, f"extracted_{name.lower()}")

        # Compresión
        archiver = SBArchiver(mode=mode)
        t0 = time.perf_counter()
        stats = archiver.compress(corpus_dir, sb_path)
        comp_time = time.perf_counter() - t0

        comp_size = os.path.getsize(sb_path)
        comp_mb = comp_size / (1024 * 1024)
        ratio = (1 - (comp_size / info["total_bytes"])) * 100
        comp_speed = orig_mb / comp_time if comp_time > 0 else 0

        # Descompresión
        t0 = time.perf_counter()
        archiver.decompress(sb_path, extract_dir)
        decomp_time = time.perf_counter() - t0
        decomp_speed = orig_mb / decomp_time if decomp_time > 0 else 0

        # Verificación de integridad SHA-256 archivo por archivo
        integrity_ok = True
        for root, _, files in os.walk(corpus_dir):
            for file in files:
                orig_file = os.path.join(root, file)
                rel = os.path.relpath(orig_file, corpus_dir)
                ext_file = os.path.join(extract_dir, rel)
                if not os.path.exists(ext_file):
                    integrity_ok = False
                    break
                with open(orig_file, "rb") as f1, open(ext_file, "rb") as f2:
                    if hashlib.sha256(f1.read()).digest() != hashlib.sha256(f2.read()).digest():
                        integrity_ok = False
                        break

        results.append({
            "mode": name,
            "orig_size": info["total_bytes"],
            "comp_size": comp_size,
            "ratio": ratio,
            "comp_time": comp_time,
            "comp_speed": comp_speed,
            "decomp_time": decomp_time,
            "decomp_speed": decomp_speed,
            "integrity": "PASS" if integrity_ok else "FAIL"
        })

        print(f"Tamano Comprimido: {comp_mb:.2f} MB | Reduccion: {ratio:.1f}%")
        print(f"Velocidad Compresion: {comp_speed:.1f} MB/s ({comp_time:.3f} s)")
        print(f"Velocidad Descompresion: {decomp_speed:.1f} MB/s ({decomp_time:.3f} s)")
        print(f"Integridad SHA-256: {'OK (100% Exacto)' if integrity_ok else 'FALLO'}")

    shutil.rmtree(temp_dir, ignore_errors=True)
    return results

if __name__ == "__main__":
    run_benchmark()
