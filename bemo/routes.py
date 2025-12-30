import json
import requests
import os
from os import environ as env
import secrets
import stripe
from flask import render_template, flash, redirect, url_for, request
from werkzeug.utils import secure_filename
from PIL import Image
from functools import wraps
from urllib.parse import quote_plus, urlencode
from bemo import app, db, session, oauth, cache
from bemo.forms import Confirm, Picture, Code, PayoutSettings
from bemo.models import User, Problem, Submission
import random
import http.client
import base64
from datetime import datetime
from re import escape

auth0 = oauth.register(
    'auth0',
    client_id=app.config.get("AUTH0_CLIENT_ID"),
    client_secret=app.config.get("AUTH0_CLIENT_SECRET"),
    client_kwargs={
        'scope': 'openid email profile',
    },
    server_metadata_url=f'https://{app.config.get("AUTH0_DOMAIN")}/.well-known/openid-configuration',
)

headers = {
          'x-rapidapi-key': "477e10fe7dmsh5189385f45a93e1p171958jsn2102f60c1c61",
          'x-rapidapi-host': "judge0-ce.p.rapidapi.com",
          'Content-Type': "application/json"
}

# Judge0 status codes mapping
JUDGE0_STATUS = {
    1: "In Queue",
    2: "Processing",
    3: "Accepted",
    4: "Wrong Answer",
    5: "Time Limit Exceeded",
    6: "Compilation Error",
    7: "Runtime Error (SIGSEGV)",
    8: "Runtime Error (SIGXFSZ)",
    9: "Runtime Error (SIGFPE)",
    10: "Runtime Error (SIGABRT)",
    11: "Runtime Error (NZEC)",
    12: "Runtime Error (Other)",
    13: "Internal Error",
    14: "Exec Format Error"
}

# ACE editor modes for different languages
LANGUAGE_MODES = {
    '71': 'python',      # Python
    '62': 'java',        # Java
    '54': 'c_cpp',       # C++
    '50': 'c_cpp',       # C
    '63': 'javascript',  # JavaScript
    '78': 'kotlin',      # Kotlin
    '60': 'golang',      # Go
    '72': 'ruby',        # Ruby
    '73': 'rust',        # Rust
    '82': 'sql',         # SQL
    '74': 'typescript'   # TypeScript
}

# Valid language IDs (must match the form choices)
VALID_LANGUAGE_IDS = set(LANGUAGE_MODES.keys())

#wraps functions to require auth0 token for access
def requires_auth(f):
  @wraps(f)
  def decorated(*args, **kwargs):
    if 'id' not in session:
      # Redirect to Login page here
      pass
    return f(*args, **kwargs)
  return decorated

