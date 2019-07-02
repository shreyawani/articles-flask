from flask import Flask, render_template,flash, redirect, url_for, session, request, logging
#from data import Articles
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps
app = Flask(__name__)

#Config MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'root'
app.config['MYSQL_DB'] = 'myflaskapp'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
#init MySQL

mysql = MySQL(app)

#Articles = Articles()

@app.route("/")
def home():
    return render_template('home.html')

@app.route("/about")
def about():
    return render_template('about.html')

@app.route("/articles")
def articles():

    cur = mysql.connection.cursor()

    #Get articles
    result = cur.execute("SELECT * from articles")

    articles = cur.fetchall()
    if result > 0:
        return render_template('articles.html', articles=articles)
    else:
        msg = 'No articles found'
        return render_template('articles.html', msg=msg)
    #close connection
    cur.close()

    

@app.route("/article/<string:id>/")
def article(id):
    cur = mysql.connection.cursor()

    #Get articles
    result = cur.execute("SELECT * from articles where id = %s",[id])

    

    article = cur.fetchone()


    return render_template('article.html', article=article)

class RegisterForm(Form):
    name = StringField('Name',[validators.Length(min=1, max=50)])
    username = StringField('Username',[validators.Length(min=4, max=25)])
    email = StringField('Email',[validators.Length(min=6,max=50)])
    password = PasswordField('Password',[validators.DataRequired(),validators.EqualTo('confirm', message = 'Password do not match')])
    confirm = PasswordField('Confirm Password')

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))

        #create Cursor
        cur = mysql.connection.cursor()
        #Execute query 
        cur.execute("INSERT INTO user(name, email, username, password) VALUES(%s, %s, %s, %s)", (name, email, username, password))

        #COmmit TO DB

        mysql.connection.commit()

        #close connection
        cur.close()

        flash('You are now registered and can log in', 'success')

        return redirect(url_for('home'))
    return render_template('register.html',form=form)
#user login
@app.route("/login", methods=['GET','POST'])
def login():
    if request.method == 'POST':
        # GET FORM FIELDS
        username = request.form['username']
        password_candidate = request.form['password']

        # create cursor
        cur = mysql.connection.cursor()

        #get user by username
        result = cur.execute("SELECT * FROM user WHERE username = %s",[username])

        if result > 0:
            #get started with
            data = cur.fetchone()
            password = data['password']

            #compare passwords
            if sha256_crypt.verify(password_candidate, password):
                #passed
                session['logged_in'] = True
                session['username'] = username

                flash('You are now logged in', 'success')
                return redirect(url_for('dashboard'))

            else:
                error = 'Invalid login'
                return render_template('login.html', error=error)

            #close connection
            cur.close()

        else:
            error = 'USername not found'
            return render_template('login.html', error=error)
    return render_template('login.html')
#check if user logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwrags):
        if 'logged_in' in session:
            return f(*args, **kwrags)
        else:
            flash('Unauthorized,please login', 'danger')
            return redirect(url_for('login'))
    return wrap
#log out

@app.route('/logout')
def logout():
    session.clear()
    flash("You are now logged out", 'success')

    return redirect(url_for('login'))

#dashboard

@app.route('/dashboard')
@is_logged_in
def dashboard():
    #create cursor
    cur = mysql.connection.cursor()

    #Get articles
    result = cur.execute("SELECT * from articles")

    articles = cur.fetchall()
    if result > 0:
        return render_template('dashboard.html', articles=articles)
    else:
        msg = 'No articles found'
        return render_template('dashboard.html', msg=msg)
    #close connection
    cur.close()

#article form class
   

class ArticleForm(Form):
    title = StringField('Title',[validators.Length(min=1, max=200)])
    body = TextAreaField('Body',[validators.Length(min=30)])

@app.route('/add_article', methods=['GET','POST'])
@is_logged_in
def add_article():
    form = ArticleForm(request.form)
    if request.method == 'POST' and form.validate():
        title = form.title.data
        body = form.body.data

    #create cursor
        cur = mysql.connection.cursor()

        #execute
        cur.execute("INSERT INTO articles(title,body,author) VALUES(%s, %s, %s)", (title,body,session['username']))

        #commit
        mysql.connection.commit()

        #close connection
        cur.close()

        flash('Article Created','success')

        return redirect(url_for('dashboard'))
    return render_template('add_article.html', form=form)

@app.route('/edit_article/<string:id>', methods=['GET','POST'])
@is_logged_in
def edit_article(id):
    #create cursor
    cur = mysql.connection.cursor()

    #Get article by id
    result = cur.execute("select * from articles where id = %s",[id])

    article = cur.fetchone()

    #get form
    form = ArticleForm(request.form)

    # populate article form fields
    form.title.data = article['title']
    form.body.data = article['body']

    if request.method == 'POST' and form.validate():
        title = request.form['title']
        body = request.form['body']

    #create cursor
        cur = mysql.connection.cursor()

        #execute
        cur.execute("update articles set title=%s, body=%s where id = %s", (title,body,id))

        #commit
        mysql.connection.commit()

        #close connection
        cur.close()

        flash('Article Updated','success')

        return redirect(url_for('dashboard'))
    return render_template('edit_article.html', form=form)

#delete article
@app.route('/delete_article/<string:id>', methods=["POST"])
@is_logged_in
def delete_article(id):
    #create cursor
    cur = mysql.connection.cursor()

    #Execute
    cur.execute("delete from articles where id = %s", [id])

    mysql.connection.commit()

        #close connection
    cur.close()

    flash('Article Deleted','success')
    return redirect(url_for('dashboard'))

if __name__ == "__main__":
    app.secret_key='secret123'
    app.run(debug=True) 