import asyncio
import random
from typing import Optional, Dict
import aiohttp
from aiohttp_proxy import ProxyConnector
import stem
import stem.control
import stem.process
import os
import sys
import logging
import psutil
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)

class TorCircuitManager:
    _instance = None
    _lock = asyncio.Lock()

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, base_socks_port: int = 9050, max_instances: int = 100):
        if not hasattr(self, 'initialized'):
            self.base_socks_port = base_socks_port
            self.max_instances = max_instances
            self.tor_processes: Dict[int, stem.process.launch_tor_with_config] = {}
            self.control_ports: Dict[int, int] = {}
            self.next_port = base_socks_port
            self.active_circuits: Dict[int, asyncio.Task] = {}
            self.initialized = True

    def _is_port_available(self, port: int) -> bool:
        for conn in psutil.net_connections():
            if conn.laddr.port == port:
                return False
        return True

    def _get_next_available_ports(self) -> tuple[int, int]:
        socks_port = self.next_port
        while not self._is_port_available(socks_port):
            socks_port += 2
        
        control_port = socks_port + 1
        while not self._is_port_available(control_port):
            control_port += 2
            
        self.next_port = max(socks_port, control_port) + 1
        return socks_port, control_port

    async def create_tor_circuit(self) -> Optional[tuple[int, int]]:
        try:
            socks_port, control_port = self._get_next_available_ports()
            tor_data_dir = Path(tempfile.gettempdir()) / f"tor_data_{socks_port}"
            tor_data_dir.mkdir(exist_ok=True)

            tor_config = {
                'SocksPort': str(socks_port),
                'ControlPort': str(control_port),
                'DataDirectory': str(tor_data_dir),
                'CookieAuthentication': '1',
                'MaxCircuitDirtiness': '60',
                '__DisablePredictedCircuits': '1',
                '__LeaveStreamsUnattached': '1'
            }

            tor_path = 'tor.exe' if sys.platform == 'win32' else 'tor'
            if sys.platform == 'win32' and not os.path.exists(tor_path):
                 if os.path.exists(os.path.join(os.getcwd(), "tor", "tor.exe")):
                     tor_path = os.path.join(os.getcwd(), "tor", "tor.exe")
                 else:
                    logger.warning("tor.exe не найден. Пожалуйста, установите Tor.")
                    return None

            tor_process = stem.process.launch_tor_with_config(
                config=tor_config,
                tor_cmd=tor_path,
                take_ownership=True,
                init_msg_handler=lambda line: logger.debug(f"Tor init: {line}")
            )

            if tor_process:
                self.tor_processes[socks_port] = tor_process
                self.control_ports[socks_port] = control_port
                logger.info(f"Запущена цепочка Tor на SOCKS порту {socks_port}")
                return socks_port, control_port

        except Exception as e:
            logger.error(f"Не удалось создать цепочку Tor: {e}")
        return None

    async def create_aiohttp_connector(self, socks_port: int) -> Optional[ProxyConnector]:
        try:
            return ProxyConnector.from_url(f"socks5://127.0.0.1:{socks_port}", ssl=False)
        except Exception as e:
            logger.error(f"Не удалось создать коннектор для порта {socks_port}: {e}")
            return None

    async def _circuit_maintenance(self, socks_port: int):
        while True:
            await asyncio.sleep(60)
            try:
                with stem.control.Controller.from_port(port=self.control_ports[socks_port]) as controller:
                    controller.authenticate()
                    controller.signal(stem.Signal.NEWNYM)
                    logger.debug(f"Обновлена цепочка Tor для порта {socks_port}")
            except Exception as e:
                logger.error(f"Ошибка при обновлении цепочки Tor: {e}")
                break 

    async def get_circuit(self) -> Optional[int]:
        async with self._lock:
            if len(self.tor_processes) >= self.max_instances:
                return random.choice(list(self.tor_processes.keys()))
            
            result = await self.create_tor_circuit()
            if result:
                socks_port, control_port = result
                self.active_circuits[socks_port] = asyncio.create_task(
                    self._circuit_maintenance(socks_port)
                )
                return socks_port
            return None

    async def cleanup(self):
        async with self._lock:
            for task in self.active_circuits.values():
                task.cancel()
            if self.active_circuits:
                await asyncio.gather(*self.active_circuits.values(), return_exceptions=True)
            
            for process in self.tor_processes.values():
                try:
                    process.kill()
                except Exception as e:
                    logger.debug(f"Ошибка при остановке процесса Tor: {e}")
            
            self.tor_processes.clear()
            self.control_ports.clear()
            self.active_circuits.clear()
            logger.info("Все цепочки Tor очищены.")

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.cleanup()