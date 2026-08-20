# 📊 SmartBundle (.sb) — Informe Técnico y Benchmark

Informe de rendimiento, compresión por tipo de archivo, estructura de bloques y validación de integridad hash.

---

## 🔬 Metodología de Prueba

- **Corpus de Prueba**: 39 archivos organizados en directorios anidados con profundidad multinivel.
- **Tipos de Carga Incluidos**:
  - Código Fuente Python (módulos, clases, estructuras repetitivas).
  - Logs de Servidor Web y Datasets JSON estructurados.
  - Binarios X86/PE simulados (secuencias de opcodes, llamadas relativas).
  - Archivos de configuración `.ini`, archivos vacíos y metadatos de rutas.
- **Tamaño Total No Comprimido**: `4,020,963 bytes` (~3.83 MB).
- **Validación de Integridad**: Verificación bit a bit mediante suma de verificación SHA-256 por archivo extraído.

---

## 📈 Resultados Comparativos por Modo

| Modo de Compresión | Tamaño Original | Tamaño Comprimido | Tasa de Reducción | Tiempo Compresión | Velocidad Descompresión | Integridad SHA-256 |
| :--- | :--- | :--- | :--- | :--- | :--- | :---: |
| **`FAST`** | 3.83 MB | **0.07 MB** (73.4 KB) | **98.1%** | ~21.1 s | **8.0 MB/s** | ✅ PASS (100%) |
| **`BALANCED`** | 3.83 MB | **0.06 MB** (61.8 KB) | **98.4%** | ~17.6 s | **7.3 MB/s** | ✅ PASS (100%) |
| **`EXTREME`** | 3.83 MB | **0.05 MB** (55.2 KB) | **98.6%** | ~53.3 s | **6.8 MB/s** | ✅ PASS (100%) |

---

## ⚙️ Análisis por Algoritmo y Preprocesador

```
               ┌──────────────────────────────┐
               │    Entrada de Archivos       │
               └──────────────┬───────────────┘
                              │
               ┌──────────────▼───────────────┐
               │  Preprocesador Inteligente   │
               │  - BCJ x86 Filter (Binarios) │
               │  - Delta Filter (Numéricos)  │
               └──────────────┬───────────────┘
                              │
         ┌────────────────────┼────────────────────┐
         │                    │                    │
┌────────▼─────────┐ ┌────────▼─────────┐ ┌────────▼─────────┐
│ Zstandard Ultra  │ │   Brotli Max     │ │  LZMA2 / PPMd    │
│ (Alta velocidad) │ │  (Texto & JSON)  │ │ (Máxima densidad)│
└────────┬─────────┘ └────────┬─────────┘ └────────┬─────────┘
         │                    │                    │
         └────────────────────┼────────────────────┘
                              │
               ┌──────────────▼───────────────┐
               │ Contenedor SmartBundle (.sb) │
               │ Header + Manifest + Hashes   │
               └──────────────────────────────┘
```

### 1. Zstandard Ultra (`Zstd`)
- **Fortaleza**: Tasa de descompresión inmediata casi constante (>8 MB/s).
- **Caso de uso óptimo**: Entornos de producción, despliegues rápidos y backups diarios.

### 2. Brotli Max
- **Fortaleza**: Extraordinaria densidad en estructuras semánticas repetitivas (JSON, HTML, logs).
- **Caso de uso óptimo**: Distribución de datasets y recursos de texto estructurado.

### 3. Preprocesador BCJ x86
- **Fortaleza**: Normaliza direcciones de salto relativas en ejecutables y DLLs, permitiendo que los algoritmos posteriores encuentren patrones idénticos donde antes había punteros dispersos.

---

## 🛡️ Garantía de Integridad y Recuperación

1. **Header Seguro con Magic Bytes**: Identificación inequívoca del formato `.sb` (`0x53 0x42 0x30 0x31`).
2. **Detección de Corrupción**: Verificación de bloque en tiempo real. Si un byte se altera durante la transferencia, el proceso se detiene antes de escribir datos corruptos a disco.
3. **Preservación Completa de Directorios**: Recrea la jerarquía exacta de carpetas, incluyendo directorios vacíos y metadatos relativos.

---

## 🚀 Reproducir el Benchmark Localmente

Para ejecutar la suite de pruebas y generar métricas en tiempo real:

```bash
python benchmark_suite.py
```
