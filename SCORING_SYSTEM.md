# Improved Scoring and Leaderboard System

## Overview
This document describes the enhanced scoring system implemented in Bemo to reward students based on multiple factors as specified in the requirements.

## Scoring Priority (As Specified)
The scoring system prioritizes rewards in the following order:

1. **First to solve a problem** ✅ Implemented
2. **Finding the optimal solution** ⏳ Reserved for future (requires time complexity analysis)
3. **Consistency and streaks** ✅ Implemented  
4. **Top 3 monthly leaderboard** ✅ Implemented

## Scoring Components

### 1. Problem Solving Base Score
Every problem solved earns a base score calculated as:
```
Base Score = 100 points × (problem_rating / 1000)
```

**Examples:**
- Rating 800 problem: 80 points
- Rating 1500 problem: 150 points
- Rating 2000 problem: 200 points

### 2. First Solve Bonus (Priority #1)
Being the **first person globally** to solve a problem earns a **2x multiplier**:
```
First Solve Score = Base Score × 2
```

**Example:** First solve of rating 1000 problem = 200 points (instead of 100)

### 3. Streak Bonuses (Priority #3 - Consistency)
Solving problems on consecutive days builds a streak that awards bonus points:

**Calculation:**
```python
streak_bonus = base_bonus + (base_bonus × week_multiplier)
where:
  base_bonus = 10 points × streak_days
  week_multiplier = (streak_days // 7) × 1.5
```

**Examples:**
- 2-day streak: 20 points
- 7-day streak: 70 + (70 × 1.5) = 175 points
- 14-day streak: 140 + (140 × 3.0) = 560 points

**Streak Rules:**
- Streak increments when solving a problem the next calendar day
- Streak resets to 1 if a day is skipped
- Longest streak is tracked separately for historical records
- Multiple solves on the same day don't increase streak

### 4. Monthly Leaderboard (Priority #4)

#### Monthly Score Tracking
- Every user has a `monthly_score` that accumulates all points earned in the current month
- Monthly scores automatically reset to 0 at the start of each new month
- Historical rankings are preserved in the `monthly_leaderboard` table

#### Top 3 Monthly Rewards
At the end of each month, the top 3 users receive cash rewards via Stripe:

| Rank | Reward |
|------|--------|
| 🥇 1st | $50.00 |
| 🥈 2nd | $25.00 |
| 🥉 3rd | $10.00 |

**Payout Requirements:**
- User must have Stripe account connected via `/payout-settings`
- Rewards are processed automatically via Stripe Transfers API
- Payout history is tracked to prevent duplicate payments

## Database Schema Changes

### User Table - New Fields
```python
current_streak: Integer      # Current consecutive days streak
longest_streak: Integer      # Best streak ever achieved
last_solve_date: Date        # Date of last problem solved
monthly_score: Integer       # Points earned this month
last_monthly_reset: Date     # When monthly score was last reset
```

### New Table: MonthlyLeaderboard
```python
id: Integer (PK)
user_id: Integer (FK)
year: Integer
month: Integer
rank: Integer                # 1, 2, or 3 for top winners
score: Integer               # Final monthly score
reward_paid: Boolean         # Whether reward has been paid
created_at: DateTime
```

### Solves Table - Enhanced
```python
solved_at: DateTime          # Timestamp of when problem was solved
```

## API Usage

### Scoring Functions (bemo/scoring.py)

#### `update_user_streak(user, solve_date=None)`
Updates user's streak when they solve a problem.
```python
from bemo.scoring import update_user_streak

streak_bonus = update_user_streak(user)
user.score += streak_bonus
db.session.commit()
```

#### `calculate_problem_score(problem, is_first_solve=False)`
Calculates score for solving a problem.
```python
from bemo.scoring import calculate_problem_score

score = calculate_problem_score(problem, is_first_solve=True)
```

