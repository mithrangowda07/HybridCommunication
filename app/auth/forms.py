from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError, Regexp
from app.models import User

class LoginForm(FlaskForm):
    phone_number = StringField('Phone Number', validators=[
        DataRequired(),
        Regexp(r'^\+?1?\d{9,15}$', message='Invalid phone number format')
    ])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    phone_number = StringField('Phone Number', validators=[
        DataRequired(),
        Regexp(r'^\+?1?\d{9,15}$', message='Invalid phone number format')
    ])
    display_name = StringField('Display Name', validators=[
        DataRequired(),
        Length(min=2, max=64)
    ])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=6, message='Password must be at least 6 characters long')
    ])
    password2 = PasswordField('Repeat Password', validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match')
    ])
    submit = SubmitField('Register')

    def validate_phone_number(self, phone_number):
        user = User.query.filter_by(phone_number=phone_number.data).first()
        if user is not None:
            raise ValidationError('Phone number already registered.') 