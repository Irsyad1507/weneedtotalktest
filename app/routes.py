from flask import render_template, flash, request, redirect, url_for
from app import app, db, login_manager
from app.models import User, Posts
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, login_required, logout_user, current_user
from app.webforms import LoginForm, PostForm, UserForm, PasswordForm, NameForm, SearchForm
from werkzeug.utils import secure_filename
import uuid as uuid
import os

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Pass Info to Navbar
@app.context_processor
def base():
    form = SearchForm()
    return dict(form=form)

# Create Admin Page
@app.route('/admin')
@login_required
def admin():
    id = current_user.id
    if id == 1:
        return render_template("admin.html")
    else:
        flash("Only real admin can access the admin page")
        return redirect(url_for('posts'))


# Create Search Function
@app.route('/search', methods=["POST"])
def search():
    form = SearchForm()
    posts = Posts.query
    if form.validate_on_submit():
        # Get Form data
        post.searched = form.searched.data
        # Query Database
        posts = posts.filter(Posts.content.like('%' + post.searched + '%'))
        posts = posts.order_by(Posts.title).all()

        return render_template("search.html", 
                               form=form, 
                               searched=post.searched, 
                               posts=posts)

# Create Login Page
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            # Check Hash
            if check_password_hash(user.password_hash, form.password.data):
                login_user(user)
                flash('Login Successful!')
                return redirect(url_for('dashboard'))
            else:
                flash('Wrong Password')
        else:
            flash("Username Doesn't Exist")


    return render_template('login.html', form=form)

# Create Logout Page
@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    flash("You've been logged out")
    return redirect(url_for('login'))

# Create Dashboard Page
@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    form = UserForm()
    id = current_user.id
    name_to_update = User.query.get_or_404(id)
    if request.method == 'POST':
        name_to_update.name = request.form.get('name')
        name_to_update.email = request.form.get('email')
        name_to_update.favourite_colour = request.form.get('favourite_colour')
        name_to_update.username = request.form.get('username')
        name_to_update.about_author = request.form.get('about_author')

        # Check for profile picture
        if request.files.get('profile_picture'):
            name_to_update.profile_picture = request.files.get('profile_picture')

        
            # Fetch image name
            picture_filename = secure_filename(name_to_update.profile_picture.filename)
            # Set UUID
            picture_name = str(uuid.uuid1()) + "_" + picture_filename
            # Save Image
            saved = request.files.get('profile_picture')
            
            
            # Save to db as string
            name_to_update.profile_picture = picture_name
            try:
                db.session.commit()
                saved.save(os.path.join(app.config['UPLOAD_FOLDER'], picture_name))
                flash('User Updated Successfully')
                return render_template('dashboard.html', 
                                    form=form, 
                                    name_to_update=name_to_update)
            except:
                flash('Error Updating User')
                return render_template('dashboard.html', 
                                    form=form, 
                                    name_to_update=name_to_update)
        else:
            db.session.commit()
            flash('User Updated Successfully')
            return render_template('dashboard.html', form=form, name_to_update=name_to_update)
    else:
        return render_template('dashboard.html', 
                                   form=form, 
                                   name_to_update=name_to_update, 
                                   id=id)
    return render_template('dashboard.html')






@app.route('/posts/delete/<int:id>')
@login_required
def delete_post(id):
    post_to_delete = Posts.query.get_or_404(id)
    id = current_user.id
    if id == post_to_delete.poster.id or id == 16:

        try:
            db.session.delete(post_to_delete)
            db.session.commit()

            # Return message
            flash('Post Deleted')
            return redirect(url_for('posts'))

        except:
            # Return error message
            flash('Failed to delete')
            return redirect(url_for('posts'))
    else:
        # Return message
        flash("You cannot delete someone else's post...")
        return redirect(url_for('posts'))

@app.route('/posts')
def posts():
    # Fetch all posts from database
    posts = Posts.query.order_by(Posts.date_posted)
    return render_template('posts.html', posts=posts)

@app.route('/posts/<int:id>')
def post(id):
    post = Posts.query.get_or_404(id)
    return render_template('post.html', post=post)

