# Import modules

import random
import os

# Configuration — simulated environment data

user_list = ["root", "admin", "isaak", "ubuntu", "guest"]
ip_list = ["192.168.1.10", "192.168.1.50", "192.168.1.99", "10.0.0.5", "172.16.0.22"]
black_list = ["10.0.0.5", "192.168.1.99"]
granted_users_list = ["root", "admin"]
total_lines = 500
output_dir = "sample_data"

def generate_blacklist():
    with open(output_dir + "/black_list.txt", "w") as f:
        f.write("\n".join(black_list))

def generate_granted_users_list():
    with open(output_dir + "/granted_users_list.txt", "w") as f:
        f.write("\n".join(granted_users_list))

def generate_auth_log():
    lines = []
    for i in range(total_lines):
       user = random.choice(user_list)
       ip = random.choice(ip_list)
       if ip in black_list:
           resultado = "Failed"
       else:
           resultado = random.choice(["Failed", "Accepted"])
       hora = f"{random.randint(0,23):02d}:{random.randint(0,59):02d}:{random.randint(0,59):02d}"
       linea = f"Jan 01 {hora} server sshd: {resultado} password for {user} from {ip}"
       lines.append(linea)
    with open(output_dir + "/auth_log.txt", "w") as f:
        f.write("\n".join(lines))

# Main — create output directory and run generators

if __name__ == "__main__":
    os.makedirs(output_dir, exist_ok=True)
    generate_auth_log()
    generate_blacklist()
    generate_granted_users_list()
    print("Archivos generados en", output_dir)