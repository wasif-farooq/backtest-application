import pandas as pd


class TradeSimulation:
    def __init__(self, candles_df, signals_df, capital, leverage, maker_fee_rate, taker_fee_rate, tp_percent, sl_percent, with_compounding):
        self.candles_df = candles_df.copy()
        self.signals_df = signals_df.copy()
        self.capital = capital
        self.leverage = leverage
        self.maker_fee_rate = maker_fee_rate
        self.taker_fee_rate = taker_fee_rate
        self.tp_percent = tp_percent
        self.sl_percent = sl_percent
        self.with_compounding = with_compounding  # Store the compounding flag

        self.active_trades = []
        self.completed_trades = []

        self.candles_df['Datetime'] = pd.to_datetime(
            self.candles_df['Datetime'])
        self.signals_df['time'] = pd.to_datetime(self.signals_df['time'])

    def run_simulation(self):
        self.candles_df.sort_values('Datetime', inplace=True)
        self.signals_df.sort_values('time', inplace=True)

        for _, candle in self.candles_df.iterrows():
            current_time = candle['Datetime']
            last_candle = {
                "Datetime": candle["Datetime"],
                "Open": candle["Open"],
                "High": candle["High"],
                "Low": candle["Low"],
                "Close": candle["Close"]
            }

            # Process active trades for TP/SL conditions
            for trade in self.active_trades[:]:
                trade_size = self.capital * self.leverage
                maker_fee = trade_size * self.maker_fee_rate
                taker_fee = trade_size * self.taker_fee_rate
                trade_fee = taker_fee - maker_fee

                if trade["Direction"] == "BUY":
                    if last_candle["High"] >= trade["Take_Profit"]:
                        price_diff = trade["Take_Profit"] - \
                            trade["Entry_Price"]
                        raw_profit = trade_size * \
                            (price_diff / trade["Entry_Price"])
                        profit_loss = raw_profit - trade_fee
                        self.capital += profit_loss

                        trade["Profit_Loss"] = profit_loss
                        trade["Result"] = "PROFIT"
                        trade["Capital"] = self.capital
                        trade["Close_Time"] = last_candle['Datetime']
                        self.completed_trades.append(trade)
                        self.active_trades.remove(trade)

                    elif last_candle["Low"] <= trade["Stop_Loss"]:
                        price_diff = trade["Stop_Loss"] - trade["Entry_Price"]
                        raw_loss = trade_size * \
                            (price_diff / trade["Entry_Price"])
                        profit_loss = raw_loss - trade_fee
                        self.capital += profit_loss
                        trade["Profit_Loss"] = profit_loss
                        trade["Result"] = "LOSS"
                        trade["Capital"] = self.capital
                        trade["Close_Time"] = last_candle['Datetime']
                        self.completed_trades.append(trade)
                        self.active_trades.remove(trade)

                elif trade["Direction"] == "SELL":
                    if last_candle["Low"] <= trade["Take_Profit"]:
                        price_diff = abs(
                            trade["Take_Profit"] - trade["Entry_Price"])
                        raw_profit = trade_size * \
                            (price_diff / trade["Entry_Price"])
                        profit_loss = raw_profit - trade_fee
                        self.capital += profit_loss
                        trade["Profit_Loss"] = profit_loss
                        trade["Result"] = "PROFIT"
                        trade["Capital"] = self.capital
                        trade["Close_Time"] = last_candle['Datetime']

                        self.completed_trades.append(trade)
                        self.active_trades.remove(trade)

                    elif last_candle["High"] >= trade["Stop_Loss"]:
                        price_diff = trade["Entry_Price"] - trade["Stop_Loss"]
                        raw_loss = trade_size * \
                            (price_diff / trade["Entry_Price"])
                        profit_loss = raw_loss - trade_fee
                        self.capital += profit_loss
                        trade["Profit_Loss"] = profit_loss
                        trade["Result"] = "LOSS"
                        trade["Capital"] = self.capital
                        trade["Close_Time"] = last_candle['Datetime']
                        self.completed_trades.append(trade)
                        self.active_trades.remove(trade)

            if self.capital <= 0:
                break
            # If no active trades, open a new trade at current time from signals
            if not self.active_trades:
                signals_at_time = self.signals_df[self.signals_df['time']
                                                  == current_time]
                for _, signal in signals_at_time.iterrows():
                    direction = "BUY" if signal["Buy"] == 1 else "SELL"
                    entry_price = float(signal["Entry"])
                    if direction == "BUY":
                        tp = entry_price * (1 + self.tp_percent/100)
                        sl = entry_price * (1 - self.sl_percent/100)
                    else:
                        tp = entry_price * (1 - self.tp_percent/100)
                        sl = entry_price * (1 + self.sl_percent/100)

                    trade = {
                        "Datetime": current_time,
                        "Direction": direction,
                        "Entry_Price": entry_price,
                        "Take_Profit": tp,
                        "Stop_Loss": sl
                    }
                    self.active_trades.append(trade)
                    # Open only one trade at a time
                    break

        return self.completed_trades