@app.route('/posts/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_post(id):
    post = Posts.query.get_or_404(id)
    form = PostForm()
    if form.validate_on_submit():
        post.title = form.title.data
        # post.author = form.author.data
        post.slug = form.slug.data
        post.content = form.content.data
        # Update data
        db.session.add(post)
        db.session.commit()
        flash('Post Updated')
        return redirect(url_for('post', id=post.id))
    
    if current_user.id == post.poster.id or current_user.id == 16:
        form.title.data = post.title
        # form.author.data = post.author
        form.slug.data = post.slug
        form.content.data = post.content
        return render_template('edit_post.html', form=form)
    else:
        flash("You cannot edit someone else's post...")
        return redirect(url_for('posts'))



# Add Post Page
@app.route('/add-post', methods=['GET', 'POST'])
#@login_required
def add_post():
    form = PostForm()

    if form.validate_on_submit():
        poster = current_user.id
        post = Posts(title=form.title.data, content=form.content.data, poster_id=poster, slug=form.slug.data)
        # Clear Form Data
        form.title.data = ''
        form.content.data = ''
        # form.author.data = ''
        form.slug.data = ''

        # Add Post Data to Database
        db.session.add(post)
        db.session.commit()

        # Return Message
        flash('Post Submitted Successfully!')

    # Redirect to webpage
    return render_template('add_post.html', form=form)

    
@app.route('/delete/<int:id>')
@login_required
def delete(id):
    if id == current_user.id:

        user_to_delete = User.query.get_or_404(id)
        name = None
        form = UserForm()

        try:
            db.session.delete(user_to_delete)
            db.session.commit()
            flash('User Deleted!')
            return redirect(url_for('add_user'))

        except:
            flash('Error deleting user')
            return redirect(url_for('add_user'))
    else:
        flash('You cannot delete someone else...')
        return redirect(url_for("add_user"))

# Update Database Record
@app.route('/update/<int:id>', methods=['GET', 'POST'])
@login_required
def update(id):
    form = UserForm()
    name_to_update = User.query.get_or_404(id)
    if request.method == 'POST':
        name_to_update.name = request.form.get('name')
        name_to_update.email = request.form.get('email')
        name_to_update.favourite_colour = request.form.get('favourite_colour')
        name_to_update.username = request.form.get('username')
        try:
            db.session.commit()
            flash('User Updated Successfully')
            return render_template('update.html', 
                                   form=form, 
                                   name_to_update=name_to_update, id=id)
        except:
            flash('Error Updating User')
            return render_template('update.html', 
                                   form=form, 
                                   name_to_update=name_to_update, 
                                   id=id)
    else:
        return render_template('update.html', 
                                   form=form, 
                                   name_to_update=name_to_update, 
                                   id=id)




# def index():
#     return "<h1>Hello World!</h1>"

# Filters:
# safe
# capitalize
# lower
# upper
# title
# trim
# striptags


@app.route('/user/add', methods=['GET', 'POST'])
def add_user():
    name = None
    form = UserForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None:
            # Hash Password
            hashed_pw = generate_password_hash(form.password_hash.data)
            user = User(username=form.username.data, name=form.name.data, email=form.email.data, favourite_colour=form.favourite_colour.data, password_hash=hashed_pw)
            db.session.add(user)
            db.session.commit()
        name = form.name.data
        form.name.data = ''
        form.username.data = ''
        form.email.data = ''
        form.favourite_colour.data = ''
        form.password_hash.data = ''

        flash("User Added Successfully!")
    users = User.query.order_by(User.date_added)
    return render_template("add_user.html", 
                           form=form, 
                           name=name, 
                           users=users)

# Create route decorator
@app.route('/')
def index():
    first_name = "Rick"
    stuff = "This is bold text"
    flash("Welcome to our website!")
    items = [1, 2, 3, "SAJE"]
    return render_template("index.html", 
                           first_name=first_name, 
                           stuff=stuff, 
                           items=items)

# Create custom error pages

# Invalid URL
@app.errorhandler(404)
def pageNotFound(e):
    return render_template("404.html"), 404

# Internal Server Error
@app.errorhandler(500)
def pageNotFound(e):
    return render_template("500.html"), 500
