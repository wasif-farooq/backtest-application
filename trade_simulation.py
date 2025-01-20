import pandas as pd
import numpy as np


class TradeSimulation:
    def __init__(
        self,
        candles_df,
        signals_df,
        capital,
        leverage,
        maker_fee_rate,
        taker_fee_rate,
        tp_percent,
        sl_percent,
        with_compounding,
        use_alternate_signall,
        interval
    ):
        self.candles_df = candles_df.copy()
        self.signals_df = signals_df.copy()
        self.capital = capital
        self.inital_capital = capital
        self.leverage = leverage
        self.maker_fee_rate = maker_fee_rate
        self.taker_fee_rate = taker_fee_rate
        self.tp_percent = tp_percent
        self.sl_percent = sl_percent
        self.with_compounding = with_compounding  # Store the compounding flag
        self.use_alternate_signall = use_alternate_signall
        self.interval = interval

        self.active_trades = []
        self.completed_trades = []

    def tranform(self):
        self.candles_df['Datetime'] = pd.to_datetime(
            self.candles_df['Datetime'])

        self.candles_df['Datetime'] = self.candles_df['Datetime'].dt.tz_convert(
            'Asia/Karachi'
        )
        self.candles_df.set_index('Datetime', inplace=True)

        self.signals_df['time'] = pd.to_datetime(self.signals_df['time'])
        self.signals_df['time'] = self.signals_df['time'].dt.tz_convert(
            'Asia/Karachi'
        )

        self.signals_df.set_index('time', inplace=True)

        buy = self.signals_df['Buy'] == 1
        sell = self.signals_df['Sell'] == 1

        self.signals_df['Direction'] = np.where(
            buy,
            "BUY",
            np.where(
                sell,
                "SELL",
                "NaN"
            )
        )

        self.signals_df['Stop_Loss'] = np.where(
            buy,
            self.signals_df['Entry'] * (1 - self.sl_percent/100),
            np.where(
                sell,
                self.signals_df['Entry'] * (1 + self.sl_percent/100),
                np.nan
            )
        )

        self.signals_df['Take_Profit'] = np.where(
            buy,
            self.signals_df['Entry'] * (1 + self.tp_percent/100),
            np.where(
                sell,
                self.signals_df['Entry'] * (1 - self.tp_percent/100),
                np.nan
            )
        )

        self.signals_df = self.signals_df[[
            'Entry',
            'Take_Profit',
            'Stop_Loss',
            'Direction'
        ]]

        self.candles_df = pd.merge(
            self.candles_df,
            self.signals_df,
            how='left',
            left_index=True,
            right_index=True
        )

    def run_backtest(self):
        for index, row in self.candles_df.iterrows():
            self.simulate_trades(row, index)
            if self.capital <= 0:
                # self.capital = 500
                break

        return self.completed_trades

    def record_trade(self, trade, index, result, price_diff, close_price=0):
        completed = {
            "Datetime": trade['Datetime'],
            "Direction": trade['Direction'],
            "Trade Open Price": trade['Entry_Price'],
            "Trade Close Price": close_price if close_price > 0 else trade['Stop_Loss'],
            "Profit_Loss": trade['Profit_Loss'],
            'Stop_Loss': trade['Stop_Loss'],
            'Take_Profit': trade['Take_Profit'],
            'Diff': price_diff,
            'capital': self.capital,
            'Close_Time': index,
            'Result': result,
            'Closed_Normally': "no" if close_price > 0 else "yes"
        }
        self.completed_trades.append(completed)
        self.active_trades.remove(trade)

    def calculate_long_profit_loss(self, trade, price):
        trade_size = self.capital * self.leverage
        maker_fee = trade_size * self.maker_fee_rate / 100
        taker_fee = trade_size * self.taker_fee_rate / 100
        trade_fee = taker_fee - maker_fee
        self.capital = self.capital if self.with_compounding else self.inital_capital

        price_diff = price - trade['Entry_Price']
        raw_loss = trade_size * (price_diff / trade['Entry_Price'])
        trade['Profit_Loss'] = raw_loss - trade_fee
        self.capital += trade['Profit_Loss']
        result = "PROFIT" if trade['Profit_Loss'] > 0 else "LOSS"

        return price_diff, result

    def calculate_short_profit_loss(self, trade, price):
        trade_size = self.capital * self.leverage
        maker_fee = trade_size * self.maker_fee_rate / 100
        taker_fee = trade_size * self.taker_fee_rate / 100
        trade_fee = taker_fee - maker_fee
        self.capital = self.capital if self.with_compounding else self.inital_capital

        price_diff = trade['Entry_Price'] - price
        raw_loss = trade_size * (price_diff / trade['Entry_Price'])
        trade['Profit_Loss'] = raw_loss - trade_fee
        self.capital += trade['Profit_Loss']
        result = "PROFIT" if trade['Profit_Loss'] > 0 else "LOSS"

        return price_diff, result

    def calculate_trade(self, trade, last_candle, index):
        if trade['Direction'] == "BUY":
            if last_candle['High'] >= trade['Take_Profit']:
                price_diff, result = self.calculate_long_profit_loss(
                    trade,
                    trade['Take_Profit']
                )

                self.record_trade(
                    trade,
                    index,
                    result,
                    price_diff,
                )

            elif last_candle['Low'] <= trade['Stop_Loss']:
                price_diff, result = self.calculate_long_profit_loss(
                    trade,
                    trade['Stop_Loss']
                )

                self.record_trade(
                    trade,
                    index,
                    result,
                    price_diff,
                )

        elif trade['Direction'] == "SELL":
            if last_candle['Low'] <= trade['Take_Profit']:
                price_diff, result = self.calculate_short_profit_loss(
                    trade,
                    trade['Take_Profit']
                )

                self.record_trade(
                    trade,
                    index,
                    result,
                    price_diff,
                )

            elif last_candle['High'] >= trade['Stop_Loss']:
                price_diff, result = self.calculate_short_profit_loss(
                    trade,
                    trade['Stop_Loss']
                )

                self.record_trade(
                    trade,
                    index,
                    result,
                    price_diff,
                )

    def simulate_trades(self, last_candle, index):

        if last_candle is None:
            return

        if len(self.active_trades) > 0:
            minute = pd.Timedelta(minutes=int(self.interval))
            seconds = pd.Timedelta(seconds=1)

            skip_time = pd.to_datetime(
                self.active_trades[-1]['Datetime']) + minute - seconds
            if index <= skip_time:
                return

        for trade in self.active_trades[:]:
            self.calculate_trade(
                trade,
                last_candle,
                index
            )

        if (
            self.use_alternate_signall and
            len(self.active_trades) > 0
        ):
            trade = self.active_trades[-1]
            if (
                last_candle['Direction'] == 'BUY' and
                trade['Direction'] == 'SELL'
            ):
                price_diff, result = self.calculate_short_profit_loss(
                    trade,
                    last_candle['Entry']
                )

                self.record_trade(
                    trade,
                    index,
                    result,
                    price_diff,
                    last_candle['Entry']
                )

            if (
                last_candle['Direction'] == 'SELL' and
                trade['Direction'] == 'BUY'
            ):
                price_diff, result = self.calculate_long_profit_loss(
                    trade,
                    last_candle['Entry']
                )

                self.record_trade(
                    trade,
                    index,
                    result,
                    price_diff,
                    last_candle['Entry']
                )

        if len(self.active_trades) > 0:
            return

        if (
            last_candle['Direction'] == 'BUY' or
            last_candle['Direction'] == 'SELL'
        ):
            trade_direction = last_candle['Direction']
            entry_price = last_candle['Entry']
            take_profit = last_candle['Take_Profit']
            stop_loss = last_candle['Stop_Loss']

            trade = {
                'Datetime': index,
                'Direction': trade_direction,
                'Stop_Loss': stop_loss,
                'Take_Profit': take_profit,
                'Entry_Price': entry_price
            }

            self.active_trades.append(trade)
