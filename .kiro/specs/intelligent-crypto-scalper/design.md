# Design Document: Intelligent Crypto Scalper Strategy

## Overview

This document outlines the technical design for a professional-grade Pine Script v5 scalping strategy optimized for cryptocurrency markets on the 5-minute timeframe. The strategy implements intelligent market analysis, adaptive risk management, and sophisticated trade execution logic to maximize profitability while minimizing drawdown through smart entry filtering and dynamic profit protection.

### Core Design Principles

1. **Quality over Quantity**: Filter aggressively to trade only high-probability setups
2. **Adaptive Risk Management**: All stop losses and take profits adjust to current market volatility
3. **Profit Protection First**: Every trade aims for net profit through partial exits and trailing stops
4. **Market Regime Awareness**: Avoid trading during unfavorable market conditions
5. **Scalability**: Clean, modular code structure for easy maintenance and optimization

## Architecture

### High-Level Component Structure

```
┌─────────────────────────────────────────────────────────────┐
│                    Strategy Inputs Layer                     │
│  (User-configurable parameters for all components)          │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                  Market Analysis Engine                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  Volatility  │  │   Structure  │  │   Momentum   │     │
│  │   Analysis   │  │   Detection  │  │   Filters    │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    Entry Signal Generator                    │
│  (Combines all filters to produce high-probability signals) │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                  Frequency Control System                    │
│  (Cooldown, rate limiting, overtrading prevention)          │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                   Risk Management Module                     │
│  (Position sizing, SL/TP calculation, adaptive adjustments) │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    Trade Execution Engine                    │
│  (Order placement, partial exits, trailing stops)           │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                   Visualization & Reporting                  │
│  (Chart overlays, labels, performance statistics)           │
└─────────────────────────────────────────────────────────────┘
```

## Components and Interfaces

### 1. Market Analysis Engine

#### 1.1 Volatility Analysis Module

**Purpose**: Determine if market conditions are suitable for scalping

**Indicators Used**:
- ATR (Average True Range) - Primary volatility measure
- Kaufman Efficiency Ratio - Trend vs noise detection
- ATR percentile ranking - Relative volatility assessment

**Interface**:
```pinescript
// Inputs
atr_period: int
volatility_threshold: float

// Outputs
is_volatile_enough: bool
current_atr: float
market_is_choppy: bool
```

**Logic**:
1. Calculate ATR over specified period
2. Compute Kaufman Efficiency Ratio: `abs(change(close, period)) / sum(abs(change(close)), period)`
3. Determine if ATR > SMA(ATR) * threshold
4. Flag choppy markets when efficiency ratio < 0.3 and ATR is below 50th percentile

#### 1.2 Market Structure Detection Module

**Purpose**: Identify micro-trends through swing highs/lows and breakout patterns

**Components**:
- Swing high/low detection using lookback period
- Breakout identification (price exceeding recent structure)
- Liquidity sweep detection (false breakout with reversal)

**Interface**:
```pinescript
// Inputs
swing_lookback: int
liquidity_buffer: float

// Outputs
recent_swing_high: float
recent_swing_low: float
bullish_breakout: bool
bearish_breakout: bool
liquidity_sweep_long: bool
liquidity_sweep_short: bool
```

**Logic**:
1. Track swing highs: `highest(high, lookback)`
2. Track swing lows: `lowest(low, lookback)`
3. Detect breakouts: `close > swing_high[1]` or `close < swing_low[1]`
4. Identify liquidity sweeps:
   - Long: `low < swing_low AND close > swing_low AND bullish_candle`
   - Short: `high > swing_high AND close < swing_high AND bearish_candle`

#### 1.3 Momentum Filter Module

**Purpose**: Confirm directional bias through multiple momentum indicators

**Indicators**:
- Volume spike detection
- Fast MA slope analysis
- Candle body size relative to recent average
- RSI for overbought/oversold conditions

