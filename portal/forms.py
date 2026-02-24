from flask_wtf import FlaskForm, RecaptchaField
from app import app
from wtforms import StringField, SubmitField, PasswordField, IntegerField, SelectField
from wtforms.validators import DataRequired, Email, EqualTo
from models import Charity
from validators import PasswordRequirements