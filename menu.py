import subprocess


# Function to print colored text to the console
def print_color(text, color):
    print(f"\033[1;{color}m{text}\033[0m")


def setup_server():
    try:
        print_color("\nSetting up server", "33")
        subprocess.run(["python3", "setup_env.py"], check=True)
        subprocess.run(["python3", "-m", "venv", "zap_venv"], check=True)
        activate_cmd = ". zap_venv/bin/activate && "
        commands = ["python setup_nginx.py"]
        for cmd in commands:
            subprocess.run(["bash", "-c", activate_cmd + cmd], check=True)
    except subprocess.CalledProcessError as e:
        print_color(
            f"An error occurred while trying to start the Flask server: {e}", "31"
        )


def start_flask_server():
    try:
        print_color("\nStarting Zap Server", "33")
        subprocess.run(["python3", "-m", "venv", "zap_venv"], check=True)
        activate_cmd = ". zap_venv/bin/activate && "
        #commands = ["tmux new-session -s zap_server -d python zap_server.py"]
        commands = ["python zap_server.py"]
        for cmd in commands:
            subprocess.run(["bash", "-c", activate_cmd + cmd], check=True)

        print_color("\n\nZap Server is running", "32")
    except subprocess.CalledProcessError as e:
        print_color(
            f"An error occurred while trying to start the Flask server: {e}", "31"
        )


def stop_flask_server():
    """Stops the Flask server running in a tmux session named 'python'."""
    try:
        subprocess.run(["tmux", "kill-session", "-t", "zap_server"], check=True)
        print_color("\nFlask server stopped successfully.", "33")
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while trying to stop the Flask server: {e}")


while True:
    print_color(
        "\n##########################################################################################",
        "31",
    )
    print_color(
        """ \n
                                                                                   
@@@@@@@@  @@@@@@  @@@@@@@      @@@@@@ @@@@@@@@ @@@@@@@  @@@  @@@ @@@@@@@@ @@@@@@@  
     @@! @@!  @@@ @@!  @@@    !@@     @@!      @@!  @@@ @@!  @@@ @@!      @@!  @@@ 
   @!!   @!@!@!@! @!@@!@!      !@@!!  @!!!:!   @!@!!@!  @!@  !@! @!!!:!   @!@!!@!  
 !!:     !!:  !!! !!:             !:! !!:      !!: :!!   !: .:!  !!:      !!: :!!  
:.::.: :  :   : :  :          ::.: :  : :: ::   :   : :    ::    : :: ::   :   : : 
                                                                                                                                      
    """,
        "34",
    )
    print("\nPlease select an option:\n")
    print_color("1) Setup Reverse Proxy and LNURL server", "33")
    print_color("2) Start Zap Server", "32")
    print_color("3) Stop Zap Server", "31")
    print_color("4) Exit menu", "31")

    options = {
        "1": setup_server,
        "2": start_flask_server,
        "3": stop_flask_server,
        "4": lambda: print_color("Exited menu", "31"),
    }

    try:
        choice = input("\nEnter an option number (1-4): ")
        if choice in options:
            options[choice]()
            if choice == "4":
                print()
                break
    except ValueError:
        print_color("Invalid choice. Please enter a valid option number.", "31")
