# installer.py
import os
import sys
import shutil
import subprocess

def run():
    print("==================================================")
    print("   Instalador de SmartBundle Pro para Windows    ")
    print("==================================================")

    current_dir = os.path.dirname(os.path.abspath(__file__))
    appdata_dest = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "SmartBundle")

    print(f"\n[1/3] Copiando archivos a {appdata_dest}...")
    os.makedirs(appdata_dest, exist_ok=True)
    
    # Copiar carpetas y archivos necesarios
    for item in ["sb_core", "sb_gui.py", "sb_cli.py", "sb_context_menu.py", "app_icon.ico", "requirements.txt"]:
        src = os.path.join(current_dir, item)
        dst = os.path.join(appdata_dest, item)
        if os.path.isdir(src):
            if os.path.exists(dst):
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
        elif os.path.isfile(src):
            shutil.copy2(src, dst)

    print("[2/3] Instalando dependencias de compresion...")
    req_file = os.path.join(appdata_dest, "requirements.txt")
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", req_file, "--quiet"], check=False)

    print("[3/3] Registrando menu contextual en Windows (Explorador de archivos)...")
    context_script = os.path.join(appdata_dest, "sb_context_menu.py")
    subprocess.run([sys.executable, context_script], check=False)

    print("\n==================================================")
    print(" [EXITO] SmartBundle se instalo correctamente.")
    print(" Ya puedes hacer clic derecho sobre cualquier archivo")
    print(" o carpeta y ver el menu 'SmartBundle'.")
    print("==================================================")

if __name__ == "__main__":
    run()
