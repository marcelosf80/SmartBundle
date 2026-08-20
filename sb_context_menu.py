# sb_context_menu.py
import os
import sys
import winreg

def get_base_dir() -> str:
    return os.path.dirname(os.path.abspath(__file__))

def get_python_exe() -> str:
    return sys.executable

def install_context_menu():
    """Registra menú contextual en cascada para Windows 10/11."""
    base_dir = get_base_dir()
    cli_path = os.path.join(base_dir, "sb_cli.py")
    gui_path = os.path.join(base_dir, "sb_gui.py")
    icon_path = os.path.join(base_dir, "app_icon.ico")
    
    python_exe = get_python_exe()
    pythonw_exe = os.path.join(os.path.dirname(python_exe), "pythonw.exe")
    if not os.path.exists(pythonw_exe):
        pythonw_exe = python_exe

    if not os.path.exists(icon_path):
        icon_path = "shell32.dll,48"

    # Targets: Archivos (*) y Carpetas (Directory)
    targets = [
        r"Software\Classes\*\shell\SmartBundle",
        r"Software\Classes\Directory\shell\SmartBundle",
        r"Software\Classes\Directory\Background\shell\SmartBundle"
    ]

    for root_target in targets:
        # Menú principal en cascada
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, root_target)
        winreg.SetValueEx(key, "MUIVerb", 0, winreg.REG_SZ, "SmartBundle")
        winreg.SetValueEx(key, "Icon", 0, winreg.REG_SZ, icon_path)
        winreg.SetValueEx(key, "SubCommands", 0, winreg.REG_SZ, "")

        # Subopciones
        shell_key = winreg.CreateKey(key, "shell")

        # 1. Comprimir Ultra (Extremo)
        c1 = winreg.CreateKey(shell_key, "01_compress_ultra")
        winreg.SetValueEx(c1, "MUIVerb", 0, winreg.REG_SZ, "Comprimir en .sb (Ultra Extremo)")
        winreg.SetValueEx(c1, "Icon", 0, winreg.REG_SZ, icon_path)
        c1_cmd = winreg.CreateKey(c1, "command")
        winreg.SetValueEx(c1_cmd, "", 0, winreg.REG_SZ, f'"{python_exe}" "{cli_path}" compress "%1" -m extreme')

        # 2. Comprimir Rápido
        c2 = winreg.CreateKey(shell_key, "02_compress_fast")
        winreg.SetValueEx(c2, "MUIVerb", 0, winreg.REG_SZ, "Comprimir en .sb (Rápido Zstd)")
        winreg.SetValueEx(c2, "Icon", 0, winreg.REG_SZ, icon_path)
        c2_cmd = winreg.CreateKey(c2, "command")
        winreg.SetValueEx(c2_cmd, "", 0, winreg.REG_SZ, f'"{python_exe}" "{cli_path}" compress "%1" -m fast')

        # 3. Abrir en SmartBundle GUI
        c3 = winreg.CreateKey(shell_key, "03_open_gui")
        winreg.SetValueEx(c3, "MUIVerb", 0, winreg.REG_SZ, "Abrir en SmartBundle GUI")
        winreg.SetValueEx(c3, "Icon", 0, winreg.REG_SZ, icon_path)
        c3_cmd = winreg.CreateKey(c3, "command")
        winreg.SetValueEx(c3_cmd, "", 0, winreg.REG_SZ, f'"{pythonw_exe}" "{gui_path}"')

    # Registro de asociación para archivos .sb
    sb_ext = winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Classes\.sb")
    winreg.SetValueEx(sb_ext, "", 0, winreg.REG_SZ, "SmartBundleArchive")

    sb_class = winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Classes\SmartBundleArchive")
    winreg.SetValueEx(sb_class, "", 0, winreg.REG_SZ, "Archivo Comprimido SmartBundle")
    
    # Icono del tipo de archivo
    default_icon = winreg.CreateKey(sb_class, "DefaultIcon")
    winreg.SetValueEx(default_icon, "", 0, winreg.REG_SZ, icon_path)

    # Opciones de menú para archivos .sb
    sb_shell = winreg.CreateKey(sb_class, "shell")
    
    # Extraer aquí
    x_here = winreg.CreateKey(sb_shell, "01_extract_here")
    winreg.SetValueEx(x_here, "MUIVerb", 0, winreg.REG_SZ, "Extraer aquí")
    winreg.SetValueEx(x_here, "Icon", 0, winreg.REG_SZ, icon_path)
    x_here_cmd = winreg.CreateKey(x_here, "command")
    winreg.SetValueEx(x_here_cmd, "", 0, winreg.REG_SZ, f'"{python_exe}" "{cli_path}" decompress "%1"')

    # Listar / Verificar integridad
    x_list = winreg.CreateKey(sb_shell, "02_list")
    winreg.SetValueEx(x_list, "MUIVerb", 0, winreg.REG_SZ, "Verificar integridad y listar contenido")
    winreg.SetValueEx(x_list, "Icon", 0, winreg.REG_SZ, icon_path)
    x_list_cmd = winreg.CreateKey(x_list, "command")
    winreg.SetValueEx(x_list_cmd, "", 0, winreg.REG_SZ, f'"{python_exe}" "{cli_path}" list "%1"')

    # Abrir con GUI
    x_gui = winreg.CreateKey(sb_shell, "03_gui")
    winreg.SetValueEx(x_gui, "MUIVerb", 0, winreg.REG_SZ, "Abrir con SmartBundle")
    winreg.SetValueEx(x_gui, "Icon", 0, winreg.REG_SZ, icon_path)
    x_gui_cmd = winreg.CreateKey(x_gui, "command")
    winreg.SetValueEx(x_gui_cmd, "", 0, winreg.REG_SZ, f'"{pythonw_exe}" "{gui_path}"')

    # Acción por defecto al hacer doble clic: abrir GUI
    winreg.SetValueEx(sb_shell, "", 0, winreg.REG_SZ, "03_gui")

    print("[OK] Menu contextual en cascada y asociacion .sb instalados exitosamente.")

