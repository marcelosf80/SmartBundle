# tests/test_sb.py
import os
import shutil
import tempfile
import unittest
import hashlib

from sb_core import SBArchiver, CompressionMode

class TestSBArchiver(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.out_dir = tempfile.mkdtemp()
        
        # Crear dataset de prueba heterogéneo
        # 1. Archivo de texto repetitivo / código
        with open(os.path.join(self.test_dir, "code.py"), "w", encoding="utf-8") as f:
            f.write("def calculate_fibonacci(n):\n    if n <= 1: return n\n    return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)\n" * 200)

        # 2. JSON estructurado
        with open(os.path.join(self.test_dir, "data.json"), "w", encoding="utf-8") as f:
            f.write('{"users": [{"id": %d, "name": "User_%d", "active": true} for i in range(1000)]}' % (1, 1))

        # 3. Binario pseudo-ejecutable con instrucciones repetitivas
        with open(os.path.join(self.test_dir, "binary.bin"), "wb") as f:
            f.write(b"\xe8\x12\x34\x56\x78\x90\xe9\xaa\xbb\xcc\xdd" * 500)

        # 4. Subdirectorio con archivo vacío y archivo pequeño
        sub_dir = os.path.join(self.test_dir, "subdir")
        os.makedirs(sub_dir, exist_ok=True)
        with open(os.path.join(sub_dir, "empty.txt"), "wb") as f:
            pass
        with open(os.path.join(sub_dir, "notes.txt"), "w", encoding="utf-8") as f:
            f.write("Super Binary Archive Test Note\n" * 50)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)
        shutil.rmtree(self.out_dir, ignore_errors=True)

    def _verify_exact_match(self, orig_dir, extracted_dir):
        for root, _, files in os.walk(orig_dir):
            for f in files:
                orig_file = os.path.join(root, f)
                rel_path = os.path.relpath(orig_file, orig_dir)
                extracted_file = os.path.join(extracted_dir, rel_path)

                self.assertTrue(os.path.exists(extracted_file), f"Falta archivo extraído: {rel_path}")
                
                with open(orig_file, "rb") as f1, open(extracted_file, "rb") as f2:
                    h1 = hashlib.sha256(f1.read()).hexdigest()
                    h2 = hashlib.sha256(f2.read()).hexdigest()
                    self.assertEqual(h1, h2, f"Discrepancia hash en: {rel_path}")

    def test_compression_extreme(self):
        sb_file = os.path.join(self.out_dir, "test_extreme.sb")
        extract_path = os.path.join(self.out_dir, "extracted_extreme")
        
        archiver = SBArchiver(mode=CompressionMode.EXTREME)
        stats = archiver.compress(self.test_dir, sb_file)
        
        self.assertTrue(os.path.exists(sb_file))
        self.assertGreater(stats["compressed_size"], 0)
        self.assertLess(stats["compressed_size"], stats["uncompressed_size"])

        archiver.decompress(sb_file, extract_path)
        self._verify_exact_match(self.test_dir, extract_path)

    def test_compression_fast(self):
        sb_file = os.path.join(self.out_dir, "test_fast.sb")
        extract_path = os.path.join(self.out_dir, "extracted_fast")
        
        archiver = SBArchiver(mode=CompressionMode.FAST)
        archiver.compress(self.test_dir, sb_file)
        archiver.decompress(sb_file, extract_path)
        self._verify_exact_match(self.test_dir, extract_path)

    def test_inspect_manifest(self):
        sb_file = os.path.join(self.out_dir, "test_inspect.sb")
        archiver = SBArchiver(mode=CompressionMode.BALANCED)
        archiver.compress(self.test_dir, sb_file)

        manifest = archiver.inspect(sb_file)
        self.assertEqual(len(manifest.files), 5)

if __name__ == "__main__":
    unittest.main()
