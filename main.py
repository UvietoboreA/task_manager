import os
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import flask
from flask import Flask, render_template, redirect, url_for
from flask_wtf import FlaskForm
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditorField
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import DateTime
from sqlalchemy.orm import relationship
from wtforms import SubmitField, StringField, PasswordField, EmailField
from wtforms.validators import DataRequired
from flask_login import LoginManager, login_user, logout_user, current_user, login_required, UserMixin


load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('secret_key')
Bootstrap(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///task.db'
db = SQLAlchemy(app)

app.config['SQL_TRACK_MODIFICATIONS'] = False


login_manager = LoginManager()
login_manager.init_app(app)


class User(UserMixin, db.Model):
    __tablename__ = 'user_table'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(100), nullable=True)

    tasks = relationship("Tasks", back_populates="user")


class Tasks(db.Model):
    __tablename__ = 'task_details'
    id = db.Column(db.Integer, primary_key=True)
    task_title = db.Column(db.String(100), nullable=False)
    list_to_do = db.Column(db.String(100), nullable=False)
    time = db.Column(DateTime, default=datetime.now)

    user_name = db.Column(db.String(100), db.ForeignKey('user_table.name'))

    user = relationship("User", back_populates="tasks")


class SignUp(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    email = EmailField('Email Address', validators=[DataRequired()])
    code = PasswordField('Secret Access Code', validators=[DataRequired()])
    submit = SubmitField('Sign Up')


class Login(FlaskForm):
    email = StringField('Email Address', validators=[DataRequired()])
    code = PasswordField('Your Secret Access Code', validators=[DataRequired()])
    submit = SubmitField('Log In')

class T_Manager(FlaskForm):
    task_title = StringField('Title of Task', validators=[DataRequired()])
    list_to_do = CKEditorField('How to achieve the task', validators=[DataRequired()])
    submit = SubmitField('DONE')

with app.app_context():
    db.create_all()


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


@app.route("/")
def home():
    return render_template('first.html')


@app.route("/signup", methods=['GET', 'POST'])
def signup():
    form1 = SignUp()

    if form1.validate_on_submit():

        two_email = User.query.filter_by(email=form1.email.data).first()
        hashed_code = generate_password_hash(password=form1.code.data, salt_length=16, method= 'pbkdf2:sha256')

        if two_email:
            flask.flash('You have already signed up with this email, log in instead')
            return redirect(url_for('login'))
        
        
        new_user = User(
                name=form1.name.data,
                email=form1.email.data,
                code=hashed_code
            )

        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for('addtask', name=current_user.name))

    return render_template('signup.html', form1=form1)


@app.route("/login", methods=['GET', 'POST'])
def login():

    form2 = Login()

    if form2.validate_on_submit():
        check_email = User.query.filter_by(email=form2.email.data).first()
        
        if check_email is None:
            flask.flash('Email not found, sign up instead')
            return redirect(url_for('signup'))
        
        elif not check_password_hash(check_email.code, form2.code.data):
            flask.flash('Incorrect password')
            return redirect(url_for('login'))
        
        else:
            login_user(check_email)
            return redirect(url_for('addtask', name=check_email.name))
        
    return render_template("login.html", form2=form2)


@login_required
@app.route("/tasks/<name>", methods=['GET', 'POST'])
def tasks(name):

    user_tasks = Tasks.query.filter_by(user_name=name).all()
    return render_template('index.html', tasks=user_tasks, name=current_user.name)


@login_required
@app.route("/add", methods=['GET', 'POST'])
def addtask():

    form3 = T_Manager()

    if form3.validate_on_submit():
        new_task = Tasks(
            task_title=form3.task_title.data,
            list_to_do=form3.list_to_do.data,
            time=datetime.now(),
            user_name=current_user.name
        )
        db.session.add(new_task)
        db.session.commit()
        return redirect(url_for('tasks', name=current_user.name))
    
    return render_template('add.html', form3=form3)


@login_required
@app.route("/update/<name>/<int:task_id>", methods=['GET', 'POST'])
def updatetask(name, task_id):

    form3 = T_Manager()
    
    to_edit = db.session.get(Tasks, task_id)

    form3.task_title.data = to_edit.task_title

    if form3.validate_on_submit():
        to_edit.task_title = form3.task_title.data
        to_edit.list_to_do = form3.list_to_do.data
        db.session.commit()
        return redirect(url_for('tasks', name=name))
    
    return render_template('update.html', form3=form3, task=to_edit)


@login_required
@app.route("/delete/<name>/<int:task_id>", methods=['GET', 'POST'])
def deletetask(name, task_id):

    to_delete = db.session.get(Tasks, task_id)

    if to_delete.user_name == name:
        db.session.delete(to_delete)
        db.session.commit()
        return redirect(url_for('tasks', name=current_user.name))
    
    return redirect(url_for('tasks', name=current_user.name))


@login_required
@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))



if __name__ == '__main__':
    app.run(debug=True)
