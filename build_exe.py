import os
import sys
import subprocess
from pathlib import Path

def build():
    base_dir = Path(__file__).resolve().parent
    dist_dir = base_dir / "dist"
    build_dir = base_dir / "build"

    os.environ["DJANGO_SETTINGS_MODULE"] = "core.settings.dev"

    print("=== Iniciando Empacotamento do Buscador de Músicas (EXE) ===")

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--name=BuscadorDeMusicas",
        "--onefile",
        "--noconsole",
        "--collect-all=core",
        "--collect-all=customtkinter",
        "--collect-all=finder_files",
        "--collect-all=ai",
        "--add-data=ai/prompts;ai/prompts",
        "--add-data=.env.example;.env.example",
        "--add-data=db.sqlite3;.",
        f"--workpath={build_dir}",
        f"--distpath={dist_dir}",
        "frontend_ctk/app.py"
    ]

    print("Comando PyInstaller:", " ".join(cmd))
    res = subprocess.run(cmd, cwd=base_dir)

    if res.returncode == 0:
        exe_path = dist_dir / "BuscadorDeMusicas.exe"
        print(f"\n[OK] Build concluido com sucesso! Executavel gerado em: {exe_path}")
    else:
        print(f"\n[ERRO] Erro no empacotamento. Codigo de saida: {res.returncode}")
        sys.exit(res.returncode)

if __name__ == "__main__":
    build()
