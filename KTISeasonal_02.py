import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

class KTISeasonalStrategy:
    def __init__(self, symbol="SPY", start_date="2010-01-01", end_date="2024-12-31", initial_capital=10000):
        self.symbol = symbol
        self.start_date = start_date
        self.end_date = end_date
        self.initial_capital = initial_capital
        self.data = None
        self.trades = []
        self.portfolio_values = []
        self.portfolio_dates = []
        self.us_holidays = []
        self.us_holidays_year = None
        
    def download_data(self):
        """Download price data using yfinance"""
        print(f"Downloading {self.symbol} data from {self.start_date} to {self.end_date}...")
        self.data = yf.download(self.symbol, start=self.start_date, end=self.end_date, auto_adjust=True)
        
        if self.data.empty:
            raise ValueError("No data found for the specified symbol and date range!")
        
        self.data.index = pd.to_datetime(self.data.index)
        print(f"Downloaded {len(self.data)} trading days of data")
        return self.data

    def get_us_holidays(self, year):
        """Get major US holidays for a given year"""
        # Find holidays by detecting gaps in trading days (excluding weekends)
        holidays = []
        if self.data is not None:
            year_dates = self.data[self.data.index.year == year].index
            for i in range(1, len(year_dates)):
                prev_day = year_dates[i - 1]
                curr_day = year_dates[i]
                gap = (curr_day - prev_day).days
                if gap > 1:
                    # Check each missing day in the gap
                    for j in range(1, gap):
                        missing_day = prev_day + timedelta(days=j)
                        if missing_day.weekday() < 5:  # Not a weekend
                            holidays.append(missing_day)
        return holidays

    def is_trading_day(self, date):
        """Check if a date is a trading day (weekday, not holiday)"""
        if not self.us_holidays_year or self.us_holidays_year != date.year or not self.us_holidays:
            self.us_holidays = self.get_us_holidays(date.year)
            self.us_holidays_year = date.year
        return date.weekday() < 5 and date not in self.us_holidays

    def days_of_month(self, date):
        """
        Days of the month
        Returns: +1 or 0 based on seasonal analysis
        """
        # Get all trading days for the month
        month_dates = pd.date_range(date.replace(day=1), date.replace(day=28) + timedelta(days=4))
        month_dates = month_dates[month_dates.month == date.month]
        trading_days = [d for d in month_dates if self.is_trading_day(d)]
        # Find the index of the current date in trading_days
        try:
            idx = trading_days.index(pd.Timestamp(date.year, date.month, date.day))
        except ValueError:
            return 0  # Not a trading day
        # Positive: 1-based index from start, Negative: -1 is last trading day, -2 is second last, etc.
        trading_day_num = idx + 1
        trading_day_num_neg = trading_day_num - len(trading_days) - 1
        if trading_day_num in [1, 2, 3, 4, 9, 10, 11, 12] or trading_day_num_neg in [-2, -1]:
            return 1
        return 0
    
    def november_to_may(self, date):
        """
        November to May
        Returns: +1 or 0 based on seasonal analysis
        """
        # Returns +1 if date is a trading day between Nov 1 and the third trading day of May
        if date.month >= 11 or date.month <= 5:
            if date.month == 5:
                # Find the third trading day of May for this year
                may_dates = pd.date_range(datetime(date.year, 5, 1), datetime(date.year, 5, 31))
                trading_days_may = []
                for d in may_dates:
                    if self.is_trading_day(d):
                        trading_days_may.append(d)
                        if len(trading_days_may) == 3:
                            third_trading_day_may = trading_days_may[2]
                            # If date is before or on the third trading day of May
                            if pd.Timestamp(date) <= pd.Timestamp(third_trading_day_may):
                                return 1
                            break
            else:
                return 1
        return 0
    
    def summer_rally(self, date):
        """
        Summer Rally
        Returns: +1 or 0 based on seasonal analysis
        """
        # Summer Rally: +1 if last 3 trading days of June or first 9 trading days of July
        # Get all trading days for June
        if date.month == 6:
            june_dates = pd.date_range(datetime(date.year, 6, 1), datetime(date.year, 6, 30))
            trading_days_june = [d for d in june_dates if self.is_trading_day(d)]
            if pd.Timestamp(date) in trading_days_june[-3:]:
                return 1
        elif date.month == 7:
            july_dates = pd.date_range(datetime(date.year, 7, 1), datetime(date.year, 7, 31))
            trading_days_july = [d for d in july_dates if self.is_trading_day(d)]
            if pd.Timestamp(date) in trading_days_july[:9]:
                return 1
        return 0
    
    def september(self, date):
        """
        September
        Returns: 0, or -1 based on seasonal analysis
        """
        # If today is a trading day during the month of September, then –1
        if date.month == 9 and self.is_trading_day(date):
            return -1
        return 0
    
    def election_cycle(self, date):
        """
        Election Cycle
        Returns: +1 or 0 based on seasonal analysis
        """
        year = date.year

        # Determine the type of year in the US presidential cycle
        # Presidential elections: 2024, 2020, 2016, etc.
        presidential_year = (year - 2024) % 4 == 0
        preelection_year = (year - 2023) % 4 == 0
        midterm_year = (year - 2022) % 4 == 0

        # 1. October 1 of a midterm year to September 30 of preelection year
        if midterm_year:
            start = datetime(year, 10, 1).date()
            if start <= date:
                return 1
        elif preelection_year:
            # Check if date is before September 30 of preelection year
            if (datetime(year, 1, 1).date() <= date <= datetime(year, 9, 30).date()):
                return 1
            # 2. November 1 of preelection year to December 31 of preelection year
            elif datetime(year, 11, 1).date() <= date <= datetime(year, 12, 31).date():
                return 1
        elif presidential_year:
            # 3. June 1 to December 31 of a presidential election year
            if datetime(year, 6, 1).date() <= date <= datetime(year, 12, 31).date():
                return 1

        return 0
    
    def march_to_july_preelec_year(self, date):
        """
        March to July of Pre-Election Year
        Returns: +1 or 0 based on seasonal analysis
        """
        year = date.year
        preelection_year = (year - 2023) % 4 == 0
        if preelection_year and date.month in [3, 4, 5, 6, 7]:
            return 1
        return 0

    def midterm_election(self, date):
        """
        Midterm Election
        Returns: +1 or 0 based on seasonal analysis
        """
        year = date.year
        # US midterm elections: every even year not divisible by 4 (e.g., 2022, 2018, 2014, ...)
        if year % 2 == 0 and year % 4 != 0:
            # US federal elections are held on the Tuesday following the first Monday in November
            # Find first Monday in November
            nov_1 = datetime(year, 11, 1)
            days_to_monday = (7 - nov_1.weekday()) % 7
            first_monday = nov_1 + timedelta(days=days_to_monday)
            if first_monday.weekday() != 0:
                raise ValueError("First Monday calculation error")
            election_day = first_monday + timedelta(days=1)  # Tuesday after first Monday

            # Get all trading days in October, November and December
            possible_dates = pd.date_range(datetime(year, 10, 1), datetime(year, 12, 31))
            trading_days = [d for d in possible_dates if self.is_trading_day(d)]

            # Find index of election day in trading_days
            try:
                idx = trading_days.index(pd.Timestamp(election_day))
            except ValueError:
                return 0  # Election day not a trading day

            # Get window: 5 trading days before to 3 trading days after (inclusive)
            window_start = max(0, idx - 5)
            window_end = min(len(trading_days) - 1, idx + 3)
            window_days = trading_days[window_start:window_end + 1]

            if pd.Timestamp(date) in window_days:
                return 1
        return 0
    
    def cycle_40_weeks(self, date):
        """
        40-Week Cycle
        Returns: +1 or 0 based on seasonal analysis
        """
        # 40-Week Cycle: +1 if today is within the most recent 20-week bullish phase
        # Assume bullish phase is the first 20 weeks of each 40-week period since start_date
        cycle_40_weeks_start = datetime(1967, 4, 21)  # Known bullish phase start date
        start = pd.to_datetime(cycle_40_weeks_start)
        delta_days = (date - start.date()).days
        if delta_days < 0:
            return 0
        weeks_since_start = delta_days // 7
        cycle_week = weeks_since_start % 40
        if 0 <= cycle_week < 20:
            return 1
        return 0
    
    def cycle_212_weeks(self, date):
        """
        212-Week Cycle
        Returns: +1 or 0 based on seasonal analysis
        """
        # 212-Week Cycle: +1 if today is within 6 months after the latest 212-week cycle buy date
        cycle_212_weeks_start = datetime(1950, 7, 24)  # Known bullish phase start date
        start = pd.to_datetime(cycle_212_weeks_start)
        delta_days = (date - start.date()).days
        if delta_days < 0:
            return 0
        weeks_since_start = delta_days // 7
        cycles_completed = weeks_since_start // 212
        latest_cycle_start = start + timedelta(weeks=cycles_completed * 212)
        buy_window_end = latest_cycle_start + pd.DateOffset(months=6)
        if latest_cycle_start.date() <= date <= buy_window_end.date():
            return 1
        return 0
    
    def oct_of4_till_march_of6(self, date):
        """
        October of year 4 through
        March of year 6
        Returns: +1 or 0 based on seasonal analysis
        """
        year = date.year
        decade_start = (year // 10) * 10
        oct_1_of4 = datetime(decade_start + 4, 10, 1).date()
        mar_31_of6 = datetime(decade_start + 6, 3, 31).date()
        if oct_1_of4 <= date <= mar_31_of6:
            return 1
        return 0
    
    def march_of8_till_sept_of9(self, date):
        """
        March of year 8 through
        September of year 9
        Returns: +1 or 0 based on seasonal analysis
        """
        year = date.year
        decade_start = (year // 10) * 10
        mar_1_of8 = datetime(decade_start + 8, 3, 1).date()
        sep_30_of9 = datetime(decade_start + 9, 9, 30).date()
        if mar_1_of8 <= date <= sep_30_of9:
            return 1
        return 0

    def oct_of2_even_decade_till_dec_of5(self, date):
        """
        October of year 2 of even-
        numbered decade
        through December of
        year 5 of same decade
        Returns: +1 or 0 based on seasonal analysis
        """
        year = date.year
        decade_start = (year // 10) * 10
        if decade_start % 20 == 0:
            oct_1_of2 = datetime(decade_start + 2, 10, 1).date()
            dec_31_of5 = datetime(decade_start + 5, 12, 31).date()
            if oct_1_of2 <= date <= dec_31_of5:
                return 1
        return 0
    
    def holidays(self, date):
        """
        Holidays
        Returns: +1 or 0 based on seasonal analysis
        """
        if not self.us_holidays_year or self.us_holidays_year != date.year or not self.us_holidays:
            self.us_holidays = self.get_us_holidays(date.year)
            self.us_holidays_year = date.year
        holiday_dates = self.us_holidays
        year = date.year
        # Get all trading days of the year (+1 month buffer)
        possible_dates = pd.date_range(datetime(year-1, 12, 1), datetime(year+1, 1, 31))
        trading_days = [d for d in possible_dates if self.is_trading_day(d)]
        # For each major holiday, check if date is within 3 trading days before/after
        for holiday in holiday_dates:
            # Find index of holiday in trading_days
            day_before = holiday - timedelta(days=1)
            while True:
                try:
                    idx = trading_days.index(pd.Timestamp(day_before))
                    break
                except ValueError:
                    if pd.Timestamp(day_before) < trading_days[0]:
                        raise ValueError("Holiday before first trading day")
                    day_before -= timedelta(days=1) # holiday not a trading day
            window_start = max(0, idx - 2)
            window_end = min(len(trading_days) - 1, idx + 3)
            window_days = trading_days[window_start:window_end + 1]

            if pd.Timestamp(date) in window_days:
                return 1
        return 0
    
    def calculate_kti(self, date):
        """
        Calculate KTI (Known Trends Index) by summing all seasonal trends (13 total)
        Returns: Sum of all seasonal trend values
        """
        trend1 = self.days_of_month(date)
        trend2 = self.november_to_may(date)
        trend3 = self.summer_rally(date)
        trend4 = self.september(date)
        trend5 = self.election_cycle(date)
        trend6 = self.march_to_july_preelec_year(date)
        trend7 = self.midterm_election(date)
        trend8 = self.cycle_40_weeks(date)
        trend9 = self.cycle_212_weeks(date)
        trend10 = self.oct_of4_till_march_of6(date)
        trend11 = self.march_of8_till_sept_of9(date)
        trend12 = self.oct_of2_even_decade_till_dec_of5(date)
        trend13 = self.holidays(date)

        kti_value = trend1 + trend2 + trend3 + trend4 + trend5 + trend6 + trend7 + trend8 + trend9 + trend10 + trend11 + trend12 + trend13

        return kti_value, {
            'trend1': trend1,
            'trend2': trend2,
            'trend3': trend3,
            'trend4': trend4,
            'trend5': trend5,
            'trend6': trend6,
            'trend7': trend7,
            'trend8': trend8,
            'trend9': trend9,
            'trend10': trend10,
            'trend11': trend11,
            'trend12': trend12,
            'trend13': trend13
        }
    
# testing data: results do not match with results from study (offset of some 10% of return (200% points))

    def get_position_size(self, kti_value):
        """
        Determine position size based on KTI value
        Returns: position_size (1.0 = 100%, 2.0 = 200% leverage, -1.0 = 100% short)
        """
        if kti_value >= 5:
            return 2.0  # 2x leverage long
        elif kti_value >= 3:
            return 1.0  # 1x long
        elif kti_value <= 1:
            return -1.0  # 1x short
        else:
            return 0.0  # No position (cash)
    
    def backtest_strategy(self):
        """
        Main backtesting logic
        """
        if self.data is None:
            self.download_data()
        
        current_value = self.initial_capital
        current_position = 0.0  # Current position size
        current_shares = 0.0    # Current number of shares
        
        self.trades = []
        self.portfolio_values = [current_value]
        self.portfolio_dates = [self.data.index[0]]
        
        kti_values = []
        position_sizes = []
        
        print("Running KTI Seasonal Strategy backtest...")
        
        for i, (date, row) in enumerate(self.data.iterrows()):

            # Calculate KTI for this date
            kti_value, trend_breakdown = self.calculate_kti(date.date())
            kti_values.append(kti_value)
            
            # Determine target position
            target_position = self.get_position_size(kti_value)
            position_sizes.append(target_position)
            
            # Check if position change is needed
            if target_position != current_position:
                # Close current position if any
                if current_shares != 0:
                    exit_price = float(row['Open'])
                    if current_shares > 0:  # Closing long position
                        profit = current_shares * (exit_price - entry_price)
                    else:  # Closing short position
                        profit = abs(current_shares) * (entry_price - exit_price)
                    current_value += profit
                    
                    # Record trade
                    self.trades.append({
                        'exit_date': date,
                        'exit_price': exit_price,
                        'position': 'CLOSE',
                        'shares': current_shares,
                        'value': current_value,
                        'kti': kti_value
                    })
                    current_position = 0
                    current_shares = 0
                    entry_price = 0
                
                # Open new position if target is not zero
                if target_position != 0:
                    entry_price = float(row['Open'])
                    position_value = current_value * abs(target_position)
                    current_shares = position_value / entry_price
                    
                    if target_position < 0:  # Short position
                        current_shares = -current_shares
                    current_position = target_position
                    
                    # Record trade
                    self.trades.append({
                        'entry_date': date,
                        'entry_price': entry_price,
                        'position': 'LONG' if target_position > 0 else 'SHORT',
                        'leverage': abs(target_position),
                        'shares': current_shares,
                        'kti': kti_value,
                        'trend_breakdown': trend_breakdown
                    })
                else: # we have a 1% annual return on cash
                    current_value *= 1 + (0.01 / 252)  # Approximate daily return for cash
                    continue
                
                # Record portfolio value
                self.portfolio_values.append(current_value)
                self.portfolio_dates.append(date)
            else:
                if current_shares != 0:
                    # Update portfolio value based on current position
                    current_price = float(row['Open'])
                    if current_shares > 0:  # Long position
                        profit = current_shares * (current_price - entry_price)
                        entry_price = current_price  # Update entry price to current price
                        current_value += profit
                    else:  # Short position
                        profit = abs(current_shares) * (-current_price + entry_price)
                        entry_price = current_price  # Update entry price to current price
                        current_value += profit
                    self.portfolio_values.append(current_value)
                    self.portfolio_dates.append(date)
                else:
                    # No position, just hold cash with 1% annual return
                    current_value *= 1 + (0.01 / 252)  # Approximate daily return for cash
        
        # create lists for results DataFrame
        indexes = []
        opens = []
        for i in range(len(self.data)):
            if self.is_trading_day(self.data.index[i]):
                indexes.append(self.data.index[i])
                opens.append(float(self.data.iloc[i]["Open"]))

        # Create results DataFrame
        self.results_df = pd.DataFrame({
            'Date': indexes,
            "Open": opens,
            'KTI': kti_values,
            'Position_Size': position_sizes
        })
        
        print(f"Backtest completed. Total trades: {len([t for t in self.trades if 'entry_date' in t])}")
        
        return pd.Series(self.portfolio_values[1:], index=self.portfolio_dates[1:])
    
    def calculate_statistics(self, portfolio_series):
        """Calculate performance statistics"""
        # Strategy statistics
        total_return = (portfolio_series.iloc[-1] - self.initial_capital) / self.initial_capital * 100
        
        # Calculate max drawdown
        peak = portfolio_series.cummax()
        drawdown = (portfolio_series - peak) / peak
        max_drawdown = drawdown.min() * 100
        
        # Buy and hold comparison
        buy_hold_data = self.data.loc[portfolio_series.index, "Open"]
        initial_price = float(buy_hold_data.iloc[0])
        shares_bought = self.initial_capital / initial_price
        buy_hold_values = buy_hold_data * shares_bought
        buy_hold_return = float((buy_hold_values.iloc[-1] - self.initial_capital) / self.initial_capital * 100)
        
        # Calculate buy and hold max drawdown
        buy_hold_peak = buy_hold_values.cummax()
        buy_hold_drawdown = (buy_hold_values - buy_hold_peak) / buy_hold_peak
        buy_hold_max_drawdown = float(buy_hold_drawdown.min() * 100)
        
        # Trade statistics
        entry_trades = [t for t in self.trades if 'entry_date' in t]
        winning_trades = 0
        total_trades = len(entry_trades)
        
        # Calculate individual trade returns (simplified)
        if total_trades > 0:
            # This is a simplified calculation - in practice you'd match entry/exit pairs
            avg_kti = np.mean([t['kti'] for t in entry_trades])
        else:
            avg_kti = 0
        
        return {
            'strategy_return': total_return,
            'strategy_max_drawdown': max_drawdown,
            'buy_hold_return': buy_hold_return,
            'buy_hold_max_drawdown': buy_hold_max_drawdown,
            'excess_return': total_return - buy_hold_return,
            'total_trades': total_trades,
            'avg_kti': avg_kti,
            'final_value': portfolio_series.iloc[-1],
            'buy_hold_final': float(buy_hold_values.iloc[-1])
        }
    
    def print_results(self, stats):
        """Print backtest results"""
        print(f"\n=== KTI SEASONAL STRATEGY RESULTS ===")
        print(f"Symbol: {self.symbol}")
        print(f"Period: {self.start_date} to {self.end_date}")
        print(f"Initial Capital: ${self.initial_capital:,.2f}")
        
        print(f"\n--- KTI STRATEGY PERFORMANCE ---")
        print(f"Final Portfolio Value: ${stats['final_value']:,.2f}")
        print(f"Total Return: {stats['strategy_return']:.2f}%")
        print(f"Max Drawdown: {stats['strategy_max_drawdown']:.2f}%")
        print(f"Total Trades: {stats['total_trades']}")
        print(f"Average KTI: {stats['avg_kti']:.2f}")
        
        print(f"\n--- BUY & HOLD COMPARISON ---")
        print(f"Buy & Hold Final Value: ${stats['buy_hold_final']:,.2f}")
        print(f"Buy & Hold Return: {stats['buy_hold_return']:.2f}%")
        print(f"Buy & Hold Max Drawdown: {stats['buy_hold_max_drawdown']:.2f}%")
        
        print(f"\n--- PERFORMANCE COMPARISON ---")
        print(f"Excess Return: {stats['excess_return']:.2f}%")
        print(f"Strategy Outperformed: {'Yes' if stats['excess_return'] > 0 else 'No'}")
    
    def plot_results(self, portfolio_series, stats):
        """Plot backtest results"""
        # Calculate buy and hold for plotting
        buy_hold_data = self.data.loc[portfolio_series.index, "Open"]
        initial_price = float(buy_hold_data.iloc[0])
        shares_bought = self.initial_capital / initial_price
        buy_hold_values = buy_hold_data * shares_bought
        buy_hold_list = []
        for i in range(len(buy_hold_values)):
            buy_hold_list.append(float(buy_hold_values.iloc[i]))
        buy_hold_values = pd.Series(buy_hold_list, index=portfolio_series.index)

        
        # Create plots
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
        
        # Plot 1: Portfolio Performance Comparison
        ax1.plot(portfolio_series.index, portfolio_series.values, 'b-', linewidth=2, label='KTI Strategy')
        ax1.plot(buy_hold_values.index, buy_hold_values.values, 'orange', linewidth=2, label='Buy & Hold')
        ax1.axhline(y=self.initial_capital, color='r', linestyle='--', alpha=0.7, label='Initial Capital')
        ax1.set_title(f'{self.symbol} - KTI Strategy vs Buy & Hold')
        ax1.set_ylabel('Portfolio Value ($)')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Plot 2: KTI Values Over Time
        ax2.plot(self.results_df['Date'], self.results_df['KTI'], 'purple', linewidth=1, alpha=0.7)
        ax2.axhline(y=5, color='green', linestyle='--', alpha=0.7, label='2x Long Threshold (>5)')
        ax2.axhline(y=3, color='blue', linestyle='--', alpha=0.7, label='1x Long Threshold (>3)')
        ax2.axhline(y=1, color='red', linestyle='--', alpha=0.7, label='Short Threshold (<1)')
        ax2.set_title('KTI Values Over Time')
        ax2.set_ylabel('KTI Value')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # Plot 3: Position Sizes Over Time
        position_colors = {'2.0': 'darkgreen', '1.0': 'green', '0.0': 'gray', '-1.0': 'red'}
        for pos_size in [2.0, 1.0, 0.0, -1.0]:
            mask = self.results_df['Position_Size'] == pos_size
            if mask.any():
                label = f"{'2x Long' if pos_size == 2.0 else '1x Long' if pos_size == 1.0 else 'Cash' if pos_size == 0.0 else '1x Short'}"
                ax3.scatter(self.results_df.loc[mask, 'Date'], 
                          self.results_df.loc[mask, 'Position_Size'], 
                          c=position_colors.get(str(pos_size), 'black'), 
                          alpha=0.6, s=1, label=label)
        ax3.set_title('Position Sizes Over Time')
        ax3.set_ylabel('Position Size')
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        
        # Plot 4: Performance Difference
        performance_diff = portfolio_series - buy_hold_values
        ax4.plot(performance_diff.index, performance_diff.values, 'purple', linewidth=2)
        ax4.axhline(y=0, color='black', linestyle='--', alpha=0.7)
        ax4.fill_between(performance_diff.index, performance_diff.values, 0, 
                        where=(performance_diff.values >= 0), color='green', alpha=0.3, label='Outperforming')
        ax4.fill_between(performance_diff.index, performance_diff.values, 0, 
                        where=(performance_diff.values < 0), color='red', alpha=0.3, label='Underperforming')
        ax4.set_title('Strategy vs Buy & Hold Performance Difference')
        ax4.set_xlabel('Date')
        ax4.set_ylabel('Difference ($)')
        ax4.legend()
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.show(block=True)
    
    def run_full_backtest(self):
        """Run complete backtest and display results"""
        # Download data and run backtest
        portfolio_series = self.backtest_strategy()
        
        # Calculate statistics
        stats = self.calculate_statistics(portfolio_series)
        
        # Print results
        self.print_results(stats)
        
        # Plot results
        self.plot_results(portfolio_series, stats)
        
        return portfolio_series, stats

def main():
    """Main execution function"""
    # Configure matplotlib backend
    import matplotlib
    matplotlib.use('TkAgg')
    
    # Initialize and run strategy
    strategy = KTISeasonalStrategy(
        symbol="SPY", # "^DJI",
        start_date="1994-01-01", # "1193-02-01"
        end_date="2007-12-31",
        initial_capital=10000
    )
    
    # Run full backtest
    portfolio_series, stats = strategy.run_full_backtest()
    
    print("\nBacktest completed successfully!")
    return strategy, portfolio_series, stats

if __name__ == "__main__":
    strategy, portfolio_series, stats = main()
