# sb_context_menu.py
import os
import sys
import winreg

def get_python_exe() -> str:
    return sys.executable

def install_context_menu():
    """Registra la opción en el menú contextual de Windows (HKEY_CURRENT_USER)."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    cli_path = os.path.join(script_dir, "sb_cli.py")
    python_exe = get_python_exe()

    # Comando para archivos y carpetas
    cmd_str = f'"{python_exe}" "{cli_path}" compress "%1"'

    # 1. Menú contextual para Archivos (*\shell\SuperBinary)
    key_file = winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Classes\*\shell\SuperBinary")
    winreg.SetValueEx(key_file, "", 0, winreg.REG_SZ, "Comprimir en Super Binary (.sb)")
    winreg.SetValueEx(key_file, "Icon", 0, winreg.REG_SZ, "shell32.dll,48")
    
    key_file_cmd = winreg.CreateKey(key_file, "command")
    winreg.SetValueEx(key_file_cmd, "", 0, winreg.REG_SZ, cmd_str)

    # 2. Menú contextual para Carpetas (Directory\shell\SuperBinary)
    key_dir = winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Classes\Directory\shell\SuperBinary")
    winreg.SetValueEx(key_dir, "", 0, winreg.REG_SZ, "Comprimir en Super Binary (.sb)")
    winreg.SetValueEx(key_dir, "Icon", 0, winreg.REG_SZ, "shell32.dll,48")
    
    key_dir_cmd = winreg.CreateKey(key_dir, "command")
    winreg.SetValueEx(key_dir_cmd, "", 0, winreg.REG_SZ, cmd_str)

    # 3. Menú contextual para Descomprimir archivos .sb (.sb\shell\ExtractSB)
    key_sb = winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Classes\.sb\shell\ExtractSB")
    winreg.SetValueEx(key_sb, "", 0, winreg.REG_SZ, "Descomprimir archivo .sb")
    winreg.SetValueEx(key_sb, "Icon", 0, winreg.REG_SZ, "shell32.dll,48")

    key_sb_cmd = winreg.CreateKey(key_sb, "command")
    decomp_cmd = f'"{python_exe}" "{cli_path}" decompress "%1"'
    winreg.SetValueEx(key_sb_cmd, "", 0, winreg.REG_SZ, decomp_cmd)

    print("[OK] Menu contextual de Windows registrado correctamente (Archivos, Carpetas y .sb).")

def uninstall_context_menu():
    """Elimina las entradas del registro del menú contextual."""
    paths = [
        r"Software\Classes\*\shell\SuperBinary\command",
        r"Software\Classes\*\shell\SuperBinary",
        r"Software\Classes\Directory\shell\SuperBinary\command",
        r"Software\Classes\Directory\shell\SuperBinary",
        r"Software\Classes\.sb\shell\ExtractSB\command",
        r"Software\Classes\.sb\shell\ExtractSB",
    ]
    for p in paths:
        try:
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, p)
        except FileNotFoundError:
            pass
    print("[OK] Menu contextual desinstalado del sistema.")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "uninstall":
        uninstall_context_menu()
    else:
        install_context_menu()
