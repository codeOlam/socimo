"""Sign-up & log-in forms."""
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, FileField, TextAreaField
from wtforms.validators import (
    DataRequired,
    Email,
    EqualTo,
    Length,
    Optional,
    ValidationError
)

from app.models import User


class SignupForm(FlaskForm):
    """User Sign-up Form."""
    name = StringField('Name', validators=[DataRequired()])
    email = StringField('Email', validators=[Length(min=6), 
                                            Email(message='Enter a valid email.'),
                                            DataRequired()]
                        )
    password = PasswordField('Password',
        validators=[DataRequired(),
                    Length(min=6, message='Select a stronger password.')]
        )
    confirm = PasswordField('Confirm Your Password',
        validators=[DataRequired(),
                    EqualTo('password', message='Passwords must match.')]
        )
    photo = FileField('Photo', validators=[Optional()])
    submit = SubmitField('Register')


    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email')


class LoginForm(FlaskForm):
    """User Log-in Form."""
    email = StringField('Email',
        validators=[DataRequired(), Email(message='Enter a valid email.')])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Log In')



class PostForm(FlaskForm):
    """
    The post form
    """

    content = TextAreaField('Content')
    submit = SubmitField('Publish')


class FollowUnfollowForm(FlaskForm):
    submit = SubmitField('Submit')