**Interface**:
```pinescript
// Inputs
volume_spike_multiplier: float
ma_fast_period: int
min_candle_body_pct: float
rsi_period: int

// Outputs
volume_confirms: bool
ma_slope_bullish: bool
ma_slope_bearish: bool
candle_body_valid: bool
rsi_not_extreme: bool
momentum_score: int  // 0-4 based on confirmations
```

**Logic**:
1. Volume spike: `volume > sma(volume, 20) * multiplier`
2. MA slope: `(ma[0] - ma[3]) / ma[3] > threshold`
3. Candle body: `abs(close - open) / close > min_pct`
4. RSI filter: `30 < rsi < 70` for entries
5. Momentum score: Count of confirmed indicators

### 2. Entry Signal Generator

**Purpose**: Combine all analysis components to produce final entry signals using a tiered approach for increased frequency while maintaining profitability

**Tiered Entry Philosophy**:
The strategy uses three confidence tiers to maximize trading opportunities:
- **Tier 1 (High Confidence)**: Strictest filters, larger position size, standard targets
- **Tier 2 (Medium Confidence)**: Relaxed filters, medium position size, tighter targets
- **Tier 3 (Quick Scalp)**: Opportunistic entries, smaller position size, very quick exits

This approach allows 2-3x more trades while maintaining profitability through:
1. Smaller position sizes on lower-confidence setups
2. Faster profit-taking on opportunistic trades
3. Immediate breakeven management on all trades
4. No cooldown after profitable trades

**Signal Requirements**:

**Long Entry Criteria** (Tiered approach for frequency):

**Tier 1 - High Confidence (Strict)**: ALL must be true
1. Market is volatile enough (not choppy)
2. Bullish breakout OR liquidity sweep detected
3. Momentum score >= 3 (3+ confirmations)
4. Volume spike present
5. Not in cooldown period

**Tier 2 - Medium Confidence (Relaxed)**: ALL must be true
1. Market volatility acceptable (ATR > 70% of average)
2. Bullish breakout OR strong momentum
3. Momentum score >= 2 (2+ confirmations)
4. Not in cooldown period
5. Previous trade was profitable OR no recent trades

**Tier 3 - Quick Scalp (Opportunistic)**: ALL must be true
1. Strong volume spike (> 2x average)
2. Large candle body (> 0.5% move)
3. Momentum score >= 1
4. Immediate stop loss very tight (< 0.3%)
5. Quick profit target (0.5-0.8%)

**Short Entry Criteria**: Same tiered structure for bearish setups

**Interface**:
```pinescript
// Outputs
enter_long_tier1: bool  // High confidence
enter_long_tier2: bool  // Medium confidence
enter_long_tier3: bool  // Quick scalp
enter_short_tier1: bool
enter_short_tier2: bool
enter_short_tier3: bool
entry_tier: int  // 1, 2, or 3
entry_quality_score: float  // 0.0-1.0 confidence rating
position_size_multiplier: float  // Adjusted based on tier
```

### 3. Frequency Control System

**Purpose**: Prevent overtrading and manage trade frequency intelligently

**Components**:

#### 3.1 Cooldown Manager
- Tracks time since last trade
- Implements configurable cooldown period (in bars)
- Extended cooldown after consecutive losses

#### 3.2 Rate Limiter (Relaxed for Frequency)
- Tracks trades per hour (increased limit: 6-8 trades/hour)
- Enforces maximum trades per session (50-80 trades/day)
- Resets counters at hour boundaries
- **Adaptive Limits**: Increase limits during high volatility periods
- **Win Streak Bonus**: Allow more trades after 3+ consecutive wins

**Interface**:
```pinescript
// Inputs
cooldown_bars: int
max_trades_per_hour: int
extended_cooldown_after_losses: int

// State Variables
var int last_trade_bar
var int trades_this_hour
var int consecutive_losses

// Outputs
can_trade_now: bool
bars_until_next_trade: int
```

**Logic**:
1. **Reduced Standard Cooldown**: `bar_index - last_trade_bar >= 1` (only 1 bar minimum)
2. **Smart Cooldown Adjustment**:
   - After win: No cooldown (immediate re-entry allowed)
   - After loss: 2-3 bar cooldown
   - After 2 consecutive losses: 5 bar cooldown
