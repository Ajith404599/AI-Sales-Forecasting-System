#!/usr/bin/env python3
"""
Product & Analytics Management System - Unified Service Runner
Launches both the FastAPI backend and the Streamlit frontend with a single command.
"""

import argparse
import os
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path

# Enable ANSI escape sequences on Windows console
if sys.platform == "win32":
    os.system("")

# ANSI Color codes for clean formatted logs
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"


def print_banner(backend_port: int, frontend_port: int, host: str):
    banner = f"""
{CYAN}{BOLD}========================================================================{RESET}
{GREEN}{BOLD}   ⚡ Product & Analytics Management System - Unified Runner{RESET}
{CYAN}{BOLD}========================================================================{RESET}
  {BOLD}* Backend API (FastAPI):{RESET}    {CYAN}http://{host}:{backend_port}{RESET}
  {BOLD}* API Swagger Docs:{RESET}         {CYAN}http://{host}:{backend_port}/docs{RESET}
  {BOLD}* Frontend UI (Streamlit):{RESET}  {GREEN}http://localhost:{frontend_port}{RESET}
{CYAN}{BOLD}========================================================================{RESET}
  {DIM}Press {RESET}{YELLOW}{BOLD}Ctrl + C{RESET}{DIM} at any time to gracefully stop all services.{RESET}
{CYAN}{BOLD}========================================================================{RESET}
"""
    print(banner, flush=True)


def get_python_executable(root_dir: Path) -> str:
    """Find virtualenv python if available, otherwise use sys.executable."""
    if sys.platform == "win32":
        venv_python = root_dir / ".venv" / "Scripts" / "python.exe"
    else:
        venv_python = root_dir / ".venv" / "bin" / "python"

    if venv_python.exists():
        return str(venv_python)
    return sys.executable


def stream_output(process: subprocess.Popen, prefix: str, color: str):
    """Stream subprocess stdout/stderr line by line with formatted prefix."""
    try:
        if process.stdout:
            for line in iter(process.stdout.readline, b""):
                if not line:
                    break
                decoded = line.decode("utf-8", errors="replace").rstrip()
                if decoded:
                    print(f"{color}{prefix}{RESET} {decoded}", flush=True)
    except Exception:
        pass


def terminate_process_tree(proc: subprocess.Popen):
    """Terminate process and all child processes cleanly across platforms."""
    if proc is None or proc.poll() is not None:
        return

    pid = proc.pid
    if sys.platform == "win32":
        try:
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(pid)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False
            )
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass
    else:
        try:
            proc.terminate()
            proc.wait(timeout=2)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass


def main():
    parser = argparse.ArgumentParser(
        description="Run both FastAPI backend and Streamlit frontend concurrently."
    )
    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Host for FastAPI backend (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--backend-port",
        type=int,
        default=8000,
        help="Port for FastAPI backend (default: 8000)",
    )
    parser.add_argument(
        "--frontend-port",
        type=int,
        default=8501,
        help="Port for Streamlit frontend (default: 8501)",
    )
    parser.add_argument(
        "--no-reload",
        action="store_true",
        help="Disable auto-reload on backend code changes",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run Streamlit in headless mode (do not auto-open browser)",
    )

    args = parser.parse_args()

    root_dir = Path(__file__).resolve().parent
    backend_dir = root_dir / "app" / "backend"
    frontend_dir = root_dir / "app" / "frontend"

    if not backend_dir.exists():
        print(f"{RED}Error: Backend directory not found at {backend_dir}{RESET}", file=sys.stderr)
        sys.exit(1)
    if not frontend_dir.exists():
        print(f"{RED}Error: Frontend directory not found at {frontend_dir}{RESET}", file=sys.stderr)
        sys.exit(1)

    python_exe = get_python_executable(root_dir)
    print_banner(args.backend_port, args.frontend_port, args.host)
    print(f"{DIM}[System] Using Python interpreter: {python_exe}{RESET}\n", flush=True)

    # Prepare backend environment & command
    backend_env = os.environ.copy()
    backend_env["PYTHONPATH"] = str(backend_dir)
    backend_cmd = [
        python_exe,
        "-m",
        "uvicorn",
        "app.main:app",
        "--host",
        args.host,
        "--port",
        str(args.backend_port),
    ]
    if not args.no_reload:
        backend_cmd.append("--reload")

    # Prepare frontend environment & command
    frontend_env = os.environ.copy()
    frontend_env["PYTHONPATH"] = str(frontend_dir)
    frontend_env["API_BASE_URL"] = f"http://{args.host}:{args.backend_port}"
    frontend_cmd = [
        python_exe,
        "-m",
        "streamlit",
        "run",
        "app.py",
        "--server.port",
        str(args.frontend_port),
        "--server.headless",
        "true" if args.headless else "false",
        "--browser.gatherUsageStats",
        "false",
    ]

    backend_proc = None
    frontend_proc = None
    threads = []

    def handle_exit(signum=None, frame=None):
        print(f"\n{YELLOW}[System] Shutting down services...{RESET}", flush=True)
        if backend_proc:
            terminate_process_tree(backend_proc)
        if frontend_proc:
            terminate_process_tree(frontend_proc)
        print(f"{GREEN}[System] All services stopped cleanly. Goodbye!{RESET}\n", flush=True)
        sys.exit(0)

    # Register signal handlers
    signal.signal(signal.SIGINT, handle_exit)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, handle_exit)

    try:
        # Start Backend process
        print(f"{CYAN}[Backend]{RESET} Starting FastAPI backend on http://{args.host}:{args.backend_port} ...", flush=True)
        backend_proc = subprocess.Popen(
            backend_cmd,
            cwd=str(backend_dir),
            env=backend_env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=1,
        )

        t_backend = threading.Thread(
            target=stream_output,
            args=(backend_proc, "[Backend] ", CYAN),
            daemon=True,
        )
        t_backend.start()
        threads.append(t_backend)

        # Brief pause to allow backend to bind port before frontend boots
        time.sleep(1.5)

        # Start Frontend process
        print(f"{GREEN}[Frontend]{RESET} Starting Streamlit frontend on http://localhost:{args.frontend_port} ...", flush=True)
        frontend_proc = subprocess.Popen(
            frontend_cmd,
            cwd=str(frontend_dir),
            env=frontend_env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=1,
        )

        t_frontend = threading.Thread(
            target=stream_output,
            args=(frontend_proc, "[Frontend]", GREEN),
            daemon=True,
        )
        t_frontend.start()
        threads.append(t_frontend)

        # Monitor loop
        while True:
            # If backend died unexpectedly
            if backend_proc.poll() is not None:
                print(f"{RED}[Backend] Process exited with code {backend_proc.returncode}{RESET}", flush=True)
                break

            # If frontend died unexpectedly
            if frontend_proc.poll() is not None:
                print(f"{RED}[Frontend] Process exited with code {frontend_proc.returncode}{RESET}", flush=True)
                break

            time.sleep(0.5)

    except KeyboardInterrupt:
        pass
    finally:
        handle_exit()


if __name__ == "__main__":
    main()
