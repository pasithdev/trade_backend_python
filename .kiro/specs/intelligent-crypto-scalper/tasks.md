# Implementation Plan

- [x] 1. Set up Pine Script v5 strategy foundation and input parameters





  - Create the base strategy declaration with proper settings (overlay, pyramiding, commission, slippage)
  - Define all input parameters organized by functional groups (Market Analysis, Entry Filters, Risk Management, Frequency Control, Visualization)
  - Set up initial capital, default quantity type, and margin settings for crypto scalping
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7, 8.8_

- [x] 2. Implement volatility analysis module





  - [x] 2.1 Calculate ATR and ATR-based volatility metrics


    - Implement ATR calculation with configurable period
    - Calculate ATR SMA for relative volatility comparison
    - Create volatility expansion detection logic (ATR > SMA(ATR) * threshold)
    - _Requirements: 1.2, 1.4_
  - [x] 2.2 Implement Kaufman Efficiency Ratio for chop detection


    - Calculate price change over lookback period
    - Calculate sum of absolute price changes (noise)
    - Compute efficiency ratio (signal / noise)
    - Create choppy market flag when efficiency < 0.3
    - _Requirements: 1.1, 1.2_
  - [x] 2.3 Create composite volatility filter


    - Combine ATR and Kaufman metrics
    - Implement minimum volatility threshold check
    - Output boolean flag for tradeable market conditions
    - _Requirements: 1.2, 1.5_

- [x] 3. Implement market structure detection module






  - [x] 3.1 Create swing high/low detection system

    - Calculate highest high over lookback period
    - Calculate lowest low over lookback period
    - Store recent swing levels in variables
    - _Requirements: 1.3, 1.5_
  - [x] 3.2 Implement breakout detection logic


    - Detect bullish breakout (close > previous swing high)
    - Detect bearish breakout (close < previous swing low)
    - Add tolerance buffer for noise filtering
    - _Requirements: 1.3, 2.1_
  - [x] 3.3 Create liquidity sweep identification


    - Detect false breakouts with reversal (price briefly breaks level then closes back)
    - Implement bullish sweep: low < swing_low AND close > swing_low AND bullish candle
    - Implement bearish sweep: high > swing_high AND close < swing_high AND bearish candle
    - _Requirements: 1.4, 2.1_

- [x] 4. Implement momentum filter module





  - [x] 4.1 Create volume spike detection


    - Calculate volume moving average (20-period)
    - Detect volume spikes (volume > avg * multiplier)
    - Output boolean confirmation flag
    - _Requirements: 2.1, 2.2_
  - [x] 4.2 Implement fast MA slope analysis

    - Calculate fast moving average (8-period EMA)
    - Compute MA slope over 3 bars
    - Determine bullish/bearish slope based on threshold
    - _Requirements: 2.1, 2.3_

  - [x] 4.3 Create candle body size filter

    - Calculate candle body as abs(close - open) / close
    - Compare to minimum body percentage threshold
    - Detect significantly larger candles vs recent average

    - _Requirements: 2.1, 2.4_
  - [x] 4.4 Implement RSI filter for extremes

    - Calculate RSI with configurable period
    - Create overbought/oversold thresholds
    - Filter out entries at extreme RSI levels

    - _Requirements: 2.1, 2.3_

  - [x] 4.5 Create momentum confirmation scoring system

    - Count number of confirmed momentum indicators
    - Require minimum confirmations (default 2) for entry
    - Output momentum score (0-4)
    - _Requirements: 2.1, 2.2, 2.3, 2.4_

