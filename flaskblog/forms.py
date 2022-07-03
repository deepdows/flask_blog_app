from flask_wtf import FlaskForm, RecaptchaField
from flask_wtf.file import FileField, FileAllowed
from flask_login import current_user
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField
from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from flaskblog.models import User
from flaskblog import bcrypt

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[
        DataRequired(),
    ])
    email = EmailField('Email', validators=[
        DataRequired(),
        Email()
    ])
    password = PasswordField('Password',validators=[
        DataRequired(),
        Length(min=8)
    ])
    confirm_password = PasswordField('Confirm password',validators=[
        DataRequired(),
        EqualTo('password', message='The passwords don\'t match')
    ])
    recaptcha = RecaptchaField()
    submit = SubmitField('Sign Up')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('This email already exists, try to login in')
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('This username is already taken')

class LoginForm(FlaskForm):
    email = EmailField('Email', validators=[
        DataRequired(),
        Email()
    ])
    password = PasswordField('Password',validators=[
        DataRequired()
    ])
    submit = SubmitField('Sign In')
    remember = BooleanField('Remember Me')

class UpdateAccountForm(FlaskForm):
    username = StringField('Username', validators=[
        DataRequired()
    ])
    email = EmailField('Email', validators=[
        DataRequired(),
        Email()
    ])
    current_password = PasswordField('Current password',validators=[
        DataRequired()
    ])
    new_password = PasswordField('New password')
    confirm_new_password = PasswordField('Confirm new password')
    imageUpload = FileField('imageUpload', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'svg'])
    ])

    submit = SubmitField('Update')

    def validate_username(self, username):
        if username.data != current_user.username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('This username is already taken')
    def validate_email(self, email):
        if email.data != current_user.email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('This email is already taken')
    def validate_new_password(self, new_password):
        if new_password.data:
            if bcrypt.check_password_hash(current_user.password, new_password.data):
                raise ValidationError('The same password as before')
    def validate_confirm_new_password(self, confirm_new_password):
        if self.new_password.data:
            if confirm_new_password.data:
                if self.new_password.data != confirm_new_password.data:
                    raise ValidationError('The passwords don\'t match')
            else:
                raise ValidationError('Field mustn\'t be empty')
        
class PostForm(FlaskForm):
    title = StringField('Title', validators=[
        DataRequired()
    ])
    description = StringField('Description', validators=[
        DataRequired()
    ])
    postImage = FileField('postImage', validators=[
        FileAllowed(['jpg', 'jpeg', 'png'])
    ])
    content = TextAreaField('Content', validators=[
        DataRequired()
    ])
    submit = SubmitField('Post')

    def validate_postImage(self, postImage):
        if not postImage.data:
           raise ValidationError('Add post image')


class UpdatePostForm(FlaskForm):
    title = StringField('Title', validators=[
        DataRequired()
    ])
    description = StringField('Description', validators=[
        DataRequired()
    ])
    postImage = FileField('postImage', validators=[
        FileAllowed(['jpg', 'jpeg', 'png'])
    ])
    content = TextAreaField('Content', validators=[
        DataRequired()
    ])
    submit = SubmitField('Post')

class RequestResetForm(FlaskForm):
    email = EmailField('Email', validators=[
        DataRequired(),
        Email()
    ])
    recaptcha = RecaptchaField()
    submit = SubmitField('Request reset')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if not user:
            raise ValidationError('Account with the email doesn\'t exist')

class ResetPasswordForm(FlaskForm):
    new_password = PasswordField('New password',validators=[
        DataRequired(),
        Length(min=8)
    ])
    confirm_new_password = PasswordField('Confirm new password',validators=[
        DataRequired(),
        EqualTo('new_password', message='The passwords don\'t match')
    ])
    submit = SubmitField('Reset password')

class CommentForm(FlaskForm): 
    comment = StringField('Comment', validators=[
        DataRequired(),
        Length(min=10, max=300)
    ])
    submit = SubmitField('Send')