def uninstall_context_menu():
    """Elimina el menú contextual y asociaciones de registro."""
    keys_to_delete = [
        r"Software\Classes\*\shell\SmartBundle\shell\01_compress_ultra\command",
        r"Software\Classes\*\shell\SmartBundle\shell\01_compress_ultra",
        r"Software\Classes\*\shell\SmartBundle\shell\02_compress_fast\command",
        r"Software\Classes\*\shell\SmartBundle\shell\02_compress_fast",
        r"Software\Classes\*\shell\SmartBundle\shell\03_open_gui\command",
        r"Software\Classes\*\shell\SmartBundle\shell\03_open_gui",
        r"Software\Classes\*\shell\SmartBundle\shell",
        r"Software\Classes\*\shell\SmartBundle",
        
        r"Software\Classes\Directory\shell\SmartBundle\shell\01_compress_ultra\command",
        r"Software\Classes\Directory\shell\SmartBundle\shell\01_compress_ultra",
        r"Software\Classes\Directory\shell\SmartBundle\shell\02_compress_fast\command",
        r"Software\Classes\Directory\shell\SmartBundle\shell\02_compress_fast",
        r"Software\Classes\Directory\shell\SmartBundle\shell\03_open_gui\command",
        r"Software\Classes\Directory\shell\SmartBundle\shell\03_open_gui",
        r"Software\Classes\Directory\shell\SmartBundle\shell",
        r"Software\Classes\Directory\shell\SmartBundle",

        r"Software\Classes\Directory\Background\shell\SmartBundle\shell\01_compress_ultra\command",
        r"Software\Classes\Directory\Background\shell\SmartBundle\shell\01_compress_ultra",
        r"Software\Classes\Directory\Background\shell\SmartBundle\shell\02_compress_fast\command",
        r"Software\Classes\Directory\Background\shell\SmartBundle\shell\02_compress_fast",
        r"Software\Classes\Directory\Background\shell\SmartBundle\shell\03_open_gui\command",
        r"Software\Classes\Directory\Background\shell\SmartBundle\shell\03_open_gui",
        r"Software\Classes\Directory\Background\shell\SmartBundle\shell",
        r"Software\Classes\Directory\Background\shell\SmartBundle",

        r"Software\Classes\SmartBundleArchive\shell\01_extract_here\command",
        r"Software\Classes\SmartBundleArchive\shell\01_extract_here",
        r"Software\Classes\SmartBundleArchive\shell\02_list\command",
        r"Software\Classes\SmartBundleArchive\shell\02_list",
        r"Software\Classes\SmartBundleArchive\shell\03_gui\command",
        r"Software\Classes\SmartBundleArchive\shell\03_gui",
        r"Software\Classes\SmartBundleArchive\shell",
        r"Software\Classes\SmartBundleArchive\DefaultIcon",
        r"Software\Classes\SmartBundleArchive",
        r"Software\Classes\.sb",
    ]

    for k in keys_to_delete:
        try:
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, k)
        except FileNotFoundError:
            pass

    print("[OK] Menu contextual y asociaciones desinstalados.")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "uninstall":
        uninstall_context_menu()
    else:
        install_context_menu()