- [x] 5. Implement tiered entry signal generator for high frequency trading



  - [x] 5.1 Create Tier 1 (High Confidence) long entry logic


    - Require market volatility above threshold
    - Require breakout OR liquidity sweep
    - Require momentum score >= 3 confirmations
    - Require volume spike present
    - Output tier1_long_entry boolean
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6_
  - [x] 5.2 Create Tier 2 (Medium Confidence) long entry logic

    - Require acceptable volatility (70% of average)
    - Require breakout OR strong momentum
    - Require momentum score >= 2 confirmations
    - Check previous trade was profitable OR no recent trades
    - Output tier2_long_entry boolean
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6_

  - [x] 5.3 Create Tier 3 (Quick Scalp) long entry logic

    - Require strong volume spike (> 2x average)
    - Require large candle body (> 0.5% move)
    - Require momentum score >= 1 confirmation
    - Set very tight stop loss (< 0.3%)
    - Set quick profit target (0.5-0.8%)
    - Output tier3_long_entry boolean

    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6_

  - [x] 5.4 Create Tier 1, 2, 3 short entry logic (mirror of long logic)
    - Implement all three tiers for bearish setups
    - Use same confidence levels and requirements

    - Output tier1/2/3_short_entry booleans
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6_

  - [x] 5.5 Implement entry tier selection and position sizing adjustment

    - Determine which tier triggered (priority: Tier 1 > Tier 2 > Tier 3)
    - Set position size multiplier: Tier 1 = 100%, Tier 2 = 70%, Tier 3 = 40%
    - Calculate entry quality score based on tier and confirmations
    - Output selected entry_tier and position_size_multiplier
    - _Requirements: 2.1, 2.2, 6.1, 6.2_

- [x] 6. Implement adaptive frequency control system for high-frequency trading





  - [x] 6.1 Create smart cooldown manager with win/loss awareness


    - Track bar index of last trade entry
    - Implement zero cooldown after winning trades
    - Implement 2-3 bar cooldown after losing trades
    - Implement 5 bar cooldown after 2+ consecutive losses
    - Calculate bars remaining until next trade allowed
    - _Requirements: 5.2, 5.3, 5.4_
  - [x] 6.2 Implement win streak bonus system


    - Track consecutive winning trades
    - Remove cooldown entirely after 3+ consecutive wins
    - Provide bonus period of 3 trades with no cooldown
    - Reset bonus after loss or after 3 bonus trades used
    - _Requirements: 5.5_
  - [x] 6.3 Create dynamic hourly rate limiter based on volatility


    - Track current hour and trades within that hour
    - Set limit to 8 trades/hour during high volatility
    - Set limit to 6 trades/hour during normal volatility
    - Set limit to 3 trades/hour during low volatility
    - Reset counter when hour changes
    - _Requirements: 5.1, 5.4_
  - [x] 6.4 Implement profit factor monitoring and adaptive throttling


    - Calculate real-time profit factor for current session
    - Switch to Tier 1 only if profit factor drops below 1.5
    - Enter recovery mode (Tier 1 only) after 3 consecutive losses
    - Exit recovery mode after 2 consecutive wins
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_
  - [x] 6.5 Combine all frequency controls into can_trade flag


    - Check cooldown period has elapsed (or waived due to win)
    - Verify hourly limit not exceeded for current volatility regime
    - Check if recovery mode restricts to Tier 1 only
    - Output can_trade boolean and allowed_tiers array
    - _Requirements: 5.1, 5.2, 5.3, 5.4_

