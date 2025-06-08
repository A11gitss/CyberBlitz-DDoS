CyberBlitz README
================

Overview
--------
CyberBlitz is a powerful, modular, and highly customizable stress-testing tool designed for security researchers, penetration testers, and system administrators. Built in Python, it provides a comprehensive suite of Layer 4 and Layer 7 attack methods to simulate high-load scenarios, helping to evaluate the resilience of networks, servers, and applications. With advanced features like traffic spoofing, proxy support, and browser emulation, CyberBlitz is a go-to tool for controlled, ethical stress testing.

Legal Disclaimer: CyberBlitz is intended for educational and authorized testing purposes only. Unauthorized use against systems without explicit permission is illegal and unethical. Always obtain consent from system owners before conducting tests.

Features
--------
CyberBlitz is packed with features to make it a versatile and robust tool:

- Comprehensive Attack Methods:
  - Layer 4 Attacks: AMP (NTP, DNS, STUN, WSD, SADP), TCP (TCP-ACK, TCP-SYN, TCP-BYPASS, OVH-TCP), UDP (UDP, UDP-VSE, UDP-BYPASS), Game-specific (GAME, GAME-MC, GAME-WARZONE, GAME-R6, FIVEM-KILL), Special (SSH, GAME-KILL, TCP-SOCKET, DISCORD, SLOWLORIS).
  - Layer 7 Attacks: HTTP/HTTPS (HTTPS-FLOODER, HTTPS-BYPASS, HTTP-BROWSER, HTTPS-ARTERMIS), Locust for distributed load testing.
  - Botnet Simulation: UDPBYPASS-BOT, OVH-HEX, GREBOT, TCPBOT.
- Traffic Spoofing and Anonymity:
  - Supports Tor (torpy or torsocks) for anonymized traffic.
  - Integrates SOCKS5 proxy chains for non-transparent proxying.
  - Spoofs User-Agent, cookies, browser fingerprints, timezone, screen resolution, and language using Faker and fake-useragent.
- High Performance:
  - Leverages asyncio for asynchronous HTTP attacks and concurrent.futures for Layer 4 attacks.
  - Optimized threading for maximum throughput.
- Browser Emulation:
  - Supports Selenium and Playwright for realistic browser-based attacks with customizable behaviors (clicks, scrolling).
- User-Friendly Interface:
  - Beautiful CLI powered by Click and Rich, featuring progress bars and result tables.
- Logging: Detailed logs stored in logs/cyberblitz.log for monitoring and debugging.

Use Cases
---------
CyberBlitz is designed for ethical stress testing in controlled environments, such as:
- Testing the resilience of web servers, APIs, and network infrastructure.
- Simulating DDoS attacks to evaluate mitigation strategies.
- Assessing the performance of firewalls, WAFs, and CDNs under load.
- Conducting penetration testing with explicit permission.
- Educational purposes to understand attack vectors and defense mechanisms.

**Guaranteed Impact**: When used correctly in a controlled environment, CyberBlitz can generate significant load, potentially overwhelming unprotected systems. It is 100% effective for testing server limits, identifying bottlenecks, and validating security configurations.

Installation
-----------
Prerequisites:
- Python 3.11 or 3.12 (Python 3.13 may have compatibility issues with some libraries).
- Tor installed for Tor-based anonymity (torpy or torsocks).
- Chrome browser for Selenium or Playwright (automatically managed by Playwright).

Setup:
1. Clone or download the CyberBlitz repository:
   git clone <repository_url>
   cd CyberBlitz

2. Install dependencies:
   pip install -r requirements.txt

3. Ensure Tor is running (for Tor-based attacks):
   - On Windows: Install Tor Browser or Tor Expert Bundle and run tor.exe.
   - On Linux/macOS: Install Tor with sudo apt install tor or brew install tor and start it with tor.

4. (Optional) Configure torsocks for system-level Tor integration.

Usage
-----
CyberBlitz is controlled via a command-line interface (CLI) using the main.py script. The primary command is attack, which launches a stress test with customizable options.

Command Structure:
python main.py attack [OPTIONS]

Options:
--target        Target IP or URL (required). Example: 192.168.1.1 or http://example.com
--port          Target port (for Layer 4 attacks). Default: 80. Example: 80
--method        Attack method (required). Example: TCP-SYN or HTTPS-FLOODER
--threads       Number of threads/tasks. Default: 100. Example: 200
--duration      Attack duration (seconds). Default: 60. Example: 120
--use-tor       Enable Tor for anonymity. Example: --use-tor
--tor-lib       Tor library (torpy or torsocks). Default: torpy. Example: --tor-lib torsocks
--use-proxy     Enable SOCKS5 proxies. Example: --use-proxy
--browser       Browser emulation (none, selenium, playwright). Default: none. Example: --browser playwright
--clicks        Enable clicks in browser emulation. Example: --clicks
--scroll        Enable scrolling in browser emulation. Example: --scroll
--delay         Delay between browser actions (seconds). Default: 1.0. Example: --delay 0.5

