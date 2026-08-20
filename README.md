# SmartBundle (.sb) 📦⚡

Archivador y compresor inteligente de alto rendimiento para Windows con preprocesadores avanzados (BCJ x86, Delta), motores de compresión múltiple (Zstandard Ultra, Brotli Max, LZMA2, PPMd) y verificación de integridad xxHash64.

---

## 📥 Descarga

Descarga la versión compilada lista para usar:

👉 **[Descargar última versión en Releases](../../releases/latest)**

1. Descarga `SmartBundle-Windows.zip`.
2. Descomprime el archivo.
3. Ejecuta `SmartBundle.exe` (Interfaz Gráfica) o utilízalo desde la consola mediante `sb_cli.exe`.

---

## 🚀 Características

- **Compresión Multi-Motor**:
  - `Zstandard Ultra`: Velocidad extrema y alta tasa de compresión.
  - `Brotli Max`: Optimizado para texto, datos web y código fuente.
  - `LZMA2 Extreme`: Máxima tasa de compresión para archivos grandes y binarios.
  - `PPMd`: Especializado en compresión de texto y logs sin pérdida.
- **Preprocesamiento Inteligente**: Filtros BCJ para ejecutables x86/x64 y transformaciones Delta para datos numéricos.
- **Integridad Segura**: Hashes de verificación xxHash64 por archivo y bloque.
- **Interfaz Gráfica Moderna**: Soporte Drag & Drop, selección de algoritmos y monitoreo de progreso.
- **Integración con Menú Contextual**: Comprimir y extraer directamente desde el explorador de Windows.

---

## 🛠️ Ejecución y Desarrollo

### Requisitos
- Python 3.10+
- Windows 10/11

### Instalación
```bash
pip install -r requirements.txt
```

### Ejecutar Interfaz Gráfica
```bash
python sb_gui.py
```

### Ejecutar CLI
```bash
# Comprimir
python sb_cli.py c ruta/carpeta -o salida.sb -m ultra

# Extraer
python sb_cli.py x salida.sb -o ruta/destino

# Listar contenido
python sb_cli.py l salida.sb

# Test de integridad
python sb_cli.py t salida.sb
```

### Compilar a ejecutable (.exe)
```bash
pip install pyinstaller
pyinstaller --noconfirm --onedir --windowed --icon "app_icon.ico" --name "SmartBundle" sb_gui.py
```
