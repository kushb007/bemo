from datetime import datetime, timezone
from bemo import db, app

solves = db.Table('solves',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('problem_id', db.Integer, db.ForeignKey('problem.id'), primary_key=True),
    db.Column('solved_at', db.DateTime, nullable=False, default=datetime.utcnow)
)

class User(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  sub = db.Column(db.String(120), unique=True, nullable=False)
  username = db.Column(db.String(20), unique=True, nullable=False)
  firstname = db.Column(db.String(20), nullable=False)
  lastname = db.Column(db.String(20), nullable=False)
  email = db.Column(db.String(120), unique=True, nullable=False)
  verified = db.Column(db.Boolean, nullable=False)
  img_file = db.Column(db.Text, nullable=False, default='default.jpeg')
  score = db.Column(db.Integer, nullable=False, default=0)
  contribution = db.Column(db.Integer, nullable=False, default=0)
  setup = db.Column(db.Boolean, nullable=False, default=False)
  stripe_account_id = db.Column(db.String(120), nullable=True)
  first_solves = db.Column(db.Integer, nullable=False, default=0)
  last_milestone_paid = db.Column(db.Integer, nullable=False, default=0)
  # Streak tracking
  current_streak = db.Column(db.Integer, nullable=False, default=0)
  longest_streak = db.Column(db.Integer, nullable=False, default=0)
  last_solve_date = db.Column(db.Date, nullable=True)
  # Monthly leaderboard tracking
  monthly_score = db.Column(db.Integer, nullable=False, default=0)
  last_monthly_reset = db.Column(db.Date, nullable=True)
  solved_problems = db.relationship('Problem', secondary=solves, lazy='subquery',
        backref=db.backref('solvers', lazy=True))

class Problem(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  title = db.Column(db.String(20), unique=True, nullable=False)
  date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow())
  statement = db.Column(db.Text, nullable=False, default='')
  tags = db.Column(db.Text,nullable=False, default='[]')
  rating = db.Column(db.Integer, nullable=False, default=0)
  cases = db.Column(db.Integer, nullable=False, default=0)
  #filenames comma separated
  inputs = db.Column(db.Text,nullable=False, default='[]')
  outputs = db.Column(db.Text, nullable=False, default='[]')
  solved = db.Column(db.Integer, nullable=False, default=0)
  # Expected optimal time complexity (e.g., 'O(n)', 'O(n^2)', 'O(log n)')
  optimal_complexity = db.Column(db.String(20), nullable=True)

class Submission(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  user_id = db.Column(db.Integer,db.ForeignKey(User.id),nullable=False)
  problem_id = db.Column(db.Integer,db.ForeignKey(Problem.id),nullable=False)
  language_id = db.Column(db.String(10), nullable=False, default='54')  # Track language used
  correct = db.Column(db.Integer, default=0)
  incorrect = db.Column(db.Integer,default=0)
  cases = db.Column(db.Integer, default=0)
  recieved = db.Column(db.Integer, default=0)
  last_check = db.Column(db.DateTime, nullable=False, default=datetime.now(timezone.utc))
  checks = db.Column(db.Integer, nullable=False, default=0)
  #json formatted tokens
  tokens = db.Column(db.Text, nullable=False, default='[]')
  status = db.Column(db.Text, nullable=False, default='[]')
  submitted_at = db.Column(db.DateTime, nullable=False, default=datetime.now(timezone.utc))
  # Store execution times from Judge0 (JSON array of times per test case in seconds)
  execution_times = db.Column(db.Text, nullable=True, default='[]')
  # Detected time complexity for this submission
  detected_complexity = db.Column(db.String(20), nullable=True)


  def __repr__(self):
    return f"User('{self.status}','{self.id}')"

class MonthlyLeaderboard(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  user_id = db.Column(db.Integer, db.ForeignKey(User.id), nullable=False)
  year = db.Column(db.Integer, nullable=False)
  month = db.Column(db.Integer, nullable=False)
  rank = db.Column(db.Integer, nullable=False)
  score = db.Column(db.Integer, nullable=False)
  reward_paid = db.Column(db.Boolean, nullable=False, default=False)
  created_at = db.Column(db.DateTime, nullable=False, default=datetime.now(timezone.utc))
  
  # Composite unique constraint for user, year, month
  __table_args__ = (db.UniqueConstraint('user_id', 'year', 'month', name='_user_month_uc'),)
  
  def __repr__(self):
    return f"MonthlyLeaderboard(user_id={self.user_id}, rank={self.rank}, {self.year}-{self.month})"

class ProblemComplexitySolve(db.Model):
  """Tracks the first solver for each time complexity level of a problem."""
  id = db.Column(db.Integer, primary_key=True)
  problem_id = db.Column(db.Integer, db.ForeignKey(Problem.id), nullable=False)
  complexity = db.Column(db.String(20), nullable=False)  # e.g., 'O(n)', 'O(n^2)'
  first_solver_id = db.Column(db.Integer, db.ForeignKey(User.id), nullable=False)
  solved_at = db.Column(db.DateTime, nullable=False, default=datetime.now(timezone.utc))
  submission_id = db.Column(db.Integer, db.ForeignKey(Submission.id), nullable=False)
  
  # Unique constraint: only one first solver per problem per complexity
  __table_args__ = (db.UniqueConstraint('problem_id', 'complexity', name='_problem_complexity_uc'),)
  
  def __repr__(self):
    return f"ProblemComplexitySolve(problem={self.problem_id}, complexity={self.complexity}, solver={self.first_solver_id})"