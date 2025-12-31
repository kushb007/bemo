# Time Complexity-Based Scoring System

## Overview
The time complexity-based scoring system rewards students for being the first to solve a problem at each time complexity level. This implements the requirement that "the scoring system should only apply to the first submission of an open time complexity."

## How It Works

### Complexity Hierarchy
We track solutions across multiple time complexity levels, ordered from best to worst:
1. **O(1)** - Constant time
2. **O(log n)** - Logarithmic
3. **O(n)** - Linear
4. **O(n log n)** - Linearithmic  
5. **O(n²)** - Quadratic
6. **O(n³)** - Cubic
7. **O(2^n)** - Exponential
8. **O(n!)** - Factorial

### Cascading Closure Rules
When a problem is solved at a particular complexity level, **that complexity and all easier complexities are closed** from future scoring:

- ✅ Solving at **O(n)** closes: O(n), O(log n), O(1)
- ❌ Solving at **O(n)** does NOT close: O(n log n), O(n²), O(n³), etc.

This means:
- If someone solves a problem in O(n²), they get points
- Later, someone solves it in O(n) - they ALSO get points (better complexity!)
- But now O(1) and O(log n) are closed, even though no one solved at those levels
- O(n log n), O(n³), etc. remain open for future solvers

### Scoring Formula

#### Base Problem Score
```
Base Score = 100 points × (problem_rating / 1000)
```

#### Complexity Bonus (New!)
```
Complexity Bonus = (problem_rating / 10) × complexity_multiplier

Where complexity_multiplier is:
- O(1): 8x
- O(log n): 7x
- O(n): 6x
- O(n log n): 5x
- O(n²): 4x
- O(n³): 3x
- O(2^n): 2x
- O(n!): 1x
```

Better complexities get higher bonuses!

#### Total Points
```
Total = Base Score + Complexity Bonus + Streak Bonus
```

### Examples

#### Example 1: Progressive Optimization
Problem rating: 1000

1. **Alice** solves in O(n²):
   - Base: 100 points
   - Complexity bonus: (1000/10) × 4 = 400 points
   - **Total: 500 points** ✅
   - **Closes:** O(n²), O(n³), O(2^n), O(n!) (and worse)

2. **Bob** solves in O(n):
   - Base: 100 points
   - Complexity bonus: (1000/10) × 6 = 600 points
   - **Total: 700 points** ✅
   - **Closes:** O(n), O(log n), O(1)

3. **Carol** tries to solve in O(n log n):
   - O(n log n) is between O(n) and O(n²), both closed
   - Actually, O(n log n) was already closed when Bob solved at O(n)
   - **No points** ❌

4. **Dave** tries to solve in O(n²):
   - Already solved by Alice
   - **No points** ❌

#### Example 2: Harder Before Easier
Problem rating: 1500

1. **Eve** solves in O(n³):
   - Complexity bonus: (1500/10) × 3 = 450 points
   - **Gets points** ✅
   - **Closes:** O(n³) and worse

2. **Frank** solves in O(n):
   - Complexity bonus: (1500/10) × 6 = 900 points
   - **Gets points** ✅ (Better complexity!)
   - **Closes:** O(n), O(log n), O(1)

3. **Grace** solves in O(n²):
   - O(n²) is between O(n) and O(n³), both closed
   - **No points** ❌

## Database Schema

### Problem Table
```python
optimal_complexity: String(20)  # Expected best complexity (e.g., "O(n)")
```

### Submission Table
```python
execution_times: Text  # JSON array of execution times per test case
detected_complexity: String(20)  # Detected complexity for this submission
```

### ProblemComplexitySolve Table (New!)
```python
id: Integer (PK)
problem_id: Integer (FK to Problem)
complexity: String(20)  # e.g., "O(n)"
first_solver_id: Integer (FK to User)
solved_at: DateTime
submission_id: Integer (FK to Submission)

# Unique constraint: (problem_id, complexity)
# Only ONE first solver per complexity level per problem
```

## API Functions

### From `bemo/complexity.py`:

#### `is_complexity_open_for_scoring(problem_id, complexity)`
Check if a complexity level is still available for scoring.
```python
if is_complexity_open_for_scoring(problem_id, "O(n)"):
    # Award points
```

#### `record_complexity_solve(problem_id, user_id, submission_id, complexity)`
Record that a user achieved a complexity level first.
```python
if record_complexity_solve(problem.id, user.id, submission.id, "O(n)"):
    # Success - award points
else:
    # Someone else got there first (race condition)
```

#### `calculate_complexity_bonus(problem_rating, complexity)`
Calculate bonus points for achieving a complexity.
```python
bonus = calculate_complexity_bonus(1000, "O(n)")  # Returns 600
```

#### `get_problem_complexity_status(problem_id)`
Get status of all complexity levels for a problem.
```python
status = get_problem_complexity_status(problem_id)
# Returns: {"O(1)": {"open": False, "solver": "alice"}, ...}
```

## Complexity Detection

### Current Implementation
We estimate complexity from execution time using heuristics:
```python
detected_complexity = estimate_complexity_from_time(avg_time, problem_rating)
```

This is **simplified** - production should use:
- Input size analysis from test cases
- Curve fitting (scipy/numpy)
- Multiple test case size variations
- Language-specific constant factor adjustments

### Future Improvements
1. **Parse input sizes** from test case files
2. **Curve fitting** to detect growth rate
3. **Multiple languages** - normalize for language overhead
4. **Manual override** - let problem authors set expected complexity
5. **Code analysis** - static analysis for loop structures

## Migration

Run the migration script to add new fields and tables:
```bash
python migrate_complexity_tracking.py
```

This adds:
- Problem.optimal_complexity
- Submission.execution_times
- Submission.detected_complexity
- ProblemComplexitySolve table

## Testing Scenarios

### Scenario 1: Simple Linear Problem
```
Problem: Find maximum in array (rating: 800)
Expected: O(n)

Test Case 1: array size 100 → 0.001s
Test Case 2: array size 1000 → 0.010s
Test Case 3: array size 10000 → 0.100s

Detection: O(n) (linear growth)
```

### Scenario 2: Two Users Race
```
1. Alice submits O(n²) at 10:00:00.000
2. Bob submits O(n²) at 10:00:00.001
3. Database sees Alice first
4. Alice gets points, Bob gets none
```

### Scenario 3: Cascading Closures
```
Problem has these complexities open:
[O(1), O(log n), O(n), O(n log n), O(n²)]

1. User solves at O(n log n):
   - Closes: O(n log n), O(n), O(log n), O(1)
   - Open: [O(n²), O(n³), ...]

2. Another user solves at O(n²):
   - Closes: O(n²), O(n³), ...
   - Open: [] (all closed now)
```

## Backward Compatibility

- Existing submissions without complexity data continue to work
- Old scoring still applies to problems without complexity tracking
- Migration is non-destructive
- Can run migration multiple times safely

## Security Considerations

- Race conditions handled with unique database constraint
- Multiple simultaneous submissions only credit first one
- Execution time manipulation prevented by Judge0 API
- All complexity detection happens server-side

## Performance

- Complexity lookup: Single database query with index
- Recording solve: Transaction with unique constraint (prevents duplicates)
- Status check: Cached for 60 seconds per problem
- Negligible overhead on submission checking

## Future Enhancements

1. **Problem complexity editor** - Let authors set expected complexity
2. **Complexity leaderboard** - Show who has the most optimal solutions
3. **Visualization** - Graph showing complexity vs. execution time
4. **Analysis mode** - Detailed breakdown of how complexity was detected
5. **Challenge mode** - "Can you beat O(n log n)?"
