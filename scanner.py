'''python
import psutil
import socket
from .categorizer import categorize_api

def scan_processes():
    """
    Scans for running processes and identifies those with network connections.
    """
    api_list = []
    for proc in psutil.process_iter(['pid', 'name', 'connections']):
        try:
            connections = proc.info['connections']
            if connections:
                for conn in connections:
                    # Filter for TCP/IP connections (inet) and listening status
                    if conn.family in (socket.AF_INET, socket.AF_INET6) and conn.status == psutil.CONN_LISTEN and conn.laddr:
                        api_info = {
                            'pid': proc.info['pid'],
                            'name': proc.info['name'],
                            'port': conn.laddr.port,
                            'address': conn.laddr.ip,
                        }
                        category, description, is_suspicious = categorize_api(api_info)
                        api_info['category'] = category
                        api_info['description'] = description
                        api_info['is_suspicious'] = is_suspicious
                        api_list.append(api_info)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return sorted(api_list, key=lambda x: x['port'])
