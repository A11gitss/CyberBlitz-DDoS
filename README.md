<div align="center">
  <img src="https://raw.githubusercontent.com/A11gitss/CyberBlitz-DDoS/main/banner.png
  " alt="CyberBlitz Banner" style="max-width: 100%;"/>
</div>

<div align="center">
  <h1 align="center">CyberBlitz - Advanced Stress Testing Tool</h1>
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

## 🇷🇺

### О проекте

**CyberBlitz** — это многофункциональный и мощный инструмент для проведения стресс-тестирования, спроектированный для специалистов по безопасности и разработчиков. Он позволяет имитировать широкий спектр атак — от низкоуровневых сетевых флудов (Layer 4) до сложных атак на уровне приложений (Layer 7), нацеленных на обход современных систем защиты.

Архитектура приложения позволяет управлять им двумя способами:
1.  **Графический пользовательский интерфейс (GUI):** Написанный на `PyQt5`, он предоставляет интуитивно понятное управление всеми функциями, отслеживание метрик в реальном времени и доступ к расширенным настройкам.
2.  **Интерфейс командной строки (CLI):** Созданный с помощью `click`, он идеально подходит для автоматизации, интеграции в скрипты и быстрого запуска атак.

### Ключевые возможности

*   **Атаки Layer 7 (Уровень приложения):**
    *   **Продвинутый обход Cloudflare (`HTTPS-BYPASS`, `CF-TLS`):** Использует `tls-client` для имитации TLS-отпечатков браузеров и `Playwright` для автоматического решения JavaScript-челленджей и получения валидационных cookie (`cf_clearance`).
    *   **Эмуляция реального браузера (`HTTP-BROWSER`):** Запускает полноценный браузер для имитации действий пользователя (клики, скроллинг), делая трафик неотличимым от легитимного.
    *   **Интеграция с Locust (`LOCUST`):** Позволяет проводить распределенное стресс-тестирование для создания огромной нагрузки.

*   **Атаки Layer 4 (Сетевой уровень):**
    *   **TCP/UDP Флуды:** Включают `TCP-SYN`, `TCP-ACK` и различные виды `UDP`-флуда.
    *   **Атаки с амплификацией (AMP):** Используют уязвимые NTP, DNS и STUN серверы для многократного усиления атаки.
    *   **Специализированные атаки:** Методы, нацеленные на игровые серверы, сервисы (`SSH`) и "медленные" атаки типа `Slowloris`.

*   **Обход Anti-DDoS провайдеров:**
    *   CyberBlitz спроектирован для обхода не только **Cloudflare** и **OVH**, но и других провайдеров, полагающихся на клиентские проверки. Благодаря эмуляции браузера и продвинутому спуфингу, он может быть эффективен против **DDoS-Guard, StormWall, Imperva** и других систем, которые анализируют поведение клиента, TLS-отпечатки и заголовки.

*   **Продвинутая анонимность и спуфинг:**
    *   **Менеджер Tor:** Автоматически запускает и ротирует несколько независимых цепочек Tor для максимальной анонимности.
    *   **Детализированный спуфинг:** Генерирует полноценную "личность" браузера, включая современные заголовки `Sec-CH-UA`, язык, часовой пояс, разрешение экрана и реалистичные `Referer`.

*   **Мониторинг и отчетность:**
    *   Собирает метрики в реальном времени (RPS, задержка) и экспортирует их в `JSON`, `CSV` или `HTML`-отчеты с графиками.

### Установка

1.  **Клонируйте репозиторий:**
    ```bash
    git clone https://github.com/A11gitss/CyberBlitz-DDoS.git
    cd CyberBlitz-DDoS
    ```

2.  **Создайте и активируйте виртуальное окружение (рекомендуется):**
    ```bash
    python -m venv venv
    # Windows
    .\venv\Scripts\activate
    # macOS/Linux
    source venv/bin/activate
    ```

3.  **Установите зависимости:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Установите браузерные движки для Playwright:**
    ```bash
    playwright install
    ```

### Как использовать

#### Графический интерфейс (GUI)

Для запуска GUI выполните команду:
```bash
python gui.py
```
Интерфейс позволяет легко настроить все параметры атаки: выбрать цель, порт, метод, количество потоков и длительность. Во вкладках "Сеть и Спуфинг" и "Дополнительно" можно включить Tor/прокси и тонко настроить параметры эмуляции браузера.

#### Интерфейс командной строки (CLI)

**Общий формат:**
```bash
python cli.py --target <IP_ИЛИ_URL> --method <МЕТОД> [ОПЦИИ]
```

**Примеры запуска атак:**

*   **Простой UDP флуд на IP-адрес:**
    ```bash
    python cli.py --target 1.2.3.4 --port 80 --method UDP --threads 100 --duration 120
    ```

*   **HTTPS флуд на сайт с использованием Tor:**
    ```bash
    python cli.py --target https://example.com --method HTTPS-FLOODER --threads 50 --duration 300 --use-tor
    ```

*   **Атака с эмуляцией браузера для обхода базовой защиты:**
    ```bash
    python cli.py --target https://example.com --method HTTP-BROWSER --threads 10 --duration 180 --clicks --scroll
    ```

