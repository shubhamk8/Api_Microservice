from flask_wtf import Form
from wtforms.fields import StringField, IntegerField, BooleanField, SubmitField, SelectField
from wtforms.validators import DataRequired, url, Length, Email, Regexp, EqualTo, ValidationError
from model import User, Book

class OrderBookForm(Form):
    book_title = StringField('Title : ', validators=[DataRequired()])
    #isbn = StringField('ISBN : ', validators=[DataRequired()])
    quantity = IntegerField('Quantity : ', validators=[DataRequired()])