- [x] 7. Implement tiered risk management module with profit guarantees





  - [x] 7.1 Create tiered position sizing calculator


    - Calculate equity (initial capital + net profit)
    - Compute base risk amount (equity * 0.8%)
    - Apply tier multiplier: Tier 1 = 100%, Tier 2 = 70%, Tier 3 = 40%
    - Calculate position size based on stop distance and tier
    - Implement min/max position size limits
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_
  - [x] 7.2 Implement adaptive stop loss calculation with tighter scalping stops


    - Calculate ATR-based stop distance (1.2x ATR for scalping)
    - Determine swing-based stop levels
    - For Tier 3, use very tight stops (< 0.3%)
    - Choose optimal stop (closer to entry but not too tight)
    - Enforce minimum and maximum stop distance per tier
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_
  - [x] 7.3 Create three-tier dynamic take profit system


    - Calculate TP1 (40% position): 0.6:1 R:R for ultra-quick profit
    - Calculate TP2 (40% position): 1.2:1 R:R for standard profit
    - Calculate TP3 (20% position): Trailing stop with 0.8x ATR
    - Adjust targets based on entry tier (tighter for Tier 2/3)
    - _Requirements: 4.1, 4.2, 4.4, 4.5_
  - [x] 7.4 Implement immediate breakeven management system


    - Move stop to entry + 0.1% as soon as TP1 is hit
    - Implement 5-minute rule: move to BE if trade open 5+ bars without TP1
    - Implement 10-minute rule: close 50% at market if open 10+ bars
    - Ensure every trade hitting TP1 becomes profitable
    - _Requirements: 4.1, 4.2, 4.3, 4.6_
  - [x] 7.5 Implement risk validation checks per tier


    - Verify stop loss distance is within acceptable range for tier
    - Ensure minimum R:R ratio is met (varies by tier)
    - Validate position size doesn't exceed limits
    - Skip trade if risk parameters invalid
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [x] 8. Implement tiered trade execution engine with profit protection





  - [x] 8.1 Create tiered entry order placement logic


    - Execute strategy.entry() with tier-adjusted position size
    - Store entry tier, entry price, stop loss, and all TP levels
    - Initialize trade state variables including tier information
    - Track entry time for time-based profit locks
    - _Requirements: 2.5, 2.6, 6.1, 6.2_
  - [x] 8.2 Implement three-tier partial exit system


    - Monitor price reaching TP1 level (40% exit at 0.6:1 R:R)
    - Close first partial position and move SL to breakeven + 0.1%
    - Monitor price reaching TP2 level (40% exit at 1.2:1 R:R)
    - Close second partial position
    - Set flags indicating TP1 and TP2 hit status
    - Activate trailing stop for remaining 20%
    - _Requirements: 4.1, 4.2, 4.6_
  - [x] 8.3 Create tight trailing stop logic for runners


    - Calculate trailing stop distance (0.8x ATR)
    - Update trailing stop as price moves favorably
    - Close remaining 20% position when trailing stop hit
    - Only activate after TP2 is hit
    - _Requirements: 4.2, 4.3, 4.5_
  - [x] 8.4 Implement immediate breakeven and time-based profit locks


    - Move SL to breakeven + 0.1% immediately when TP1 hits
    - Implement 5-bar rule: move to BE if no TP1 after 5 bars
    - Implement 10-bar rule: close 50% at market if no TP1 after 10 bars
    - Ensure stop loss never moves against position
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 4.6_
  - [x] 8.5 Create comprehensive trade state management


    - Define state variables (entry_tier, entry_price, entry_bar, stop_loss, tp1/tp2/tp3, flags)
    - Track TP1_hit, TP2_hit, breakeven_moved flags
    - Reset all state on new entry
    - Update state during trade lifecycle
    - Clean up state on trade close
    - _Requirements: 4.1, 4.2, 4.3, 4.6_
  - [x] 8.6 Implement post-trade analysis for frequency control


    - Determine if closed trade was win or loss
    - Update consecutive win/loss counters
    - Calculate session profit factor
    - Trigger recovery mode if needed
    - Update cooldown based on trade outcome
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [x] 9. Implement visualization system





  - [x] 9.1 Create entry/exit markers


    - Plot green triangle up for long entries with "LONG" label
    - Plot red triangle down for short entries with "SHORT" label
    - Add exit markers at trade close points
    - _Requirements: 7.1, 7.2, 7.3_
  - [x] 9.2 Draw stop loss and take profit lines


    - Plot red solid line for active stop loss
    - Plot green dashed line for TP1 level
    - Plot purple crosses for trailing stop
    - Update lines as trade progresses
    - _Requirements: 7.4_
  - [x] 9.3 Add market condition indicators


    - Shade background gray during choppy markets
    - Mark swing highs/lows with small triangles
    - Draw horizontal lines at key breakout levels
    - _Requirements: 7.5_
  - [x] 9.4 Create enhanced performance statistics table with tier breakdown


    - Build table in top-right corner with 2-3 columns
    - Display net profit with color coding
    - Show total trades broken down by tier (Tier 1/2/3 counts)
    - Display win rate overall and per tier
    - Show profit factor with color coding (green if > 2.0)
    - Add average win/loss and max drawdown
    - Display current position status, entry tier, and trades this hour
    - Show consecutive wins/losses and win streak bonus status
    - Display current volatility regime and hourly trade limit
    - _Requirements: 7.6_
  - [x] 9.5 Implement filtered signal markers


    - Plot small markers for rejected signals
    - Show reason for rejection (optional)
    - Use subtle colors to avoid chart clutter
    - _Requirements: 7.7_
