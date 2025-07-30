ATTACK_METHODS = {
    'L4': {
        'AMP': ['NTP', 'DNS', 'STUN', 'WSD', 'SADP'],
        'TCP': ['TCP-ACK', 'TCP-SYN', 'TCP-BYPASS', 'OVH-TCP'],
        'UDP': ['UDP', 'UDP-VSE', 'UDP-BYPASS'],
        'GAME': ['GAME', 'GAME-MC', 'GAME-WARZONE', 'GAME-R6', 'FIVEM-KILL'],
        'SPECIAL': ['SSH', 'GAME-KILL', 'TCP-SOCKET', 'DISCORD', 'SLOWLORIS']
    },
    'L7': {
        'HTTP/HTTPS': ['HTTPS-FLOODER', 'HTTPS-BYPASS', 'HTTP-BROWSER', 'HTTPS-ARTERMIS'],
        'DISTRIBUTED': ['LOCUST'],
        'BOTNET': ['UDPBYPASS-BOT', 'OVH-HEX', 'GREBOT', 'TCPBOT']
    }
}

BROWSER_CONFIGS = {
    'EMULATION': ['none', 'selenium', 'playwright'],
    'BEHAVIORS': ['clicks', 'scroll', 'form_fill', 'navigation'],
    'PROFILES': ['chrome_120', 'chrome_117', 'firefox_118', 'safari_16_5', 'okhttp4_android_11']
}

PROXY_CONFIGS = {
    'TYPES': ['socks4', 'socks5', 'http', 'https'],
    'ROTATION': ['round_robin', 'random', 'sticky'],
    'AUTH_METHODS': ['none', 'username_password', 'key_based'],
    'SOURCES': ['api', 'file'],
    'FILE_FORMAT': 'IP:PORT format, one proxy per line'
}

TLS_CONFIGS = {
    'VERSIONS': ['TLS 1.2', 'TLS 1.3'],
    'CIPHERS': ['default', 'modern', 'intermediate', 'old'],
    'FINGERPRINTS': ['chrome', 'firefox', 'ios', 'android']
}

MONITORING_OPTIONS = {
    'METRICS': ['requests_per_second', 'latency', 'success_rate', 'bandwidth'],
    'EXPORT_FORMATS': ['csv', 'json', 'html'],
    'GRAPHS': ['line', 'bar', 'pie']
}
