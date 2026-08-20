# sb_context_menu.py
import os
import sys
import winreg

def get_installed_paths():
    """Detecta si se ejecuta desde Archivos de Programa o desde la carpeta de desarrollo."""
    prog_files = os.environ.get("ProgramFiles", r"C:\Program Files")
    default_install = os.path.join(prog_files, "SmartBundle")
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    if os.path.exists(os.path.join(default_install, "SmartBundle.exe")):
        exe_path = os.path.join(default_install, "SmartBundle.exe")
        icon_path = os.path.join(default_install, "app_icon.ico")
    elif os.path.exists(os.path.join(current_dir, "dist", "SmartBundle", "SmartBundle.exe")):
        exe_path = os.path.join(current_dir, "dist", "SmartBundle", "SmartBundle.exe")
        icon_path = os.path.join(current_dir, "app_icon.ico")
    elif os.path.exists(os.path.join(current_dir, "SmartBundle.exe")):
        exe_path = os.path.join(current_dir, "SmartBundle.exe")
        icon_path = os.path.join(current_dir, "app_icon.ico")
    else:
        # Fallback a python
        py_exe = sys.executable
        pyw_exe = os.path.join(os.path.dirname(py_exe), "pythonw.exe")
        if not os.path.exists(pyw_exe): pyw_exe = py_exe
        gui_p = os.path.join(current_dir, "sb_gui.py")
        cli_p = os.path.join(current_dir, "sb_cli.py")
        exe_path = f'"{pyw_exe}" "{gui_p}"'
        icon_path = os.path.join(current_dir, "app_icon.ico")
        return exe_path, exe_path, icon_path, False

    if not os.path.exists(icon_path):
        icon_path = exe_path

    return f'"{exe_path}"', f'"{exe_path}"', icon_path, True

def install_context_menu(target_hive=winreg.HKEY_CURRENT_USER):
    """
    Registra el menú contextual al estilo WinRAR:
    - SmartBundle >
      - Añadir al archivo...
      - Añadir a "<nombre>.sb" (Equilibrado)
      - Añadir a "<nombre>.sb" (Ultra Extremo)
    Y para archivos .sb:
      - Extraer ficheros...
      - Extraer aquí
      - Extraer en <carpeta>\
    """
    gui_cmd, cli_cmd, icon_p, is_exe = get_installed_paths()

    # Targets: Archivos (*), Carpetas (Directory) y Fondo de Explorador (Directory\Background)
    targets = [
        r"Software\Classes\*\shell\SmartBundle",
        r"Software\Classes\Directory\shell\SmartBundle"
    ]

    for root_target in targets:
        key = winreg.CreateKey(target_hive, root_target)
        winreg.SetValueEx(key, "MUIVerb", 0, winreg.REG_SZ, "SmartBundle")
        winreg.SetValueEx(key, "Icon", 0, winreg.REG_SZ, icon_p)
        winreg.SetValueEx(key, "SubCommands", 0, winreg.REG_SZ, "")

        shell_key = winreg.CreateKey(key, "shell")

        # 1. Añadir al archivo... (Abre la GUI)
        s1 = winreg.CreateKey(shell_key, "01_add_gui")
        winreg.SetValueEx(s1, "MUIVerb", 0, winreg.REG_SZ, "Añadir al archivo...")
        winreg.SetValueEx(s1, "Icon", 0, winreg.REG_SZ, icon_p)
        s1_cmd = winreg.CreateKey(s1, "command")
        winreg.SetValueEx(s1_cmd, "", 0, winreg.REG_SZ, f'{gui_cmd} "%1"')

        # 2. Añadir a archivo .sb (Equilibrado)
        s2 = winreg.CreateKey(shell_key, "02_add_fast")
        winreg.SetValueEx(s2, "MUIVerb", 0, winreg.REG_SZ, 'Añadir al archivo .sb (Equilibrado)')
        winreg.SetValueEx(s2, "Icon", 0, winreg.REG_SZ, icon_p)
        s2_cmd = winreg.CreateKey(s2, "command")
        if is_exe:
            current_dir = os.path.dirname(icon_p)
            cli_p = os.path.join(current_dir, "sb_cli.py")
            cmd = f'"{sys.executable}" "{cli_p}" compress "%1" -m balanced' if os.path.exists(cli_p) else f'{gui_cmd} "%1"'
        else:
            cmd = f'{cli_cmd} compress "%1" -m balanced'
        winreg.SetValueEx(s2_cmd, "", 0, winreg.REG_SZ, cmd)

        # 3. Añadir a archivo .sb (Ultra Extremo)
        s3 = winreg.CreateKey(shell_key, "03_add_ultra")
        winreg.SetValueEx(s3, "MUIVerb", 0, winreg.REG_SZ, 'Añadir al archivo .sb (Ultra Extremo)')
        winreg.SetValueEx(s3, "Icon", 0, winreg.REG_SZ, icon_p)
        s3_cmd = winreg.CreateKey(s3, "command")
        if is_exe:
            current_dir = os.path.dirname(icon_p)
            cli_p = os.path.join(current_dir, "sb_cli.py")
            cmd = f'"{sys.executable}" "{cli_p}" compress "%1" -m extreme' if os.path.exists(cli_p) else f'{gui_cmd} "%1"'
        else:
            cmd = f'{cli_cmd} compress "%1" -m extreme'
        winreg.SetValueEx(s3_cmd, "", 0, winreg.REG_SZ, cmd)

    # 4. Configurar asociación para archivos .sb
    sb_ext = winreg.CreateKey(target_hive, r"Software\Classes\.sb")
    winreg.SetValueEx(sb_ext, "", 0, winreg.REG_SZ, "SmartBundleArchive")

    sb_class = winreg.CreateKey(target_hive, r"Software\Classes\SmartBundleArchive")
    winreg.SetValueEx(sb_class, "", 0, winreg.REG_SZ, "Archivo Comprimido SmartBundle")
    
    default_icon = winreg.CreateKey(sb_class, "DefaultIcon")
    winreg.SetValueEx(default_icon, "", 0, winreg.REG_SZ, icon_p)

    sb_shell = winreg.CreateKey(sb_class, "shell")
    
    # Menú en cascada para .sb
    sb_main = winreg.CreateKey(sb_shell, "SmartBundle")
    winreg.SetValueEx(sb_main, "MUIVerb", 0, winreg.REG_SZ, "SmartBundle")
    winreg.SetValueEx(sb_main, "Icon", 0, winreg.REG_SZ, icon_p)
    winreg.SetValueEx(sb_main, "SubCommands", 0, winreg.REG_SZ, "")

    sb_sub_shell = winreg.CreateKey(sb_main, "shell")

    # Extraer ficheros... (Abre GUI)
    e1 = winreg.CreateKey(sb_sub_shell, "01_extract_gui")
    winreg.SetValueEx(e1, "MUIVerb", 0, winreg.REG_SZ, "Extraer ficheros...")
    winreg.SetValueEx(e1, "Icon", 0, winreg.REG_SZ, icon_p)
    e1_cmd = winreg.CreateKey(e1, "command")
    winreg.SetValueEx(e1_cmd, "", 0, winreg.REG_SZ, f'{gui_cmd} "%1"')

    # Extraer aquí
    e2 = winreg.CreateKey(sb_sub_shell, "02_extract_here")
    winreg.SetValueEx(e2, "MUIVerb", 0, winreg.REG_SZ, "Extraer aquí")
    winreg.SetValueEx(e2, "Icon", 0, winreg.REG_SZ, icon_p)
    e2_cmd = winreg.CreateKey(e2, "command")
    if is_exe:
        current_dir = os.path.dirname(icon_p)
        cli_p = os.path.join(current_dir, "sb_cli.py")
        cmd = f'"{sys.executable}" "{cli_p}" decompress "%1"' if os.path.exists(cli_p) else f'{gui_cmd} "%1"'
    else:
        cmd = f'{cli_cmd} decompress "%1"'
    winreg.SetValueEx(e2_cmd, "", 0, winreg.REG_SZ, cmd)

    # Doble clic abre con SmartBundle GUI
    open_cmd_key = winreg.CreateKey(sb_shell, "open")
    winreg.SetValueEx(open_cmd_key, "", 0, winreg.REG_SZ, "Abrir con SmartBundle")
    winreg.SetValueEx(open_cmd_key, "Icon", 0, winreg.REG_SZ, icon_p)
    open_cmd = winreg.CreateKey(open_cmd_key, "command")
    winreg.SetValueEx(open_cmd, "", 0, winreg.REG_SZ, f'{gui_cmd} "%1"')

    print(f"[OK] Menu contextual estilo WinRAR y asociacion .sb registrados con icono: {icon_p}")

