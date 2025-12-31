"""
Scoring system utilities for the Bemo competitive programming platform.

This module handles:
- Streak tracking and rewards
- Monthly leaderboard management
- Score calculations
"""

from datetime import date, datetime, timezone, timedelta
from bemo import db
from bemo.models import User, MonthlyLeaderboard, Problem
import calendar

# Scoring constants
STREAK_BONUS_BASE = 10  # Base points per day of streak
STREAK_BONUS_MULTIPLIER = 1.5  # Multiplier for longer streaks (every 7 days)
PROBLEM_BASE_SCORE = 100  # Base score for solving a problem
MONTHLY_TOP_3_REWARDS = {
    1: 5000,  # $50.00 for 1st place
    2: 2500,  # $25.00 for 2nd place
    3: 1000   # $10.00 for 3rd place
}


def update_user_streak(user, solve_date=None):
    """
    Update user's streak when they solve a problem.
    
    Args:
        user: User object
        solve_date: Date of solve (defaults to today)
    
    Returns:
        int: Streak bonus points awarded
    """
    if solve_date is None:
        solve_date = date.today()
    
    # Convert datetime to date if needed
    if isinstance(solve_date, datetime):
        solve_date = solve_date.date()
    
    if user.last_solve_date is None:
        # First solve ever
        user.current_streak = 1
        user.longest_streak = 1
        user.last_solve_date = solve_date
        return 0  # No bonus for first solve
    
    # Convert last_solve_date to date if it's datetime
    last_date = user.last_solve_date
    if isinstance(last_date, datetime):
        last_date = last_date.date()
    
    days_diff = (solve_date - last_date).days
    
    if days_diff == 0:
        # Same day, no streak update needed
        return 0
    elif days_diff == 1:
        # Consecutive day - increment streak
        user.current_streak += 1
        user.longest_streak = max(user.longest_streak, user.current_streak)
        user.last_solve_date = solve_date
    elif days_diff > 1:
        # Streak broken - reset to 1
        user.current_streak = 1
        user.last_solve_date = solve_date
        return 0  # No bonus when streak breaks
    else:
        # Solve date is before last solve (shouldn't happen normally)
        return 0
    
    # Calculate streak bonus
    streak_bonus = calculate_streak_bonus(user.current_streak)
    return streak_bonus


def calculate_streak_bonus(streak_days):
    """
    Calculate bonus points for maintaining a streak.
    
    Formula: Base points + (weeks completed * multiplier * base)
    """
    if streak_days < 2:
        return 0
    
    weeks_completed = streak_days // 7
    base_bonus = STREAK_BONUS_BASE * streak_days
    week_multiplier = weeks_completed * STREAK_BONUS_MULTIPLIER
    
    total_bonus = int(base_bonus + (base_bonus * week_multiplier))
    return total_bonus


def calculate_problem_score(problem, is_first_solve=False):
    """
    Calculate score for solving a problem.
    
    Args:
        problem: Problem object
        is_first_solve: Boolean indicating if this is the first solve globally
    
    Returns:
        int: Points awarded for solving this problem
    """
    base_score = PROBLEM_BASE_SCORE
    
    # Factor in problem rating/difficulty
    if problem.rating > 0:
        difficulty_multiplier = problem.rating / 1000.0
        base_score = int(base_score * difficulty_multiplier)
    
    # Bonus for being first to solve
    if is_first_solve:
        base_score = int(base_score * 2)  # Double points for first solve
    
    return base_score


def update_monthly_score(user, points):
    """
    Update user's monthly score and check for month reset.
    
    Args:
        user: User object
        points: Points to add to monthly score
    """
    current_date = date.today()
    
    # Check if we need to reset monthly score
    if user.last_monthly_reset is None:
        user.last_monthly_reset = current_date
        user.monthly_score = 0
    else:
        last_reset = user.last_monthly_reset
        if isinstance(last_reset, datetime):
            last_reset = last_reset.date()
        
        # Reset if we're in a new month
        if current_date.month != last_reset.month or current_date.year != last_reset.year:
            # Archive the previous month's ranking before reset
            archive_monthly_leaderboard(last_reset.year, last_reset.month)
            user.monthly_score = 0
            user.last_monthly_reset = current_date
    
    user.monthly_score += points


