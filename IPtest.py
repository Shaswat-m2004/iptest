




# import subprocess
# import platform
# import re
# import os
# import pandas as pd
# from concurrent.futures import ThreadPoolExecutor
# from typing import Dict, List

# class StoreNetworkDiagnostics:
#     def __init__(self, master_data_path: str = r"C:\Users\91702\Documents\programming\trent\IPtest\Activestores.xlsx"):
#         self.os_type = platform.system().lower()
#         self.ping_flag = '-n' if self.os_type == 'windows' else '-c'
#         self.timeout_flag = '-w' if self.os_type == 'windows' else '-W'
        
#         self.store_mapping = self._load_store_mapping(master_data_path)

#     def _load_store_mapping(self, path: str) -> Dict[str, str]:
#         mapping = {}
#         if os.path.exists(path):
#             try:
#                 df = pd.read_excel(path)
#                 if 'Store Code' in df.columns and 'IP' in df.columns:
#                     df['Store Code'] = df['Store Code'].astype(str).str.strip().str.upper()
#                     df['IP'] = df['IP'].astype(str).str.strip()
#                     mapping = dict(zip(df['Store Code'], df['IP']))
#             except Exception as e:
#                 print(f"Warning: Could not read master data file. {e}")
#         return mapping

#     def resolve_target(self, input_val: str) -> str:
#         clean_input = str(input_val).strip().upper()
#         if clean_input in self.store_mapping:
#             return self.store_mapping[clean_input]
#         return clean_input

#     def sanitize_base_ip(self, ip_input: str) -> str:
#         ip_input = ip_input.strip()
#         if not re.match(r'^[\d\.]+$', ip_input):
#             raise ValueError(f"Invalid input: '{ip_input}'. Must be a valid IP or a recognized Store Code.")

#         parts = ip_input.split('.')
#         dot_count = len(parts) - 1

#         if dot_count == 2:
#             base_ip = ip_input
#         elif dot_count == 3:
#             last_octet = parts[3]
#             if last_octet not in ['1', '12', '81']:
#                 raise ValueError("If entering a full IP, it must be the base network.")
#             base_ip = '.'.join(parts[:3])
#         else:
#             raise ValueError("Invalid format. Enter a base IP (e.g., 198.18.0) or Store Code.")

#         for part in base_ip.split('.'):
#             if not part.isdigit() or not (0 <= int(part) <= 255):
#                 raise ValueError(f"Invalid IP range detected in octet: {part}")

#         return base_ip

#     def _ping_ip(self, ip_address: str) -> bool:
#         command = ['ping', self.ping_flag, '1', self.timeout_flag, '1', ip_address]
#         try:
#             result = subprocess.run(command, capture_output=True, text=True)
#             output = result.stdout.upper()
#             if result.returncode == 0 and "TTL=" in output:
#                 return True
#             return False
#         except Exception:
#             return False

#     def check_network_link(self, base_ip: str) -> bool:
#         return self._ping_ip(f"{base_ip}.1")

#     def check_store_server(self, base_ip: str) -> bool:
#         return self._ping_ip(f"{base_ip}.12")
        
#     def check_store_wifi(self, base_ip: str) -> bool:
#         return self._ping_ip(f"{base_ip}.81")

#     def check_counter(self, base_ip: str, counter_number: int) -> bool:
#         return self._ping_ip(f"{base_ip}.{111 + counter_number}")
        
#     def check_beauty_counter(self, base_ip: str, counter_number: int) -> bool:
#         # IPs .171 to .175
#         return self._ping_ip(f"{base_ip}.{170 + counter_number}")

#     def check_external_urls_via_ssh(self, target_ip: str, username: str, password: str, urls: List[str] = None) -> Dict[str, str]:
#         if urls is None or len(urls) == 0:
#             urls = ["google.com", "wikipedia.org", "facebook.com", "amazon.com", "netflix.com"]

#         results = {}
#         try:
#             import paramiko
#         except ImportError:
#             return {"SSH_ERROR": "Paramiko library is missing. Run 'pip install paramiko'."}

#         ssh = paramiko.SSHClient()
#         ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
#         try:
#             ssh.connect(target_ip, username=username, password=password, timeout=5)
#             for url in urls:
#                 clean_url = url.replace("https://", "").replace("http://", "").strip()
#                 command = f"ping -c 1 -W 2 {clean_url}"
#                 stdin, stdout, stderr = ssh.exec_command(command)
#                 exit_status = stdout.channel.recv_exit_status()
#                 results[clean_url] = "Reachable" if exit_status == 0 else "Unreachable"
#         except paramiko.AuthenticationException:
#             return {"SSH_ERROR": "Authentication Failed. Incorrect Username or Password."}
#         except Exception as e:
#             return {"SSH_ERROR": f"Connection Failed: {str(e)}"}
#         finally:
#             ssh.close()
            
#         return results