3. **Increased Hourly Limit**: Reset `trades_this_hour` when `hour != hour[1]`
4. **Dynamic Limits**: 
   - High volatility: Allow up to 8 trades/hour
   - Normal volatility: Allow up to 6 trades/hour
   - Low volatility: Limit to 3 trades/hour
5. **Win Streak Bonus**: After 3+ wins, remove cooldown entirely for next 3 trades

### 4. Risk Management Module

**Purpose**: Calculate position sizes and set adaptive stop loss/take profit levels

#### 4.1 Position Sizing Calculator

**Method**: Fixed percentage risk per trade

**Formula**:
```
risk_amount = equity * risk_percentage
stop_distance = atr * atr_multiplier
position_size = risk_amount / stop_distance
```

**Interface**:
```pinescript
// Inputs
risk_percentage: float  // e.g., 0.01 for 1%
atr_multiplier_sl: float

// Outputs
calculated_position_size: float
max_loss_amount: float
```

#### 4.2 Adaptive Stop Loss System

**Long Position Stop Loss**:
- Primary: `entry_price - (atr * atr_multiplier)`
- Alternative: `recent_swing_low * (1 - buffer)`
- Use whichever is closer to entry but not less than minimum distance

**Short Position Stop Loss**:
- Primary: `entry_price + (atr * atr_multiplier)`
- Alternative: `recent_swing_high * (1 + buffer)`
- Use whichever is closer to entry but not less than minimum distance

**Interface**:
```pinescript
// Inputs
atr_multiplier_sl: float
swing_buffer: float
min_sl_distance_pct: float
max_sl_distance_pct: float

// Outputs
long_stop_loss: float
short_stop_loss: float
stop_distance_pct: float
```

#### 4.3 Dynamic Take Profit System

**Multi-Tier Profit Taking** (Optimized for Frequent Scalping):

**Tier 1 - Ultra Quick Scalp** (40% of position):
- Target: `entry + (stop_distance * 0.6)` (0.6:1 R:R - very quick)
- Percentage: 40%
- Purpose: Lock in profit fast, reduce risk immediately

**Tier 2 - Standard Profit** (40% of position):
- Target: `entry + (stop_distance * 1.2)` (1.2:1 R:R)
- Percentage: 40%
- Purpose: Capture main move

**Tier 3 - Runner** (Remaining 20%):
- Activation: After Tier 2 is hit
- Trail distance: `atr * 0.8` (tight trailing)
- Trail offset: Adjusts dynamically
- Purpose: Catch extended moves

**Breakeven Management**:
- Move stop to breakeven + 0.1% after Tier 1 hits
- Ensures every trade that hits Tier 1 is profitable

**Interface**:
```pinescript
// Inputs
tp1_rr_ratio: float  // e.g., 1.0 for 1:1
partial_close_pct: float  // e.g., 50
trail_atr_multiplier: float

// Outputs
long_tp1: float
short_tp1: float
trailing_stop_price: float
tp1_hit: bool
```

### 5. Trade Execution Engine

**Purpose**: Manage order placement and exit logic

**Order Flow**:

1. **Entry Phase**:
   ```pinescript
   if enter_long and strategy.position_size == 0
       strategy.entry("Long", strategy.long, qty=position_size)
       store_entry_data(entry_price, stop_loss, tp_levels)
   ```

2. **Partial Exit Phase**:
   ```pinescript
   if position_size > 0 and close >= tp1_price and not tp1_hit
       strategy.close("Long", qty_percent=partial_close_pct)
       tp1_hit := true
       activate_trailing_stop()
   ```

3. **Trailing Stop Phase**:
   ```pinescript
   if tp1_hit and position_size > 0
       update_trailing_stop(close, atr)
       if close <= trailing_stop_price
           strategy.close("Long", comment="Trail")
   ```

4. **Stop Loss Management**:
   ```pinescript
   strategy.exit("Long Exit", "Long", stop=stop_loss, limit=tp1_price)
   ```

