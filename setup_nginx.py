import subprocess
import os
from dotenv import load_dotenv


def print_color(text, color):
    print(f"\033[1;{color}m{text}\033[0m")



def setup_nginx():
    load_dotenv()
    contact = os.getenv("CONTACT")
    domain_name = os.getenv("DOMAIN")
    nginx_filepath = os.getenv("NGINX_FILE_PATH")
    if os.path.exists(nginx_filepath):
        try:
            subprocess.run(["sudo", "rm", nginx_filepath], check=True)
            print_color("File removed successfully.", "32")
        except subprocess.CalledProcessError as e:
            print(f"An error occurred while removing the file: {e}")
    nginx_config = f"""
server {{
    server_name {domain_name};

    location / {{    
        add_header 'Access-Control-Allow-Origin' '*';
        add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS';
        add_header 'Access-Control-Allow-Headers' 'DNT,X-CustomHeader,Keep-Alive,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Authorization';
        add_header 'Content-Type' 'application/json';
    
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header Host $host;
        proxy_pass http://127.0.0.1:5000;
        proxy_http_version 1.1;
    }}
}}
    """


    nginx_filepath = "/path/to/nginx.conf"
    nginx_config = "your nginx configuration"

    try:
        # Open a subprocess running sudo tee to write to the file with elevated privileges
        process = subprocess.Popen(['sudo', 'tee', nginx_filepath], stdin=subprocess.PIPE, universal_newlines=True)
        process.communicate(nginx_config)
    
        if process.returncode == 0:
            print_color("The default configuration file has been written successfully.", "32")
        else:
            raise Exception(f"tee command returned non-zero exit status {process.returncode}")
    
    except PermissionError as e:
        print_color(
            "Permission denied: Please run this script with elevated privileges.", "31"
        )
    except Exception as e:
        print_color(
            f"An error occurred while writing the default configuration file: {e}", "31"
        )


    try:
        subprocess.run(["sudo", "service", "nginx", "restart"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while restarting nginx: {e}")

    cert_file_path = f"/etc/letsencrypt/live/{domain_name}/fullchain.pem"

    if os.path.isfile(cert_file_path):
        print("The file exists!")
    else:
        print("The file doesn't exist!")
        try:
            subprocess.run(
                [
                    "sudo",
                    "certbot",
                    "--nginx",
                    "-d",
                    domain_name,
                    "--non-interactive",
                    "--agree-tos",
                    "--email",
                    contact,
                ],
                check=True,
            )
        except subprocess.CalledProcessError as e:
            print(f"An error occurred while running certbot: {e}")

    try:
        subprocess.run(["sudo", "service", "nginx", "restart"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while restarting nginx: {e}")

if __name__ == "__main__":
    setup_nginx()