-

- [x] 10. Add tiered configuration and customization options



  - [x] 10.1 Organize inputs into logical groups with tier support


    - Group market analysis parameters
    - Group tiered entry filter parameters (separate for each tier)
    - Group tiered risk management parameters
    - Group adaptive frequency control parameters
    - Group profit guarantee mechanism parameters
    - Group visualization toggles
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7, 8.8_
  - [x] 10.2 Implement enable/disable toggles for tiers and filters


    - Add toggle to enable/disable each tier (Tier 1, 2, 3)
    - Add toggle for volume filter per tier
    - Add toggle for MA slope filter
    - Add toggle for candle body filter per tier
    - Add toggle for RSI filter
    - Add toggle for win streak bonus system
    - Add toggle for time-based profit locks
    - _Requirements: 8.6_
  - [x] 10.3 Add visualization control inputs with tier indicators


    - Toggle for swing point markers
    - Toggle for SL/TP lines (all three levels)
    - Toggle for chop zone shading
    - Toggle for statistics table with tier breakdown
    - Toggle for entry tier labels on chart
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7, 8.8_

- [x] 11. Implement error handling and validation





  - [x] 11.1 Add NA value checks


    - Check ATR is not NA before calculations
    - Validate swing levels exist before use
    - Use nz() function for safe defaults
    - _Requirements: 3.5, 6.3, 6.4_
  - [x] 11.2 Implement position size validation


    - Ensure position size is positive and non-zero
    - Cap position size at maximum allowed
    - Skip trade if position size invalid
    - _Requirements: 6.3, 6.4_
  - [x] 11.3 Add stop loss distance validation


    - Verify stop loss is not too close to entry
    - Ensure stop loss is not too far from entry
    - Skip trade if stop distance invalid
    - _Requirements: 3.5_

- [x] 12. Optimize performance and code quality




  - [x] 12.1 Optimize indicator calculations


    - Store frequently used values in variables
    - Avoid redundant calculations
    - Use built-in functions efficiently
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 2.1, 2.2, 2.3, 2.4_
  - [x] 12.2 Add code documentation


    - Add header comment with strategy description
    - Document each major section
    - Comment complex calculations
    - Add inline comments for clarity
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7, 8.8_
  - [x] 12.3 Implement clean variable naming


    - Use descriptive names for all variables
    - Follow consistent naming conventions
    - Group related variables together
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7, 8.8_

- [x] 13. Final integration and testing




  - [x] 13.1 Integrate all modules into complete strategy


    - Connect market analysis to entry signals
    - Link frequency control to trade execution
    - Wire risk management to order placement
    - Connect visualization to strategy state
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 3.1, 3.2, 3.3, 3.4, 3.5, 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 5.1, 5.2, 5.3, 5.4, 5.5, 6.1, 6.2, 6.3, 6.4, 6.5, 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7_
  - [x] 13.2 Verify strategy compiles without errors


    - Check for syntax errors
    - Validate all variable declarations
    - Ensure proper function calls
    - Test on TradingView Pine Editor
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7, 8.8_
  - [x] 13.3 Configure strategy tester settings


    - Set appropriate commission and slippage
    - Configure initial capital and position sizing
    - Enable proper order execution settings
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_
  - [x] 13.4 Run initial backtest and validate results


    - Test on BTC/USDT 5-minute chart
    - Verify trades are being generated
    - Check that SL/TP logic works correctly
    - Validate performance metrics display
    - _Requirements: 7.6, 1.1, 1.2, 1.3, 1.4, 1.5, 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 3.1, 3.2, 3.3, 3.4, 3.5, 4.1, 4.2, 4.3, 4.4, 4.5, 4.6_
