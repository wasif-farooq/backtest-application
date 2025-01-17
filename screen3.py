import os
import json
import time
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLabel, QPushButton, QHBoxLayout,
    QDateEdit, QComboBox, QLineEdit, QPlainTextEdit
)
from PyQt5.QtCore import QDate
from binance_data import BinanceData


class Screen3(QWidget):
    def __init__(self, mainWindow, parent=None):
        super().__init__(parent)
        self.mainWindow = mainWindow
        self.added_symbols = []
        self.load_symbols()

        main_layout = QVBoxLayout(self)

        # Back button
        self.backButton = QPushButton("Back")
        main_layout.addWidget(self.backButton)
        self.backButton.clicked.connect(self.goBack)

        # Log panel for download logs
        self.log_text_edit = QPlainTextEdit()
        self.log_text_edit.setReadOnly(True)
        main_layout.addWidget(QLabel("Download Logs:"))
        main_layout.addWidget(self.log_text_edit)

        # Section 1: Form to add new symbol
        form_layout = QFormLayout()
        form_layout.setSpacing(10)

        self.start_date_edit = QDateEdit()
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDate(QDate.currentDate())

        self.end_date_edit = QDateEdit()
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDate(QDate.currentDate())

        self.symbol_edit = QLineEdit()

        self.timeframe_combo = QComboBox()
        self.timeframe_combo.addItems([
            "1 minute", "3 minute", "5 minute", "15 minute",
            "30 minute", "1 hour", "4 hour", "1 day"
        ])

        form_layout.addRow("Start Date:", self.start_date_edit)
        form_layout.addRow("End Date:", self.end_date_edit)
        form_layout.addRow("Symbol:", self.symbol_edit)
        form_layout.addRow("Timeframe:", self.timeframe_combo)

        self.add_symbol_button = QPushButton("Add Symbol")
        form_layout.addRow(self.add_symbol_button)

        main_layout.addLayout(form_layout)

        # Section 2: List of added symbols
        self.symbols_layout = QVBoxLayout()
        main_layout.addLayout(self.symbols_layout)

        self.add_symbol_button.clicked.connect(self.add_symbol)

        self.update_symbol_list()

    def load_symbols(self):
        try:
            with open('added_symbols.json', 'r') as f:
                self.added_symbols = json.load(f)
        except Exception:
            self.added_symbols = []

    def save_symbols(self):
        with open('added_symbols.json', 'w') as f:
            json.dump(self.added_symbols, f)

    def add_symbol(self):
        start_date = self.start_date_edit.date().toPyDate()
        end_date = self.end_date_edit.date().toPyDate()
        symbol = self.symbol_edit.text().strip().upper()
        timeframe_text = self.timeframe_combo.currentText()

        timeframe_map = {
            "1 minute": "1m", "3 minute": "3m", "5 minute": "5m",
            "15 minute": "15m", "30 minute": "30m",
            "1 hour": "1h", "4 hour": "4h", "1 day": "1d"
        }
        interval = timeframe_map.get(timeframe_text, "1m")

        if not symbol:
            self.log_text_edit.appendPlainText("Symbol cannot be empty.")
            return

        self.log_text_edit.appendPlainText(
            f"Starting download for {symbol} {interval}..."
        )

        start_time = int(time.mktime(start_date.timetuple()) * 1000)
        end_time = int(time.mktime(end_date.timetuple()) * 1000)

        API_URL = "https://fapi.binance.com"
        binance_data = BinanceData(
            api_url=API_URL, symbol=symbol, interval=interval)

        current_start_time = start_time
        all_data = []

        try:
            while current_start_time < end_time:
                self.log_text_edit.appendPlainText(
                    f"Fetching data from {time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(current_start_time / 1000))}..."
                )
                chunk_data = binance_data.fetch_kline_data(
                    start_time=current_start_time, end_time=end_time, limit=500
                )
                if not chunk_data:
                    self.log_text_edit.appendPlainText(
                        f"No more data available for {symbol} {interval}."
                    )
                    break

                all_data.extend(chunk_data)
                # Move to the next time range
                current_start_time = chunk_data[-1][0] + 1

                # Introduce a small delay to avoid hitting API rate limits
                time.sleep(0.1)

            if all_data:
                binance_data.process_and_save_data(all_data)
                self.log_text_edit.appendPlainText(
                    f"Data fetched and saved for {symbol} {interval}."
                )

                file_name = f"data/{symbol}--{interval}.csv"
                existing = next(
                    (s for s in self.added_symbols if s["symbol"]
                     == symbol and s["interval"] == interval), None
                )
                if not existing:
                    self.added_symbols.append({
                        "symbol": symbol,
                        "interval": interval,
                        "file": file_name
                    })
                else:
                    existing["file"] = file_name

                self.save_symbols()
                self.update_symbol_list()
            else:
                self.log_text_edit.appendPlainText(
                    f"No data found for {symbol} {interval}.")
        except Exception as e:
            self.log_text_edit.appendPlainText(f"Error during download: {e}")

    def update_symbol_list(self):
        while self.symbols_layout.count():
            child = self.symbols_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        for symbol_info in self.added_symbols:
            h_layout = QHBoxLayout()
            label = QLabel(
                f"{symbol_info['symbol']} - {symbol_info['interval']}")
            delete_button = QPushButton("Delete")
            delete_button.clicked.connect(
                lambda checked, s=symbol_info: self.delete_symbol(s))
            h_layout.addWidget(label)
            h_layout.addWidget(delete_button)
            self.symbols_layout.addLayout(h_layout)

    def delete_symbol(self, symbol_info):
        file_path = symbol_info["file"]
        if os.path.exists(file_path):
            os.remove(file_path)
        self.added_symbols = [
            s for s in self.added_symbols if s != symbol_info]
        self.save_symbols()
        self.update_symbol_list()

    def goBack(self):
        if hasattr(self.mainWindow, 'screen1'):
            self.mainWindow.screen1.refreshCandleFiles()
            self.mainWindow.stack.setCurrentWidget(self.mainWindow.screen1)
