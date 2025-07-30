from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QTabWidget, QWidget,
    QListWidget, QHBoxLayout, QPushButton, QLineEdit,
    QMessageBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QLabel, QComboBox, QCheckBox, QSpinBox, QDoubleSpinBox,
    QGroupBox, QGridLayout, QScrollArea, QInputDialog
)
from config import CONFIG, logger
from utils.spoofing import BROWSER_PROFILES
import random

class UserAgentMatrixDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("User-Agent Configuration")
        self.setGeometry(100, 100, 1000, 800)
        self.setStyleSheet(parent.styleSheet())

        # Загрузка конфигурации
        self.matrix_data = CONFIG["spoofing"].get("ua_matrix", {})
        self.os_list = sorted(BROWSER_PROFILES.keys())
        self.browser_list = []
        for os_browsers in BROWSER_PROFILES.values():
            self.browser_list.extend(os_browsers.keys())
        self.browser_list = sorted(set(self.browser_list))

        # Создаем scroll area для всего контента
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # Создаем основной layout
        main_layout = QVBoxLayout()
        
        # Группа матрицы UA
        matrix_group = QGroupBox("User-Agent Matrix")
        matrix_layout = QVBoxLayout()
        
        # Таблица UA
        self.table = QTableWidget(len(self.os_list), len(self.browser_list))
        self.table.setHorizontalHeaderLabels(self.browser_list)
        self.table.setVerticalHeaderLabels(self.os_list)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.populate_table()
        matrix_layout.addWidget(self.table)
        matrix_group.setLayout(matrix_layout)
        scroll_layout.addWidget(matrix_group)

        # Группа настроек мобильных устройств
        mobile_group = QGroupBox("Mobile Device Settings")
        mobile_layout = QGridLayout()
        
        self.mobile_enabled = QCheckBox("Enable Mobile Emulation")
        self.mobile_enabled.setChecked(CONFIG["spoofing"].get("enable_mobile", True))
        mobile_layout.addWidget(self.mobile_enabled, 0, 0)
        
        mobile_layout.addWidget(QLabel("Mobile Screen Resolutions:"), 1, 0)
        self.mobile_resolutions = QListWidget()
        self.mobile_resolutions.addItems(CONFIG["spoofing"].get("mobile_screen_pool", 
            ["375x812", "414x896", "360x800", "390x844"]))
        mobile_layout.addWidget(self.mobile_resolutions, 2, 0)
        
        mobile_group.setLayout(mobile_layout)
        scroll_layout.addWidget(mobile_group)

        # Группа настроек версий
        version_group = QGroupBox("Browser Version Settings")
        version_layout = QGridLayout()
        
        version_layout.addWidget(QLabel("Minimum Chrome Version:"), 0, 0)
        self.chrome_min = QSpinBox()
        self.chrome_min.setRange(70, 120)
        self.chrome_min.setValue(CONFIG["spoofing"].get("chrome_min_version", 90))
        version_layout.addWidget(self.chrome_min, 0, 1)
        
        version_layout.addWidget(QLabel("Maximum Chrome Version:"), 1, 0)
        self.chrome_max = QSpinBox()
        self.chrome_max.setRange(70, 120)
        self.chrome_max.setValue(CONFIG["spoofing"].get("chrome_max_version", 120))
        version_layout.addWidget(self.chrome_max, 1, 1)
        
        version_layout.addWidget(QLabel("Browser Selection Weights:"), 2, 0)
        weights_layout = QHBoxLayout()
        self.browser_weights = {}
        for browser in ["Chrome", "Firefox", "Safari", "Edge"]:
            weight_layout = QVBoxLayout()
            weight_layout.addWidget(QLabel(browser))
            weight_spin = QDoubleSpinBox()
            weight_spin.setRange(0.0, 1.0)
            weight_spin.setSingleStep(0.1)
            weight_spin.setValue(CONFIG["spoofing"].get(f"{browser.lower()}_weight", 0.25))
            self.browser_weights[browser] = weight_spin
            weight_layout.addWidget(weight_spin)
            weights_layout.addLayout(weight_layout)
        version_layout.addLayout(weights_layout, 3, 0, 1, 2)
        
        version_group.setLayout(version_layout)
        scroll_layout.addWidget(version_group)

        scroll.setWidget(scroll_widget)
        main_layout.addWidget(scroll)

        # Кнопки
        buttons_layout = QHBoxLayout()
        save_button = QPushButton("Save & Close")
        save_button.clicked.connect(self.save_and_close)
        reset_button = QPushButton("Reset to Defaults")
        reset_button.clicked.connect(self.reset_to_defaults)
        buttons_layout.addWidget(reset_button)
        buttons_layout.addWidget(save_button)
        main_layout.addLayout(buttons_layout)

        layout = QVBoxLayout(self)
        self.table = QTableWidget(len(self.os_list), len(self.browser_list))
        self.table.setHorizontalHeaderLabels(self.browser_list)
        self.table.setVerticalHeaderLabels(self.os_list)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        self.populate_table()
        layout.addWidget(self.table)

        save_button = QPushButton("Save & Close")
        save_button.clicked.connect(self.save_and_close)
        layout.addWidget(save_button)

    def populate_table(self):
        for r, os_name in enumerate(self.os_list):
            for c, browser_name in enumerate(self.browser_list):
                item = QTableWidgetItem()
                item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
                is_enabled = self.matrix_data.get(os_name, {}).get(browser_name, False)
                item.setCheckState(Qt.Checked if is_enabled else Qt.Unchecked)
                self.table.setItem(r, c, item)

    def reset_to_defaults(self):
        # Сброс матрицы UA
        for r, os_name in enumerate(self.os_list):
            for c, browser_name in enumerate(self.browser_list):
                item = self.table.item(r, c)
                default_enabled = browser_name in ["Chrome", "Firefox"] and os_name in ["Windows", "Linux"]
                item.setCheckState(Qt.Checked if default_enabled else Qt.Unchecked)
        
        # Сброс мобильных настроек
        self.mobile_enabled.setChecked(True)
        self.mobile_resolutions.clear()
        self.mobile_resolutions.addItems(["375x812", "414x896", "360x800", "390x844"])
        
        # Сброс версий браузеров
        self.chrome_min.setValue(90)
        self.chrome_max.setValue(120)
        
        # Сброс весов
        default_weights = {"Chrome": 0.4, "Firefox": 0.3, "Safari": 0.2, "Edge": 0.1}
        for browser, weight in default_weights.items():
            self.browser_weights[browser].setValue(weight)

    def save_and_close(self):
        # Сохранение матрицы UA
        if "spoofing" not in CONFIG:
            CONFIG["spoofing"] = {}
        if "ua_matrix" not in CONFIG["spoofing"]:
            CONFIG["spoofing"]["ua_matrix"] = {}
            
        for r, os_name in enumerate(self.os_list):
            for c, browser_name in enumerate(self.browser_list):
                is_checked = self.table.item(r, c).checkState() == Qt.Checked
                if os_name not in CONFIG["spoofing"]["ua_matrix"]:
                    CONFIG["spoofing"]["ua_matrix"][os_name] = {}
                CONFIG["spoofing"]["ua_matrix"][os_name][browser_name] = is_checked
        
        # Сохранение мобильных настроек
        CONFIG["spoofing"]["enable_mobile"] = self.mobile_enabled.isChecked()
        CONFIG["spoofing"]["mobile_screen_pool"] = [
            self.mobile_resolutions.item(i).text()
            for i in range(self.mobile_resolutions.count())
        ]
        
        # Сохранение настроек версий
        CONFIG["spoofing"]["chrome_min_version"] = self.chrome_min.value()
        CONFIG["spoofing"]["chrome_max_version"] = self.chrome_max.value()
        
        # Сохранение весов
        for browser, spin in self.browser_weights.items():
            CONFIG["spoofing"][f"{browser.lower()}_weight"] = spin.value()
        
        logger.info("Настройки User-Agent обновлены.")
        self.accept()

class HeaderConfigDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Header Configuration")
        self.setGeometry(100, 100, 1000, 800)
        self.setStyleSheet(parent.styleSheet())
        
        main_layout = QVBoxLayout(self)
        
        # Создаем scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # Группа основных заголовков
        basic_group = QGroupBox("Basic Headers Configuration")
        basic_layout = QGridLayout()
        
        # Настройка Accept заголовков
        basic_layout.addWidget(QLabel("Accept Headers:"), 0, 0)
        self.accept_headers = QListWidget()
        default_accepts = [
            "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        ]
        self.accept_headers.addItems(CONFIG["spoofing"].get("accept_headers", default_accepts))
        basic_layout.addWidget(self.accept_headers, 1, 0)
        
        # Настройка языков
        basic_layout.addWidget(QLabel("Languages:"), 0, 1)
        self.languages = QListWidget()
        self.languages.addItems(CONFIG["spoofing"].get("language_pool", ["en-US,en;q=0.9", "en-GB,en;q=0.8"]))
        basic_layout.addWidget(self.languages, 1, 1)
        
        basic_group.setLayout(basic_layout)
        scroll_layout.addWidget(basic_group)
        
        # Группа настроек безопасности
        security_group = QGroupBox("Security Headers")
        security_layout = QVBoxLayout()
        
        self.security_options = {
            "enable_dnt": QCheckBox("Enable Do Not Track (DNT)"),
            "enable_upgrade_insecure": QCheckBox("Enable Upgrade-Insecure-Requests"),
            "enable_sec_fetch": QCheckBox("Enable Sec-Fetch Headers"),
            "randomize_ordered_headers": QCheckBox("Randomize Header Order"),
            "spoof_ip": QCheckBox("Spoof IP in X-Forwarded-For"),
            "spoof_asn": QCheckBox("Spoof ASN"),
        }
        
        for option, checkbox in self.security_options.items():
            checkbox.setChecked(CONFIG["spoofing"].get(option, True))
            security_layout.addWidget(checkbox)
        
        security_group.setLayout(security_layout)
        scroll_layout.addWidget(security_group)
        
        # Группа рефереров
        referer_group = QGroupBox("Referer Configuration")
        referer_layout = QVBoxLayout()
        
        self.smart_referer = QCheckBox("Enable Smart Referer Generation")
        self.smart_referer.setChecked(CONFIG["spoofing"].get("smart_referer", True))
        referer_layout.addWidget(self.smart_referer)
        
        referer_layout.addWidget(QLabel("Custom Referers:"))
        self.referer_list = QListWidget()
        self.referer_list.addItems(CONFIG["spoofing"].get("referer_pool", []))
        referer_layout.addWidget(self.referer_list)
        
        referer_buttons = QHBoxLayout()
        add_referer = QPushButton("Add Referer")
        add_referer.clicked.connect(lambda: self.add_to_list(self.referer_list))
        remove_referer = QPushButton("Remove Selected")
        remove_referer.clicked.connect(lambda: self.remove_from_list(self.referer_list))
        referer_buttons.addWidget(add_referer)
        referer_buttons.addWidget(remove_referer)
        referer_layout.addLayout(referer_buttons)
        
        referer_group.setLayout(referer_layout)
        scroll_layout.addWidget(referer_group)
        
        # Группа настроек прокси
        proxy_group = QGroupBox("Proxy Headers Configuration")
        proxy_layout = QVBoxLayout()
        
        self.proxy_options = {
            "real_ip": QCheckBox("Add X-Real-IP"),
            "via": QCheckBox("Add Via Header"),
            "forwarded": QCheckBox("Add Forwarded Header"),
            "client_ip": QCheckBox("Add Client-IP")
        }
        
        for option, checkbox in self.proxy_options.items():
            checkbox.setChecked(CONFIG["spoofing"].get(f"proxy_{option}", True))
            proxy_layout.addWidget(checkbox)
            
        proxy_group.setLayout(proxy_layout)
        scroll_layout.addWidget(proxy_group)
        
        scroll.setWidget(scroll_widget)
        main_layout.addWidget(scroll)
        
        # Кнопки
        buttons_layout = QHBoxLayout()
        save_button = QPushButton("Save & Close")
        save_button.clicked.connect(self.save_and_close)
        reset_button = QPushButton("Reset to Defaults")
        reset_button.clicked.connect(self.reset_to_defaults)
        buttons_layout.addWidget(reset_button)
        buttons_layout.addWidget(save_button)
        main_layout.addLayout(buttons_layout)
        
    def add_to_list(self, list_widget):
        text, ok = QInputDialog.getText(self, "Add Item", "Enter value:")
        if ok and text:
            list_widget.addItem(text)

    def remove_from_list(self, list_widget):
        for item in list_widget.selectedItems():
            list_widget.takeItem(list_widget.row(item))

    def reset_to_defaults(self):
        # Сброс Accept заголовков
        self.accept_headers.clear()
        self.accept_headers.addItems([
            "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        ])
        
        # Сброс языков
        self.languages.clear()
        self.languages.addItems([
            "en-US,en;q=0.9",
            "en-GB,en;q=0.8",
            "ru-RU,ru;q=0.9,en;q=0.8"
        ])
        
        # Сброс опций безопасности
        for checkbox in self.security_options.values():
            checkbox.setChecked(True)
            
        # Сброс настроек рефереров
        self.smart_referer.setChecked(True)
        self.referer_list.clear()
        self.referer_list.addItems([
            "https://www.google.com/",
            "https://www.bing.com/",
            "https://duckduckgo.com/"
        ])
        
        # Сброс настроек прокси
        for checkbox in self.proxy_options.values():
            checkbox.setChecked(True)

    def save_and_close(self):
        if "spoofing" not in CONFIG:
            CONFIG["spoofing"] = {}
            
        # Сохранение Accept заголовков
        CONFIG["spoofing"]["accept_headers"] = [
            self.accept_headers.item(i).text()
            for i in range(self.accept_headers.count())
        ]
        
        # Сохранение языков
        CONFIG["spoofing"]["language_pool"] = [
            self.languages.item(i).text()
            for i in range(self.languages.count())
        ]
        
        # Сохранение настроек безопасности
        for option, checkbox in self.security_options.items():
            CONFIG["spoofing"][option] = checkbox.isChecked()
            
        # Сохранение настроек рефереров
        CONFIG["spoofing"]["smart_referer"] = self.smart_referer.isChecked()
        CONFIG["spoofing"]["referer_pool"] = [
            self.referer_list.item(i).text()
            for i in range(self.referer_list.count())
        ]
        
        # Сохранение настроек прокси
        for option, checkbox in self.proxy_options.items():
            CONFIG["spoofing"][f"proxy_{option}"] = checkbox.isChecked()
            
        logger.info("Настройки заголовков обновлены.")
        self.accept()

class HeaderPoolsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Header & Spoofing Pools")
        self.setGeometry(150, 150, 600, 500)
        self.setStyleSheet(parent.styleSheet())

        self.pools = {
            "Referer": CONFIG["spoofing"]["referer_pool"],
            "Language": CONFIG["spoofing"]["language_pool"],
            "Timezone": CONFIG["spoofing"]["timezone_pool"],
            "Screen Size": CONFIG["spoofing"]["screen_size_pool"]
        }

        main_layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        
        for name, items in self.pools.items():
            tab = QWidget()
            self.tabs.addTab(tab, name)
            self.setup_tab_ui(tab, name, items)

        main_layout.addWidget(self.tabs)
        
        save_button = QPushButton("Save & Close")
        save_button.clicked.connect(self.save_and_close)
        main_layout.addWidget(save_button)

    def setup_tab_ui(self, tab, pool_name, items):
        layout = QVBoxLayout(tab)
        list_widget = QListWidget()
        list_widget.addItems(items)
        layout.addWidget(list_widget)

        input_layout = QHBoxLayout()
        add_input = QLineEdit()
        add_input.setPlaceholderText("Enter new value...")
        add_button = QPushButton("Add")
        gen_button = QPushButton("Generate & Add")
        remove_button = QPushButton("Remove Selected")

        input_layout.addWidget(add_input)
        input_layout.addWidget(add_button)
        input_layout.addWidget(gen_button)
        layout.addLayout(input_layout)
        layout.addWidget(remove_button)

        # --- Connections ---
        add_button.clicked.connect(lambda: self.add_item(list_widget, add_input))
        gen_button.clicked.connect(lambda: self.generate_item(list_widget, pool_name))
        remove_button.clicked.connect(lambda: self.remove_item(list_widget))

    def add_to_list(self, list_widget):
        text, ok = QInputDialog.getText(self, "Add Item", "Enter value:")
        if ok and text:
            list_widget.addItem(text)

    def remove_from_list(self, list_widget):
        for item in list_widget.selectedItems():
            list_widget.takeItem(list_widget.row(item))

    def reset_to_defaults(self):
        # Сброс Accept заголовков
        self.accept_headers.clear()
        self.accept_headers.addItems([
            "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        ])
        
        # Сброс языков
        self.languages.clear()
        self.languages.addItems([
            "en-US,en;q=0.9",
            "en-GB,en;q=0.8",
            "ru-RU,ru;q=0.9,en;q=0.8"
        ])
        
        # Сброс опций безопасности
        for checkbox in self.security_options.values():
            checkbox.setChecked(True)
            
        # Сброс настроек рефереров
        self.smart_referer.setChecked(True)
        self.referer_list.clear()
        self.referer_list.addItems([
            "https://www.google.com/",
            "https://www.bing.com/",
            "https://duckduckgo.com/"
        ])
        
        # Сброс настроек прокси
        for checkbox in self.proxy_options.values():
            checkbox.setChecked(True)

    def save_and_close(self):
        if "spoofing" not in CONFIG:
            CONFIG["spoofing"] = {}
            
        # Сохранение Accept заголовков
        CONFIG["spoofing"]["accept_headers"] = [
            self.accept_headers.item(i).text()
            for i in range(self.accept_headers.count())
        ]
        
        # Сохранение языков
        CONFIG["spoofing"]["language_pool"] = [
            self.languages.item(i).text()
            for i in range(self.languages.count())
        ]
        
        # Сохранение настроек безопасности
        for option, checkbox in self.security_options.items():
            CONFIG["spoofing"][option] = checkbox.isChecked()
            
        # Сохранение настроек рефереров
        CONFIG["spoofing"]["smart_referer"] = self.smart_referer.isChecked()
        CONFIG["spoofing"]["referer_pool"] = [
            self.referer_list.item(i).text()
            for i in range(self.referer_list.count())
        ]
        
        # Сохранение настроек прокси
        for option, checkbox in self.proxy_options.items():
            CONFIG["spoofing"][f"proxy_{option}"] = checkbox.isChecked()
            
        logger.info("Настройки заголовков обновлены.")
        self.accept()

    def add_item(self, list_widget, add_input):
        #...
        text = add_input.text().strip()
        if text:
            list_widget.addItem(text)
            add_input.clear()
        else:
            QMessageBox.warning(self, "Input Error", "Cannot add an empty value.")

    def remove_item(self, list_widget):
        selected_items = list_widget.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Selection Error", "Please select an item to remove.")
            return
        for item in selected_items:
            list_widget.takeItem(list_widget.row(item))

    def generate_item(self, list_widget, pool_name):
        # Простая генерация случайных значений для примера
        if pool_name == "Referer":
            item = f"https://{random.choice(['google', 'bing', 'duckduckgo'])}.com/search?q=cyberblitz"
        elif pool_name == "Language":
            item = random.choice(["en-GB,en;q=0.9", "es-ES,es;q=0.9", "fr-FR,fr;q=0.9"])
        elif pool_name == "Timezone":
            item = random.choice(["Europe/Paris", "Asia/Tokyo", "Australia/Sydney"])
        elif pool_name == "Screen Size":
            item = f"{random.choice([1440, 1600, 1920])}x{random.choice([900, 1080, 1200])}"
        else:
            item = "Generated-Value"
        list_widget.addItem(item)

    def save_and_close(self):
        for i in range(self.tabs.count()):
            tab_name = self.tabs.tabText(i)
            list_widget = self.tabs.widget(i).findChild(QListWidget)
            items = [list_widget.item(j).text() for j in range(list_widget.count())]
            self.pools[tab_name] = items
        
        # Обновляем глобальный конфиг
        CONFIG["spoofing"]["referer_pool"] = self.pools["Referer"]
        CONFIG["spoofing"]["language_pool"] = self.pools["Language"]
        CONFIG["spoofing"]["timezone_pool"] = self.pools["Timezone"]
        CONFIG["spoofing"]["screen_size_pool"] = self.pools["Screen Size"]
        
        logger.info("Пулы заголовков обновлены.")
        self.accept()
