# Import modules
import random
import os

# Configuration — simulated environment data
users = ["root", "admin", "isaak", "ubuntu", "guest"]
ips = ["192.168.1.10", "192.168.1.50", "192.168.1.99", "10.0.0.5", "172.16.0.22"]
blacklist = ["10.0.0.5", "192.168.1.99"]
privileged_users = ["root", "admin"]
total_lines = 500
output_dir = "sample_data"

def generate_blacklist():
    with open(output_dir + "/blacklist.txt", "w") as f:
        f.write("\n".join(blacklist))

def generate_privileged_users():
    with open(output_dir + "/privileged_users.txt", "w") as f:
        f.write("\n".join(privileged_users))

def generate_auth_log():
    lines = []
    for i in range(total_lines):
        user = random.choice(users)
        ip = random.choice(ips)
        if ip in blacklist:
            result = "Failed"
        else:
            result = random.choice(["Failed", "Accepted"])
        timestamp = f"{random.randint(0,23):02d}:{random.randint(0,59):02d}:{random.randint(0,59):02d}"
        entry = f"Jan 01 {timestamp} server sshd: {result} password for {user} from {ip}"
        lines.append(entry)
    with open(output_dir + "/auth_log.txt", "w") as f:
        f.write("\n".join(lines))

# Main — create output directory and run generators
if __name__ == "__main__":
    os.makedirs(output_dir, exist_ok=True)
    generate_auth_log()
    generate_blacklist()
    generate_privileged_users()
    print("Files generated in", output_dir)
