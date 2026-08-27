




import streamlit as st
import pandas as pd
import os
from IPtest import StoreNetworkDiagnostics

# ==========================================
# CREDENTIAL MANAGER LOGIC
# ==========================================
CRED_FILE = "data.csv"

def load_credentials():
    if os.path.exists(CRED_FILE):
        try:
            df = pd.read_csv(CRED_FILE)
            return df.set_index("DeviceType").to_dict(orient="index")
        except Exception:
            return {}
    return {}

def save_credentials(srv_user, srv_pass, cnt_user, cnt_pass):
    df = pd.DataFrame([
        {"DeviceType": "Server", "Username": srv_user, "Password": srv_pass},
        {"DeviceType": "Counter", "Username": cnt_user, "Password": cnt_pass},
    ])
    df.to_csv(CRED_FILE, index=False)

# ==========================================
# INPUT SANITIZATION HELPERS
# ==========================================
def parse_specific_counters(counter_str: str) -> list:
    if not counter_str.strip(): return []
    counters = []
    for x in counter_str.split(','):
        x = x.strip()
        if x.isdigit():
            val = int(x)
            if 1 <= val <= 50:
                counters.append(val)
    return sorted(list(set(counters)))

def parse_store_inputs(input_str: str, max_items: int = 5) -> list:
    if not input_str.strip(): return []
    items = [x.strip().upper() for x in input_str.split(',') if x.strip()]
    return items[:max_items]

# ==========================================
# UI CONFIGURATION
# ==========================================
st.set_page_config(page_title="Store Diagnostics Hub", page_icon="🔌", layout="wide")

with st.sidebar:
    st.header("🔒 SSH Credentials Manager")
    creds = load_credentials()
    srv_creds = creds.get("Server", {})
    cnt_creds = creds.get("Counter", {})

    with st.expander("Configure Credentials", expanded=not os.path.exists(CRED_FILE)):
        srv_user = st.text_input("Server Username", value=srv_creds.get("Username", ""))
        srv_pass = st.text_input("Server Password", type="password", value=srv_creds.get("Password", ""))
        cnt_user = st.text_input("Counter Username", value=cnt_creds.get("Username", ""))
        cnt_pass = st.text_input("Counter Password", type="password", value=cnt_creds.get("Password", ""))
        
        if st.button("💾 Save to data.csv", use_container_width=True):
            if srv_user and srv_pass and cnt_user and cnt_pass:
                save_credentials(srv_user, srv_pass, cnt_user, cnt_pass)
                st.success("Credentials saved!")

st.title("🔌 Enterprise Store Diagnostic Hub")
st.markdown("Automated Level 1 Triage for Retail Connectivity")
st.divider()

scanner = StoreNetworkDiagnostics()
reverse_mapping = {v: k for k, v in scanner.store_mapping.items()}

tab_single, tab_bulk = st.tabs(["🎯 Single/Quick Check (Up to 5)", "📁 Bulk File Upload"])