#generate random (hopefully unique) filename for inputted picture
def save_picture(inp_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(inp_picture.filename)
    filename = random_hex + f_ext
    picture_path = os.path.join(app.config['UPLOAD_FOLDER']+'/pics', filename)
    i = Image.open(inp_picture)
    i.thumbnail((125, 125))
    i.save(picture_path)
    return filename

#homepage
@app.route("/")
@app.route("/home")
def home():
  user = None
  if 'id' in session:
    user = User.query.filter_by(id=session['id']).first()
    print(user)
  page = request.args.get('page', 1, type=int)
  problems = Problem.query.order_by(Problem.date_posted.desc()).paginate(page=page, per_page=5)
  topsolvers = User.query.order_by(User.score).limit(5).all()
  topcontributors = User.query.order_by(User.contribution).limit(5).all()
  randommessage = random.choice(["Welcome to Bemo!","Solve problems and earn points!","Join the community!","Compete with others!","Improve your coding skills!","Get started now!"])
  return render_template('home.html', problems=problems, user=user, page=page, solvs=topsolvers,conts=topcontributors, randommessage=randommessage)

#list out problems in table format
@app.route("/problems")
@app.route("/problems/<int:page_num>")
def problems():
  user = None
  if 'id' in session:
    user = User.query.filter_by(id=session['id']).first()
  page = request.args.get('page', 1, type=int)
  problems = Problem.query.order_by(Problem.date_posted.desc()).paginate(page=page, per_page=5)
  topcontributors = User.query.order_by(User.contribution).limit(5).all()
  topsolvers = User.query.order_by(User.score).limit(5).all()
  return render_template('problems.html', problems=problems, user=user, page=page, conts=topcontributors, solvs=topsolvers)


#login route for redirects
@app.route("/login")
def login():
  return oauth.auth0.authorize_redirect(
        redirect_uri=url_for("callback", _external=True)
    )

#configured to retrieve and store from auth0
@app.route('/callback', methods=["GET", "POST"])
def callback():
    # Handles response from token endpoint
    token = oauth.auth0.authorize_access_token()
    # Store the user information in flask session
    session["user"] = token
    userinfo = token['userinfo']
    session['profile'] = {
      'user_id': userinfo['sub'],
      'name': userinfo['name'],
      'picture': userinfo['picture'],
      'sub': userinfo['sub'],
      'email': userinfo['email']
    }
    #redirect to new_login to create pair within database
    detectedusr = User.query.filter_by(sub=userinfo['sub']).first()
    print(detectedusr)
    if detectedusr is None or detectedusr.setup==False:
      return redirect(url_for('new_login'))
    session['id'] = detectedusr.id
    print("Welcome "+detectedusr.username)
    return redirect('/')

#initializes user within database
@app.route('/newlogin', methods=['GET','POST'])
def new_login():
  if 'id' in session or session['profile'] is None:
    print(session['id'])
    print(session['profile'])
    print("Redirecting to home")
    return redirect('/')
  #stores user's or auth0's picture
  pic = Picture()
  if pic.submit.data and pic.validate():
    filename=save_picture(pic.pic.data)
  else:
    filename=secrets.token_hex(8)
    with open(app.config['UPLOAD_FOLDER']+'pics/'+filename, 'wb') as f:
      f.write(requests.get(session['profile']['picture']).content) #connected default pic
  form = Confirm()
  if form.submit.data and form.validate():
    user = User(
      username=form.username.data,
      firstname=form.firstname.data, 
      lastname=form.lastname.data,
      img_file=filename, 
      email=session['profile']['email'],
      sub=session['profile']['sub'],
      verified=False)
    db.session.add(user)
    db.session.commit()
    session['id'] = User.query.filter_by(sub=session['profile']['sub']).first().id
    flash('Your account has been created! You are now able to log in', 'success')
    return redirect('/dashboard')
  #renders form with auth0's default values
  return render_template('editacct.html', 
    title='New User', 
    form=form,
    pic=pic, 
    name=session['profile']['name'],
    firstname="",
    lastname="",
    img=filename)

#displays information and settings
@app.route('/dashboard')
@requires_auth
def dashboard():
  user = User.query.filter_by(id=session['id']).first()
  solved_titles = [p.title for p in user.solved_problems]
  solved_str = json.dumps(solved_titles)
  return render_template('dashboard.html', user=user,solved=solved_str)

@app.route('/payment')
@requires_auth
def payment():
  user = User.query.filter_by(id=session['id']).first()
  return render_template('payment.html', user=user)

@app.route('/user/<username>')
def show_user(username):
    user = None
    if 'id' in session:
      user = User.query.filter_by(id=session['id']).first()
    # show the user profile for that user
    result = User.query.filter_by(username=username).first()
    if result is None:
      return "User Not Found"
    return f'User {escape(username)}'

# show the problem with the given id
@app.route('/problem/<int:prob_id>', methods=['GET','POST'])
def show_prob(prob_id):
    user = None
    if 'id' in session:
      user = User.query.filter_by(id=session['id']).first()
    result = Problem.query.filter_by(id=prob_id).first()
    if result is None:
      return "Problem Not Found"
    form = Code()
    if form.submit.data and form.validate():
      print("File input",form.code.data)
      print("Text input",form.code_area.data)
      print("Language",form.language.data)
      if form.code.data is None and form.code_area.data is None:
        flash('No code received. Please enter code or upload a file.', 'danger')
        return redirect(url_for('show_prob', prob_id=prob_id))
      bytes_code = None
      if form.code.data is None and form.code_area.data is not None:
        print("Received", form.code_area.data)
        bytes_code = base64.b64encode(bytes(form.code_area.data,'utf-8')).decode('ascii')
      else:
        print("Received", form.code.data)
        bytes_code = base64.b64encode(form.code.data.read()).decode('ascii')
      
      try:
        conn = http.client.HTTPSConnection("judge0-ce.p.rapidapi.com")
        cases = {}
        cases['submissions'] = []
        print(result.inputs)
        input_files = eval(result.inputs)
        language_id = form.language.data  # Get selected language
        
        # Validate language_id to prevent injection
        if language_id not in VALID_LANGUAGE_IDS:
            flash('Invalid language selected. Please try again.', 'danger')
            return redirect(url_for('show_prob', prob_id=prob_id))
        
        for input_file in input_files:
            case = {}
            case['language_id'] = language_id  # Use dynamic language selection
            case['source_code'] = bytes_code
            with open(app.config['UPLOAD_FOLDER']+'/problem_data/'+input_file,'r') as f:
                case['stdin'] = f.read()  # Changed from 'inputs' to 'stdin'
            cases['submissions'].append(case)
        payload = json.dumps(cases)
        conn.request("POST", "/submissions/batch?base64_encoded=true", payload, headers)
        res = conn.getresponse()
        data = res.read()
        response_text = data.decode("utf-8")
        print(response_text)
        
        # Handle potential JSON parsing errors
        try:
          response_data = json.loads(response_text)
        except json.JSONDecodeError as e:
          print(f"JSON decode error: {e}")
          flash('Error communicating with Judge0 API. Please try again.', 'danger')
          return redirect(url_for('show_prob', prob_id=prob_id))
        
        # Check if response is valid
        if not isinstance(response_data, list):
          print(f"Unexpected response format: {response_data}")
          flash('Unexpected response from Judge0 API. Please try again.', 'danger')
          return redirect(url_for('show_prob', prob_id=prob_id))
        
        tokens = []
        for d in response_data:
            print(d)
            if 'token' in d:
                tokens.append(d['token'])
            else:
                # Handle error in submission
                if 'error' in d:
                  print(f"Submission error: {d['error']}")
                tokens.append(None)
        
        # Check if we got any valid tokens
        if all(token is None for token in tokens):
          flash('Failed to submit code to Judge0. Please check your code and try again.', 'danger')
          return redirect(url_for('show_prob', prob_id=prob_id))
        
        tokens_string = json.dumps(tokens)
        submission = Submission(user_id=session['id'],problem_id=prob_id,tokens=tokens_string,cases=result.cases,language_id=language_id)
        db.session.add(submission)
        db.session.commit()
        submission_id = Submission.query.filter_by(tokens=tokens_string).first().id
        return redirect('/submission/'+str(submission_id))
      except http.client.HTTPException as e:
        print(f"HTTP connection error: {e}")
        flash('Connection error with Judge0 API. Please try again.', 'danger')
        return redirect(url_for('show_prob', prob_id=prob_id))
      except Exception as e:
        print(f"Unexpected error: {e}")
        flash('An unexpected error occurred. Please try again.', 'danger')
        return redirect(url_for('show_prob', prob_id=prob_id))
    return render_template('problem.html',problem=result,form=form,user=user,tags=eval(result.tags))

def check_milestones_and_pay(user):
    milestones = {
        1: 100,    # $1.00 for 1st first-solve
        5: 500,    # $5.00 for 5th first-solve
        10: 2000   # $20.00 for 10th first-solve
    }
    
    if user.first_solves in milestones and user.last_milestone_paid < user.first_solves:
        amount = milestones[user.first_solves]
        if user.stripe_account_id:
            try:
                # Create a transfer to the connected account
                transfer = stripe.Transfer.create(
                    amount=amount,
                    currency="usd",
                    destination=user.stripe_account_id,
                    description=f"Reward for solving {user.first_solves} problems first!"
                )
                user.last_milestone_paid = user.first_solves
                db.session.commit()
                print(f"Paid {amount} to {user.username} (Transfer ID: {transfer.id})")
            except Exception as e:
                print(f"Payout failed: {e}")
        else:
             print(f"User {user.username} earned reward but no Stripe account connected.")

@app.route('/payout-settings', methods=['GET', 'POST'])
@requires_auth
def payout_settings():
    user = User.query.filter_by(id=session['id']).first()
    form = PayoutSettings()
    
    if form.validate_on_submit():
        try:
            # Create Express Account if not exists
            if not user.stripe_account_id:
                account = stripe.Account.create(
                    type="express",
                    country="IN",
                    email=user.email,
                    capabilities={
                        "transfers": {"requested": True},
                    },
                    business_type="individual",
                    individual={
                        "first_name": user.firstname,
                        "last_name": user.lastname,
                        "email": user.email,
                    },
                    business_profile={
                        "url": url_for('show_user', username=user.username, _external=True),
                        "mcc": "8299",
                        "product_description": "Competitive programming rewards"
                    }
                )
                user.stripe_account_id = account.id
                db.session.commit()
            
            # Create account link for onboarding
            account_link = stripe.AccountLink.create(
                account=user.stripe_account_id,
                refresh_url=url_for('payout_settings', _external=True),
                return_url=url_for('stripe_return', _external=True),
                type="account_onboarding",
            )
            
            return redirect(account_link.url)
            
        except Exception as e:
            flash(f"Error setting up Stripe: {str(e)}", 'danger')
            print(e)

    return render_template('payout_settings.html', form=form, user=user)

@app.route('/stripe-return')
@requires_auth
def stripe_return():
    flash("Payout settings configured successfully! You can now receive rewards.", "success")
    return redirect(url_for('dashboard'))

@app.route('/submission/<int:sub_id>')
@cache.cached(timeout=60, query_string=True)
def show_sub(sub_id):
    user = None
    if 'id' in session:
      user = User.query.filter_by(id=session['id']).first()
    sub = Submission.query.filter_by(id=sub_id).first()
    problem = Problem.query.filter_by(id=sub.problem_id).first()
    if sub is None:
      return "Submission Not Found"
    backoff_time = min(60 ** sub.checks, 10000)
    if (datetime.utcnow()-sub.last_check).total_seconds()>backoff_time:
      print("sending request")
      sub.last_check = datetime.utcnow()
      sub.checks+=1
      tokens = eval(sub.tokens)
      if len(tokens) != problem.cases:
          tokens = [None] * problem.cases
      statuses = eval(sub.status)
      if len(statuses) != problem.cases:
          statuses = [None] * problem.cases
      results = []
      correct_cases = 0
      received_cases = 0
      for i in range(len(tokens)):
          token = tokens[i]
          if token is None:
              results.append('Compilation Error')
          else:
              if statuses[i] is None:
                  try:
                      conn = http.client.HTTPSConnection("judge0-ce.p.rapidapi.com")
                      conn.request("GET", "/submissions/"+token+"?base64_encoded=true&fields=*", headers=headers)
                      res = conn.getresponse()
                      response_text = res.read().decode("utf-8")
                      submission_data = json.loads(response_text)
                      print(submission_data)
                      
                      status_id = submission_data.get('status', {}).get('id')
                      if status_id is None:
                          results.append("Error")
                      elif status_id < 3:
                          results.append("Not finished")
                      else:
                          received_cases += 1
                          # Use the JUDGE0_STATUS mapping
                          status_description = JUDGE0_STATUS.get(status_id, "Unknown Status")
                          if status_id == 3:
                              results.append('Accepted')
                              correct_cases += 1
                          elif status_id == 4:
                              results.append('Wrong Answer')
                          elif status_id == 5:
                              results.append('Time Limit Exceeded')
                          elif status_id == 6:
                              results.append('Compilation Error')
                          elif status_id in [7, 8, 9, 10, 11, 12]:
                              results.append('Runtime Error')
                          elif status_id == 13:
                              results.append('Internal Error')
                          elif status_id == 14:
                              results.append('Exec Format Error')
                          else:
                              results.append(status_description)
                  except (http.client.HTTPException, json.JSONDecodeError, KeyError) as e:
                      print(f"Error fetching submission {token}: {e}")
                      results.append("Error")
              else:
                  # Status already determined, count it
                  results.append(statuses[i])
                  if statuses[i] == 'Accepted':
                      correct_cases += 1
                      received_cases += 1
                  elif statuses[i] not in ['Not finished', 'Error']:
                      received_cases += 1
      sub.correct = correct_cases
      sub.recieved = received_cases
      sub.status = json.dumps(results)
      print(sub.status)
      db.session.commit()
    cases_string = ""
    for status in eval(sub.status):
        if status == 'Accepted':
            cases_string += "✅"
        elif status == 'Wrong Answer':
            cases_string += "❌"
        elif status == 'Compilation Error':
            cases_string += "💥"
        elif status == 'Time Limit Exceeded':
            cases_string += "⏱️"
        elif status == 'Runtime Error':
            cases_string += "💣"
        elif status == 'Error' or status == 'Internal Error' or status == 'Exec Format Error':
            cases_string += "❗"
        elif status == 'Not finished':
            cases_string += "⚙️"
        else:
            cases_string += "⚙️"
        cases_string += "\n"
    user = None
    if 'id' in session:
      user = User.query.filter_by(id=session['id']).first()
    if sub.correct == sub.cases and user.id==sub.user_id:
        if problem not in user.solved_problems:
            user.solved_problems.append(problem)
            problem.solved += 1
            
            if problem.solved == 1:
                user.first_solves += 1
                db.session.commit()
                check_milestones_and_pay(user)
            else:
                db.session.commit()
                
            print("Accepted")
        
    return render_template('submission.html',submission=sub,problem=problem,user=user,msg1=cases_string,msg2=sub.status)


#updates user's columns
@app.route('/edit-account', methods=['GET','POST'])
@requires_auth
def editacct():
  user = User.query.filter_by(id=session['id']).first()
  pic = Picture()
  if pic.submit.data and pic.validate():
    user.img_file = save_picture(pic.pic.data)
    db.session.commit()
  form = Confirm()
  if form.submit.data and form.validate():
    user.username = form.username.data
    user.firstname = form.firstname.data
    user.lastname = form.lastname.data
    user.setup = True
    db.session.commit()
    flash('Your account has been updated!', 'success')
    return redirect('/dashboard')
  return render_template('editacct.html', title='Update User',
    form=form,
    pic=pic, 
    name=user.username,
    firstname=user.firstname,
    lastname=user.lastname,
    img=user.img_file)

@app.route('/delete-user',methods =["GET", "POST"])
@requires_auth
def deleteuser():
  if request.method == "POST":
    user = User.query.filter_by(id=session['id']).first()
    user.delete()
    db.commit()
    flash("User Deleted")
    return redirect('/logout')
  return render_template('delacct.html')

#clears session and redirects to auth0's logout endpoint
@app.route('/logout')
def logout():
    # Clear session stored data
    session.clear()
    # Redirect user to logout endpoint
    flash('Logged out!')
    
    domain = app.config.get("AUTH0_DOMAIN")
    client_id = app.config.get("AUTH0_CLIENT_ID")
    
    if not domain or not client_id:
        flash("Error: Auth0 configuration missing.")
        return redirect(url_for("home"))

    return redirect(
        "https://" + domain
        + "/v2/logout?"
        + urlencode(
            {
                "returnTo": url_for("home", _external=True),
                "client_id": client_id,
            },
            quote_via=quote_plus,
        )
    )
