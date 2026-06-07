# Import modules
import re
import collections
import os

# Input files
auth_log_file = "sample_data/auth_log.txt"
blacklist_file = "sample_data/blacklist.txt"
privileged_users_file = "sample_data/privileged_users.txt"

def load_files(auth_log_file, blacklist_file, privileged_users_file):
    with open(auth_log_file, "r") as f:
        log = f.read().splitlines()
    with open(blacklist_file, "r") as f:
        blacklist = f.read().splitlines()
    with open(privileged_users_file, "r") as f:
        privileged = f.read().splitlines()
    return log, blacklist, privileged

def analyze_log(log):
    failed_by_user = collections.Counter()
    failed_by_ip = collections.Counter()
    for line in log:
        if "failed" in line.lower():
            user = re.search(r"for (\w+) from", line).group(1)
            ip = re.search(r"from (\d+\.\d+\.\d+\.\d+)", line).group(1)
            failed_by_user[user] += 1
            failed_by_ip[ip] += 1
    return failed_by_ip, failed_by_user

def detect_brute_force(failed_by_ip, threshold=10):
    suspicious = []
    for ip in failed_by_ip:
        if failed_by_ip[ip] > threshold:
            suspicious.append(ip)
    return suspicious

def flagged_ips(log, blacklist):
    flagged = []
    for line in log:
        ip = re.search(r"from (\d+\.\d+\.\d+\.\d+)", line)
        if ip:
            ip = ip.group(1)
            if ip in blacklist:
                flagged.append(ip)
    return flagged

def detect_night_activity(log, privileged):
    night_events = []
    for line in log:
        if "accepted" in line.lower():
            hour = re.search(r"(\d{2}):(\d{2}):(\d{2})", line)
            user = re.search(r"for (\w+) from", line)
            if hour and user:
                hour = int(hour.group(1))
                user = user.group(1)
                if hour < 6 and user in privileged:
                    night_events.append(line)
    return night_events

def generate_report(failed_by_user, failed_by_ip, suspicious, flagged, night_events):
    with open("output/report.txt", "w") as f:
        f.write("=== SOC LOG ANALYSIS REPORT ===\n\n")
        f.write("--- FAILED LOGINS BY USER ---\n")
        for user, count in failed_by_user.most_common():
            f.write(f"{user}: {count}\n")
        f.write("\n--- FAILED LOGINS BY IP ---\n")
        for ip, count in failed_by_ip.most_common():
            f.write(f"{ip}: {count}\n")
        f.write("\n--- BRUTE FORCE SUSPICIOUS IPs ---\n")
        for ip in suspicious:
            f.write(f"{ip}\n")
        f.write("\n--- BLACKLISTED IPs DETECTED ---\n")
        for ip, count in collections.Counter(flagged).most_common():
            f.write(f"{ip}: {count} hits\n")
        f.write("\n--- NIGHT ACTIVITY (00:00-06:00) ---\n")
        for line in night_events:
            f.write(f"{line}\n")

# Main — run analysis and generate report
if __name__ == "__main__":
    log, blacklist, privileged = load_files(auth_log_file, blacklist_file, privileged_users_file)
    failed_by_ip, failed_by_user = analyze_log(log)
    suspicious = detect_brute_force(failed_by_ip)
    flagged = flagged_ips(log, blacklist)
    night_events = detect_night_activity(log, privileged)
    os.makedirs("output", exist_ok=True)
    generate_report(failed_by_user, failed_by_ip, suspicious, flagged, night_events)
    print("Report generated in output/report.txt")
