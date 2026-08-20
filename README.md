# SmartBundle (.sb) 📦⚡

Archivador y compresor inteligente de alto rendimiento para Windows con preprocesadores avanzados (BCJ x86, Delta), motores de compresión múltiple (Zstandard Ultra, Brotli Max, LZMA2, PPMd) y verificación de integridad bit a bit con SHA-256 / xxHash64.

---

## 📥 Descarga

Descarga la versión compilada lista para usar en Windows (sin necesidad de instalar Python):

👉 **[Descargar última versión en Releases](../../releases/latest)**

1. Descarga `SmartBundle-Windows.zip`.
2. Descomprime el archivo.
3. Ejecuta `SmartBundle.exe` (Interfaz Gráfica) o utilízalo desde la consola mediante `sb_cli.exe`.

---

## 📊 Rendimiento y Benchmark

Pruebas realizadas sobre un corpus heterogéneo (código fuente, JSON/logs estructurados, binarios x86/PE y carpetas multinivel con 39 archivos):

| Modo | Reducción | Velocidad Descompresión | Integridad SHA-256 |
| :--- | :---: | :---: | :---: |
| **`FAST`** | **98.1%** | **8.0 MB/s** | ✅ PASS (100%) |
| **`BALANCED`** | **98.4%** | **7.3 MB/s** | ✅ PASS (100%) |
| **`EXTREME`** | **98.6%** | **6.8 MB/s** | ✅ PASS (100%) |

👉 **[Ver Informe Técnico Completo y Metodología (BENCHMARK_REPORT.md)](./BENCHMARK_REPORT.md)**

---

## 🚀 Características

- **Compresión Multi-Motor**:
  - `Zstandard Ultra`: Velocidad extrema y alta tasa de compresión.
  - `Brotli Max`: Optimizado para texto, datos web y código fuente.
  - `LZMA2 Extreme`: Máxima densidad para archivos grandes y binarios.
  - `PPMd`: Especializado en compresión de texto y logs sin pérdida.
- **Preprocesamiento Inteligente**: Filtros BCJ para ejecutables x86/x64 y transformaciones Delta para datos numéricos.
- **Integridad Segura**: Hashes de verificación por archivo y bloque con comprobación automática.
- **Interfaz Gráfica Moderna**: Soporte Drag & Drop, selección de algoritmos y monitoreo de progreso.
- **Integración con Menú Contextual**: Comprimir y extraer directamente desde el explorador de Windows.

---

## 🛠️ Ejecución y Desarrollo

### Requisitos
- Python 3.10+
- Windows 10/11

### Instalación de dependencias
```bash
pip install -r requirements.txt
```

### Ejecutar Interfaz Gráfica
```bash
python sb_gui.py
```

### Ejecutar CLI
```bash
# Comprimir carpeta o archivos
python sb_cli.py c ruta/carpeta -o salida.sb -m ultra

# Extraer archivo .sb
python sb_cli.py x salida.sb -o ruta/destino

# Listar contenido
python sb_cli.py l salida.sb

# Test de integridad
python sb_cli.py t salida.sb
```

### Ejecutar Suite de Pruebas y Benchmark
```bash
# Tests unitarios
python -m unittest discover -s tests

# Benchmark completo de velocidad y ratio
python benchmark_suite.py
```
