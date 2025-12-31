"""
Time complexity detection and management for the Bemo competitive programming platform.

This module handles:
- Complexity hierarchy and comparison
- Time complexity detection from execution data
- Cascading complexity closing logic
"""

from typing import List, Optional, Tuple
import json
from bemo import db
from bemo.models import Problem, ProblemComplexitySolve, Submission, User


# Define complexity hierarchy (lower index = better/easier complexity)
COMPLEXITY_HIERARCHY = [
    'O(1)',        # Constant
    'O(log n)',    # Logarithmic
    'O(n)',        # Linear
    'O(n log n)',  # Linearithmic
    'O(n^2)',      # Quadratic
    'O(n^3)',      # Cubic
    'O(2^n)',      # Exponential
    'O(n!)',       # Factorial
]

# Map complexity strings to their hierarchy index
COMPLEXITY_INDEX = {comp: idx for idx, comp in enumerate(COMPLEXITY_HIERARCHY)}


def get_complexity_rank(complexity: str) -> int:
    """
    Get the rank/index of a complexity in the hierarchy.
    Lower rank = better/easier complexity.
    
    Args:
        complexity: Complexity string (e.g., 'O(n)')
    
    Returns:
        int: Index in hierarchy, or -1 if not found
    """
    return COMPLEXITY_INDEX.get(complexity, -1)


def is_complexity_easier_or_equal(comp1: str, comp2: str) -> bool:
    """
    Check if comp1 is easier than or equal to comp2.
    
    Args:
        comp1: First complexity
        comp2: Second complexity
    
    Returns:
        bool: True if comp1 is easier or equal to comp2
    """
    rank1 = get_complexity_rank(comp1)
    rank2 = get_complexity_rank(comp2)
    
    if rank1 == -1 or rank2 == -1:
        return False
    
    return rank1 <= rank2


def is_complexity_harder(comp1: str, comp2: str) -> bool:
    """
    Check if comp1 is harder than comp2.
    
    Args:
        comp1: First complexity
        comp2: Second complexity
    
    Returns:
        bool: True if comp1 is harder than comp2
    """
    rank1 = get_complexity_rank(comp1)
    rank2 = get_complexity_rank(comp2)
    
    if rank1 == -1 or rank2 == -1:
        return False
    
    return rank1 > rank2


def detect_complexity_from_execution(execution_times: List[float], input_sizes: List[int]) -> str:
    """
    Detect time complexity based on execution times and input sizes.
    
    This is a simplified heuristic. For production, you would use more sophisticated
    curve fitting algorithms.
    
    Args:
        execution_times: List of execution times in seconds
        input_sizes: List of input sizes (e.g., array length, n)
    
    Returns:
        str: Detected complexity string (e.g., 'O(n)')
    """
    if not execution_times or not input_sizes or len(execution_times) != len(input_sizes):
        return 'O(n)'  # Default assumption
    
    # If all times are very similar, likely O(1)
    if len(execution_times) > 1:
        max_time = max(execution_times)
        min_time = min(execution_times)
        if max_time > 0 and (max_time - min_time) / max_time < 0.2:  # Less than 20% variation
            return 'O(1)'
    
    # Calculate growth ratios
    # For simplicity, we'll use a basic heuristic:
    # - If time grows slower than input: O(log n)
    # - If time grows linearly with input: O(n)
    # - If time grows as input * log(input): O(n log n)
    # - If time grows quadratically: O(n^2)
    
    # For now, return a default based on average time growth
    # In production, use proper curve fitting (scipy, numpy)
    
    if len(execution_times) >= 2 and len(input_sizes) >= 2:
        # Calculate simple ratio
        time_ratio = execution_times[-1] / max(execution_times[0], 0.0001)
        size_ratio = input_sizes[-1] / max(input_sizes[0], 1)
        
        if time_ratio < 2 and size_ratio > 10:
            return 'O(log n)'
        elif time_ratio < size_ratio * 1.5:
            return 'O(n)'
        elif time_ratio < size_ratio * 2:
            return 'O(n log n)'
        elif time_ratio < size_ratio ** 2 * 1.5:
            return 'O(n^2)'
        else:
            return 'O(n^3)'
    
    return 'O(n)'  # Default


def estimate_complexity_from_time(avg_time: float, problem_rating: int) -> str:
    """
    Estimate complexity based on average execution time and problem rating.
    This is a fallback when we don't have detailed input size information.
    
    Args:
        avg_time: Average execution time in seconds
        problem_rating: Problem difficulty rating
    
    Returns:
        str: Estimated complexity
    """
    # Higher rated problems typically have higher expected complexity
    if problem_rating < 800:
        # Easy problems typically O(1) to O(n)
        if avg_time < 0.01:
            return 'O(1)'
        else:
            return 'O(n)'
    elif problem_rating < 1200:
        # Medium problems typically O(n) to O(n log n)
        if avg_time < 0.01:
            return 'O(n)'
        else:
            return 'O(n log n)'
    elif problem_rating < 1600:
        # Hard problems typically O(n log n) to O(n^2)
        if avg_time < 0.05:
            return 'O(n log n)'
        else:
            return 'O(n^2)'
    else:
        # Very hard problems can be O(n^2) or worse
        if avg_time < 0.1:
            return 'O(n^2)'
        else:
            return 'O(n^3)'