Supported Attack Methods:
- Layer 4:
  - AMP: NTP, DNS, STUN, WSD, SADP
  - TCP: TCP-ACK, TCP-SYN, TCP-BYPASS, OVH-TCP
  - UDP: UDP, UDP-VSE, UDP-BYPASS
  - Game: GAME, GAME-MC (Minecraft), GAME-WARZONE (Call of Duty: Warzone), GAME-R6 (Rainbow Six Siege), FIVEM-KILL (FiveM)
  - Special: SSH, GAME-KILL, TCP-SOCKET, DISCORD, SLOWLORIS
- Layer 7:
  - HTTP/HTTPS: HTTPS-FLOODER, HTTPS-BYPASS, HTTP-BROWSER, HTTPS-ARTERMIS
  - Distributed: LOCUST
- Botnet:(NOT WORKING!)
  - UDPBYPASS-BOT, OVH-HEX, GREBOT, TCPBOT

Example Commands:
1. TCP-SYN Flood with Tor and Proxies:
   python main.py attack --target 192.168.1.1 --port 80 --method TCP-SYN --threads 200 --duration 120 --use-tor --tor-lib torpy --use-proxy

2. HTTPS Flood with Playwright and Browser Actions:
   python main.py attack --target http://example.com --method HTTPS-FLOODER --threads 150 --duration 60 --use-browser playwright --clicks --scroll --delay 0.5

3. Slowloris Attack:
   python main.py attack --target 192.168.1.1 --port 80 --method SLOWLORIS --threads 200 --duration 120

4. Locust Distributed Load Test:
   python main.py attack --target http://example.com --method LOCUST --threads 100 --duration 60

5. Minecraft Game Server Attack with Proxies:
   python main.py attack --target 192.168.1.1 --port 25565 --method GAME-MC --threads 300 --duration 90 --use-proxy

Project Structure
-----------------
CyberBlitz/
├── config.py              # Configuration and logging
├── cli.py                # Interactive CLI (Click + Rich)
├── attacks/
│   ├── __init__.py
│   ├── layer4.py         # Layer 4 attacks (Scapy, custom Slowloris)
│   ├── layer7.py         # Layer 7 attacks (Asyncio, Selenium, Playwright, Locust)
│   ├── botnet.py         # Botnet simulation attacks
├── utils/
│   ├── __init__.py
│   ├── proxy.py          # Proxy management (Torpy, Proxychains)
│   ├── spoofing.py       # Traffic spoofing (Faker, User-Agent, Fingerprint)
├── logs/
│   └── cyberblitz.log    # Attack logs
├── main.py               # Entry point
└── requirements.txt      # Dependencies

Dependencies
------------
Listed in requirements.txt:
- scapy==2.5.0
- requests==2.31.0
- torpy==1.1.6
- aiohttp==3.8.4
- selenium==4.8.0
- playwright==1.30.0
- locust==2.15.0
- faker==13.3.0
- fake-useragent==0.1.11
- click==8.1.3
- rich==12.6.0

Troubleshooting
---------------
- Slowloris Issues: The project uses a custom Slowloris implementation to avoid dependency issues. Ensure your system supports socket operations.
- Tor Errors: Verify that Tor is running (tor process or Tor Browser). For torsocks, configure it correctly in your system.
- Python Version: Use Python 3.11 or 3.12 for maximum compatibility. Python 3.13 may cause issues with some libraries.
- Proxy Issues: Ensure the proxy list from proxyscrape.com is accessible. Alternatively, provide your own proxy list in config.py.

Notes
-----
- Performance: CyberBlitz is optimized for high performance with asynchronous HTTP attacks and multi-threaded Layer 4 attacks. Adjust --threads based on your system's capabilities.
- Anonymity: Use --use-tor and --use-proxy for maximum anonymity. Spoofing options (User-Agent, cookies, etc.) are enabled by default.
- Browser Emulation: Selenium and Playwright require a compatible browser (Chrome for Selenium, managed automatically by Playwright).
- Ethical Use: Always obtain permission before testing. Misuse can lead to legal consequences.

Contributing
------------
Contributions are welcome! Submit pull requests or issues to the repository. Ideas for new attack methods, optimizations, or features are appreciated.
Telegram: https://t.me/a11_89d

License
-------
This project is provided for educational purposes under the MIT License. Use responsibly and ethically.