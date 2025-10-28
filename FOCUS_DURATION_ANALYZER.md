# Focus Duration Analyzer Implementation

## Overview

The Focus Duration Analyzer is a new agentic feature that analyzes your past distraction patterns to recommend optimal focus block durations. Instead of arbitrarily choosing how long to focus, it learns from your behavior and suggests personalized duration recommendations.

## What It Does

1. **Analyzes Past Sessions**: Looks at your completed sessions from the last 30 days (configurable)
2. **Finds First Distractions**: For each session, determines how long you were focused before the first distraction occurred
3. **Calculates Statistics**: Computes mean, median, and typical patterns
4. **Recommends Duration**: Suggests a focus block duration that's about 75% of your typical first distraction time (for safety margin)

## Example

If your analysis shows:
- Session 1: First distraction at 15 minutes
- Session 2: First distraction at 18 minutes  
- Session 3: First distraction at 12 minutes
- Session 4: First distraction at 16 minutes
- Session 5: First distraction at 20 minutes

**Statistics**:
- Mean: 16.2 minutes
- Median: 16 minutes

**Recommendation**: 12 minutes (75% of median)

The recommendation is displayed in the Dashboard tab with a message like:
> "💡 Based on your past 5 sessions, your typical first distraction occurs around 16 minutes. We recommend 12-minute focus blocks to maximize your productivity."

## Features

### Smart Analysis
- Requires minimum of 3 sessions to generate recommendations (configurable)
- Uses median (not mean) for robustness against outliers
- Applies a safety factor (recommends 75% of typical duration)
- Minimum recommended duration of 5 minutes

### Personalized Messages
- For < 10 minutes: "Short focus blocks for optimal productivity"
- For 10-25 minutes: "Medium focus blocks to maximize productivity"
- For > 25 minutes: "Longer focus blocks"
- Adjusts message based on your data patterns

### Confidence Levels
- **High**: 10+ sessions analyzed
- **Medium**: 5-9 sessions analyzed
- **Low**: 3-4 sessions analyzed

## Configuration

All settings in `config/default_config.json`:

```json
{
  "focus_analyzer_enabled": true,
  "focus_analyzer_min_sessions": 3,
  "focus_analyzer_lookback_days": 30,
  "focus_analyzer_recommendation_factor": 0.75
}
```

### Settings Explained
- **`focus_analyzer_enabled`**: Turn the feature on/off
- **`focus_analyzer_min_sessions`**: Minimum sessions needed (default: 3)
- **`focus_analyzer_lookback_days`**: How far back to analyze (default: 30 days)
- **`focus_analyzer_recommendation_factor`**: Safety factor 0.0-1.0 (default: 0.75 = 75%)

## Files Modified/Created

### New Files
1. **`src/focus_guardian/ai/focus_duration_analyzer.py`** (NEW)
   - Core analysis logic
   - `FocusDurationAnalyzer` class
   - Statistical analysis methods

### Modified Files
2. **`src/focus_guardian/core/database.py`**
   - Added `get_first_distraction_time(session_id)` method
   - Added `get_sessions_with_distractions(limit)` method

3. **`src/focus_guardian/core/config.py`**
   - Added config getters:
     - `is_focus_analyzer_enabled()`
     - `get_focus_analyzer_min_sessions()`
     - `get_focus_analyzer_lookback_days()`
     - `get_focus_analyzer_recommendation_factor()`

4. **`src/focus_guardian/session/session_manager.py`**
   - Added `focus_analyzer` instance variable
   - Added initialization logic
   - Added `get_focus_duration_recommendation()` method

5. **`src/focus_guardian/ui/main_window.py`**
   - Added `focus_recommendation_label` widget to dashboard
   - Added `_update_focus_recommendation()` method
   - Displays recommendation in the Dashboard tab

6. **`config/default_config.json`**
   - Added analyzer configuration keys

## How to Use

1. **Automatic**: The recommendation appears automatically in the Dashboard tab
2. **First Time**: You need at least 3 completed sessions with distractions for it to work
3. **Updates**: The recommendation updates as you complete more sessions
4. **Disable**: Set `focus_analyzer_enabled` to `false` in config

## Technical Details

### Algorithm
1. Query database for completed sessions from last N days
2. For each session with distractions:
   - Get session start time
   - Get first distraction event timestamp
   - Calculate duration: `first_distraction_time - session_start_time`
3. Calculate statistics:
   - Mean and median of all first distraction times
4. Generate recommendation:
   - `recommended = median * recommendation_factor`
   - Minimum: 5 minutes
   - Round to whole minutes

### Database Queries
```sql
-- Get first distraction time for a session
SELECT started_at FROM sessions WHERE session_id = ?;
SELECT started_at FROM distraction_events WHERE session_id = ? ORDER BY started_at LIMIT 1;

-- Get sessions with distractions
SELECT DISTINCT s.* 
FROM sessions s
INNER JOIN distraction_events de ON s.session_id = de.session_id
WHERE s.status = 'completed'
ORDER BY s.started_at DESC
LIMIT ?;
```

## Benefits

1. **Personalized**: Based on YOUR actual behavior, not generic advice
2. **Adaptive**: Changes as you build more data
3. **Actionable**: Gives specific duration recommendations
4. **Non-intrusive**: Doesn't force behavior, just suggests
5. **Scientific**: Based on statistical analysis, not guesswork

## Future Enhancements

Could be extended to:
- Show time-of-day patterns (better focus in morning vs afternoon?)
- Show day-of-week patterns (better focus on certain days?)
- Adaptive recommendations that change over time
- Integration with calendar to suggest focus blocks
- Mobile app recommendations based on desktop data

