from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, validators

class RegistrationForm(FlaskForm):
    username = StringField('Username', [validators.Length(min=4, max=25)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords must match')
    ])
    confirm = PasswordField('Repeat Password')


class LoginForm(FlaskForm):
    username = StringField('Username')
    password = PasswordField('Password')


class RecipeForm(FlaskForm):
    title = StringField('Название', [validators.DataRequired()])
    description = TextAreaField('Описание')
    ingredients = TextAreaField('Ингредиенты', [validators.DataRequired()])
    instructions = TextAreaField('Инструкции', [validators.DataRequired()])
