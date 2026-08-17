from flask             import Flask, session, render_template, request, redirect, url_for, flash
from flask_sqlalchemy  import SQLAlchemy
from datetime          import datetime
from flask_login       import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from login             import db, User

#global contents########################################
app = Flask(__name__)    #creat Flask application.   app is our container object
print('app name -', app);print() #app name - <Flask 'flasktutorial'>

app.config['SECRET_KEY'] = 'my_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///to_do_list.db"
db.init_app(app) #pass in URI of the database

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)
@login_manager.user_loader
def load_user(user_id):   #get user info for this session
    return User.query.filter_by(id=int(user_id)).first()


###SQLAlchemy###########################################
class DB_tasks(db.Model):
    id          = db.Column(db.Integer, primary_key=True)
    content     = db.Column(db.String(100), nullable=False)
    completed   = db.Column(db.Integer, default=0)
    do_on       = db.Column(db.String(50))
    created     = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)


###@app.route index()###########################################
@app.route('/', methods=["POST", "GET"]) #in order to create a route to our home page we need to use a Flask decorator.  This points to our index.html page
@login_required
def index(): #create a route to the index.html page #route will recieve both FORM POST an GET's

    print('inside index()');print()
    #add a task
    if request.method == "POST":
        print('inside index POST')
        print(); print('request.method == POST'); print()

        #contains the content (id or name attribute??) of the input box in the HTML form
        current_task = request.form.get('content')

        print(); print(current_task); print()
        new_task = DB_tasks(content=current_task, user_id=current_user.id)
        try:
            db.session.add(new_task)
            db.session.commit()
            #refresh the homepage after the record is committed.
            return redirect("/")
        except Exception as e:
            print(f"ERROR - {e}")
            return f"ERROR - {e}"
    #see all tasks
    else:
        current_id = int(current_user.id)
        #if not adding a tasks then query the database result set of current tasks
        #this will occur when the page first opens has no requests have been raised
        tasks = DB_tasks.query.filter_by(user_id=current_id).order_by(DB_tasks.created).all()

        print(f"DEBUG: Logged in as User ID {current_id}. Found {len(tasks)} tasks.")
        print('leaving index()');print()
        return render_template('index.html', tasks=tasks) #because the @app.route opens this page the return can be a string which would output to a browser


###@app.route delete()###########################################
@login_required
@app.route('/delete/<id>')
def delete(id):

    delete_task = DB_tasks.query.get_or_404(id)
    if delete_task.user_id != current_user.id:
        flash("You do not have permission to delete this task.")
        return redirect("/login")
    try:
        db.session.delete(delete_task)
        db.session.commit()
        return redirect("/")
    except Exception as e:
        print(f"ERROR - {e}")
        return f"ERROR - {e}"


###@app.route update()###########################################
@login_required
@app.route('/update/<id>', methods=["POST", "GET"])
def update(id):
    print('inside update')

    update_task = DB_tasks.query.get_or_404(id)
    if request.method == "POST":

        print(); print('update() POST found'); print()

        update_task.content  = request.form.get('content')
        if update_task.user_id != current_user.id:
            flash("You do not have permission to update this task.")
            return redirect("/login")

        try:
            db.session.update(update_task)
            db.session.commit()
            return redirect("/")
        except Exception as e:
            print(f"ERROR - {e}")
            return f"ERROR - {e}"
    else:
        print(); print('render update page'); print()
        return render_template('update.html', tasks=update_task)


@app.route('/register', methods = ['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user_exists = User.query.filter_by(username=username).first()
        if user_exists:
            flash('Username already exists')
            return redirect(url_for('register'))

        hashed_pw = generate_password_hash(password)
        new_user = User(username=username, password_hash=hashed_pw)

        db.session.add(new_user)
        db.session.commit()

        flash('Account created!, Please login.')
        return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/login', methods = ['GET', 'POST'])
def login():
    print('inside login route from ToDoApp.py');print()

    if request.method == 'POST':
        print('inside POST route from ToDoApp.py');print()

        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password')

    print('Past POST route from ToDoApp.py - render login.html');print()
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():

    logout_user()
    flash("You've been logged out.")
    return redirect(url_for('login'))


##EXECUTION SECTION################################################
if __name__ in "__main__":

    with app.app_context():
        db.create_all()
    print('app_run() - execute the script');print()
    app.run(debug=True)
    print("past app.run()");print()