**State Management**:
```pinescript
// Track trade state
var float entry_price = na
var float stop_loss_price = na
var float tp1_price = na
var bool tp1_hit = false
var float trailing_stop = na

// Reset on new entry
reset_trade_state() =>
    entry_price := close
    stop_loss_price := calculated_sl
    tp1_price := calculated_tp1
    tp1_hit := false
    trailing_stop := na
```

### 6. Visualization & Reporting Module

**Purpose**: Provide clear visual feedback and performance metrics

#### 6.1 Chart Overlays

**Entry/Exit Markers**:
- Long entry: Green triangle up below bar with "LONG" text
- Short entry: Red triangle down above bar with "SHORT" text
- Exit markers: Small circles at exit points

**Stop Loss / Take Profit Lines**:
- Stop loss: Red solid line
- Take profit 1: Green dashed line
- Trailing stop: Purple crosses

**Market Condition Indicators**:
- Choppy market: Gray background shading (90% transparency)
- Swing highs/lows: Small triangles at pivot points
- Breakout levels: Horizontal lines at key levels

#### 6.2 Performance Statistics Table

**Metrics Displayed** (top-right corner):
- Net Profit (with color coding)
- Total Trades
- Win Rate %
- Profit Factor
- Average Win / Average Loss
- Max Drawdown %
- Current Position Status
- Trades This Hour

**Table Structure**:
```pinescript
var table stats_table = table.new(position.top_right, 2, 8)
// Column 0: Metric name
// Column 1: Metric value (color-coded)
```

## Data Models

### Trade State Model
```pinescript
type TradeState
    float entry_price
    float stop_loss
    float tp1_price
    float tp2_price
    bool tp1_hit
    float trailing_stop
    int entry_bar
    string direction  // "long" or "short"
```

### Market Condition Model
```pinescript
type MarketCondition
    bool is_volatile
    bool is_choppy
    float atr_value
    float efficiency_ratio
    float swing_high
    float swing_low
```

### Frequency Control Model
```pinescript
type FrequencyState
    int last_trade_bar
    int trades_this_hour
    int consecutive_losses
    int cooldown_remaining
```

## Profit Guarantee Mechanisms

### Core Profit Protection Strategy

To ensure frequent trading remains profitable, the strategy implements multiple layers of profit protection:

#### 1. Immediate Breakeven Management
- **Trigger**: As soon as Tier 1 profit target (40% of position) is hit
- **Action**: Move stop loss to entry + 0.1% (small profit lock)
- **Result**: Every trade that reaches first target becomes profitable

#### 2. Tiered Position Sizing
- **Tier 1 Entries**: 100% of calculated position size (high confidence)
- **Tier 2 Entries**: 70% of calculated position size (medium confidence)
- **Tier 3 Entries**: 40% of calculated position size (opportunistic)
- **Result**: Lower risk on less certain setups

#### 3. Adaptive Profit Targets
- **Tier 1 Trades**: Standard targets (0.6:1, 1.2:1, trailing)
- **Tier 2 Trades**: Tighter targets (0.5:1, 1.0:1, trailing)
- **Tier 3 Trades**: Very tight targets (0.4:1, 0.8:1, no trailing)
- **Result**: Faster profit-taking on lower-confidence trades

#### 4. Win-Based Cooldown Removal
- **After Win**: No cooldown, immediate re-entry allowed
- **After Loss**: 2-3 bar cooldown to avoid revenge trading
- **Win Streak (3+)**: Bonus period with no cooldown for 3 trades
- **Result**: Capitalize on favorable market conditions

#### 5. Dynamic Frequency Limits
- **High Volatility**: Up to 8 trades/hour (more opportunities)
- **Normal Volatility**: Up to 6 trades/hour (standard)
- **Low Volatility**: Max 3 trades/hour (conservative)
- **Result**: Trade more when conditions are favorable

#### 6. Profit Factor Monitoring
- **Real-time Tracking**: Monitor profit factor throughout session
- **Adaptive Throttling**: If profit factor drops below 1.5, switch to Tier 1 only
- **Recovery Mode**: After 3 consecutive losses, require Tier 1 signals only
- **Result**: Automatic risk reduction during drawdown periods

