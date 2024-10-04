from flask import Flask, render_template, url_for, request, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin,LoginManager,login_user,logout_user,login_required,current_user
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SECRET_KEY'] = 'your_secret_key_here' 
db = SQLAlchemy(app)

login_manager=LoginManager()
login_manager.login_view='login'
login_manager.init_app(app)

class User(db.Model,UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    workouts=db.relationship('Workout',backref='author',lazy=True)

    def __repr__(self):
        return f'<User {self.username}>'

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)
    
class Workout(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    pushups=db.Column(db.Integer,nullable=False)
    date_posted=db.Column(db.DateTime,nullable=False,default=datetime.utcnow)
    comment=db.Column(db.Text,nullable=False)
    user_id=db.Column(db.Integer,db.ForeignKey('user.id'),nullable=False)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html',name=current_user.username)

@app.route('/new_workout',methods=['GET','POST'])
@login_required
def new_workout():
    if request.method=='POST':
        pushups=request.form.get('pushups')
        comment=request.form.get('comment')
        workout=Workout(pushups=pushups,comment=comment,author=current_user)
        db.session.add(workout)
        db.session.commit()
        flash('Your workout has been added')
        return redirect(url_for('user_workouts'))
    return render_template('create_workout.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists. Please choose a different one.')
            return redirect(url_for('signup'))
        if password != confirm_password:
            flash('Passwords do not match')
            return redirect(url_for('signup'))
        
        new_user = User(username=username, email=email)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        
        flash('Account created successfully')
        return redirect(url_for('login'))
    
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember=True if request.form.get('remember') else False
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user, remember=remember)
            return redirect(url_for('profile'))
        else:
            flash('Invalid email or password')
            return redirect(url_for('login'))
    
    return render_template('login.html')

@app.route('/reset_passward', methods=['GET', 'POST'])
def reset_passward():
    if request.method == 'POST':
        email = request.form.get('email')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        user = User.query.filter_by(email=email).first()
        if not user:
            flash('Email not found')
            return redirect(url_for('reset_passward'))

        if new_password != confirm_password:
            flash('Passwords do not match')
            return redirect(url_for('reset_passward'))

        user.set_password(new_password)
        db.session.commit()
        flash('Password reset successfully')
        return redirect(url_for('login'))

    return render_template('reset.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/user_account')
@login_required
def user_workouts():
    user=User.query.filter_by(email=current_user.email).first_or_404()
    workouts=user.workouts
    return render_template('user_account.html',workouts=workouts,user=user)

@app.route('/workout/<int:workout_id>/update',methods=['GET','POST'])
@login_required
def update_workout(workout_id):
    workout=Workout.query.get_or_404(workout_id)
    if request.method=='POST':
        workout.pushups=request.form.get('pushups')
        workout.comment=request.form.get('comment')
        db.session.commit()
        flash('workout has been updated successfully!!')
        return redirect(url_for('user_workouts'))


    return render_template('update_workout.html',workout=workout)

@app.route('/workout/<int:workout_id>/delete',methods=['GET','POST'])
@login_required
def delete_workout(workout_id):
    workout=Workout.query.get_or_404(workout_id)
    db.session.delete(workout)
    db.session.commit()
    flash('Workout has been deleted successfully!!')
    return redirect(url_for('user_workouts'))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)