"""
Citizen Scheme AI - Safe Switch Launcher
Allows seamless switching between the Modern Web Portal (FastAPI) and Classic Streamlit UI (app.py).

Usage:
    python run.py                   # Launches Modern Web Portal (FastAPI, default)
    python run.py --ui modern       # Launches Modern Web Portal at http://127.0.0.1:8000
    python run.py --ui classic      # Launches Classic Streamlit App at http://localhost:8501
    python run.py --test            # Runs complete test suite (pytest tests -v)
"""

import sys
import os
import argparse
import subprocess

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))


def run_modern(host: str = "127.0.0.1", port: int = 8000):
    """Launches the modern FastAPI web portal."""
    print("=" * 70)
    print("🇮🇳 Citizen Scheme AI — Modern Civic Tech Web Portal")
    print(f"🌐 Serving at: http://{host}:{port}")
    print("💡 To revert to Classic Streamlit UI at any time, run:")
    print("   python run.py --ui classic   OR   streamlit run app.py")
    print("=" * 70)
    try:
        import uvicorn
        # Ensure working directory is project root
        os.chdir(PROJECT_ROOT)
        uvicorn.run("server:app", host=host, port=port, reload=False)
    except ImportError:
        print("❌ Error: uvicorn is not installed. Run 'pip install -r requirements.txt'")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n🛑 Modern Web Portal stopped.")


def run_classic(port: int = 8501):
    """Launches the original, untouched Streamlit application."""
    print("=" * 70)
    print("🇮🇳 Citizen Scheme AI — Classic Streamlit Interface")
    print(f"🌐 Launching Streamlit on port {port}...")
    print("💡 To switch to the Modern Web Portal, run:")
    print("   python run.py --ui modern   OR   python server.py")
    print("=" * 70)
    cmd = [sys.executable, "-m", "streamlit", "run", "app.py", f"--server.port={port}"]
    try:
        subprocess.run(cmd, cwd=PROJECT_ROOT)
    except KeyboardInterrupt:
        print("\n🛑 Classic Streamlit App stopped.")


def run_tests():
    """Runs repository test suite."""
    print("=" * 70)
    print("🧪 Running Citizen Scheme AI Verification Test Suite...")
    print("=" * 70)
    cmd = [sys.executable, "-m", "pytest", "tests", "-v"]
    res = subprocess.run(cmd, cwd=PROJECT_ROOT)
    sys.exit(res.returncode)


def main():
    parser = argparse.ArgumentParser(
        description="Citizen Scheme AI Launcher (Safe Switch between Modern & Classic UIs)"
    )
    parser.add_argument(
        "--ui",
        choices=["modern", "classic"],
        default="modern",
        help="Interface mode: 'modern' for FastAPI SPA portal, 'classic' for Streamlit app"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="Custom port to bind the server to"
    )
    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Host address (for modern UI)"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run unit & integration test suite"
    )

    args = parser.parse_args()

    if args.test:
        run_tests()
        return

    if args.ui == "classic":
        port = args.port or 8501
        run_classic(port=port)
    else:
        port = args.port or 8000
        run_modern(host=args.host, port=port)


if __name__ == "__main__":
    main()