#### 7. Time-Based Profit Locks
- **5-Minute Rule**: If trade is open for 5+ bars without hitting TP1, move SL to breakeven
- **10-Minute Rule**: If trade is open for 10+ bars, close 50% at market
- **Result**: Prevent trades from turning into losses due to time decay

### Expected Outcome
With these mechanisms:
- **Estimated Win Rate**: 55-65% (higher due to quick profit-taking)
- **Estimated Profit Factor**: 2.0-2.5 (protected by breakeven management)
- **Estimated Trade Frequency**: 8-15 trades/day (3x increase vs standard)
- **Estimated Max Drawdown**: 8-12% (controlled by tiered sizing)

## Error Handling

### Invalid Data Handling
- Check for `na` values before calculations
- Use `nz()` function for safe array access
- Validate ATR is not zero before position sizing

### Position Management Errors
- Verify position size is within broker limits
- Ensure stop loss is not too close to entry (minimum distance)
- Validate take profit is beyond entry price

### Edge Cases
- Handle first bars where indicators are not yet calculated
- Manage array bounds when accessing swing highs/lows
- Prevent division by zero in risk calculations

## Testing Strategy

### Unit Testing Approach
1. **Volatility Filter Tests**: Verify choppy market detection
2. **Structure Detection Tests**: Confirm breakout and sweep identification
3. **Momentum Filter Tests**: Validate multi-indicator confirmation
4. **Position Sizing Tests**: Ensure correct risk-based calculations
5. **Frequency Control Tests**: Verify cooldown and rate limiting

### Integration Testing
1. **Full Signal Generation**: Test complete entry logic flow
2. **Trade Management**: Verify partial exits and trailing stops
3. **Multi-Trade Scenarios**: Test consecutive wins/losses handling

### Backtesting Parameters
- **Timeframe**: 5-minute
- **Symbols**: BTC/USDT, ETH/USDT, major crypto pairs
- **Period**: Minimum 6 months of data
- **Initial Capital**: $10,000
- **Commission**: 0.075% per trade
- **Slippage**: 2 ticks

### Performance Targets
- **Win Rate**: > 55% (higher win rate for frequent trading)
- **Profit Factor**: > 2.0 (ensure profitability with more trades)
- **Max Drawdown**: < 12%
- **Average Trades Per Day**: 8-15 (increased frequency)
- **Risk/Reward Ratio**: > 1.2:1 average (tighter but more frequent)
- **Minimum Trades Per Hour**: 1-2 during active sessions

## Configuration Parameters

### Input Groups

**Market Analysis**:
- `atr_period`: 14 (range: 10-20)
- `swing_lookback`: 10 (range: 5-20)
- `volatility_threshold`: 1.0 (range: 0.5-2.0)
- `kaufman_period`: 15 (range: 10-30)

**Entry Filters** (Tiered for Frequency):
- `volume_spike_multiplier_tier1`: 2.0 (range: 1.5-3.0) - High confidence
- `volume_spike_multiplier_tier2`: 1.5 (range: 1.2-2.0) - Medium confidence
- `volume_spike_multiplier_tier3`: 2.5 (range: 2.0-4.0) - Quick scalp (very high)
- `ma_fast_period`: 8 (range: 5-15)
- `min_candle_body_pct_tier1`: 0.4 (range: 0.3-0.8) - Larger moves
- `min_candle_body_pct_tier2`: 0.25 (range: 0.15-0.5) - Medium moves
- `min_candle_body_pct_tier3`: 0.5 (range: 0.4-1.0) - Very large moves
- `rsi_period`: 14 (range: 10-20)
- `min_momentum_confirmations_tier1`: 3 (range: 2-4) - Strict
- `min_momentum_confirmations_tier2`: 2 (range: 1-3) - Relaxed
- `min_momentum_confirmations_tier3`: 1 (range: 1-2) - Opportunistic