#     def diagnose_store(self, raw_input: str, target_counters: List[int] = None, target_beauty_counters: List[int] = None,
#                        run_link: bool = True, run_server: bool = True, 
#                        run_wifi: bool = False, run_counters: bool = True, run_beauty: bool = False) -> Dict[str, str]:
        
#         try:
#             resolved_ip = self.resolve_target(raw_input)
#             base_ip = self.sanitize_base_ip(resolved_ip)
#         except ValueError as e:
#             return {"Error": str(e), "ips": ["N/A"]}

#         if not any([run_link, run_server, run_wifi, run_counters, run_beauty]):
#             return {"Error": "No diagnostic targets selected.", "ips": ["N/A"]}

#         if target_counters is None:
#             target_counters = [1, 2, 3, 4, 5]

#         results_report = {}
#         ips_map = {} 
        
#         with ThreadPoolExecutor(max_workers=15) as executor:
#             futures = {}
            
#             if run_link:
#                 futures[executor.submit(self.check_network_link, base_ip)] = ("Network Link", "LINK DOWN", f"{base_ip}.1")
            
#             if run_server:
#                 futures[executor.submit(self.check_store_server, base_ip)] = ("Store Server", "SERVER DOWN", f"{base_ip}.12")
                
#             if run_wifi:
#                 futures[executor.submit(self.check_store_wifi, base_ip)] = ("Store WiFi", "WIFI DOWN", f"{base_ip}.81")
            
#             if run_counters:
#                 for i in target_counters:
#                     futures[executor.submit(self.check_counter, base_ip, i)] = (f"Counter {i}", "COUNTER LINK DOWN", f"{base_ip}.{111 + i}")
                    
#             if run_beauty:
#                 # If list is empty/None, check all 5 by default
#                 b_counters = target_beauty_counters if target_beauty_counters else [1, 2, 3, 4, 5]
#                 for i in b_counters: 
#                     futures[executor.submit(self.check_beauty_counter, base_ip, i)] = (f"Beauty Cntr {i}", "BEAUTY COUNTER DOWN", f"{base_ip}.{170 + i}")

#             for future in futures:
#                 device_name, error_msg, ip_addr = futures[future]
#                 ips_map[device_name] = ip_addr 
                
#                 try:
#                     is_online = future.result()
#                     results_report[device_name] = "Online" if is_online else error_msg
#                 except Exception as e:
#                     results_report[device_name] = f"EXECUTION ERROR: {str(e)}"

#         results_report["ips"] = [ips_map[device] for device in results_report.keys()]
#         results_report["resolved_base"] = base_ip 
        
#         return results_report








import subprocess
import platform
import re
import os
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Optional

# Determine the directory where this script resides to resolve relative paths reliably
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_EXCEL_PATH = os.path.join(BASE_DIR, "Activestores.xlsx")