# ==========================================
# TAB 1: SINGLE / QUICK CHECK
# ==========================================
with tab_single:
    user_input_raw = st.text_input(
        "Store Code(s) or Base IP(s)", 
        placeholder="e.g., Z101, Z102 or 192.168.10",
        help="Enter up to 5 Store Codes separated by commas. Lowercase letters are automatically fixed."
    )
    
    st.markdown("#### 1. Target Configurations")
    c_col1, c_col2 = st.columns(2)
    with c_col1:
        st.markdown("**POS Counters Setup**")
        s_cnt_mode = st.radio("Input Method", ["Sequential (1 to N)", "Specific (Comma-separated)"], key="s_c_mode", horizontal=True)
        if "Sequential" in s_cnt_mode:
            s_target_counters_list = list(range(1, st.number_input("Total POS Counters to Check", 1, 50, 10, key="s_c_num") + 1))
        else:
            s_target_counters_list = parse_specific_counters(st.text_input("Specific POS Counters", "1,2,3", key="s_c_spec"))
    
    with c_col2:
        st.markdown("**Beauty Counters Setup**")
        st.write(" ") # Spacing to align with radio button
        s_target_beauty_list = parse_specific_counters(st.text_input("Specific Beauty Counters (Leave blank for all)", "", help="e.g., 1,3. Blank checks 1-5.", key="s_b_spec"))

    st.markdown("#### 2. Select Ping Targets")
    chk_col1, chk_col2, chk_col3, chk_col4, chk_col5 = st.columns(5)
    with chk_col1: run_link = st.checkbox("Link (.1)", value=True, key="s_link")
    with chk_col2: run_server = st.checkbox("Server (.12)", value=True, key="s_server")
    with chk_col3: run_wifi = st.checkbox("WiFi (.81)", value=False, key="s_wifi")
    with chk_col4: run_counters = st.checkbox("POS Counters", value=True, key="s_pos")
    with chk_col5: run_beauty = st.checkbox("Beauty Counters", value=False, key="s_beauty")

    st.markdown("#### 3. Select URL Testing Options (via SSH)")
    url_col1, url_col2 = st.columns([1, 2])
    with url_col1:
        url_test_server = st.checkbox("URL Test on Server", disabled=not (run_link and run_server), key="s_url_srv")
        url_test_counters = st.checkbox("URL Test on POS Counters", disabled=not (run_link and run_server and run_counters), key="s_url_cnt")
    with url_col2:
        default_urls = ["google.com", "wikipedia.org", "facebook.com", "amazon.com", "netflix.com"]
        selected_urls = st.multiselect("Advanced: Select URLs to test", options=default_urls, default=default_urls, key="s_urls")

    if st.button("Run Diagnostics", type="primary", use_container_width=True):
        stores_to_check = parse_store_inputs(user_input_raw)

        if not stores_to_check:
            st.warning("⚠️ Please enter at least one Store Code or Base IP.")
        elif run_counters and not s_target_counters_list:
            st.warning("⚠️ You checked 'POS Counters' but provided invalid/no counter numbers.")
        else:
            if len(user_input_raw.split(',')) > 5:
                st.info("💡 You entered more than 5 stores. Processing the first 5.")
            
            for store_val in stores_to_check:
                with st.spinner(f"Resolving and running diagnostics for {store_val}..."):
                    report = scanner.diagnose_store(
                        store_val, 
                        target_counters=s_target_counters_list, 
                        target_beauty_counters=s_target_beauty_list,
                        run_link=run_link, run_server=run_server, run_wifi=run_wifi, 
                        run_counters=run_counters, run_beauty=run_beauty
                    )
                    
                    if "Error" in report:
                        st.error(f"🚨 **Input Error for {store_val}:** {report['Error']}")
                        continue
                        
                    ips_list = report.pop("ips", [])
                    resolved_base = report.pop("resolved_base", "Unknown")
                    display_code = store_val if store_val in scanner.store_mapping else reverse_mapping.get(resolved_base, "Unknown Code")
                    
                    st.info(f"📍 **Store:** `{display_code}` | **Network:** `{resolved_base}.x`")
                    
                    table_data = []
                    for idx, (device, status) in enumerate(report.items()):
                        ip_addr = ips_list[idx] if idx < len(ips_list) else "Unknown"
                        table_data.append({"Device": device, "IP Address": ip_addr, "Ping Status": status})
                    
                    df = pd.DataFrame(table_data)
                    styled_df = df.style.map(lambda v: 'color: #00FF00; font-weight: bold;' if v == "Online" else 'color: #FF0000; font-weight: bold;', subset=['Ping Status'])
                    st.dataframe(styled_df, use_container_width=True, hide_index=True)

                    if (url_test_server or url_test_counters) and selected_urls:
                        loaded_creds = load_credentials()
                        if not loaded_creds:
                            st.error("🚨 Cannot run URL tests: SSH Credentials missing.")
                        else:
                            st.markdown(f"**🌐 SSH External Connectivity Report ({display_code})**")
                            
                            if url_test_server and report.get("Store Server") == "Online":
                                srv_cred = loaded_creds.get("Server", {})
                                server_ip = f"{resolved_base}.12"
                                url_results = scanner.check_external_urls_via_ssh(server_ip, srv_cred.get("Username"), srv_cred.get("Password"), selected_urls)
                                
                                with st.expander(f"🖥️ Server ({server_ip}) URL Report", expanded=True):
                                    if "SSH_ERROR" in url_results:
                                        st.error(url_results["SSH_ERROR"])
                                    else:
                                        st.dataframe(pd.DataFrame(list(url_results.items()), columns=["URL", "Status"]).style.map(lambda v: 'color: #00FF00;' if v == "Reachable" else 'color: #FF0000;', subset=['Status']), use_container_width=True, hide_index=True)

                            if url_test_counters:
                                cnt_cred = loaded_creds.get("Counter", {})
                                for idx, (device, status) in enumerate(report.items()):
                                    if "Counter" in device and "Beauty" not in device and status == "Online":
                                        counter_ip = ips_list[idx]
                                        url_results = scanner.check_external_urls_via_ssh(counter_ip, cnt_cred.get("Username"), cnt_cred.get("Password"), selected_urls)
                                        
                                        with st.expander(f"🛒 {device} ({counter_ip}) URL Report", expanded=False):
                                            if "SSH_ERROR" in url_results:
                                                st.error(url_results["SSH_ERROR"])
                                            else:
                                                st.dataframe(pd.DataFrame(list(url_results.items()), columns=["URL", "Status"]).style.map(lambda v: 'color: #00FF00;' if v == "Reachable" else 'color: #FF0000;', subset=['Status']), use_container_width=True, hide_index=True)
                st.divider()