def archive_monthly_leaderboard(year, month):
    """
    Archive the monthly leaderboard and determine top 3 winners.
    
    Args:
        year: Year to archive
        month: Month to archive
    """
    # Get top users by monthly_score
    top_users = User.query.order_by(User.monthly_score.desc()).limit(10).all()
    
    if not top_users:
        return
    
    # Create or update leaderboard entries for top 3
    for rank, user in enumerate(top_users[:3], start=1):
        if user.monthly_score > 0:  # Only archive if they have points
            # Check if entry already exists
            existing = MonthlyLeaderboard.query.filter_by(
                user_id=user.id,
                year=year,
                month=month
            ).first()
            
            if existing:
                existing.rank = rank
                existing.score = user.monthly_score
            else:
                entry = MonthlyLeaderboard(
                    user_id=user.id,
                    year=year,
                    month=month,
                    rank=rank,
                    score=user.monthly_score,
                    reward_paid=False
                )
                db.session.add(entry)
    
    try:
        db.session.commit()
    except Exception as e:
        print(f"Error archiving monthly leaderboard: {e}")
        db.session.rollback()


def check_and_pay_monthly_rewards():
    """
    Check for unpaid monthly rewards and process payments.
    This should be run periodically (e.g., at the start of each month).
    """
    import stripe
    from flask import current_app
    
    # Get unpaid rewards
    unpaid_entries = MonthlyLeaderboard.query.filter_by(reward_paid=False).all()
    
    for entry in unpaid_entries:
        user = User.query.get(entry.user_id)
        if not user or not user.stripe_account_id:
            continue
        
        reward_amount = MONTHLY_TOP_3_REWARDS.get(entry.rank)
        if not reward_amount:
            continue
        
        try:
            # Create a transfer to the connected account
            transfer = stripe.Transfer.create(
                amount=reward_amount,
                currency="usd",
                destination=user.stripe_account_id,
                description=f"Rank #{entry.rank} reward for {calendar.month_name[entry.month]} {entry.year}"
            )
            
            entry.reward_paid = True
            db.session.commit()
            print(f"Paid ${reward_amount/100:.2f} to {user.username} for rank {entry.rank} ({entry.year}-{entry.month:02d})")
        except Exception as e:
            print(f"Failed to pay monthly reward to {user.username}: {e}")
            db.session.rollback()


def get_current_monthly_leaderboard(limit=10):
    """
    Get the current month's leaderboard.
    
    Args:
        limit: Number of top users to return
    
    Returns:
        list: List of (rank, user, score) tuples
    """
    top_users = User.query.order_by(User.monthly_score.desc()).limit(limit).all()
    return [(rank, user, user.monthly_score) for rank, user in enumerate(top_users, start=1)]


def get_historical_monthly_leaderboard(year, month, limit=10):
    """
    Get a historical monthly leaderboard.
    
    Args:
        year: Year to retrieve
        month: Month to retrieve
        limit: Number of entries to return
    
    Returns:
        list: List of MonthlyLeaderboard entries
    """
    return MonthlyLeaderboard.query.filter_by(
        year=year,
        month=month
    ).order_by(MonthlyLeaderboard.rank.asc()).limit(limit).all()


def get_user_monthly_history(user_id, limit=12):
    """
    Get a user's monthly leaderboard history.
    
    Args:
        user_id: User ID
        limit: Number of months to return
    
    Returns:
        list: List of MonthlyLeaderboard entries
    """
    return MonthlyLeaderboard.query.filter_by(
        user_id=user_id
    ).order_by(
        MonthlyLeaderboard.year.desc(),
        MonthlyLeaderboard.month.desc()
    ).limit(limit).all()