def uninstall_context_menu(target_hive=winreg.HKEY_CURRENT_USER):
    """Elimina las entradas de registro creadas."""
    keys = [
        r"Software\Classes\*\shell\SmartBundle\shell\01_add_gui\command",
        r"Software\Classes\*\shell\SmartBundle\shell\01_add_gui",
        r"Software\Classes\*\shell\SmartBundle\shell\02_add_fast\command",
        r"Software\Classes\*\shell\SmartBundle\shell\02_add_fast",
        r"Software\Classes\*\shell\SmartBundle\shell\03_add_ultra\command",
        r"Software\Classes\*\shell\SmartBundle\shell\03_add_ultra",
        r"Software\Classes\*\shell\SmartBundle\shell",
        r"Software\Classes\*\shell\SmartBundle",
        
        r"Software\Classes\Directory\shell\SmartBundle\shell\01_add_gui\command",
        r"Software\Classes\Directory\shell\SmartBundle\shell\01_add_gui",
        r"Software\Classes\Directory\shell\SmartBundle\shell\02_add_fast\command",
        r"Software\Classes\Directory\shell\SmartBundle\shell\02_add_fast",
        r"Software\Classes\Directory\shell\SmartBundle\shell\03_add_ultra\command",
        r"Software\Classes\Directory\shell\SmartBundle\shell\03_add_ultra",
        r"Software\Classes\Directory\shell\SmartBundle\shell",
        r"Software\Classes\Directory\shell\SmartBundle",

        r"Software\Classes\SmartBundleArchive\shell\SmartBundle\shell\01_extract_gui\command",
        r"Software\Classes\SmartBundleArchive\shell\SmartBundle\shell\01_extract_gui",
        r"Software\Classes\SmartBundleArchive\shell\SmartBundle\shell\02_extract_here\command",
        r"Software\Classes\SmartBundleArchive\shell\SmartBundle\shell\02_extract_here",
        r"Software\Classes\SmartBundleArchive\shell\SmartBundle\shell",
        r"Software\Classes\SmartBundleArchive\shell\SmartBundle",
        r"Software\Classes\SmartBundleArchive\shell\open\command",
        r"Software\Classes\SmartBundleArchive\shell\open",
        r"Software\Classes\SmartBundleArchive\shell",
        r"Software\Classes\SmartBundleArchive\DefaultIcon",
        r"Software\Classes\SmartBundleArchive",
        r"Software\Classes\.sb",
    ]
    for k in keys:
        try:
            winreg.DeleteKey(target_hive, k)
        except FileNotFoundError:
            pass
    print("[OK] Entradas de menu contextual eliminadas.")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "uninstall":
        uninstall_context_menu()
    else:
        install_context_menu()
