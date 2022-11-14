from flask import Flask, request, render_template, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
import hashlib
import secret
import os
app = Flask(__name__)
database_file_name = "database.db"

# this is purely for ease of use, and in a real application would most likely be deleted
if os.path.exists(database_file_name):
    os.remove(database_file_name)


# I am defining the hashing function here, so if I want to change it, I don't have to do so in multiple places
def hashing_function(string):
    encoded_string = bytes(string, encoding="utf-8")
    sha256_hash = hashlib.sha256(encoded_string)
    hexdigest = sha256_hash.hexdigest()
    return hexdigest

digest_size = 256

# setup the secret key
app.config["SECRET_KEY"] = secret.secret_key
app.config['SQLALCHEMY_DATABASE_URI'] =\
    'sqlite:///' + os.path.join(
    os.path.abspath(os.path.dirname(__file__)),
    database_file_name)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), nullable=False)
    password_hash = db.Column(db.String(digest_size))


    def __init__(self, username, password_hash):
        self.username = username
        self.password_hash = password_hash
        
    def __repr__(self):
        return f"User('{self.username}', '{self.password_hash}')"

# each user can write notes. These notes have a title and a body. They also have a user_id which is a foreign key to the user table
class Note(db.Model):
    __tablename__ = 'notes'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    body = db.Column(db.String(120), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    def __init__(self, title, body, user_id):
        self.title = title
        self.body = body
        self.user_id = user_id
        
    def __repr__(self):
        return f"Note('{self.title}', '{self.body}', '{self.user_id}')"

# create the tables in the database
with app.app_context():
    db.create_all()
    db.session.commit()

@app.route('/')
@app.route('/index')
def index():
    # if the user is not logged in, redirect them to the login page
    if 'user_id' not in session:
        return redirect(url_for('login'))
    # also redirect them if the user is still logged in but they are not in the database (although this would probably only happen during development)
    if ((user := User.query.filter_by(id=session['user_id']).first()) == None):
        return redirect(url_for('login'))
    # get all the notes for the user
    notes = Note.query.filter_by(user_id=session['user_id']).all()
    return render_template('index.html', user=user, notes=notes)

@app.route('/login')
def login():
    return render_template('login.html')

@app.route("/logging_in", methods=["POST"])
def logging_in():
    # get the username and password from the request
    username = request.form.get('username')
    password = request.form.get('password')
    password_hash = hashing_function(password)
    # get the user with the given username and password
    user = User.query.filter_by(username=username, password_hash=password_hash).first()
    # if the user is not found, redirect them to the login page
    if user is None:
        flash("that user is not in the database")
        return redirect(url_for('login'))
    # if the user is found, add the user_id to the session
    session['user_id'] = user.id
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    # remove the user_id from the session
    session.pop('user_id', None)
    return redirect(url_for('login'))

@app.route('/signup', methods=['POST'])
def signup():
    # get the username and password from the request
    try:
        username = request.form['username']
        password = request.form['password']
    except Exception:
        return redirect(url_for("login"))
    password_hash = hashing_function(password)
    # create a new user with the given username and password hash
    user = User(username, password_hash)
    # add the user to the database
    db.session.add(user)
    db.session.commit()
    # add the user_id to the session
    session['user_id'] = user.id
    return redirect(url_for('index'))

@app.route("/create_note", methods=["POST"])
def create_note():
    # create a note it should be associated with the user through the session['user_id']
    note = Note(request.form['title'], request.form['body'], session['user_id'])
    db.session.add(note)
    db.session.commit()
    return redirect(url_for('index'))

@app.route("/note/<note_id>")
def display_note(note_id):
    # lookup the note in the database by the id
    note = Note.query.filter_by(id=note_id).first()
    # render the note template
    return render_template('note.html', note=note)

@app.route("/delete_note/<note_id>")
def delete_note(note_id):
    # lookup the note in the database by the id
    note = Note.query.filter_by(id=note_id).first()
    # delete the note
    db.session.delete(note)
    db.session.commit()
    return redirect(url_for('index'))

@app.route("/change_username", methods=["POST"])
def change_username():
    # get the user_id from the session
    user_id = session['user_id']
    # get the new username and password from the request
    username = request.form['username']
    # update the user in the database
    user = User.query.filter_by(id=user_id).first()
    user.username = username if username else user.username # Doesn't make the change if it is blank or None
    db.session.commit()
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)