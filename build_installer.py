"""Build Windows installer for Plain language."""

import os
import sys
import subprocess
from pathlib import Path

def build_msi():
    """Build MSI installer using setuptools bdist_msi."""
    print("Building MSI installer...")
    try:
        try:
            import win32com.client  # type: ignore
            print("pywin32 found")
        except ImportError:
            print("Installing pywin32...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pywin32"])
    except Exception as e:
        print(f"Warning: {e}")
    
    subprocess.check_call([sys.executable, "setup.py", "bdist_msi"])
    print("MSI installer created in dist/ directory")
    return True

def build_exe():
    """Build EXE installer using PyInstaller."""
    print("Building EXE installer...")
    try:
        try:
            import PyInstaller  # type: ignore
        except ImportError:
            print("Installing PyInstaller...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
    except Exception as e:
        print(f"Warning: {e}")
    
    spec_content = """# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['plain/cli.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['plain', 'click', 'plain.compiler', 'plain.enhanced_transpiler', 'plain.runtime', 'plain.repl'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='plain',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
"""
    
    with open("plain.spec", "w") as f:
        f.write(spec_content)
    
    subprocess.check_call([sys.executable, "-m", "PyInstaller", "plain.spec", "--clean"])
    print("EXE created in dist/ directory")
    return True

if __name__ == "__main__":
    print("Plain Language Installer Builder")
    print("=" * 50)
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "msi":
            build_msi()
        elif sys.argv[1] == "exe":
            build_exe()
        else:
            print("Usage: python build_installer.py [msi|exe]")
    else:
        print("Choose installer type:")
        print("1. MSI (Windows Installer)")
        print("2. EXE (Standalone executable)")
        choice = input("Enter choice (1 or 2): ")
        
        if choice == "1":
            build_msi()
        elif choice == "2":
            build_exe()
        else:
            print("Invalid choice")

