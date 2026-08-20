#!/usr/bin/env python3
"""
Latigo Student — Build Script (Nuitka Only - No Obfuscation)
Auto-creates missing __init__.py files for packages
FIXED: Added explicit account modules (like teacher version)
"""
import os
import sys
import shutil
import subprocess
from pathlib import Path

# ── Config ──
APP_NAME = "LatigoStudent"
ENTRY_POINT = "main.py"
ICON_FILE = "latigo.png"
OUTPUT_DIR = "dist"
PYTHON = sys.executable

# ============================================================
# DATA_DIRS: المجلدات التي سيتم نسخها كبيانات
# ============================================================
DATA_DIRS = [
    "account",
    "Attention",
    "Behavioral",
    "classroom",
    "icons",
    "sounds",
    "teacherselector",
]

# ============================================================
# PACKAGES: الحزم (المجلدات) التي سيتم تضمينها
# ============================================================
PACKAGES = [
    "account",
    "Attention",
    "Behavioral",
    "classroom",
    "teacherselector",
]

# ============================================================
# ROOT_MODULES: ملفات بايثون منفصلة في الجذر
# ============================================================
ROOT_MODULES = [
    "config",
    "token_manager",
    "ui",
    "quiz",
    "notification",
]

# ============================================================
# PACKAGES_WITH_INIT: المجلدات التي تحتاج __init__.py
# ============================================================
PACKAGES_WITH_INIT = [
    "account",
    "Attention",
    "Behavioral",
    "classroom",
    "teacherselector",
]

def ensure_init_files():
    """Auto-create __init__.py for all package folders if missing."""
    print("[INIT] Checking for missing __init__.py files...")
    for pkg in PACKAGES_WITH_INIT:
        pkg_path = Path(pkg)
        if pkg_path.exists() and pkg_path.is_dir():
            init_file = pkg_path / "__init__.py"
            if not init_file.exists():
                print(f"   Creating {init_file}")
                with open(init_file, "w") as f:
                    f.write(f'# {pkg} package\n')
            else:
                print(f"   {init_file} already exists")

    # Also ensure account/ subdirectories have __init__.py
    account_dir = Path("account")
    if account_dir.exists():
        for subdir in account_dir.iterdir():
            if subdir.is_dir() and not subdir.name.startswith("__"):
                init_file = subdir / "__init__.py"
                if not init_file.exists():
                    print(f"   Creating {init_file}")
                    with open(init_file, "w") as f:
                        f.write(f'# {subdir.name} sub-package\n')

def shell(cmd, cwd=None):
    """Run a command and stream output."""
    print(f"\n>>> {' '.join(cmd)}")
    subprocess.run(cmd, cwd=cwd, check=True)

def clean():
    print("[CLEAN] Cleaning old builds...")
    for d in [OUTPUT_DIR, f"{APP_NAME}.build", f"{APP_NAME}.dist", f"{APP_NAME}.onefile-build", ".nuitka"]:
        p = Path(d)
        if p.exists():
            shutil.rmtree(p, ignore_errors=True)
            print(f"   removed {d}")

def run_nuitka():
    print("\n[NUITKA] Compiling with Nuitka...")

    nuitka = [
        PYTHON, "-m", "nuitka",
        "--standalone",
        "--enable-plugin=pyside6",
        "--enable-plugin=tk-inter",
        "--windows-console-mode=disable",
        "--windows-icon-from-ico=" + ICON_FILE,
        "--company-name=Latigo",
        "--product-name=Latigo Student",
        "--file-version=1.0.0.0",
        "--product-version=1.0.0",
        "--output-dir=" + OUTPUT_DIR,
        "--output-filename=" + APP_NAME,
        "--follow-imports",
        "--jobs=2",
        "--assume-yes-for-downloads",
        "--prefer-source-code",

        # Skip PyMuPDF (fitz) completely
        "--nofollow-import-to=fitz",
        "--nofollow-import-to=PyMuPDF",
        "--nofollow-import-to=PyPDF2",
        "--nofollow-import-to=pdf2image",

        # ============================================================
        # ✅ تضمين cryptography
        # ============================================================
        "--include-package=cryptography",
        "--include-package=cryptography.hazmat",
        "--include-package=cryptography.hazmat.primitives",
        "--include-package=cryptography.hazmat.primitives.kdf",
        "--include-package=cryptography.fernet",

        # ✅ تضمين requests وتبعياتها
        "--include-package=requests",
        "--include-package=urllib3",
        "--include-package=charset_normalizer",
        "--include-package=certifi",
        "--include-package=idna",

        # ✅ تضمين websockets
        "--include-package=websockets",

        # ✅ OpenCV (cv2) و MediaPipe
        "--include-package=cv2",
        "--include-package=mediapipe",

        # ============================================================
        # ✅ تضمين account بشكل صريح (مثل نسخة المعلم)
        # ============================================================
        "--include-package=account",
        "--include-module=account.account_config",
        "--include-module=account.ApiWorker",
        "--include-module=account.LoginWindow",
        "--include-module=account.MultiStepFormWindow",
        "--include-module=account.ModernAccountPage",
        "--include-module=account.SoundManager",
        "--include-module=account.ToggleSwitch",
        "--include-module=account.subscription",
        "--include-module=account.TeacherProfileManager",
        "--include-module=account.uploadervideo",
        "--include-module=account.client2",

        # ✅ تضمين PySide6 بشكل صريح
        "--include-package=PySide6",
        "--include-package=PySide6.QtCore",
        "--include-package=PySide6.QtGui",
        "--include-package=PySide6.QtWidgets",
        "--include-package=PySide6.QtSvg",
        "--include-package=PySide6.QtSvgWidgets",
        "--include-package=PySide6.QtNetwork",
        "--include-package=PySide6.QtPdf",
        "--include-package=PySide6.QtPdfWidgets",
        "--include-package=PySide6.QtWebEngineCore",
        "--include-package=PySide6.QtWebEngineWidgets",
        "--include-package=PySide6.QtWebChannel",
    ]

    # Force-include packages
    for pkg in PACKAGES:
        nuitka.append(f"--include-package={pkg}")

    # Include package data
    for pkg in PACKAGES:
        nuitka.append(f"--include-package-data={pkg}")

    # Include root-level modules
    print("\n[INCLUDE] Adding root-level modules:")
    for mod in ROOT_MODULES:
        mod_file = Path(f"{mod}.py")
        if mod_file.exists():
            print(f"   {mod}.py")
            nuitka.append(f"--include-module={mod}")
        else:
            print(f"   ⚠️ {mod}.py not found (skipping)")

    # Ship asset folders
    for d in DATA_DIRS:
        if Path(d).exists():
            nuitka.append(f"--include-data-dir={d}={d}")
        else:
            print(f"   [WARNING] skipping missing data dir: {d}")

    # Entry point is main.py
    nuitka.append(str(Path(ENTRY_POINT)))

    shell(nuitka)
    print(f"\n[SUCCESS] Build complete! Output: {OUTPUT_DIR}/{APP_NAME}.dist/")

def main():
    try:
        clean()
        ensure_init_files()
        run_nuitka()
        print("\n[INFO] You can now zip the folder:")
        print(f"   {Path(OUTPUT_DIR, APP_NAME + '.dist').absolute()}")
    except subprocess.CalledProcessError as e:
        print(f"\n[ERROR] Build failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
