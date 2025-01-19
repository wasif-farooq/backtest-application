import os
import csv
import pandas as pd
from PyQt5.QtWidgets import QMainWindow, QStackedWidget, QMessageBox
from screen1 import Screen1
from screen2 import Screen2
from trade_simulation import TradeSimulation


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Backtest Application")
        self.stack = QStackedWidget()

        self.screen1 = Screen1(self)
        self.screen2 = Screen2(self)

        self.stack.addWidget(self.screen1)
        self.stack.addWidget(self.screen2)
        self.setCentralWidget(self.stack)

    def showScreen2(self, formData):
        self.screen2.updateUserInputs(formData)
        monthly_stats, trades_df = self.simulateTrades(formData)
        self.screen2.updateTable(monthly_stats, trades_df)
        self.stack.setCurrentWidget(self.screen2)

    def simulateTrades(self, formData):
        candles_path = self.screen1.candleFileCombo.currentText()

        if not candles_path or not os.path.exists(candles_path):
            QMessageBox.warning(
                self, "Error", "Invalid or missing Candle File.")
            return [], pd.DataFrame()

        try:
            candles_df = pd.read_csv(candles_path, parse_dates=["Datetime"])
        except Exception as e:
            QMessageBox.warning(
                self, "Error", f"Error loading Candle File: {e}")
            return [], pd.DataFrame()

        if not formData.get("File"):
            QMessageBox.warning(self, "Error", "No Signals File provided.")
            return [], pd.DataFrame()

        try:
            signals_raw = pd.read_csv(formData["File"])
            signals_raw.columns = signals_raw.columns.str.strip()
            signals_raw['Entry'] = signals_raw['close'].astype(float)
            signals_raw = signals_raw.dropna(
                subset=['Buy Normal', 'Buy Smart', 'Sell Normal', 'Sell Smart'])
            signals_raw['sum'] = signals_raw[['Buy Normal',
                                              'Buy Smart', 'Sell Normal', 'Sell Smart']].sum(axis=1)
            filter_data = signals_raw[signals_raw['sum'] > 0].copy()

            buy_mask = (filter_data["Buy Normal"] > 0) | (
                filter_data["Buy Smart"] > 0)
            sell_mask = (filter_data["Sell Normal"] > 0) | (
                filter_data["Sell Smart"] > 0)
            filter_data['Buy'] = buy_mask.astype(int)
            filter_data['Sell'] = sell_mask.astype(int)

            columns_to_select = ["time", "Entry", "Buy", "Sell"]
            signals_df = filter_data[columns_to_select]
        except Exception as e:
            QMessageBox.warning(
                self, "Error", f"Error processing Signals File: {e}")
            return [], pd.DataFrame()

        if signals_df.empty:
            QMessageBox.warning(
                self, "Error", "No valid signals in the Signals File.")
            return [], pd.DataFrame()

        capital = formData.get("Capital", 1000)
        leverage = formData.get("Leverage", 1)
        maker_fee_rate = formData.get("MakerFees", 0.02) / 100
        taker_fee_rate = formData.get("TakerFees", 0.055) / 100
        tp_percent = formData.get("TP_percent", 0)
        sl_percent = formData.get("SL_percent", 0)
        with_compounding = formData.get("WithCompounding", False)
        use_alternate_signall = formData.get("useAlternateSignal", False)

        simulation = TradeSimulation(
            candles_df,
            signals_df,
            capital,
            leverage,
            maker_fee_rate,
            taker_fee_rate,
            tp_percent,
            sl_percent,
            with_compounding,
            use_alternate_signall
        )

        simulation.tranform()
        simulation.run_backtest()
        completed_trades = simulation.completed_trades

        monthly_stats = []
        if not completed_trades:
            return monthly_stats, pd.DataFrame()

        trades_df = pd.DataFrame(completed_trades)

        trades_df["Datetime"] = pd.to_datetime(trades_df["Datetime"])
        trades_df["Month"] = trades_df["Datetime"].dt.to_period(
            "M").astype(str)

        grouped = trades_df.groupby("Month")
        for month, group in grouped:
            winning_trades = group[group["Result"] == "PROFIT"].shape[0]
            losing_trades = group[group["Result"] == "LOSS"].shape[0]
            total_trades = winning_trades + losing_trades
            net_profit_loss = group["Profit_Loss"].sum()
            total_profit = group[group["Result"]
                                 == "PROFIT"]["Profit_Loss"].sum()
            total_loss = group[group["Result"] == "LOSS"]["Profit_Loss"].sum()
            monthly_stats.append({
                "Month": month,
                "Winning Trades": winning_trades,
                "Losing Trades": losing_trades,
                "Total Trades": total_trades,
                "Total Profit": total_profit,
                "Total Loss": total_loss,
                "Net Profit/Loss": net_profit_loss
            })

        return monthly_stats, trades_df

    def showScreen3(self):
        if not hasattr(self, 'screen3'):
            from screen3 import Screen3
            self.screen3 = Screen3(self)
            self.stack.addWidget(self.screen3)
        self.stack.setCurrentWidget(self.screen3)

