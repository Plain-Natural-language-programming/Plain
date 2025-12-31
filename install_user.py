"""Install Plain Language to user directory."""

import os
import sys
import subprocess
from pathlib import Path

def main():
    print("Installing Plain Language to User Directory")
    print("=" * 50)
    
    project_root = Path(__file__).parent.absolute()
    print(f"Project directory: {project_root}")
    
    print("\nInstalling Plain Language...")
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "--user", "-e", str(project_root)],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print("Installation successful!")
        
        version = f"{sys.version_info.major}{sys.version_info.minor}"
        scripts_path = Path.home() / "AppData" / "Roaming" / "Python" / f"Python{version}" / "Scripts"
        
        print(f"\nScripts installed to: {scripts_path}")
        
        import winreg
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment", 0, winreg.KEY_READ | winreg.KEY_WRITE)
            try:
                current_path, _ = winreg.QueryValueEx(key, "Path")
            except FileNotFoundError:
                current_path = ""
            
            scripts_str = str(scripts_path)
            if scripts_str not in current_path:
                new_path = current_path + ";" + scripts_str if current_path else scripts_str
                winreg.SetValueEx(key, "Path", 0, winreg.REG_EXPAND_SZ, new_path)
                print("\nAdded to user PATH")
                print("Please restart PowerShell/VS Code for changes to take effect!")
            else:
                print("\nAlready in user PATH")
            
            winreg.CloseKey(key)
        except Exception as e:
            print(f"\nWarning: Could not update PATH automatically: {e}")
            print(f"Please manually add to PATH: {scripts_path}")
        
        print("\nTesting installation...")
        env = os.environ.copy()
        env["Path"] = os.environ.get("Path", "") + ";" + str(scripts_path)
        result = subprocess.run(["plain", "--version"], capture_output=True, text=True, env=env)
        
        if result.returncode == 0:
            print(result.stdout.strip())
            print("\nPlain Language is now installed!")
            print("\nIf 'plain' command doesn't work, restart PowerShell/VS Code.")
        else:
            print("Warning: plain command not found in current session")
            print("Restart PowerShell/VS Code to use the 'plain' command")
    else:
        print("\nInstallation failed!")
        print(result.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()

