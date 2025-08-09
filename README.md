<div align="center">
  <img src="https://raw.githubusercontent.com/A11gitss/CyberBlitz-DDoS/main/banner.png" alt="CyberBlitz Banner" style="max-width: 100%;"/>
</div>

<div align="center">
  <h1 align="center">CyberBlitz-Go - Advanced Stress Testing Tool</h1>
</div>

<p align="center">
  <a href="https://github.com/A11gitss/CyberBlitz-DDoS/blob/main/LICENSE">
    <img src="https://img.shields.io/github/license/A11gitss/CyberBlitz-DDoS?style=for-the-badge" alt="License">
  </a>
</p>

---

### ⚠️ Предупреждение / Warning

**Этот инструмент предназначен исключительно для образовательных целей и для использования в рамках легального стресс-тестирования и анализа безопасности с явного разрешения владельца целевого ресурса.**

**Автор не несет никакой ответственности за любой ущерб или незаконные действия, совершенные с использованием этого программного обеспечения. Использование CyberBlitz для атаки на цели, на которые у вас нет разрешения, является незаконным и может повлечь за собой серьезные юридические последствия.**

**This tool is intended for educational purposes and for use in legal stress testing and security analysis with the explicit permission of the target resource owner.**

**The author bears no responsibility for any damage or illegal actions committed using this software. Using CyberBlitz to attack targets for which you do not have permission is illegal and may result in severe legal consequences.**

---

## About The Project

**CyberBlitz-Go** is a high-performance, command-line-only rewrite of the original CyberBlitz tool, built entirely in Go. It is a versatile and powerful stress-testing tool designed for security professionals and developers, leveraging Go's concurrency for maximum efficiency. It allows for the simulation of a wide range of attacks, from low-level network floods (Layer 3/4) to sophisticated application-level attacks (Layer 7) aimed at bypassing modern security systems.

### Key Features

*   **High-Performance Core:** Written in Go to utilize goroutines for massive concurrency and low overhead.
*   **Layer 7 (Application Level) Attacks:**
    *   **Advanced Cloudflare Bypass (`HTTPS-BYPASS`):** Utilizes `uTLS` to mimic real browser TLS fingerprints (JA3/JARM) to bypass advanced bot detection.
    *   **Real Browser Emulation (`HTTP-BROWSER`):** Uses `playwright-go` to launch a full-fledged headless browser to solve JavaScript challenges and other interactive security measures.
*   **Layer 4/3 (Network Level) Attacks:**
    *   **TCP/UDP Floods:** Includes `TCP-SYN` and `UDP` flood types.
    *   **ICMP Flood:** A standard ICMP echo request flood.
    *   **Slowloris:** A low-and-slow connection exhaustion attack.
*   **Advanced Anonymity & Spoofing:**
    *   **SOCKS5 & Tor Support:** Route Layer 7 attacks through SOCKS5 proxies or a local Tor instance.
    *   **Detailed Spoofing:** Generates a complete browser persona, including consistent User-Agent and modern `Sec-CH-UA` headers.

### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/A11gitss/CyberBlitz-DDoS.git
    cd CyberBlitz-DDoS
    ```

2.  **Install Go:**
    Make sure you have Go installed (version 1.21 or newer is recommended). You can download it from [go.dev](https://go.dev/dl/).

3.  **Install Dependencies:**
    This command will download all the necessary Go modules.
    ```bash
    go mod tidy
    ```

4.  **Install Playwright Browsers:**
    For the `HTTP-BROWSER` method to work, you need to install the browser binaries for Playwright.
    ```bash
    go run github.com/playwright-community/playwright-go/cmd/playwright install
    ```
    If you encounter errors on Linux, you may need to install system dependencies:
    ```bash
    go run github.com/playwright-community/playwright-go/cmd/playwright install-deps
    ```

5.  **Build the application:**
    ```bash
    go build -o bin/cyberblitz-go cmd/cyberblitz/main.go
    ```
    This will create the executable `cyberblitz-go` inside the `bin/` directory.

### How To Use

**Note:** Layer 3 attacks (like `ICMP-FLOOD`) may require root privileges. Use `sudo` for these methods.

**General format:**
```bash
./bin/cyberblitz-go --target <IP_OR_URL> --method <METHOD> [OPTIONS]
```

**Attack launch examples:**

*   **Simple UDP flood on an IP address:**
    ```bash
    ./bin/cyberblitz-go --target 1.2.3.4 --port 80 --method UDP --threads 100 --duration 120
    ```

*   **Advanced Cloudflare bypass using TLS fingerprints:**
    ```bash
    ./bin/cyberblitz-go --target https://protected.com --method HTTPS-BYPASS --threads 50 --duration 300
    ```

*   **Browser emulation attack to solve JS challenges:**
    ```bash
    ./bin/cyberblitz-go --target https://challenge.com --method HTTP-BROWSER --threads 10 --duration 180
    ```

*   **TCP SYN flood using Tor:**
    ```bash
    sudo ./bin/cyberblitz-go --target 1.2.3.4 --port 443 --method TCP-SYN --threads 200 --duration 300 --use-tor
    ```

📬 Feedback

If you have ideas, suggestions for improvement, or want to contribute — feel free to reach out:

📨 Telegram: @a11_89d

Any help or feedback is welcome!

### License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
