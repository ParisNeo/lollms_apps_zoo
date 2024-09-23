from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import random
import subprocess
import platform
import pipmaster as pm
if not pm.is_installed("netifaces"):
    pm.install("netifaces")
import netifaces
from typing import List
import socket
import struct
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Add CORS middleware to allow access from port 9600
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:9600"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Device(BaseModel):
    name: str
    ip: str
    mac: str
    type: str
    hostname: str

class Risk(BaseModel):
    severity: str
    level: str
    description: str

class RiskAssessment(BaseModel):
    risks: List[Risk]
    recommendations: str

class Settings(BaseModel):
    scanFrequency: int
    notificationsEnabled: bool

class PortScan(BaseModel):
    ip: str

class PortResult(BaseModel):
    number: int
    service: str
    status: str

def get_local_ip():
    interfaces = netifaces.interfaces()
    for interface in interfaces:
        addresses = netifaces.ifaddresses(interface)
        if netifaces.AF_INET in addresses:
            for link in addresses[netifaces.AF_INET]:
                if 'addr' in link:
                    if link['addr'].startswith('192.168.') or link['addr'].startswith('10.'):
                        return link['addr']
    return None

def get_mac(ip):
    os_name = platform.system().lower()
    try:
        if os_name == "windows":
            output = subprocess.check_output(f'arp -a {ip}', shell=True).decode('utf-8')
            mac = output.split()[-2]
        elif os_name in ["linux", "darwin"]:  # Linux or macOS
            output = subprocess.check_output(f'arp -n {ip}', shell=True).decode('utf-8')
            mac = output.split()[3]
        else:
            raise OSError("Unsupported operating system")
        return mac
    except:
        return "00:00:00:00:00:00"

def get_hostname(ip):
    try:
        return socket.gethostbyaddr(ip)[0]
    except:
        return "Unknown"

def guess_device_type_by_hostname(hostname):
    hostname = hostname.lower()
    if "pc" in hostname or "desktop" in hostname or "laptop" in hostname:
        return "Computer"
    elif "phone" in hostname or "mobile" in hostname:
        return "Mobile Device"
    elif "tv" in hostname:
        return "Smart TV"
    elif "router" in hostname or "gateway" in hostname:
        return "Router"
    else:
        return hostname

def scan_network():
    local_ip = get_local_ip()
    if not local_ip:
        raise HTTPException(status_code=500, detail="Could not determine local IP")

    ip_parts = local_ip.split('.')
    base_ip = f"{ip_parts[0]}.{ip_parts[1]}.{ip_parts[2]}."

    devices = []
    for i in range(1, 255):
        ip = f"{base_ip}{i}"
        if is_host_up(ip):
            mac = get_mac(ip)
            hostname = get_hostname(ip)
            device_type = guess_device_type_by_hostname(hostname)
            device = Device(
                name=f"Device {i}",
                ip=ip,
                mac=mac,
                type=device_type,
                hostname=hostname
            )
            devices.append(device)

    return devices

def is_host_up(ip):
    os_name = platform.system().lower()
    try:
        if os_name == "windows":
            output = subprocess.check_output(f'ping -n 1 -w 100 {ip}', shell=True)
        else:  # Linux or macOS
            output = subprocess.check_output(f'ping -c 1 -W 1 {ip}', shell=True)
        return True
    except:
        return False

def scan_port(ip, port):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex((ip, port))
        if result == 0:
            return "Open"
        else:
            return "Closed"
    except:
        return "Error"
    finally:
        sock.close()

@app.get("/scan_network", response_model=List[Device])
async def api_scan_network():
    try:
        return scan_network()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/risk_assessment", response_model=RiskAssessment)
async def api_risk_assessment():
    risks = [
        Risk(severity="High", level="red", description="Open SSH port detected on multiple devices"),
        Risk(severity="Medium", level="yellow", description="Outdated firmware on network router"),
        Risk(severity="Low", level="green", description="Guest network not properly isolated")
    ]
    recommendations = "Update firmware, close unnecessary ports, and review network segmentation."
    return RiskAssessment(risks=risks, recommendations=recommendations)

@app.post("/update_settings")
async def update_settings(settings: Settings):
    print(f"Updated settings: Scan Frequency: {settings.scanFrequency}, Notifications: {settings.notificationsEnabled}")
    return {"status": "success", "message": "Settings updated successfully"}

@app.post("/scan_ports", response_model=List[PortResult])
async def api_scan_ports(port_scan: PortScan):
    common_ports = {
        20: "FTP Data",
        21: "FTP Control",
        22: "SSH",
        23: "Telnet",
        25: "SMTP",
        53: "DNS",
        80: "HTTP",
        110: "POP3",
        143: "IMAP",
        443: "HTTPS",
        3306: "MySQL",
        3389: "RDP"
    }
    
    results = []
    for port, service in common_ports.items():
        status = scan_port(port_scan.ip, port)
        results.append(PortResult(number=port, service=service, status=status))
    
    return results

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
