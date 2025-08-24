

from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

import os
import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'devsecret')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///taxes.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'


# User model
class User(UserMixin, db.Model):
  id = db.Column(db.Integer, primary_key=True)
  email = db.Column(db.String(120), unique=True, nullable=False)
  password_hash = db.Column(db.String(128), nullable=False)
  # Profile fields (dimensions)
  residence = db.Column(db.String(10), default='r')
  region = db.Column(db.String(20), default='Mainland')
  category = db.Column(db.String(2), default='A')
  kids = db.Column(db.String(100), default='')
  activity_opened = db.Column(db.String(10), default='')
  calculations = db.relationship('Calculation', backref='user', lazy=True)

  def set_password(self, password):
    self.password_hash = generate_password_hash(password)

  def check_password(self, password):
    return check_password_hash(self.password_hash, password)

# Calculation model
class Calculation(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
  timestamp = db.Column(db.DateTime, server_default=db.func.now())
  year = db.Column(db.Integer)
  income = db.Column(db.Float)
  residence = db.Column(db.String(10))
  region = db.Column(db.String(20))
  category = db.Column(db.String(2))
  kids = db.Column(db.String(100))
  activity_opened = db.Column(db.String(10))
  expenses = db.Column(db.Float)
  status = db.Column(db.String(10))
  result_json = db.Column(db.Text)  # Store result as JSON string

  def set_password(self, password):
    self.password_hash = generate_password_hash(password)

  def check_password(self, password):
    return check_password_hash(self.password_hash, password)

@login_manager.user_loader
def load_user(user_id):
  return User.query.get(int(user_id))

# Registration route
@app.route('/register', methods=['GET', 'POST'])
def register():
  if request.method == 'POST':
    email = request.form['email'].lower()
    password = request.form['password']
    if User.query.filter_by(email=email).first():
      flash('Email already registered.', 'danger')
      return redirect(url_for('register'))
    user = User(email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    flash('Registration successful. Please log in.', 'success')
    return redirect(url_for('login'))
  return render_template('register.html')

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
  if request.method == 'POST':
    email = request.form['email'].lower()
    password = request.form['password']
    user = User.query.filter_by(email=email).first()
    if user and user.check_password(password):
      login_user(user)
      return redirect(url_for('profile'))
    flash('Invalid email or password.', 'danger')
  return render_template('login.html')

# Logout route
@app.route('/logout')
@login_required
def logout():
  logout_user()
  flash('Logged out.', 'info')
  return redirect(url_for('login'))

# Profile page for dimensions
@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
  if request.method == 'POST':
    current_user.residence = request.form.get('residence', 'r')
    # Only save region if relevant
    if current_user.residence in ['r', 'nhr']:
      current_user.region = request.form.get('region', 'Mainland')
    else:
      current_user.region = 'Mainland'
    current_user.category = request.form.get('category', 'A')
    current_user.kids = request.form.get('kids', '')
    current_user.activity_opened = request.form.get('activity_opened', '') if current_user.category == 'B' else ''
    db.session.commit()
    flash('Profile updated. You can now calculate your taxes!', 'success')
    return redirect(url_for('index'))
  return render_template('profile.html')


# Calculation page (measures)
@app.route('/', methods=['GET', 'POST'])
@login_required
def index():
  from model import Income
  result = None
  error = None
  # Use profile defaults
  profile = current_user
  # Load previous calculation if requested
  load_id = request.args.get('load')
  if load_id:
    calc = Calculation.query.filter_by(id=load_id, user_id=current_user.id).first()
    if calc:
      # Use calculation's dimensions
      year = calc.year
      income = calc.income
      expenses = calc.expenses
      status = calc.status
      residence = calc.residence
      region = calc.region
      category = calc.category
      kids = calc.kids
      opened_at = calc.activity_opened if category == 'B' else None
      try:
        kwargs = {
          'year': year,
          'income': income,
          'residence': residence,
          'region': region,
          'opened_at': opened_at,
          'expenses': expenses,
          'status': status,
          'kids': kids,
        }
        inc = Income(**kwargs)
        i = inc.income
        it = inc.income_tax
        sst = inc.social_security_tax
        st = inc.solidarity_tax
        # Remove 'Portuguese' from __repr__ output
        desc = str(inc).replace('Portuguese ', '')
        result = {
          'desc': desc,
          'wages': i,
          'income_tax': it,
          'social_security': sst,
          'solidarity_tax': st,
          'total_tax': it + sst + st,
          'effective_rate': (it + sst + st)/i if i else 0,
          'monthly_net': (i - (it + sst + st))/12,
          'status': status,
          'kids': kids,
          'opened_at': opened_at,
          'expenses': expenses
        }
        # Alternative scenarios (reuse logic from POST)
        alternatives = []
        if residence != 'nhr':
          alt_kwargs = kwargs.copy()
          alt_kwargs['residence'] = 'nhr'
          alt_kwargs['region'] = 'Mainland'
          try:
            alt_inc = Income(**alt_kwargs)
            alt_total = alt_inc.income_tax + alt_inc.social_security_tax + alt_inc.solidarity_tax
            gain = (it + sst + st) - alt_total
            alternatives.append({
              'desc': 'Non-Habitual Resident',
              'total_tax': alt_total,
              'monthly_net': (i - alt_total)/12,
              'gain': gain
            })
          except Exception:
            pass
        alt_kwargs = kwargs.copy()
        alt_kwargs['status'] = 'joint' if status == 'single' else 'single'
        try:
          alt_inc = Income(**alt_kwargs)
          alt_total = alt_inc.income_tax + alt_inc.social_security_tax + alt_inc.solidarity_tax
          gain = (it + sst + st) - alt_total
          alternatives.append({
            'desc': f"{'Joint' if status == 'single' else 'Single'} Declaration",
            'total_tax': alt_total,
            'monthly_net': (i - alt_total)/12,
            'gain': gain
          })
        except Exception:
          pass
        if kids:
          alt_kwargs = kwargs.copy()
          alt_kwargs['kids'] = ''
          try:
            alt_inc = Income(**alt_kwargs)
            alt_total = alt_inc.income_tax + alt_inc.social_security_tax + alt_inc.solidarity_tax
            gain = (it + sst + st) - alt_total
            alternatives.append({
              'desc': 'No Kids',
              'total_tax': alt_total,
              'monthly_net': (i - alt_total)/12,
              'gain': gain
            })
          except Exception:
            pass
        result['alternatives'] = alternatives
      except Exception as e:
        error = str(e)
      recent_calcs = Calculation.query.filter_by(user_id=current_user.id).order_by(Calculation.timestamp.desc()).limit(5).all()
      current_year = datetime.datetime.now().year
      return render_template('index.html', result=result, error=error, profile=profile, recent_calcs=recent_calcs, current_year=current_year)

  if request.method == 'POST':
    try:
      year = int(request.form.get('year', 2023))
      income_str = request.form['income'].replace(',', '')
      income = float(income_str)
      # Use profile dimensions
      residence = profile.residence
      region = profile.region
      category = profile.category
      kids = profile.kids or None
      opened_at = profile.activity_opened if category == 'B' else None
      expenses_str = request.form.get('expenses', '0').replace(',', '') if category == 'B' else '0'
      expenses = float(expenses_str) if category == 'B' else 0
      status = request.form.get('status', 'single')

      kwargs = {
        'year': year,
        'income': income,
        'residence': residence,
        'region': region,
        'opened_at': opened_at,
        'expenses': expenses,
        'status': status,
        'kids': kids,
      }
      inc = Income(**kwargs)
      i = inc.income
      it = inc.income_tax
      sst = inc.social_security_tax
      st = inc.solidarity_tax
      # Use __repr__ output for desc, remove 'Portuguese'
      desc = str(inc).replace('Portuguese ', '')
      result = {
        'desc': desc,
        'wages': i,
        'income_tax': it,
        'social_security': sst,
        'solidarity_tax': st,
        'total_tax': it + sst + st,
        'effective_rate': (it + sst + st)/i if i else 0,
        'monthly_net': (i - (it + sst + st))/12,
        'status': status,
        'kids': kids,
        'opened_at': opened_at,
        'expenses': expenses
      }
      # Save calculation
      import json
      calc = Calculation(
        user_id=current_user.id,
        year=year,
        income=income,
        residence=residence,
        region=region,
        category=category,
        kids=kids,
        activity_opened=opened_at,
        expenses=expenses,
        status=status,
        result_json=json.dumps(result)
      )
      db.session.add(calc)
      db.session.commit()

      # Alternative scenarios
      alternatives = []
      # Try NHR if not already
      if residence != 'nhr':
        alt_kwargs = kwargs.copy()
        alt_kwargs['residence'] = 'nhr'
        alt_kwargs['region'] = 'Mainland'
        try:
          alt_inc = Income(**alt_kwargs)
          alt_total = alt_inc.income_tax + alt_inc.social_security_tax + alt_inc.solidarity_tax
          gain = (it + sst + st) - alt_total
          alternatives.append({
            'desc': 'Non-Habitual Resident',
            'total_tax': alt_total,
            'monthly_net': (i - alt_total)/12,
            'gain': gain
          })
        except Exception:
          pass
      # Try joint/single
      alt_kwargs = kwargs.copy()
      alt_kwargs['status'] = 'joint' if status == 'single' else 'single'
      try:
        alt_inc = Income(**alt_kwargs)
        alt_total = alt_inc.income_tax + alt_inc.social_security_tax + alt_inc.solidarity_tax
        gain = (it + sst + st) - alt_total
        alternatives.append({
          'desc': f"{'Joint' if status == 'single' else 'Single'} Declaration",
          'total_tax': alt_total,
          'monthly_net': (i - alt_total)/12,
          'gain': gain
        })
      except Exception:
        pass
      # Try with/without kids
      if kids:
        alt_kwargs = kwargs.copy()
        alt_kwargs['kids'] = ''
        try:
          alt_inc = Income(**alt_kwargs)
          alt_total = alt_inc.income_tax + alt_inc.social_security_tax + alt_inc.solidarity_tax
          gain = (it + sst + st) - alt_total
          alternatives.append({
            'desc': 'No Kids',
            'total_tax': alt_total,
            'monthly_net': (i - alt_total)/12,
            'gain': gain
          })
        except Exception:
          pass
      result['alternatives'] = alternatives
    except Exception as e:
      error = str(e)
  # Show recent calculations
  recent_calcs = Calculation.query.filter_by(user_id=current_user.id).order_by(Calculation.timestamp.desc()).limit(5).all()
  current_year = datetime.datetime.now().year
  return render_template('index.html', result=result, error=error, profile=profile, recent_calcs=recent_calcs, current_year=current_year)

if __name__ == '__main__':
  app.run(debug=True, host='0.0.0.0')
