from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import func


app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite:///blog.db'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = '5a60845ca52c8ee42a2bb2d0'

db = SQLAlchemy(app)
db.init_app(app)
login_manager = LoginManager(app)


class User(db.Model, UserMixin):
    id = db.Column(db.Integer(), primary_key=True)
    first_name = db.Column(db.String(255), nullable=False)
    last_name = db.Column(db.String(255), nullable=False)
    username = db.Column(db.String(255), nullable=False, unique=True)
    email = db.Column(db.String(255), nullable=False, unique=True)
    password = db.Column(db.Text(), nullable=False)
    date_created = db.Column(db.DateTime(timezone=True), default=func.now())
    articles = db.relationship('Article', backref='user', passive_deletes=True)

    def __repr__(self):
        return f'User: <{self.username}>'


class Article(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    text = db.Column(db.Text(), nullable=False)
    date_created = db.Column(db.DateTime(timezone=True), default=func.now())
    author = db.Column(db.Integer(), db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)


class Message(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    email = db.Column(db.String(80), nullable=False)
    subject = db.Column(db.String(80), nullable=False)
    message = db.Column(db.Text(), nullable=False)

    def __repr__(self):
        return f"Message: <{self.subject}>"


@login_manager.user_loader
def user_loader(id):
    return User.query.get(int(id))


@app.route("/")
@app.route("/articles")
def home():
    articles = Article.query.all()
    return render_template("home.html", user=current_user, articles=articles)


@app.route("/create-posts", methods=['GET', 'POST'])
@login_required
def create_post():
    if request.method == 'POST':
        text = request.form.get('text')
        if not text:
            flash('field can not be empty', category='error')
        else:
            article = Article(text=text, author=current_user.id)
            db.session.add(article)
            db.session.commit()
            flash('Article created successfully', category='success')
            return redirect(url_for('home'))
    return render_template('create_posts.html', user=current_user)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password1")
        user = User.query.filter_by(email=email).first()
        if user:
            if check_password_hash(user.password, password):
                flash("Logged in!", category='success')
                login_user(user, remember=True)
                return redirect(url_for('home'))
            else:
                flash('Password is incorrect.', category='error')
        else:
            flash('Email does not exist.', category='error')
    return render_template("login.html", user=current_user)


@app.route("/sign-up", methods=["GET", "POST"])
def sign_up():
    if request.method == "POST":
        username = request.form.get("username")
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email = request.form.get("email")
        password1 = request.form.get("password1")
        password2 = request.form.get("passsword2")

        user = User.query.filter_by(username=username).first()
        if user:
            flash("This username already exists.")
            return redirect(url_for('sign_up'))

        email_exists = User.query.filter_by(email=email).first()
        if email_exists:
            flash("This email is already registered.")
            return redirect(url_for('sign_up'))

        password = generate_password_hash(password1)
        new_user = User(username=username, first_name=first_name, last_name=last_name, email=email, password=password)
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user, remember=True)
        flash('User created')
        return redirect(url_for('home'))

    return render_template('signup.html', user=current_user)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route("/delete-post/<id>", methods=['GET'])
@login_required
def delete_post(id):
    article = Article.query.filter_by(id=id).first()

    if not article:
        flash("Post does not exist.", category='error')
    elif current_user.id != article.author:
        flash('You do not have permission to delete this post.', category='error')
    else:
        db.session.delete(article)
        db.session.commit()
        flash('Article deleted.', category='success')

    return redirect(url_for('home'))


@app.route("/posts/<username>")
@login_required
def posts(username):
    user = User.query.filter_by(username=username).first()

    if not user:
        flash('No user with that username exists.', category='error')
        return redirect(url_for('home'))

    articles = Article.query.filter_by(author=user.id).all()
    return render_template("posts.html", user=current_user, articles=articles, username=username)


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        email = request.form.get('email')
        subject = request.form.get('subject')
        message = request.form.get('message')

        new_message = Message(email=email, subject=subject, message=message)
        db.session.add(new_message)
        db.session.commit()

        flash("Message sent.")
        return redirect(url_for('home'))
    return render_template('contact.html')


@app.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    article_edit = Article.query.get_or_404(id)
    if request.method == 'POST':
        article_edit.text = request.form.get('text')
        db.session.commit()
        flash("Your changes have been saved.")
        return redirect(url_for('home'))
    return render_template('edit.html', article=article_edit)


if __name__ == '__main__':
    app.run(debug=True)
