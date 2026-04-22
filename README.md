🛡️ JWT Attack Toolkit

A high-performance security toolkit for testing JSON Web Token (JWT) vulnerabilities.
This project includes both a Command-Line Interface (CLI) and a modern Ethical Hacker Web Dashboard built using Streamlit.

🚀 Key Features

This toolkit automates the identification of common JWT misconfigurations:

None Algorithm Bypass
Forge tokens by setting the alg header to none to test if the server skips signature verification.
Algorithm Confusion (RS256 → HS256)
Attempts to exploit improper public key handling by switching algorithms.
Weak Secret Brute-Force
Cracks HMAC secrets (HS256/384/512) using dictionary attacks.
KID Header Injection
Injects malicious payloads into the kid (Key ID) header for path traversal or SQL injection testing.
Token Scanner
Decodes and displays JWT headers and payloads without requiring a secret key.
🛠️ Tech Stack
Python 3 – Core logic and automation
Streamlit – Web dashboard interface
PyJWT – Token encoding/decoding
Colorama – Colored terminal output
⚙️ Installation
Clone the repository
git clone https://github.com/your-username/jwt-attack-toolkit.git
cd jwt-attack-toolkit
Install dependencies
pip install -r requirements.txt
▶️ Usage
1. Web Dashboard (Recommended)
streamlit run app.py

This will launch a browser-based interface with a hacker-style UI.

2. Terminal Interface
python jwt_attacker.py --token <YOUR_JWT> --attack info

Example:

python jwt_attacker.py --token eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9... --attack none
📁 Project Structure
jwt-attack-toolkit/
│
├── app.py                # Streamlit dashboard
├── jwt_attacker.py      # CLI tool
├── requirements.txt     # Dependencies
└── README.md            # Documentation
⚠️ Disclaimer

Authorized Penetration Testing ONLY

This tool is intended strictly for:

Educational purposes
Ethical hacking practice
Authorized security assessments

🚫 Unauthorized use against systems without explicit permission is illegal and strictly prohibited.

