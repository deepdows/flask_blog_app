from flask import render_template, url_for, flash, redirect, request, abort, Markup
from flaskblog.models import User, Post, Comment
from flaskblog.forms import (RegistrationForm, LoginForm, UpdateAccountForm,
                            PostForm, UpdatePostForm, RequestResetForm,
                            ResetPasswordForm, CommentForm)
from flaskblog import app, db, bcrypt, mail
from flask_login import login_user, current_user, logout_user, login_required
from flask_mail import Message
import secrets, os
from PIL import Image
from datetime import datetime, timedelta
from math import ceil


@app.route('/')
@app.route('/home')
def home():
    posts = Post.query.order_by(Post.date_posted.desc()).all()
    return render_template("home.html", posts=posts)


@app.route('/about')
def about():
    return render_template("about.html", title="About")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash(f'Account is successfully created!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/account')
@login_required
def account():
    image_file = url_for('static', filename='profile_pics/' + current_user.image)
    return render_template('account.html', title='Account', image_file=image_file)

def save_picture(form_picture, path, output_size):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    if path == 'static/post_pics':
        f_ext = '.jpeg'
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, path, picture_fn)
    if f_ext != '.svg':
        i = Image.open(form_picture)

        new_width, new_height = output_size
        width, height = i.size

        if not width > new_width or not height > new_height:
            coef1 = ceil(new_height / height)
            coef2 = ceil(new_width / width)
            if coef1 == 0:
                coef = 1
            if coef2 == 0:
                coef = 1
            coef = max(coef1, coef2)

            temp_width = coef * width
            temp_height = coef * height
            i = i.resize((temp_width, temp_height))

        width, height = i.size

        coef1 = height // new_height
        coef2 = width // new_width
        if not coef1:
            coef = 1
        if not coef2:
            coef = 1
        coef = min(coef1, coef2)

        if(width > new_width or height > new_height):
            left, top, right, bottom = 0, 0, width, height
            if(width > new_width):
                new_width *= coef
                left = (width - new_width)/2
                right = (width + new_width)/2
            if(height > new_height):
                new_height *= coef
                bottom = (height + new_height)/2
                top = (height - new_height)/2

            i = i.crop((left, top, right, bottom))

        i.thumbnail(output_size)

        i.save(picture_path)
    else:
        form_picture.save(picture_path)
    return picture_fn

def delete_old_picture(pic, path):
    if pic != 'default.png':
        picture_path = os.path.join(app.root_path, path, pic)
        if os.path.exists(picture_path):
            os.remove(picture_path)

# POST

@app.route('/edit_account', methods=['GET', 'POST'])
@login_required
def edit():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if bcrypt.check_password_hash(current_user.password, form.current_password.data):
            if form.imageUpload.data:
                picture_file = save_picture(form.imageUpload.data, 'static/profile_pics', (300,300))
                delete_old_picture(current_user.image, 'static/profile_pics')
                current_user.image = picture_file
            current_user.email = form.email.data
            current_user.username = form.username.data
            if form.new_password.data:
                hashed_password = bcrypt.generate_password_hash(form.new_password.data).decode('utf-8')
                current_user.password = hashed_password
            db.session.commit()
            flash('Your profile has been updated', 'success')
            return redirect(url_for('account'))
        else:
            flash('Please check your current password', 'danger')
    elif request.method == 'GET':
        form.email.data = current_user.email
        form.username.data = current_user.username
    image_file = url_for('static', filename='profile_pics/' + current_user.image)
    return render_template('edit.html', title='Edit', image_file=image_file, form=form)

@app.route('/new_post', methods=['GET', 'POST'])
@login_required
def new_post():
    if not current_user.admin:
        return redirect(url_for('home'))
    form = PostForm()
    if form.validate_on_submit():
        picture_file = save_picture(form.postImage.data, 'static/post_pics', (1280,720))
        post = Post(title=form.title.data, description=form.description.data, content=form.content.data, image=picture_file)
        db.session.add(post)
        db.session.commit()
        flash('Post has been created', 'success')
        return redirect(url_for('home'))
    return render_template('create_post.html', title='New Post', form=form, legend='New Post')