*   **Продвинутый обход Cloudflare с помощью TLS-отпечатков и прокси:**
    ```bash
    # Убедитесь, что у вас есть файл proxies.txt
    python cli.py --target https://protected.com --method HTTPS-BYPASS --threads 20 --duration 300 --use-proxy --proxy-file proxies.txt --proxy-type socks5
    ```

📬 Обратная связь

Если у вас есть идеи, предложения по улучшению или вы хотите внести вклад в развитие проекта — не стесняйтесь связаться со мной:

📨 Telegram: @a11_89d

Любая помощь и обратная связь приветствуются!

### Лицензия

Этот проект распространяется под лицензией MIT. Подробности смотрите в файле [LICENSE](LICENSE).

---

## 🇬🇧 English

### About The Project

**CyberBlitz** is a versatile and powerful stress-testing tool designed for security professionals and developers. It allows for the simulation of a wide range of attacks, from low-level network floods (Layer 4) to sophisticated application-level attacks (Layer 7) aimed at bypassing modern security systems.

The application can be operated in two ways:
1.  **Graphical User Interface (GUI):** Built with `PyQt5`, it provides an intuitive interface for managing all features, monitoring metrics in real-time, and accessing advanced settings.
2.  **Command-Line Interface (CLI):** Created with `click`, it is ideal for automation, script integration, and quick attack execution.

### Key Features

*   **Layer 7 (Application Level) Attacks:**
    *   **Advanced Cloudflare Bypass (`HTTPS-BYPASS`, `CF-TLS`):** Utilizes `tls-client` to mimic browser TLS fingerprints and `Playwright` to automatically solve JavaScript challenges and obtain validation cookies (`cf_clearance`).
    *   **Real Browser Emulation (`HTTP-BROWSER`):** Launches a full-fledged browser to simulate user actions (clicks, scrolling), making the traffic indistinguishable from legitimate users.
    *   **Locust Integration (`LOCUST`):** Enables distributed stress testing to generate immense load.

*   **Layer 4 (Network Level) Attacks:**
    *   **TCP/UDP Floods:** Includes `TCP-SYN`, `TCP-ACK`, and various `UDP` flood types.
    *   **Amplification Attacks (AMP):** Uses vulnerable NTP, DNS, and STUN servers to multiply attack traffic.
    *   **Specialized Attacks:** Methods targeting game servers, services (`SSH`), and "slow-rate" attacks like `Slowloris`.

*   **Bypassing Anti-DDoS Providers:**
    *   CyberBlitz is designed to bypass not only **Cloudflare** and **OVH** but also other providers that rely on client-side challenges. Thanks to its browser emulation and advanced spoofing, it can be effective against **DDoS-Guard, StormWall, Imperva**, and other systems that analyze client behavior, TLS fingerprints, and headers.

*   **Advanced Anonymity & Spoofing:**
    *   **Tor Manager:** Automatically launches and rotates multiple independent Tor circuits for maximum anonymity.
    *   **Detailed Spoofing:** Generates a complete browser persona, including modern `Sec-CH-UA` headers, language, timezone, screen resolution, and realistic `Referer` headers.

*   **Monitoring & Reporting:**
    *   Collects real-time metrics (RPS, latency) and exports them to `JSON`, `CSV`, or `HTML` reports with graphs.

### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/A11gitss/CyberBlitz-DDoS.git
    cd CyberBlitz-DDoS
    ```

2.  **Create and activate a virtual environment (recommended):**
    ```bash
    python -m venv venv
    # Windows
    .\venv\Scripts\activate
    # macOS/Linux
    source venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Install Playwright browser engines:**
    ```bash
    playwright install
    ```

### How To Use

#### Graphical User Interface (GUI)

To launch the GUI, run the command:
```bash
python gui.py
```
The interface allows you to easily configure all attack parameters: select the target, port, method, number of threads, and duration. In the "Network & Spoofing" and "Advanced" tabs, you can enable Tor/proxy and fine-tune browser emulation settings.

#### Command-Line Interface (CLI)

**General format:**
```bash
python cli.py --target <IP_OR_URL> --method <METHOD> [OPTIONS]
```

**Attack launch examples:**

*   **Simple UDP flood on an IP address:**
    ```bash
    python cli.py --target 1.2.3.4 --port 80 --method UDP --threads 100 --duration 120
    ```

*   **HTTPS flood on a website using Tor:**
    ```bash
    python cli.py --target https://example.com --method HTTPS-FLOODER --threads 50 --duration 300 --use-tor
    ```

*   **Browser emulation attack to bypass basic protection:**
    ```bash
    python cli.py --target https://example.com --method HTTP-BROWSER --threads 10 --duration 180 --clicks --scroll
    ```

*   **Advanced Cloudflare bypass using TLS fingerprints and proxies:**
    ```bash
    # Make sure you have a proxies.txt file
    python cli.py --target https://protected.com --method HTTPS-BYPASS --threads 20 --duration 300 --use-proxy --proxy-file proxies.txt --proxy-type socks5
    ```

📬 Feedback

If you have ideas, suggestions for improvement, or want to contribute — feel free to reach out:

📨 Telegram: @a11_89d

Any help or feedback is welcome!

### License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---
*Note: The author has not fully translated the repository's internal code and comments into English. The primary language of the codebase is Russian.*