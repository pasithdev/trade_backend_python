# Signal Debugging Guide - No Buy/Sell Arrows

## Issue
No buy/sell arrow signals are appearing on the chart.

## Debugging Features Added

I've added temporary debugging visualizations to help diagnose why signals aren't appearing. These will show you exactly what's happening with the strategy logic.

### Visual Debugging Elements

1. **Signal Generation Backgrounds**
   - Light green background = Tier 1 long signal detected
   - Light blue background = Tier 2 long signal detected
   - Light yellow background = Tier 3 long signal detected
   - Light red background = Signal blocked by frequency control

2. **Market Condition Backgrounds**
   - Gray background = Choppy market (no trading)
   - Very light lime = Tradeable market conditions

3. **Data Window Plots** (visible in data window, not on chart)
   - Momentum Score Long (blue line)
   - Momentum Score Short (red line)
   - Can Trade (1 = yes, 0 = no)
   - Cooldown OK (1 = yes, 0 = no)
   - Hourly Limit OK (1 = yes, 0 = no)

## Diagnostic Steps

### Step 1: Check if Signals Are Being Generated

Look at the chart background colors:
- **If you see light green/blue/yellow backgrounds**: Signals ARE being generated but may be blocked
- **If you see NO colored backgrounds**: Signals are NOT being generated at all

### Step 2: Check Market Conditions

- **Lots of gray background**: Market is too choppy (low volatility or sideways)
  - **Solution**: Reduce `volatility_threshold` from 1.0 to 0.7
  - **Solution**: Reduce `min_volatility_pct` from 0.7 to 0.5

- **No lime background**: Market not meeting tradeable conditions
  - **Solution**: Lower the volatility requirements

### Step 3: Check Frequency Control

- **Light red backgrounds appear**: Signals are being blocked by frequency control
  - Check the data window values:
    - `Can Trade = 0`: Frequency control is blocking
    - `Cooldown OK = 0`: Still in cooldown period
    - `Hourly Limit OK = 0`: Hit hourly trade limit

**Solutions if blocked by frequency control**:
- Reduce `cooldown_after_loss` from 2 to 0
- Increase `max_trades_hour_normal` from 6 to 12
- Disable win streak bonus temporarily

### Step 4: Check Momentum Scores

Open the Data Window (right side of TradingView) and check:
- **Momentum Score Long**: Should be 2-4 for signals
  - If always 0-1: Momentum filters too strict
  - **Solution**: Reduce `min_confirmations_tier1` from 3 to 2
  - **Solution**: Reduce `min_confirmations_tier2` from 2 to 1

### Step 5: Check Entry Filters

If no signals at all, the entry filters may be too strict:

**Quick Fix Settings** (for testing):
```
Market Analysis:
- volatility_threshold: 0.7 (was 1.0)
- min_volatility_pct: 0.5 (was 0.7)

Entry Filters - Tier 1:
- min_confirmations_tier1: 2 (was 3)
- volume_spike_tier1: 1.5 (was 2.0)

Entry Filters - Tier 2:
- min_confirmations_tier2: 1 (was 2)
- volume_spike_tier2: 1.2 (was 1.5)

Frequency Control:
- cooldown_after_win: 0
- cooldown_after_loss: 0 (was 2)
- max_trades_hour_normal: 12 (was 6)
```

## Common Issues and Solutions

### Issue 1: Market Too Choppy
**Symptom**: Constant gray background, no signals
**Solution**: 
- Reduce `volatility_threshold` to 0.6-0.7
- Try a different time period (more volatile market)
- Try a different symbol (ETH/USDT may be more volatile)

### Issue 2: Momentum Filters Too Strict
**Symptom**: No colored backgrounds at all
**Solution**:
- Reduce `min_confirmations_tier1` to 2
- Reduce `min_confirmations_tier2` to 1
- Disable some momentum filters temporarily:
  - Set `enable_rsi_filter` to false
  - Set `enable_ma_slope_filter` to false

### Issue 3: Frequency Control Blocking
**Symptom**: Colored backgrounds but red blocking backgrounds
**Solution**:
- Set all cooldown periods to 0
- Increase hourly limits to 20
- Disable `enable_win_streak_bonus`

### Issue 4: Volume Requirements Too High
**Symptom**: Occasional colored backgrounds but very rare
**Solution**:
- Reduce `volume_spike_tier1` to 1.5
- Reduce `volume_spike_tier2` to 1.2
- Reduce `volume_spike_tier3` to 2.0

### Issue 5: Wrong Timeframe or Symbol
**Symptom**: No signals on any settings
**Solution**:
- Verify you're on 5-minute timeframe
- Use BTC/USDT or ETH/USDT (most liquid)
- Try a different date range (more volatile period)
- Avoid low-volume altcoins

## Testing Procedure

1. **Start with Relaxed Settings**
   - Use the "Quick Fix Settings" above
   - This should generate signals on most markets

2. **Observe the Debugging Backgrounds**
   - Note which colors appear
   - Check if signals are being blocked (red backgrounds)

3. **Check Data Window Values**
   - Open Data Window (right panel)
   - Hover over bars to see exact values
   - Look for patterns in momentum scores

4. **Gradually Tighten Filters**
   - Once signals appear, gradually increase requirements
   - Increase `min_confirmations` one at a time
   - Increase `volume_spike` multipliers
   - Add back cooldown periods

5. **Remove Debugging Code**
   - Once working, remove the debugging section at the end
   - Or comment it out for future use

## Quick Test Configuration

For immediate testing, use these settings:

```
// Relaxed settings for testing
volatility_threshold = 0.6
min_volatility_pct = 0.4
min_confirmations_tier1 = 2
min_confirmations_tier2 = 1
min_confirmations_tier3 = 1
volume_spike_tier1 = 1.5
volume_spike_tier2 = 1.2
volume_spike_tier3 = 2.0
cooldown_after_win = 0
cooldown_after_loss = 0
cooldown_after_2losses = 0
max_trades_hour_normal = 20
```

This should generate signals on most BTC/USDT 5-minute charts.

## Removing Debugging Code

Once you've identified the issue, remove or comment out the debugging section at the end of the file:

```pinescript
// ============================================================================
// DEBUGGING PLOTS (Remove after testing)
// ============================================================================
// ... all the bgcolor and plot statements ...
```

## Expected Behavior After Fix

Once properly configured, you should see:
- Green triangles pointing up for long entries
- Red triangles pointing down for short entries
- Small "T1", "T2", or "T3" labels showing entry tier
- Red stop loss lines during active trades
- Green/blue take profit lines during active trades

---

**Created**: October 2, 2025  
**Purpose**: Diagnose why buy/sell signals aren't appearing  
**Status**: Debugging features active in code
