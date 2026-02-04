# KTI Seasonal Strategy Backtest

## Overview
This module implements a **Known Trends Index (KTI) Seasonal Strategy** backtester that uses 13 distinct seasonal and cyclical trends to generate buy/sell signals for stock trading. The strategy combines technical analysis with seasonal patterns to make investment decisions. (Strategy logic created by: https://jayonthemarkets.com)

## Features
- Downloads historical price data using Yahoo Finance
- Calculates KTI (Known Trends Index) based on 13 seasonal trends
- Dynamically determines position sizes (from -1x short to 2x leveraged long)
- Performs full backtesting with trade tracking
- Compares results against Buy & Hold strategy
- Generates performance visualizations and statistics
- Tracks US holidays to identify trading days

## 13 Seasonal Trends Analyzed

1. **Days of Month** - Bullish on specific days of the month (1-4, 9-12, and last 2 days)
2. **November to May** - Classic "Sell in May and Go Away" pattern (inverted)
3. **Summer Rally** - Last 3 trading days of June + first 9 trading days of July
4. **September** - Bearish indicator during September
5. **Election Cycle** - Presidential election cycle patterns (4-year cycles)
6. **March to July Pre-Election Year** - Bullish period in pre-election years
7. **Midterm Election** - Trading window around US midterm elections
8. **40-Week Cycle** - Bullish during first 20 weeks of each 40-week cycle
9. **212-Week Cycle** - Bullish within 6 months of 212-week cycle start
10. **October Year 4 - March Year 6** - Decade-based pattern
11. **March Year 8 - September Year 9** - Decade-based pattern
12. **October Year 2 (Even Decade) - December Year 5** - Even decade pattern
13. **Holiday Effect** - Bullish 3 days before and after market holidays

## Position Sizing Rules

Based on KTI value:
- **KTI ≥ 5**: 2x leveraged long position
- **KTI ≥ 3**: 1x long position
- **KTI ≤ 1**: 1x short position
- **KTI 2-2**: Cash position (1% annual return)

## Main Class: `KTISeasonalStrategy`

### Initialization
```python
strategy = KTISeasonalStrategy(
    symbol="SPY",                    # Stock ticker
    start_date="1994-01-01",         # Backtest start date
    end_date="2007-12-31",           # Backtest end date
    initial_capital=10000            # Starting capital
)
```

### Key Methods

#### `download_data()`
Downloads historical OHLC data from Yahoo Finance for the specified period.

#### `calculate_kti(date)`
Computes the total KTI value and trend breakdown for a given date by summing all 13 seasonal trends.

**Returns:**
- `kti_value`: Integer between -13 and +13
- `trend_breakdown`: Dictionary with individual trend values

#### `backtest_strategy()`
Runs the main backtesting engine:
- Iterates through historical data
- Calculates daily KTI values
- Opens/closes positions based on KTI thresholds
- Tracks portfolio value and trade history

**Returns:** Pandas Series with portfolio values indexed by date

#### `calculate_statistics(portfolio_series)`
Computes performance metrics:
- Total return (%)
- Maximum drawdown (%)
- Comparison against Buy & Hold
- Trade statistics

#### `plot_results(portfolio_series, stats)`
Generates 4-subplot visualization:
1. Strategy vs Buy & Hold performance
2. KTI values over time with threshold lines
3. Position sizes (scatter plot)
4. Performance difference (strategy vs benchmark)

#### `run_full_backtest()`
Orchestrates complete backtest workflow and displays results.

## Usage Example

```python
from KTISeasonal_02 import KTISeasonalStrategy

# Create strategy instance
strategy = KTISeasonalStrategy(
    symbol="SPY",
    start_date="1994-01-01",
    end_date="2007-12-31",
    initial_capital=10000
)

# Run full backtest
portfolio_series, stats = strategy.run_full_backtest()

# Access results
print(f"Strategy Return: {stats['strategy_return']:.2f}%")
print(f"Buy & Hold Return: {stats['buy_hold_return']:.2f}%")
print(f"Excess Return: {stats['excess_return']:.2f}%")
```

## Performance Metrics

The backtest produces several key metrics:
- **Total Return**: Strategy's overall profit/loss percentage
- **Max Drawdown**: Largest peak-to-trough decline
- **Excess Return**: Strategy return minus Buy & Hold return
- **Total Trades**: Number of position entries
- **Average KTI**: Mean KTI value during active positions

## Dependencies

```
yfinance       # Financial data download
pandas         # Data manipulation
numpy          # Numerical operations
matplotlib     # Visualization
```

## Notes

- The strategy uses the **opening price** for trade execution
- Cash positions earn a simulated **1% annual return**
- US holidays are automatically detected from trading day gaps
- **Known Issue**: Results may differ ~10% from original study (possible offset in calculations)
- Leveraged positions (2x) multiply portfolio allocation accordingly

## Files Generated

- Trade history in `self.trades` list
- Results DataFrame in `self.results_df` with columns: Date, Open, KTI, Position_Size
- Matplotlib figure with 4 performance charts

## Customization

To modify the strategy:
1. Adjust `start_date` and `end_date` for different periods
2. Change `initial_capital` for different starting amounts
3. Modify `get_position_size()` to change leverage rules
4. Adjust seasonal trend methods for different entry/exit logic
5. Change `symbol` to backtest different assets

## Limitations

- Uses opening prices only (no intraday fill price variability)
- Does not account for slippage or commissions
- Simplified trade matching for return calculations
- Holiday detection relies on trading day gaps
- No rebalancing within leveraged positions