class StoreNetworkDiagnostics:
    def __init__(self, master_data_path: Optional[str] = None):
        self.os_type = platform.system().lower()
        self.ping_flag = '-n' if self.os_type == 'windows' else '-c'
        self.timeout_flag = '-w' if self.os_type == 'windows' else '-W'
        
        # If no path is provided, use DEFAULT_EXCEL_PATH.
        # If a relative path is passed, resolve it relative to BASE_DIR.
        if master_data_path is None:
            resolved_path = DEFAULT_EXCEL_PATH
        elif not os.path.isabs(master_data_path):
            resolved_path = os.path.join(BASE_DIR, master_data_path)
        else:
            resolved_path = master_data_path

        self.store_mapping = self._load_store_mapping(resolved_path)

    def _load_store_mapping(self, path: str) -> Dict[str, str]:
        mapping = {}
        if os.path.exists(path):
            try:
                df = pd.read_excel(path)
                if 'Store Code' in df.columns and 'IP' in df.columns:
                    df['Store Code'] = df['Store Code'].astype(str).str.strip().str.upper()
                    df['IP'] = df['IP'].astype(str).str.strip()
                    mapping = dict(zip(df['Store Code'], df['IP']))
            except Exception as e:
                print(f"Warning: Could not read master data file. {e}")
        return mapping

    def resolve_target(self, input_val: str) -> str:
        clean_input = str(input_val).strip().upper()
        if clean_input in self.store_mapping:
            return self.store_mapping[clean_input]
        return clean_input

    def sanitize_base_ip(self, ip_input: str) -> str:
        ip_input = ip_input.strip()
        if not re.match(r'^[\d\.]+$', ip_input):
            raise ValueError(f"Invalid input: '{ip_input}'. Must be a valid IP or a recognized Store Code.")

        parts = ip_input.split('.')
        dot_count = len(parts) - 1

        if dot_count == 2:
            base_ip = ip_input
        elif dot_count == 3:
            last_octet = parts[3]
            if last_octet not in ['1', '12', '81']:
                raise ValueError("If entering a full IP, it must be the base network.")
            base_ip = '.'.join(parts[:3])
        else:
            raise ValueError("Invalid format. Enter a base IP (e.g., 198.18.0) or Store Code.")

        for part in base_ip.split('.'):
            if not part.isdigit() or not (0 <= int(part) <= 255):
                raise ValueError(f"Invalid IP range detected in octet: {part}")

        return base_ip

    def _ping_ip(self, ip_address: str) -> bool:
        command = ['ping', self.ping_flag, '1', self.timeout_flag, '1', ip_address]
        try:
            result = subprocess.run(command, capture_output=True, text=True)
            output = result.stdout.upper()
            if result.returncode == 0 and "TTL=" in output:
                return True
            return False
        except Exception:
            return False

    def check_network_link(self, base_ip: str) -> bool:
        return self._ping_ip(f"{base_ip}.1")

    def check_store_server(self, base_ip: str) -> bool:
        return self._ping_ip(f"{base_ip}.12")
        
    def check_store_wifi(self, base_ip: str) -> bool:
        return self._ping_ip(f"{base_ip}.81")

    def check_counter(self, base_ip: str, counter_number: int) -> bool:
        return self._ping_ip(f"{base_ip}.{111 + counter_number}")
        
    def check_beauty_counter(self, base_ip: str, counter_number: int) -> bool:
        # IPs .171 to .175
        return self._ping_ip(f"{base_ip}.{170 + counter_number}")

    def check_external_urls_via_ssh(self, target_ip: str, username: str, password: str, urls: List[str] = None) -> Dict[str, str]:
        if urls is None or len(urls) == 0:
            urls = ["google.com", "wikipedia.org", "facebook.com", "amazon.com", "netflix.com"]

        results = {}
        try:
            import paramiko
        except ImportError:
            return {"SSH_ERROR": "Paramiko library is missing. Run 'pip install paramiko'."}

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        try:
            ssh.connect(target_ip, username=username, password=password, timeout=5)
            for url in urls:
                clean_url = url.replace("https://", "").replace("http://", "").strip()
                command = f"ping -c 1 -W 2 {clean_url}"
                stdin, stdout, stderr = ssh.exec_command(command)
                exit_status = stdout.channel.recv_exit_status()
                results[clean_url] = "Reachable" if exit_status == 0 else "Unreachable"
        except paramiko.AuthenticationException:
            return {"SSH_ERROR": "Authentication Failed. Incorrect Username or Password."}
        except Exception as e:
            return {"SSH_ERROR": f"Connection Failed: {str(e)}"}
        finally:
            ssh.close()
            
        return results

    def diagnose_store(self, raw_input: str, target_counters: List[int] = None, target_beauty_counters: List[int] = None,
                       run_link: bool = True, run_server: bool = True, 
                       run_wifi: bool = False, run_counters: bool = True, run_beauty: bool = False) -> Dict[str, str]:
        
        try:
            resolved_ip = self.resolve_target(raw_input)
            base_ip = self.sanitize_base_ip(resolved_ip)
        except ValueError as e:
            return {"Error": str(e), "ips": ["N/A"]}

        if not any([run_link, run_server, run_wifi, run_counters, run_beauty]):
            return {"Error": "No diagnostic targets selected.", "ips": ["N/A"]}

        if target_counters is None:
            target_counters = [1, 2, 3, 4, 5]

        results_report = {}
        ips_map = {} 
        
        with ThreadPoolExecutor(max_workers=15) as executor:
            futures = {}
            
            if run_link:
                futures[executor.submit(self.check_network_link, base_ip)] = ("Network Link", "LINK DOWN", f"{base_ip}.1")
            
            if run_server:
                futures[executor.submit(self.check_store_server, base_ip)] = ("Store Server", "SERVER DOWN", f"{base_ip}.12")
                
            if run_wifi:
                futures[executor.submit(self.check_store_wifi, base_ip)] = ("Store WiFi", "WIFI DOWN", f"{base_ip}.81")
            
            if run_counters:
                for i in target_counters:
                    futures[executor.submit(self.check_counter, base_ip, i)] = (f"Counter {i}", "COUNTER LINK DOWN", f"{base_ip}.{111 + i}")
                    
            if run_beauty:
                b_counters = target_beauty_counters if target_beauty_counters else [1, 2, 3, 4, 5]
                for i in b_counters: 
                    futures[executor.submit(self.check_beauty_counter, base_ip, i)] = (f"Beauty Cntr {i}", "BEAUTY COUNTER DOWN", f"{base_ip}.{170 + i}")

            for future in futures:
                device_name, error_msg, ip_addr = futures[future]
                ips_map[device_name] = ip_addr 
                
                try:
                    is_online = future.result()
                    results_report[device_name] = "Online" if is_online else error_msg
                except Exception as e:
                    results_report[device_name] = f"EXECUTION ERROR: {str(e)}"

        results_report["ips"] = [ips_map[device] for device in results_report.keys()]
        results_report["resolved_base"] = base_ip 
        
        return results_report