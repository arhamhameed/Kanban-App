# importing all the required libraries 
# os helps to handle the files paths
import os
from flask import Flask, render_template, url_for, redirect, request, g, session, flash
# crete the login page 
from flask_login import LoginManager, UserMixin, current_user,login_required, login_user
# importing SQL Alchemy for creating the database 
from flask_sqlalchemy import SQLAlchemy

#initial configurations
app = Flask(__name__)
#sets up the path of teh main directory
path = os.path.abspath(os.getcwd()) + '\\kanban.db'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + path
app.config['SECRET_KEY'] = 'noidea12345'

db = SQLAlchemy(app)

login = LoginManager()
login.init_app(app)
login.login_view = 'login'


# creating the database
class Task(db.Model):
    __tablename__ = 'Task'
    id = db.Column(db.Integer, primary_key = True)
    task = db.Column(db.String(120), unique=True, nullable=False)
    status = db.Column(db.String(10), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('User.id'))


# creating database to store users
class User(UserMixin, db.Model): 
    __tablename__ = 'User'
    id = db.Column(db.Integer, primary_key=True)
    uname = db.Column(db.String(20))
    password = db.Column(db.String(100))
    task_id = db.relationship('Task', backref='user', lazy='dynamic')

# creating the initial database
db.create_all()
db.session.commit()


# function redirects to the login page if the user is not logged in
# otherwise it will take the user directly to its Kanban Board
@app.route('/', methods= ['GET'])
@login_required
def home():
    g.user = current_user
    todolst = []
    doinglst = []
    donelst = []
    tasklst = Task.query.filter_by(user_id = g.user.id).all()
    for item in tasklst:
        if item.status == 'todo':
            todolst.append(item)
        elif item.status == 'doing':
            doinglst.append(item)
        elif item.status == 'done':
            donelst.append(item)
    return render_template('main.html', todolst = todolst, doinglst = doinglst, donelst = donelst)


# this function add the tasks to the board
@app.route('/add', methods = ['POST'])
def add():
    g.user = current_user
    todo = Task(task= request.form['tasktodo'], status = 'todo')
    todo.user = g.user
    db.session.add(todo)
    db.session.commit()
    return redirect(url_for('home'))

# this function changes teh status of teh task as well as takes it from the todo column to the Inprocess column
@app.route('/doing', methods = ['POST'])
def doing():
    imd = request.form
    form = imd.to_dict()
    task_id = next(iter(form))
    task = Task.query.filter_by(id=int(task_id)).first()
    task.status = 'doing'
    db.session.commit()
    return redirect(url_for('home'))

# this function changes the task status from doing to done and moves it to the next column 
@app.route('/done', methods = ['POST'])
def done():
    imd = request.form
    form = imd.to_dict()
    task_id = next(iter(form))
    task = Task.query.filter_by(id=int(task_id)).first()
    task.status = 'done'
    db.session.commit()
    return redirect(url_for('home'))

# this function deletes the task 
@app.route('/delete', methods = ['POST'])
def delete():
    imd = request.form
    form = imd.to_dict()
    task_id = next(iter(form))
    task = Task.query.filter_by(id=int(task_id)).first()
    db.session.delete(task)
    db.session.commit()
    return redirect(url_for('home'))

# this function helps loads the user based on its ID
@login.user_loader
def load_user(id):
    return User.query.get(int(id))

# this function allows users to login and validates their credentials
# Also it outputs appropriate error messages based on the user error
@app.route('/login', methods= ['GET','POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(uname = request.form['uname'], password = request.form['psw']).first()
        if user is None:
            error = 'The Username or Password entered is not correct'
            return render_template('login_page.html', error=error)
        login_user(user)
        return redirect(url_for('home'))
    elif request.method == 'GET':
        return render_template('login_page.html')

# this function creates a new user account
# it outputs error messages based on user errors
# redirects the user to login page once registered
@app.route('/register', methods= ['GET','POST'])
def register():
    if request.method == 'POST':
        user = User.query.filter_by(uname=request.form['uname']).first()
        if user is not None:
            error = 'This User Name already Exists'
            return render_template('register_page.html', error=error)
        if len(request.form['psw']) < 8:
            error = 'Password must be 9 characters or more'
            return render_template('register_page.html', error=error)
        if request.form['psw'] != request.form['repsw']:
            error = 'Passwords do not match'
            return render_template('register_page.html', error=error)
        
        new_user = User(uname=request.form['uname'], password=request.form['psw'])
        db.session.add(new_user)
        db.session.commit()
        flash('User successfully registered')
        return redirect(url_for('login'))
    elif request.method == 'GET':
        return render_template('register_page.html')

# this function log user out 
@app.route('/logout', methods= ['GET','POST'])
def logout():
    session.pop('logged_in', None)
    return redirect('login')

# For running the application on localhost
if __name__ == '__main__':
    app.run(debug=True)
