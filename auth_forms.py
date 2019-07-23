from flask_wtf import Form
from wtforms.fields import StringField, PasswordField, BooleanField, SubmitField, IntegerField, RadioField
from wtforms.validators import DataRequired, url, Length, Email, Regexp, EqualTo, ValidationError
from model import User



class LoginForm(Form):
    email = StringField('Email: ', validators=[DataRequired()])
    password = PasswordField('Password : ', validators=[DataRequired()])
    remember_me = BooleanField('Keep me checked in ')


class EditUserForm(Form):
    name = StringField('Name : ', validators=[DataRequired(), Regexp('[A-Za-z ]', message="Name can only contain letters.")])
    email = StringField('Email ID : ', validators=[DataRequired(), Length(5, 120), Email()])
    mobile_no = StringField('Mobile Number : ', validators=[DataRequired(), Length(10), Regexp('[0-9]')])
    password = PasswordField('Password : ', validators = [DataRequired(), EqualTo('password2', message="Passwords must match.")])
    password2 = PasswordField('Confirm Password : ', validators=[DataRequired()])

class SignupForm(EditUserForm):
    def validate_email(self, email_field):
        if User.query.filter_by(email=email_field.data).first():
            raise ValidationError('This email ID is already registered.')

    def validate_mobilenumber(self, mobilenumber_field):
        if User.query.filter_by(mobile_no=mobilenumber_field.data).first():
            raise ValidationError('Mobile number is already registered.')

class AddressForm(Form):
    HouseNumber = StringField('Flat/Plot Number: ', validators=[DataRequired()])
    SocietyName = StringField('Apartment/House Name: ', validators=[DataRequired(message="Enter own name if none applicable.")])
    Area = StringField('Neighborhood, Landmarks: ', validators=[DataRequired()])
    City = StringField('City: ', validators=[DataRequired()])
    Pincode = StringField('Pincode: ', validators=[DataRequired(), Regexp('[0-9]'), Length(6)])
    State = StringField('State: ', validators=[DataRequired()])

class PaymentForm(Form):
    ModeOfPayment = RadioField('Payment Method: ', choices=[(1, 'Cash'), (2,'Credit/Debit Card') ])
