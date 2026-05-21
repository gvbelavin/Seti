import subprocess
import time
from pathlib import Path
from datetime import datetime


NET_NAME = "lesson9-ipv6-net"
CONTAINER_A = "lesson9-a"
CONTAINER_B = "lesson9-b"
SUBNET_V6 = "fd00:7::/64"
OUT_DIR = Path("results")
PCAP_IN_CONTAINER = "/tmp/lesson9_mix.pcap"
PCAP_LOCAL = OUT_DIR / "lesson9_mix.pcap"


def cmd(command, check=True, timeout=None):
    result = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
    if check and result.returncode != 0:
        print("Error command:", " ".join(command))
        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)
        raise SystemExit(1)
    return result


def open_wireshark(file_path: Path):
    programs = [
        ["wireshark", str(file_path)],
        [r"C:\Program Files\Wireshark\Wireshark.exe", str(file_path)],
        [r"C:\Program Files (x86)\Wireshark\Wireshark.exe", str(file_path)],
    ]
    for p in programs:
        try:
            subprocess.Popen(p)
            return True
        except FileNotFoundError:
            pass
    return False


def main():
    OUT_DIR.mkdir(exist_ok=True)
    pcap_local = PCAP_LOCAL
    if pcap_local.exists():
        try:
            pcap_local.unlink()
        except PermissionError:
            suffix = datetime.now().strftime("%Y%m%d_%H%M%S")
            pcap_local = OUT_DIR / f"lesson9_mix_{suffix}.pcap"

    print("1) Cleaning old containers and network...")
    cmd(["docker", "rm", "-f", CONTAINER_A, CONTAINER_B], check=False)
    cmd(["docker", "network", "rm", NET_NAME], check=False)

    print("2) Creating IPv6 network...")
    cmd(["docker", "network", "create", "--driver", "bridge", "--ipv6", "--subnet", SUBNET_V6, NET_NAME])

    print("3) Starting containers...")
    cmd(["docker", "run", "-dit", "--name", CONTAINER_A, "--network", NET_NAME, "alpine", "sh"])
    cmd(["docker", "run", "-dit", "--name", CONTAINER_B, "--network", NET_NAME, "alpine", "sh"])

    print("4) Installing tools...")
    tools = "apk add --no-cache iputils iproute2 tcpdump netcat-openbsd"
    cmd(["docker", "exec", CONTAINER_A, "sh", "-c", tools])
    cmd(["docker", "exec", CONTAINER_B, "sh", "-c", tools])

    print("5) Reading target container IP addresses...")

    ipv4_b = cmd(
        ["docker", "inspect", "-f", "{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}", CONTAINER_B]
    ).stdout.strip()
    ipv6_b = cmd(
        ["docker", "inspect", "-f", "{{range.NetworkSettings.Networks}}{{.GlobalIPv6Address}}{{end}}", CONTAINER_B]
    ).stdout.strip()
    print("6) Starting tcpdump in background in container A...")
    cmd(
        [
            "docker",
            "exec",
            "-d",
            CONTAINER_A,
            "sh",
            "-c",
            f"rm -f {PCAP_IN_CONTAINER}; tcpdump -i eth0 -n -w {PCAP_IN_CONTAINER}",
        ]
    )
    time.sleep(1)

    print("7) Sending IPv4 and IPv6 ping...")
    cmd(["docker", "exec", CONTAINER_A, "ping", "-c", "4", ipv4_b], timeout=30)
    cmd(["docker", "exec", CONTAINER_A, "ping6", "-c", "4", ipv6_b], timeout=30)

    print("8) Sending TCP traffic with netcat...")
    cmd(["docker", "exec", "-d", CONTAINER_B, "sh", "-c", "nc -l -p 9090 -w 8 > /tmp/nc_in.txt"])
    time.sleep(1)
    cmd(["docker", "exec", CONTAINER_A, "sh", "-c", f"echo hello-ipv4 | nc -w 5 {ipv4_b} 9090"], check=False)

    cmd(["docker", "exec", "-d", CONTAINER_B, "sh", "-c", "nc -6 -l -p 9091 -w 8 > /tmp/nc6_in.txt"])
    time.sleep(1)
    cmd(
        ["docker", "exec", CONTAINER_A, "sh", "-c", f"echo hello-ipv6 | nc -6 -w 5 {ipv6_b} 9091"],
        check=False,
    )
    time.sleep(2)

    print("9) Stop capture and copy pcap file...")
    cmd(["docker", "exec", CONTAINER_A, "sh", "-c", "pkill tcpdump"], check=False)
    time.sleep(1)
    cmd(["docker", "cp", f"{CONTAINER_A}:{PCAP_IN_CONTAINER}", str(pcap_local)])

    print("10) Try opening Wireshark...")
    opened = open_wireshark(pcap_local.resolve())

    print("PCAP saved:", pcap_local.resolve())

    if opened:
        print("Wireshark opened")
    else:
        print("Wireshark not found")
        print(pcap_local.resolve())


if __name__ == "__main__":
    main()