#### `update_monthly_score(user, points)`
Updates user's monthly score and handles month transitions.
```python
from bemo.scoring import update_monthly_score

update_monthly_score(user, total_points)
```

#### `get_current_monthly_leaderboard(limit=10)`
Retrieves current month's leaderboard.
```python
from bemo.scoring import get_current_monthly_leaderboard

leaders = get_current_monthly_leaderboard(limit=5)
# Returns: [(rank, user, score), ...]
```

## Routes

### New Route: `/leaderboard`
Displays comprehensive leaderboard with three tabs:
- **Monthly**: Current month rankings with top 3 highlighted
- **All-Time**: Overall highest scorers
- **Streaks**: Most consistent problem solvers

### Updated Routes
- `/` (home): Now shows all three leaderboards side-by-side
- `/dashboard`: Displays user's streak stats and monthly score
- `/submission/<id>`: Awards points using new scoring system

## UI Components

### Dashboard Enhancements
The user dashboard now shows:
- Current streak with 🔥 icon
- Longest streak achievement
- Monthly score (separate from all-time score)
- All-time total score

### Home Page
Three-column leaderboard layout:
1. **All-Time Leaders** (Green) - Highest total scores
2. **Monthly Leaders** (Yellow) - Current month rankings with 🥇🥈🥉 medals
3. **Top Contributors** (Blue) - Contribution points

### Leaderboard Page
Tabbed interface showing:
- Monthly leaderboard with reward amounts
- All-time rankings
- Streak leaderboard with 🔥 badges
- Scoring system explanation

## Migration

Run the migration script to update existing databases:
```bash
python migrate_scoring_system.py
```

This adds:
- New columns to User table
- New MonthlyLeaderboard table
- Timestamps to solves and submission tables

## Future Development

### Time Complexity Tracking (Priority #2)
**Status:** Not yet implemented - requires further development

**Planned Approach:**
1. Analyze code execution time and memory usage from Judge0
2. Compare against known optimal complexity for each problem
3. Award bonus points for achieving optimal complexity
4. Track "best complexity achieved" per problem
5. Implement cascading rewards: solving at O(n) should award points for O(n²) and beyond, but not O(1)

**Technical Challenges:**
- Need to determine optimal complexity for each problem (requires problem metadata)
- Must account for different programming languages (constant factors vary)
- Edge case handling for small inputs where complexity doesn't matter

### Optimal Solution Detection
**Planned Features:**
- Code analysis for algorithmic patterns
- Comparison against reference implementations
- Memory efficiency scoring
- Code quality metrics (maintainability, readability)

## Testing

Run comprehensive tests:
```bash
# Basic functionality test
python test_scoring.py

# Full integration test with problem solving simulation
python test_scoring_comprehensive.py
```

## Configuration

### Scoring Constants (bemo/scoring.py)
```python
STREAK_BONUS_BASE = 10           # Base points per streak day
STREAK_BONUS_MULTIPLIER = 1.5    # Week multiplier
PROBLEM_BASE_SCORE = 100         # Base score per problem
MONTHLY_TOP_3_REWARDS = {
    1: 5000,  # $50.00 in cents
    2: 2500,  # $25.00 in cents
    3: 1000   # $10.00 in cents
}
```

## Backward Compatibility

- Existing `score` field continues to work as all-time total
- Existing `first_solves` tracking maintained for milestone rewards
- Old solves without timestamps are handled gracefully
- Migration is non-destructive and can be run multiple times

## Security Considerations

- All scoring calculations happen server-side
- Database integrity maintained with transactions
- Stripe payments use secure API with proper error handling
- Monthly leaderboard prevents duplicate reward payments via `reward_paid` flag

## Performance

- Leaderboard queries are indexed on relevant fields (score, monthly_score, streak)
- Caching applied to leaderboard routes (60-second TTL)
- Monthly reset is lazy (happens on next score update in new month)
- Efficient queries using SQLAlchemy ORM with proper eager loading