@app.route('/post/<int:post_id>', methods=['GET', 'POST'])
def post(post_id):
    post = Post.query.get_or_404(post_id)
    form = CommentForm()
    if form.validate_on_submit() and current_user.is_authenticated:
        if (Comment.query.filter_by(user_id=current_user.id, post_id=post_id)
                        .filter(datetime.now() - timedelta(minutes=60) < Comment.date_posted).count() < 2):
            comment = Comment(text=form.comment.data, post_id=post_id, user=current_user)
            db.session.add(comment)
            db.session.commit()
            flash('Your comment is added', 'success')
            return redirect(url_for('post', post_id=post_id))
        flash('You can\'t post more than 2 messages for a post an hour', 'danger')
        return redirect(url_for('post', post_id=post_id))
    comments = Comment.query.filter_by(post_id=post_id).order_by(Comment.date_posted.desc()).all()
    if current_user.is_authenticated:
        image_file = url_for('static', filename='profile_pics/' + current_user.image)
    else:
        image_file = None
    return render_template('post.html', title=post.title, post=post, content=Markup(post.content) , comments=comments,
                                        current_image_profile=image_file, form=form)

@app.route('/post/<int:post_id>/update', methods=['GET', 'POST'])
@login_required
def update_post(post_id):
    if not current_user.admin:
        abort(403)
    post = Post.query.get_or_404(post_id)
    form = UpdatePostForm()
    if form.validate_on_submit():
        post.title = form.title.data
        post.description = form.description.data
        post.content = form.content.data
        if(form.postImage.data):
            delete_old_picture(post.image, 'static/post_pics')
            post.image = save_picture(form.postImage.data, 'static/post_pics', (1280,720))
        db.session.commit()
        flash('Post has been updated', 'success')
        return redirect(url_for('post', post_id=post.id))
    elif request.method == 'GET':
        form.title.data = post.title
        form.description.data = post.description
        form.content.data = post.content
    image_file = url_for('static', filename='post_pics/' + post.image)
    return render_template('create_post.html', title='Update Post', form=form, image_file=image_file, legend='Update Post')

@app.route('/post/<int:post_id>/delete', methods=['GET', 'POST'])
@login_required
def delete_post(post_id):
    if not current_user.admin:
        abort(403)
    post = Post.query.get_or_404(post_id)
    Comment.query.filter_by(post_id=1).delete()
    delete_old_picture(post.image, 'static/post_pics')
    db.session.delete(post)
    db.session.commit()
    flash('Post has been deleted', 'success')
    return redirect(url_for('home'))

# PASSWORD RESET

def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message('Password Reset Request',
                    sender='noreply@deepdows',
                    recipients=[user.email])
    msg.html = f'''
    To reset your password, visit the link:

    <a href="{url_for('reset_token', token=token, _external=True)}" style="text-decoration: none; color: #2B74B9; "> Reset password </a>

    if you did not make this request, ignore this email.'''
    mail.send(msg)


@app.route('/reset_password', methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        send_reset_email(user)
        flash('Email was send for ' + user.email, 'info')
        return redirect(url_for('home'))
    return render_template('reset_request.html', title='Reset Password', form=form)

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('edit'))
    user = User.verify_reset_token(token)
    if user is None:
        flash('This is an invalid or expired token', 'warning')
        return redirect(url_for('reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.new_password.data).decode('utf-8')
        user.password = hashed_password
        db.session.commit()
        flash(f'Password has been updated!', 'success')
        return redirect(url_for('login'))
    return render_template('reset_token.html', title='Reset Password', form=form)

# ERRORS

@app.errorhandler(404)
def error_404(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(403)
def error_403(error):
    return render_template('errors/403.html'), 403

@app.errorhandler(500)
def error_500(error):
    return render_template('errors/500.html'), 500