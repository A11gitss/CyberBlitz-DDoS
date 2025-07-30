from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, 
    QGroupBox, QCheckBox, QComboBox, QSpinBox, 
    QLabel, QLineEdit, QPushButton, QGridLayout,
    QTableWidget, QTableWidgetItem, QWidget
)
from PyQt5.QtCore import Qt
from gui_constants import *

class AdvancedSettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Advanced Settings")
        self.setGeometry(200, 200, 800, 600)
        self.settings = {}
        if parent:
            self.setStyleSheet(parent.styleSheet())
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        tabs = QTabWidget()
        
        # Attack Methods Tab
        attack_tab = QWidget()
        attack_tab.setObjectName("attack_tab")
        attack_layout = QGridLayout()
        
        # L4 Methods
        l4_group = QGroupBox("Layer 4 Methods")
        l4_group.setObjectName("Layer 4 Methods")
        l4_layout = QVBoxLayout()
        for category, methods in ATTACK_METHODS['L4'].items():
            category_group = QGroupBox(category)
            category_group.setObjectName(f"L4_{category}")
            category_layout = QVBoxLayout()
            for method in methods:
                checkbox = QCheckBox(method)
                checkbox.setObjectName(f"method_{method}")
                category_layout.addWidget(checkbox)
            category_group.setLayout(category_layout)
            l4_layout.addWidget(category_group)
        l4_group.setLayout(l4_layout)
        
        # L7 Methods
        l7_group = QGroupBox("Layer 7 Methods")
        l7_group.setObjectName("Layer 7 Methods")
        l7_layout = QVBoxLayout()
        for category, methods in ATTACK_METHODS['L7'].items():
            category_group = QGroupBox(category)
            category_group.setObjectName(f"L7_{category}")
            category_layout = QVBoxLayout()
            for method in methods:
                checkbox = QCheckBox(method)
                checkbox.setObjectName(f"method_{method}")
                category_layout.addWidget(checkbox)
            category_group.setLayout(category_layout)
            l7_layout.addWidget(category_group)
        l7_group.setLayout(l7_layout)
        
        attack_layout.addWidget(l4_group, 0, 0)
        attack_layout.addWidget(l7_group, 0, 1)
        attack_tab.setLayout(attack_layout)
        
        # Browser Settings Tab
        browser_tab = QWidget()
        browser_layout = QVBoxLayout()
        
        emulation_group = QGroupBox("Browser Emulation")
        emulation_group.setObjectName("Browser Emulation")
        emulation_layout = QGridLayout()
        
        # Emulation type
        emulation_layout.addWidget(QLabel("Emulation Type:"), 0, 0)
        emulation_combo = QComboBox()
        emulation_combo.setObjectName("emulation_type")
        emulation_combo.addItems(BROWSER_CONFIGS['EMULATION'])
        emulation_layout.addWidget(emulation_combo, 0, 1)
        
        # Browser profile
        emulation_layout.addWidget(QLabel("Browser Profile:"), 1, 0)
        profile_combo = QComboBox()
        profile_combo.setObjectName("browser_profile")
        profile_combo.addItems(BROWSER_CONFIGS['PROFILES'])
        emulation_layout.addWidget(profile_combo, 1, 1)
        
        # Browser profile
        emulation_layout.addWidget(QLabel("Browser Profile:"), 1, 0)
        profile_combo = QComboBox()
        profile_combo.addItems(BROWSER_CONFIGS['PROFILES'])
        emulation_layout.addWidget(profile_combo, 1, 1)
        
        # Behaviors
        behavior_group = QGroupBox("Behaviors")
        behavior_group.setObjectName("behavior_group")
        behavior_layout = QVBoxLayout()
        for behavior in BROWSER_CONFIGS['BEHAVIORS']:
            checkbox = QCheckBox(behavior.replace('_', ' ').title())
            checkbox.setObjectName(f"behavior_{behavior}")
            behavior_layout.addWidget(checkbox)
        behavior_group.setLayout(behavior_layout)
        emulation_layout.addWidget(behavior_group, 2, 0, 1, 2)
        
        emulation_group.setLayout(emulation_layout)
        browser_layout.addWidget(emulation_group)
        browser_tab.setLayout(browser_layout)
        
        # Proxy Settings Tab
        proxy_tab = QWidget()
        proxy_layout = QVBoxLayout()
        
        proxy_group = QGroupBox("Proxy Configuration")
        proxy_group.setObjectName("Proxy Configuration")
        proxy_grid = QGridLayout()
        
        # Proxy type
        proxy_grid.addWidget(QLabel("Proxy Type:"), 0, 0)
        proxy_type = QComboBox()
        proxy_type.setObjectName("proxy_type")
        proxy_type.addItems(PROXY_CONFIGS['TYPES'])
        proxy_grid.addWidget(proxy_type, 0, 1)
        
        # Rotation strategy
        proxy_grid.addWidget(QLabel("Rotation Strategy:"), 1, 0)
        rotation = QComboBox()
        rotation.setObjectName("rotation_type")
        rotation.addItems(PROXY_CONFIGS['ROTATION'])
        proxy_grid.addWidget(rotation, 1, 1)
        
        # Auth method
        proxy_grid.addWidget(QLabel("Authentication:"), 2, 0)
        auth = QComboBox()
        auth.setObjectName("auth_type")
        auth.addItems(PROXY_CONFIGS['AUTH_METHODS'])
        proxy_grid.addWidget(auth, 2, 1)
        
        proxy_group.setLayout(proxy_grid)
        proxy_layout.addWidget(proxy_group)
        proxy_tab.setLayout(proxy_layout)
        
        # TLS Settings Tab
        tls_tab = QWidget()
        tls_layout = QVBoxLayout()
        
        tls_group = QGroupBox("TLS Configuration")
        tls_group.setObjectName("TLS Configuration")
        tls_grid = QGridLayout()
        
        # TLS version
        tls_grid.addWidget(QLabel("TLS Version:"), 0, 0)
        tls_version = QComboBox()
        tls_version.setObjectName("tls_version")
        tls_version.addItems(TLS_CONFIGS['VERSIONS'])
        tls_grid.addWidget(tls_version, 0, 1)
        
        # Cipher suite
        tls_grid.addWidget(QLabel("Cipher Suite:"), 1, 0)
        cipher = QComboBox()
        cipher.addItems(TLS_CONFIGS['CIPHERS'])
        tls_grid.addWidget(cipher, 1, 1)
        
        # Fingerprint
        tls_grid.addWidget(QLabel("TLS Fingerprint:"), 2, 0)
        fingerprint = QComboBox()
        fingerprint.addItems(TLS_CONFIGS['FINGERPRINTS'])
        tls_grid.addWidget(fingerprint, 2, 1)
        
        tls_group.setLayout(tls_grid)
        tls_layout.addWidget(tls_group)
        tls_tab.setLayout(tls_layout)
        
        # Monitoring Tab
        monitoring_tab = QWidget()
        monitoring_layout = QVBoxLayout()
        
        metrics_group = QGroupBox("Metrics & Monitoring")
        metrics_group.setObjectName("Metrics & Monitoring")
        metrics_layout = QVBoxLayout()
        
        # Metrics selection
        for metric in MONITORING_OPTIONS['METRICS']:
            checkbox = QCheckBox(metric.replace('_', ' ').title())
            checkbox.setObjectName(f"metric_{metric}")
            metrics_layout.addWidget(checkbox)
            
        # Export format
        export_layout = QHBoxLayout()
        export_layout.addWidget(QLabel("Export Format:"))
        export_combo = QComboBox()
        export_combo.setObjectName("export_format")
        export_combo.addItems(MONITORING_OPTIONS['EXPORT_FORMATS'])
        export_layout.addWidget(export_combo)
        
        metrics_group.setLayout(metrics_layout)
        monitoring_layout.addWidget(metrics_group)
        monitoring_layout.addLayout(export_layout)
        monitoring_tab.setLayout(monitoring_layout)
        
        # Add all tabs
        tabs.addTab(attack_tab, "Attack Methods")
        tabs.addTab(browser_tab, "Browser Settings")
        tabs.addTab(proxy_tab, "Proxy Settings")
        tabs.addTab(tls_tab, "TLS Settings")
        tabs.addTab(monitoring_tab, "Monitoring")
        
        layout.addWidget(tabs)
        
        # Buttons
        button_layout = QHBoxLayout()
        save_button = QPushButton("Save")
        save_button.clicked.connect(self.accept)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
    def get_selected_methods(self):
        methods = []
        # Находим все группы категорий атак
        l4_group = self.findChild(QGroupBox, "Layer 4 Methods")
        l7_group = self.findChild(QGroupBox, "Layer 7 Methods")
        
        # Собираем методы из обоих групп
        for group in [l4_group, l7_group]:
            if group:
                for category_group in group.findChildren(QGroupBox):
                    for checkbox in category_group.findChildren(QCheckBox):
                        if checkbox.isChecked():
                            methods.append(checkbox.text())
                            
        return methods or None  # Возвращаем None если нет выбранных методов
        
    def get_browser_settings(self):
        settings = {
            'emulation': None,
            'profile': None,
            'behaviors': []
        }
        
        emulation_group = self.findChild(QGroupBox, "Browser Emulation")
        if emulation_group:
            for combo in emulation_group.findChildren(QComboBox):
                if combo.objectName() == "emulation_type":
                    settings['emulation'] = combo.currentText()
                elif combo.objectName() == "browser_profile":
                    settings['profile'] = combo.currentText()
                    
        behavior_group = self.findChild(QGroupBox, "behavior_group")
        if behavior_group:
            for checkbox in behavior_group.findChildren(QCheckBox):
                if checkbox.isChecked():
                    settings['behaviors'].append(checkbox.text().lower())
                    
        return settings
        
    def get_proxy_settings(self):
        settings = {
            'type': None,
            'rotation': None,
            'auth': None
        }
        
        proxy_group = self.findChild(QGroupBox, "Proxy Configuration")
        if proxy_group:
            for combo in proxy_group.findChildren(QComboBox):
                if combo.objectName() == "proxy_type":
                    settings['type'] = combo.currentText()
                elif combo.objectName() == "rotation_type":
                    settings['rotation'] = combo.currentText()
                elif combo.objectName() == "auth_type":
                    settings['auth'] = combo.currentText()
                    
        return settings
        
    def get_tls_settings(self):
        settings = {
            'version': None,
            'cipher': None,
            'fingerprint': None
        }
        
        tls_group = self.findChild(QGroupBox, "TLS Configuration")
        if tls_group:
            for combo in tls_group.findChildren(QComboBox):
                if combo.objectName() == "tls_version":
                    settings['version'] = combo.currentText()
                elif combo.objectName() == "cipher_suite":
                    settings['cipher'] = combo.currentText()
                elif combo.objectName() == "tls_fingerprint":
                    settings['fingerprint'] = combo.currentText()
                    
        return settings
        
    def get_monitoring_settings(self):
        settings = {
            'metrics': [],
            'export_format': None
        }
        
        metrics_group = self.findChild(QGroupBox, "Metrics & Monitoring")
        if metrics_group:
            for checkbox in metrics_group.findChildren(QCheckBox):
                if checkbox.isChecked():
                    settings['metrics'].append(checkbox.text().lower())
                    
        export_combo = self.findChild(QComboBox, "export_format")
        if export_combo:
            settings['export_format'] = export_combo.currentText()
            
        return settings
        
    def get_all_settings(self):
        self.settings = {
            'attack_methods': self.get_selected_methods(),
            'browser': self.get_browser_settings(),
            'proxy': self.get_proxy_settings(),
            'tls': self.get_tls_settings(),
            'monitoring': self.get_monitoring_settings()
        }
        return self.settings