**Risk Management** (Adjusted for Frequent Trading):
- `risk_per_trade_pct`: 0.8 (range: 0.5-2.0) - Slightly lower per trade
- `atr_multiplier_sl`: 1.2 (range: 0.8-2.0) - Tighter stops for scalping
- `tp1_rr_ratio`: 0.6 (range: 0.4-1.0) - Quick first profit
- `tp2_rr_ratio`: 1.2 (range: 0.8-1.5) - Standard second profit
- `partial_close_pct_tier1`: 40 (range: 30-50) - First quick exit
- `partial_close_pct_tier2`: 40 (range: 30-50) - Second exit
- `trail_atr_multiplier`: 0.8 (range: 0.5-1.2) - Tight trailing for runners
- `breakeven_trigger_rr`: 0.6 - Move to BE after first target

**Frequency Control** (Optimized for High Frequency):
- `cooldown_bars_after_win`: 0 (range: 0-2) - No cooldown after wins
- `cooldown_bars_after_loss`: 2 (range: 1-5) - Short cooldown after losses
- `max_trades_per_hour_high_vol`: 8 (range: 5-12) - More trades in volatile markets
- `max_trades_per_hour_normal`: 6 (range: 3-10) - Standard frequency
- `extended_cooldown_after_losses`: 5 (range: 3-10) - Only after 2+ losses
- `win_streak_bonus_threshold`: 3 (range: 2-5) - Wins needed for bonus
- `enable_tiered_entries`: true - Allow multiple confidence tiers

**Visualization**:
- `show_swing_points`: true
- `show_sl_tp_lines`: true
- `show_chop_zones`: true
- `show_stats_table`: true

## Performance Optimization

### Computational Efficiency
1. **Minimize Indicator Recalculation**: Store frequently used values
2. **Efficient Array Operations**: Use built-in functions over loops
3. **Conditional Plotting**: Only draw when necessary
4. **State Variable Management**: Use `var` for persistent state

### Memory Management
1. **Limit Historical Data**: Use appropriate `max_bars_back`
2. **Clean Up Old Lines/Labels**: Delete after certain bars
3. **Array Size Limits**: Cap swing high/low arrays at 20 elements

### Code Organization
1. **Modular Functions**: Separate concerns into distinct functions
2. **Clear Naming**: Use descriptive variable names
3. **Comments**: Document complex logic and calculations
4. **Input Grouping**: Organize parameters by category

## Security Considerations

### Webhook Integration (Future Enhancement)
- Validate all incoming webhook data
- Use authentication tokens
- Implement rate limiting on webhook endpoints
- Log all webhook activities

### API Key Management
- Never hardcode API keys in script
- Use secure input fields for sensitive data
- Implement proper error handling for API failures

## Deployment Considerations

### TradingView Strategy Tester
- Set appropriate commission and slippage
- Use realistic initial capital
- Enable "Recalculate After Order Filled" for accuracy
- Test on multiple timeframes and symbols

### Live Trading Preparation
- Paper trade for minimum 2 weeks
- Monitor performance metrics daily
- Adjust parameters based on live market conditions
- Implement emergency stop mechanisms

### Monitoring and Maintenance
- Track daily performance metrics
- Review losing trades for pattern identification
- Adjust volatility thresholds seasonally
- Update swing lookback based on market regime changes

## Future Enhancements

### Phase 2 Features
1. **Multi-Timeframe Analysis**: Incorporate higher timeframe trend filters
2. **Machine Learning Integration**: Adaptive parameter optimization
3. **Correlation Analysis**: Avoid correlated trades across pairs
4. **Session-Based Filters**: Optimize for specific trading sessions

### Phase 3 Features
1. **Portfolio Management**: Multi-symbol position sizing
2. **Advanced Order Types**: Iceberg orders, TWAP execution
3. **Sentiment Integration**: Social media and news sentiment
4. **Backtesting Framework**: Automated parameter optimization

## Conclusion

This design provides a comprehensive framework for building a professional-grade scalping strategy that balances aggressive trade frequency with intelligent filtering and robust risk management. The modular architecture allows for easy testing, optimization, and future enhancements while maintaining code clarity and performance efficiency.
