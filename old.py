from flask import Flask, request, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import random
import secret
app = Flask(__name__)

# setup the connection to the postgres database
# the connection string is stored in the secret.py file


app.config['SQLALCHEMY_DATABASE_URI'] = secret.postgress_connection_string
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False)
    password = db.Column(db.String(120), nullable=False)
    token = db.Column(db.String(120), nullable=False)

    def __init__(self, email, password, token):
        self.email = email
        self.password = password
        self.token = token
        
    def __repr__(self):
        return f"User('{self.email}', '{self.password}', '{self.token}')"

with app.app_context():
    db.create_all()
    db.session.commit()



# render the index page
@app.route('/')
@app.route('/index')
def index():
    # get all the users from the database
    users = User.query.all()
    return render_template('index.html', users=users)

@app.route('/create_account', methods=['GET'])
def create_account():
    return render_template('create_account.html')

@app.route('/add_user', methods=['POST'])
def add_user():
    # get the data from the form
    # technically we should validate the email with regex
    email = request.form['email']
    # in a real application I would of course hash the password and generate the token more securely
    password = request.form['password']
    token = random.randint(100000, 999999)
    # create a new user object
    user = User(email, password, token)
    # add the user to the database
    db.session.add(user)
    db.session.commit()
    # then redirect to the home page
    return redirect(url_for('index'))

@app.route("/user/<int:user_id>")
def user(user_id):
    user = User.query.get(user_id)
    return render_template('user.html', user=user)


@app.route("/delete_user/<int:user_id>")
def delete_user(user_id):
    user = User.query.get(user_id)
    db.session.delete(user)
    db.session.commit()
    return redirect(url_for('index'))

@app.route("/change_details/<int:user_id>", methods=['POST'])
def change_details(user_id):
    user = User.query.get(user_id)
    if (new_email := request.form.get('email')):
        user.email = new_email
    if (new_password := request.form.get('password')):
        user.password = new_password
    db.session.commit()
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)