# ==========================================
# TAB 2: BULK UPLOAD & PROCESSING
# ==========================================
with tab_bulk:
    st.markdown("Upload a CSV/Excel file containing Store Codes or IPs.")
    
    with st.expander("⚙️ Bulk Scan Settings", expanded=True):
        b_col1, b_col2, b_col3 = st.columns(3)
        with b_col1:
            st.markdown("**Counters Setup**")
            b_cnt_mode = st.radio("POS Input Method", ["Sequential (1 to N)", "Specific (Comma-separated)"], key="b_c_mode")
            if "Sequential" in b_cnt_mode:
                b_target_counters_list = list(range(1, st.number_input("Total POS Counters", 1, 50, 5, key="b_c_num") + 1))
            else:
                b_target_counters_list = parse_specific_counters(st.text_input("Specific POS Counters", "1,2,3,4,5", key="b_c_spec"))
            
            b_target_beauty_list = parse_specific_counters(st.text_input("Specific Beauty Counters (Blank for all)", "", key="b_b_spec"))

        with b_col2:
            st.markdown("**Ping Targets:**")
            bulk_link = st.checkbox("Network Link (.1)", value=True, key="b_link")
            bulk_server = st.checkbox("Store Server (.12)", value=True, key="b_server")
            bulk_wifi = st.checkbox("WiFi (.81)", value=False, key="b_wifi")
            bulk_counters = st.checkbox("POS Counters", value=True, key="b_cnt_chk")
            bulk_beauty = st.checkbox("Beauty Counters", value=False, key="b_beauty")
            
        with b_col3:
            st.markdown("**SSH URL Tests:**")
            bulk_url_server = st.checkbox("URL Test on Server", disabled=not (bulk_link and bulk_server), key="b_url_srv")
            bulk_url_counters = st.checkbox("URL Test on POS Counters", disabled=not (bulk_link and bulk_server and bulk_counters), key="b_url_cnt")
            bulk_selected_urls = st.multiselect("URLs to test", options=default_urls, default=["google.com"], key="b_urls")

    uploaded_file = st.file_uploader("Upload Store List", type=["csv", "xlsx"])

    if uploaded_file is not None:
        try:
            df_input = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
            target_col = next((col for col in df_input.columns if any(k in str(col).lower() for k in ['ip', 'code', 'store'])), df_input.columns[0])
            base_inputs = df_input[target_col].dropna().astype(str).tolist()
            st.success(f"Loaded {len(base_inputs)} records to scan.")
            
            if st.button("🚀 Start Bulk Scan", type="primary", use_container_width=True):
                loaded_creds = load_credentials()
                
                if bulk_counters and not b_target_counters_list:
                    st.error("🚨 Invalid specific POS counters provided for Bulk Scan.")
                elif (bulk_url_server or bulk_url_counters) and not loaded_creds:
                    st.error("🚨 Cannot run URL tests: SSH Credentials are missing.")
                else:
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    top_download_container = st.empty()
                    st.write("") 
                    
                    live_results_container = st.container()
                    all_results = []
                    
                    def highlight_status(val):
                        val_upper = str(val).upper()
                        if "ONLINE" in val_upper or "REACHABLE" in val_upper: return 'color: #00FF00; font-weight: bold;'
                        elif "ERROR" in val_upper: return 'color: #FFA500; font-weight: bold;' 
                        return 'color: #FF0000; font-weight: bold;'

                    for i, val in enumerate(base_inputs):
                        status_text.text(f"Scanning Record {i+1} of {len(base_inputs)}: {val} ...")
                        clean_val = str(val).strip().upper()
                        display_code = clean_val if clean_val in scanner.store_mapping else reverse_mapping.get(clean_val, "Unknown Code")
                        display_ip = scanner.store_mapping.get(clean_val, clean_val)

                        report = scanner.diagnose_store(
                            val, 
                            target_counters=b_target_counters_list, 
                            target_beauty_counters=b_target_beauty_list,
                            run_link=bulk_link, run_server=bulk_server, run_wifi=bulk_wifi,
                            run_counters=bulk_counters, run_beauty=bulk_beauty
                        )
                        
                        store_block_results = []
                        if "Error" in report:
                            store_block_results.append({"Store Code": display_code, "Base IP": display_ip, "Target/Device": "N/A", "Status": f"ERROR: {report['Error']}"})
                        else:
                            ips_list = report.pop("ips", [])
                            resolved_base_ip = report.pop("resolved_base", "Unknown") 
                            
                            for idx, (device, status) in enumerate(report.items()):
                                ip_addr = ips_list[idx] if idx < len(ips_list) else "Unknown"
                                store_block_results.append({"Store Code": display_code, "Base IP": display_ip, "Target/Device": f"{ip_addr} ({device})", "Status": status})
                            
                            if bulk_url_server and report.get("Store Server") == "Online" and bulk_selected_urls:
                                srv_cred = loaded_creds.get("Server", {})
                                server_ip = f"{resolved_base_ip}.12"
                                url_results = scanner.check_external_urls_via_ssh(server_ip, srv_cred.get("Username"), srv_cred.get("Password"), bulk_selected_urls)
                                if "SSH_ERROR" in url_results:
                                    store_block_results.append({"Store Code": display_code, "Base IP": display_ip, "Target/Device": f"{server_ip} (Server) - SSH", "Status": f"ERROR: {url_results['SSH_ERROR']}"})
                                else:
                                    for url, url_stat in url_results.items():
                                        store_block_results.append({"Store Code": display_code, "Base IP": display_ip, "Target/Device": f"{server_ip} (Server) - {url}", "Status": url_stat})

                            if bulk_url_counters and bulk_selected_urls:
                                cnt_cred = loaded_creds.get("Counter", {})
                                for idx, (device, status) in enumerate(report.items()):
                                    if "Counter" in device and "Beauty" not in device and status == "Online":
                                        counter_ip = ips_list[idx]
                                        url_results = scanner.check_external_urls_via_ssh(counter_ip, cnt_cred.get("Username"), cnt_cred.get("Password"), bulk_selected_urls)
                                        if "SSH_ERROR" in url_results:
                                            store_block_results.append({"Store Code": display_code, "Base IP": display_ip, "Target/Device": f"{counter_ip} ({device}) - SSH", "Status": f"ERROR: {url_results['SSH_ERROR']}"})
                                        else:
                                            for url, url_stat in url_results.items():
                                                store_block_results.append({"Store Code": display_code, "Base IP": display_ip, "Target/Device": f"{counter_ip} ({device}) - {url}", "Status": url_stat})
                        
                        all_results.extend(store_block_results)
                        store_df = pd.DataFrame(store_block_results)
                        
                        with live_results_container:
                            st.markdown(f"##### 📍 Store Code: `{display_code}` | Network: `{display_ip}.x`")
                            st.dataframe(store_df.style.map(highlight_status, subset=['Status']), use_container_width=True, hide_index=True)
                            st.divider() 
                        
                        progress_bar.progress((i + 1) / len(base_inputs))
                    
                    status_text.text("✅ Bulk scan complete!")
                    csv = pd.DataFrame(all_results).to_csv(index=False).encode('utf-8')
                    top_download_container.download_button(label="📥 Download Full Report (CSV) ⬆️", data=csv, file_name='Store_Diagnostics_Report.csv', mime='text/csv', use_container_width=True, key="btn_dl_top")
                    st.download_button(label="📥 Download Full Report (CSV) ⬇️", data=csv, file_name='Store_Diagnostics_Report.csv', mime='text/csv', use_container_width=True, key="btn_dl_bottom")
        except Exception as e:
            st.error(f"🚨 Failed to process file. Error: {str(e)}")