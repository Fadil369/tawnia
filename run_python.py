#!/usr/bin/env python3
"""
Tawnia Healthcare Analytics - Python System Runner
Comprehensive startup script with environment setup, validation, and server management
"""

import os
import sys
import subprocess
import platform
import time
import signal
import json
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any
import argparse

# Configuration
PYTHON_MIN_VERSION = (3, 8)
PROJECT_DIR = Path(__file__).parent
VENV_DIR = PROJECT_DIR / "venv"
REQUIREMENTS_FILE = PROJECT_DIR / "requirements.txt"
ENV_FILE = PROJECT_DIR / ".env"
ENV_EXAMPLE_FILE = PROJECT_DIR / ".env.example"

class Colors:
    """ANSI color codes for terminal output"""
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

def print_header(text: str):
    """Print a formatted header"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text.center(60)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.END}\n")

def print_success(text: str):
    """Print success message"""
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")

def print_error(text: str):
    """Print error message"""
    print(f"{Colors.RED}✗ {text}{Colors.END}")

def print_warning(text: str):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.END}")

def print_info(text: str):
    """Print info message"""
    print(f"{Colors.BLUE}ℹ {text}{Colors.END}")

def check_python_version() -> bool:
    """Check if Python version meets requirements"""
    current_version = sys.version_info[:2]
    if current_version >= PYTHON_MIN_VERSION:
        print_success(f"Python {'.'.join(map(str, current_version))} meets requirements")
        return True
    else:
        print_error(f"Python {'.'.join(map(str, PYTHON_MIN_VERSION))} or higher required, found {'.'.join(map(str, current_version))}")
        return False

def run_command(command: list, cwd: Optional[Path] = None, capture_output: bool = False) -> tuple:
    """
    Run a system command safely with input validation (CWE-78 fix)
    
    Args:
        command: List of command arguments (validated)
        cwd: Working directory
        capture_output: Whether to capture output
        
    Returns:
        Tuple of (success, output)
    """
    # Validate command is a list and not empty
    if not isinstance(command, list) or not command:
        return False, "Command must be a non-empty list"
    
    # Validate command components contain no shell injection characters
    dangerous_chars = ['&', '|', ';', '`', '$', '(', ')', '<', '>', '"', "'", '\\', '\n', '\r']
    for arg in command:
        if not isinstance(arg, str):
            return False, "All command arguments must be strings"
        if any(char in arg for char in dangerous_chars):
            return False, f"Command argument contains dangerous characters: {arg}"
    
    try:
        if capture_output:
            # Use shell=False for security and validate all arguments
            result = subprocess.run(command, cwd=cwd, capture_output=True, text=True, check=True, shell=False)
            return True, result.stdout.strip()
        else:
            subprocess.run(command, cwd=cwd, check=True, shell=False)
            return True, ""
    except subprocess.CalledProcessError as e:
        return False, str(e)
    except FileNotFoundError:
        return False, f"Command not found: {' '.join(command)}"

def create_virtual_environment() -> bool:
    """Create Python virtual environment"""
    print_info("Creating virtual environment...")

    if VENV_DIR.exists():
        print_warning("Virtual environment already exists")
        return True

    success, error = run_command([sys.executable, "-m", "venv", str(VENV_DIR)])
    if success:
        print_success("Virtual environment created successfully")
        return True
    else:
        print_error(f"Failed to create virtual environment: {error}")
        return False

def get_venv_python() -> Path:
    """Get path to Python executable in virtual environment"""
    if platform.system() == "Windows":
        return VENV_DIR / "Scripts" / "python.exe"
    else:
        return VENV_DIR / "bin" / "python"

def get_venv_pip() -> Path:
    """Get path to pip executable in virtual environment"""
    if platform.system() == "Windows":
        return VENV_DIR / "Scripts" / "pip.exe"
    else:
        return VENV_DIR / "bin" / "pip"

def install_dependencies() -> bool:
    """Install Python dependencies"""
    print_info("Installing dependencies...")

    if not REQUIREMENTS_FILE.exists():
        print_error(f"Requirements file not found: {REQUIREMENTS_FILE}")
        return False

    pip_path = get_venv_pip()
    if not pip_path.exists():
        print_error(f"Pip not found in virtual environment: {pip_path}")
        return False

    # Upgrade pip first
    print_info("Upgrading pip...")
    success, error = run_command([str(pip_path), "install", "--upgrade", "pip"])
    if not success:
        print_warning(f"Failed to upgrade pip: {error}")

    # Install requirements
    success, error = run_command([str(pip_path), "install", "-r", str(REQUIREMENTS_FILE)])
    if success:
        print_success("Dependencies installed successfully")
        return True
    else:
        print_error(f"Failed to install dependencies: {error}")
        return False

def setup_environment_file() -> bool:
    """Setup environment configuration file"""
    print_info("Setting up environment configuration...")

    if ENV_FILE.exists():
        print_success("Environment file already exists")
        return True

    if not ENV_EXAMPLE_FILE.exists():
        print_error(f"Environment example file not found: {ENV_EXAMPLE_FILE}")
        return False

    try:
        # Copy example to actual env file
        with open(ENV_EXAMPLE_FILE, 'r') as src:
            content = src.read()

        with open(ENV_FILE, 'w') as dst:
            dst.write(content)

        print_success("Environment file created from example")
        print_warning("Please update .env file with your actual configuration values")
        return True
    except Exception as e:
        print_error(f"Failed to create environment file: {e}")
        return False

def validate_environment() -> Dict[str, Any]:
    """Validate the environment setup"""
    print_info("Validating environment setup...")

    validation_results = {
        "python_version": False,
        "virtual_environment": False,
        "dependencies": False,
        "environment_file": False,
        "project_structure": False
    }

    # Check Python version
    validation_results["python_version"] = check_python_version()

    # Check virtual environment
    venv_python = get_venv_python()
    if venv_python.exists():
        validation_results["virtual_environment"] = True
        print_success("Virtual environment exists")
    else:
        print_error("Virtual environment not found")

    # Check dependencies
    if validation_results["virtual_environment"]:
        success, output = run_command([str(venv_python), "-c", "import fastapi, pandas, sklearn"], capture_output=True)
        if success:
            validation_results["dependencies"] = True
            print_success("Core dependencies available")
        else:
            print_error("Core dependencies missing")

    # Check environment file
    if ENV_FILE.exists():
        validation_results["environment_file"] = True
        print_success("Environment file exists")
    else:
        print_warning("Environment file not found")

    # Check project structure
    required_dirs = ["src", "src/processors", "src/analysis", "src/ai", "src/reports", "src/utils", "src/models"]
    required_files = ["main.py", "requirements.txt"]

    structure_valid = True
    for dir_path in required_dirs:
        if not (PROJECT_DIR / dir_path).exists():
            print_error(f"Missing directory: {dir_path}")
            structure_valid = False

    for file_path in required_files:
        if not (PROJECT_DIR / file_path).exists():
            print_error(f"Missing file: {file_path}")
            structure_valid = False

    if structure_valid:
        validation_results["project_structure"] = True
        print_success("Project structure is valid")

    return validation_results

def run_tests() -> bool:
    """Run the test suite"""
    print_info("Running test suite...")

    venv_python = get_venv_python()
    test_file = PROJECT_DIR / "test_python.py"

    if not test_file.exists():
        print_warning("Test file not found, skipping tests")
        return True

    # Check if server is running for integration tests
    print_info("Checking if server is running for integration tests...")
    success, _ = run_command([str(venv_python), "-c",
        "import asyncio, httpx; "
        "async def check(): "
        "  try: "
        "    async with httpx.AsyncClient() as client: "
        "      response = await client.get('http://localhost:3000/health', timeout=5); "
        "      print('SERVER_RUNNING' if response.status_code == 200 else 'SERVER_DOWN'); "
        "  except: print('SERVER_DOWN'); "
        "asyncio.run(check())"
    ], capture_output=True)

    # Run unit tests only if server is not running
    test_args = [str(venv_python), "-m", "pytest", str(test_file), "-v"]
    if "SERVER_DOWN" in str(success):
        print_warning("Server not running, skipping integration tests")
        test_args.extend(["-k", "not (test_health_check or test_single_file_upload or test_rejection_analysis)"])

    success, error = run_command(test_args)
    if success:
        print_success("Tests completed successfully")
        return True
    else:
        print_warning(f"Some tests failed: {error}")
        return False

def start_server(port: int = 3000, host: str = "127.0.0.1", reload: bool = False) -> None:
    """Start the FastAPI server - Use localhost for development security (CWE-605 fix)"""
    print_info(f"Starting server on {host}:{port}...")

    venv_python = get_venv_python()

    # Prepare uvicorn command
    cmd = [str(venv_python), "-m", "uvicorn", "main:app", "--host", host, "--port", str(port)]

    if reload:
        cmd.append("--reload")
        print_info("Development mode enabled (auto-reload)")

    try:
        print_success(f"Server starting at http://{host}:{port}")
        print_info("Press Ctrl+C to stop the server")
        # Use shell=False for security (CWE-78 fix)
        subprocess.run(cmd, cwd=PROJECT_DIR, shell=False, check=True)
    except KeyboardInterrupt:
        print_info("\nServer stopped by user")
    except Exception as e:
        print_error(f"Server failed to start: {e}")

def setup_project() -> bool:
    """Complete project setup"""
    print_header("Tawnia Healthcare Analytics - Project Setup")

    # Step 1: Check Python version
    if not check_python_version():
        return False

    # Step 2: Create virtual environment
    if not create_virtual_environment():
        return False

    # Step 3: Install dependencies
    if not install_dependencies():
        return False

    # Step 4: Setup environment file
    if not setup_environment_file():
        return False

    # Step 5: Validate setup
    validation_results = validate_environment()

    # Summary
    print_header("Setup Summary")
    for check, result in validation_results.items():
        status = "✓" if result else "✗"
        color = Colors.GREEN if result else Colors.RED
        print(f"{color}{status} {check.replace('_', ' ').title()}{Colors.END}")

    all_valid = all(validation_results.values())
    if all_valid:
        print_success("\nProject setup completed successfully!")
        print_info("You can now start the server with: python run_python.py --start")
        return True
    else:
        print_error("\nProject setup completed with warnings")
        print_warning("Please address the issues above before starting the server")
        return False

def show_help():
    """Show help information"""
    print_header("Tawnia Healthcare Analytics - Python System")

    print(f"{Colors.BOLD}USAGE:{Colors.END}")
    print("  python run_python.py [OPTIONS]")

    print(f"\n{Colors.BOLD}OPTIONS:{Colors.END}")
    print("  --setup              Run complete project setup")
    print("  --start              Start the FastAPI server")
    print("  --test               Run the test suite")
    print("  --validate           Validate environment setup")
    print("  --dev                Start server in development mode (auto-reload)")
    print("  --port PORT          Specify server port (default: 3000)")
    print("  --host HOST          Specify server host (default: 0.0.0.0)")
    print("  --help               Show this help message")

    print(f"\n{Colors.BOLD}EXAMPLES:{Colors.END}")
    print("  python run_python.py --setup")
    print("  python run_python.py --start")
    print("  python run_python.py --start --dev --port 8000")
    print("  python run_python.py --test")
    print("  python run_python.py --validate")

    print(f"\n{Colors.BOLD}REQUIREMENTS:{Colors.END}")
    print(f"  Python {'.'.join(map(str, PYTHON_MIN_VERSION))} or higher")
    print("  Internet connection for dependency installation")
    print("  Write permissions in project directory")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Tawnia Healthcare Analytics - Python System Runner")
    parser.add_argument("--setup", action="store_true", help="Run complete project setup")
    parser.add_argument("--start", action="store_true", help="Start the FastAPI server")
    parser.add_argument("--test", action="store_true", help="Run the test suite")
    parser.add_argument("--validate", action="store_true", help="Validate environment setup")
    parser.add_argument("--dev", action="store_true", help="Start server in development mode")
    parser.add_argument("--port", type=int, default=3000, help="Server port (default: 3000)")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Server host (default: 127.0.0.1) - Use localhost for security")
    parser.add_argument("--help-extended", action="store_true", help="Show extended help")

    args = parser.parse_args()

    if args.help_extended:
        show_help()
        return

    if args.setup:
        setup_project()
    elif args.validate:
        print_header("Environment Validation")
        validate_environment()
    elif args.test:
        print_header("Running Tests")
        run_tests()
    elif args.start:
        print_header("Starting Server")

        # Quick validation before starting
        validation_results = validate_environment()
        critical_checks = ["python_version", "virtual_environment", "dependencies"]

        if not all(validation_results[check] for check in critical_checks):
            print_error("Critical validation checks failed. Please run --setup first.")
            return

        start_server(port=args.port, host=args.host, reload=args.dev)
    else:
        # Default: show help
        show_help()

if __name__ == "__main__":
    main()
