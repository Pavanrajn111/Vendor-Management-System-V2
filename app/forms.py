from flask_wtf import FlaskForm
from wtforms import (DecimalField, IntegerField, PasswordField, SelectField,
                     StringField, SubmitField, TextAreaField)
from wtforms.validators import (DataRequired, EqualTo, Length, NumberRange,
                                Optional, Regexp)


class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(3, 80)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6)])
    submit = SubmitField("Sign in")


class RegisterForm(FlaskForm):
    username = StringField("Username", validators=[
        DataRequired(), Length(3, 80),
        Regexp(r"^[A-Za-z0-9_.-]+$", message="Letters, numbers, . _ - only.")
    ])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=8, max=128)])
    confirm = PasswordField("Confirm password", validators=[DataRequired(), EqualTo("password")])
    role = SelectField("I am a", choices=[("customer", "Customer"), ("vendor", "Vendor")],
                       validators=[DataRequired()])
    mobile = StringField("Mobile", validators=[Optional(), Length(7, 20),
                                               Regexp(r"^[0-9+\- ]+$")])
    submit = SubmitField("Create account")


class ProductForm(FlaskForm):
    name = StringField("Product name", validators=[DataRequired(), Length(1, 120)])
    price = DecimalField("Price", validators=[DataRequired(), NumberRange(min=0)])
    submit = SubmitField("Add product")


class ReviewForm(FlaskForm):
    vendor_id = SelectField("Vendor", coerce=int, validators=[DataRequired()])
    rating = IntegerField("Rating (1–5)", validators=[DataRequired(), NumberRange(1, 5)])
    comment = TextAreaField("Comment", validators=[Optional(), Length(max=2000)])
    submit = SubmitField("Submit review")
