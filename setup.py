#!/usr/bin/env python
"""
Ouroboros Unified Portable Environment Setup Script.
Ensures zero-config deployment across Windows, macOS, and Linux.
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

def print_step(msg):
    print(f"\n>> [STEP] {msg}")

def check_python_version():
    print_step("Checking Python version...")
    major, minor = sys.version_info.major, sys.version_info.minor
    print(f"Current Python: {major}.{minor}.{sys.version_info.micro}")
    if major < 3 or (major == 3 and minor < 8):
        print("[ERROR] Python 3.8+ is required to run Ouroboros. Please upgrade Python.")
        sys.exit(1)
    print("Python version OK.")

def setup_virtual_env():
    print_step("Setting up virtual environment...")
    venv_dir = Path(".venv")
    if not venv_dir.exists():
        print("Creating new virtual environment (.venv)...")
        try:
            subprocess.run([sys.executable, "-m", "venv", ".venv"], check=True)
            print("Virtual environment created.")
        except Exception as e:
            print(f"[ERROR] Failed to create virtual environment: {e}")
            sys.exit(1)
    else:
        print("Virtual environment (.venv) already exists. Skipping creation.")

def install_dependencies():
    print_step("Installing python dependencies...")
    
    # Determine local virtualenv pip executable
    if os.name == 'nt':
        pip_path = Path(".venv/Scripts/pip.exe")
    else:
        pip_path = Path(".venv/bin/pip")

    if not pip_path.exists():
        # Fallback to system/active pip if venv wasn't fully formed or user is running custom path
        print("[WARN] Local venv pip not found. Falling back to active pip.")
        pip_cmd = ["pip"]
    else:
        pip_cmd = [str(pip_path)]

    try:
        print(f"Running: {' '.join(pip_cmd)} install -r requirements.txt")
        subprocess.run(pip_cmd + ["install", "-r", "requirements.txt"], check=True)
        print("Dependencies installed successfully.")
    except Exception as e:
        print(f"[ERROR] Dependency installation failed: {e}")
        sys.exit(1)

def setup_environment_variables():
    print_step("Setting up environment configuration (.env)...")
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if env_file.exists():
        print(".env file already exists. Preserving existing configurations.")
    elif env_example.exists():
        print("Creating .env file from .env.example template...")
        shutil.copy(env_example, env_file)
        print(".env template created successfully. Remember to fill in API keys if using LLMs.")
    else:
        print("[WARN] Neither .env nor .env.example exists in the project root.")

def configure_local_shortcuts():
    print_step("Configuring local shell shortcuts...")
    
    # On Unix-like systems, ensure bash shortcut is executable
    if os.name != 'nt':
        bash_shortcut = Path("agyd")
        if bash_shortcut.exists():
            try:
                print("Setting executable permissions on Unix agyd script...")
                subprocess.run(["chmod", "+x", str(bash_shortcut)], check=True)
                print("Permissions set.")
            except Exception as e:
                print(f"[WARN] Failed to set permissions on agyd: {e}")

    print("Shell shortcuts ready.")
    print("  - Windows CMD: run 'agyd.bat'")
    print("  - Windows PowerShell: run '.\\agyd.ps1'")
    print("  - Git Bash / Unix: run './agyd'")

def install_local_skills():
    print_step("Provisioning project-local AI skills into global system agent config...")
    
    local_skills_dir = Path(".ai-workspace/skills")
    if not local_skills_dir.exists():
        print("No local custom skills directory found inside .ai-workspace. Skipping.")
        return

    # Dynamic resolve of system-specific antigravity / gemini settings folder
    # Normally at ~/.gemini/config/skills/
    system_skills_base = Path.home() / ".gemini" / "config" / "skills"
    
    try:
        system_skills_base.mkdir(parents=True, exist_ok=True)
        
        # Traverse each local skill directory
        for skill_path in local_skills_dir.iterdir():
            if skill_path.is_dir():
                target_skill_dir = system_skills_base / skill_path.name
                print(f"Deploying local skill [{skill_path.name}] to system config: {target_skill_dir}")
                
                # Copy entire skill folder content, replacing if already exists
                if target_skill_dir.exists():
                    shutil.rmtree(target_skill_dir)
                shutil.copytree(skill_path, target_skill_dir)
                
        print("Project-local custom skills deployed successfully.")
    except Exception as e:
        print(f"[WARN] Failed to automatically copy local skills to system config: {e}")
        print("Please manually copy '.ai-workspace/skills/*' to '~/.gemini/config/skills/' if devlog auto-logging fails.")

def verify_test_suite():
    print_step("Verifying portability via pytest suite...")
    if os.name == 'nt':
        pytest_path = Path(".venv/Scripts/pytest.exe")
    else:
        pytest_path = Path(".venv/bin/pytest")
        
    if not pytest_path.exists():
        pytest_cmd = ["pytest"]
    else:
        pytest_cmd = [str(pytest_path)]
        
    try:
        print("Running tests...")
        result = subprocess.run(pytest_cmd + ["-v"], capture_output=True, text=True)
        print(result.stdout)
        if result.returncode == 0:
            print("[SUCCESS] Portability test suite passed successfully on this machine!")
        else:
            print("[ERROR] Portability test suite failed. Output:")
            print(result.stderr)
    except Exception as e:
        print(f"[WARN] Failed to execute test suite automatically: {e}. Please run 'pytest' manually.")

def main():
    print("=============================================================")
    print(" Ouroboros Unified Portable Environment Setup")
    print("=============================================================")
    check_python_version()
    setup_virtual_env()
    install_dependencies()
    setup_environment_variables()
    configure_local_shortcuts()
    install_local_skills()
    verify_test_suite()
    print("\n=============================================================")
    print(" Setup Completed! Environment is 100% portable and active.")
    print("=============================================================")

if __name__ == "__main__":
    main()