def is_complexity_open_for_scoring(problem_id: int, complexity: str) -> bool:
    """
    Check if a time complexity level is still "open" for scoring on a problem.
    
    A complexity is "closed" if:
    1. It has already been solved by someone (first solve exists)
    2. A better (easier) complexity has been solved
    
    Args:
        problem_id: Problem ID
        complexity: Complexity to check (e.g., 'O(n)')
    
    Returns:
        bool: True if complexity is open for scoring
    """
    # Check if this exact complexity has been solved
    existing_solve = ProblemComplexitySolve.query.filter_by(
        problem_id=problem_id,
        complexity=complexity
    ).first()
    
    if existing_solve:
        # This complexity has been solved, closed for scoring
        return False
    
    # Check if any easier complexity has been solved
    comp_rank = get_complexity_rank(complexity)
    if comp_rank == -1:
        return True  # Unknown complexity, allow scoring
    
    # Get all solved complexities for this problem
    all_solves = ProblemComplexitySolve.query.filter_by(problem_id=problem_id).all()
    
    for solve in all_solves:
        solved_rank = get_complexity_rank(solve.complexity)
        if solved_rank != -1 and solved_rank < comp_rank:
            # A better (easier) complexity has been solved
            # This closes the current complexity
            return False
    
    return True


def get_closed_complexities(problem_id: int, solved_complexity: str) -> List[str]:
    """
    Get list of complexities that should be closed after solving at a given complexity.
    
    When you solve at O(n), it closes O(n) and all easier complexities like O(1), O(log n).
    But it does NOT close harder complexities like O(n^2).
    
    Args:
        problem_id: Problem ID
        solved_complexity: The complexity that was just solved
    
    Returns:
        List[str]: List of complexity strings that are now closed
    """
    solved_rank = get_complexity_rank(solved_complexity)
    if solved_rank == -1:
        return [solved_complexity]  # Only close the solved one if unknown
    
    # Close this complexity and all easier ones
    closed = []
    for comp in COMPLEXITY_HIERARCHY:
        comp_rank = get_complexity_rank(comp)
        if comp_rank <= solved_rank:
            closed.append(comp)
    
    return closed


def record_complexity_solve(problem_id: int, user_id: int, submission_id: int, complexity: str) -> bool:
    """
    Record that a user has solved a problem at a specific complexity level.
    
    Args:
        problem_id: Problem ID
        user_id: User ID
        submission_id: Submission ID
        complexity: Complexity achieved
    
    Returns:
        bool: True if this was a first solve at this complexity (and should be scored)
    """
    # Check if this complexity is still open for scoring
    if not is_complexity_open_for_scoring(problem_id, complexity):
        return False
    
    # Record the solve - let caller handle commit
    try:
        solve = ProblemComplexitySolve(
            problem_id=problem_id,
            complexity=complexity,
            first_solver_id=user_id,
            submission_id=submission_id
        )
        db.session.add(solve)
        # Don't commit here - let the calling function handle transaction
        # The unique constraint will still prevent duplicates when commit happens
        return True
    except Exception as e:
        # Likely a race condition - someone else solved it first
        db.session.rollback()
        print(f"Failed to record complexity solve: {e}")
        return False


def calculate_complexity_bonus(problem_rating: int, complexity: str) -> int:
    """
    Calculate bonus points for solving at a specific complexity.
    
    Better complexities earn more points.
    
    Args:
        problem_rating: Problem difficulty rating
        complexity: Complexity achieved
    
    Returns:
        int: Bonus points
    """
    base_bonus = problem_rating // 10  # Base bonus from problem difficulty
    
    comp_rank = get_complexity_rank(complexity)
    if comp_rank == -1:
        return base_bonus
    
    # Award more points for better complexities
    # O(1) gets 8x, O(log n) gets 7x, O(n) gets 6x, O(n log n) gets 5x, etc.
    multiplier = max(1, len(COMPLEXITY_HIERARCHY) - comp_rank)
    
    return base_bonus * multiplier


def get_problem_complexity_status(problem_id: int) -> dict:
    """
    Get the status of all complexity levels for a problem.
    
    Args:
        problem_id: Problem ID
    
    Returns:
        dict: Maps complexity -> (is_open, first_solver_username if solved)
    """
    solves = ProblemComplexitySolve.query.filter_by(problem_id=problem_id).all()
    
    status = {}
    for comp in COMPLEXITY_HIERARCHY:
        status[comp] = {'open': True, 'solver': None}
    
    # Mark solved complexities
    for solve in solves:
        if solve.complexity in status:
            solver = User.query.get(solve.first_solver_id)
            status[solve.complexity] = {
                'open': False,
                'solver': solver.username if solver else 'Unknown'
            }
    
    # Mark complexities closed by easier solutions
    for comp in COMPLEXITY_HIERARCHY:
        if not status[comp]['open']:
            continue
        
        comp_rank = get_complexity_rank(comp)
        for solve in solves:
            solved_rank = get_complexity_rank(solve.complexity)
            if solved_rank != -1 and solved_rank < comp_rank:
                # A better complexity was solved, this one is closed
                status[comp]['open'] = False
                break
    
    return status
