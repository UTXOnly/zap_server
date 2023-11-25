import subprocess
import sys

venv_dir = "zap_venv"


def print_color(text, color):
    print(f"\033[1;{color}m{text}\033[0m")


def install_linux_packages():
    subprocess.run(["sudo", "apt-get", "update", "-y"], check=True)
    subprocess.run(
        [
            "sudo",
            "apt-get",
            "install",
            "-y",
            "python3-pip",
            "nginx",
            "tmux",
            "certbot",
            "python3.10-venv",
            "python3-certbot-nginx",
        ],
        check=True,
    )


def create_virtual_environment(directory):
    """Creates a virtual environment in the specified directory."""
    subprocess.check_call([sys.executable, "-m", "venv", directory])


def install_packages(requirements_file, venv_directory):
    """Installs packages from a requirements file into the virtual environment."""
    pip_executable = f"{venv_directory}/bin/pip"
    subprocess.check_call([pip_executable, "install", "-r", requirements_file])


if __name__ == "__main__":
    install_linux_packages()
    print("Creating virtual environment...")
    create_virtual_environment(venv_dir)

    requirements_file = "requirements.txt"
    print_color(f"Installing required packages from {requirements_file}...", "32")
    install_packages(requirements_file, venv_dir)

    print("Setup complete. Virtual environment created and packages installed.")
