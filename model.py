import json
from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy
from settings import *
import os
import base64
from flask_login import UserMixin

db = SQLAlchemy(app)


class Book(db.Model):
    book_id = db.Column(db.Integer, primary_key=True)
    book_name = db.Column(db.String(30))
    book_price = db.Column(db.Float)
    book_author = db.Column(db.String(30))
    book_isbn = db.Column(db.Integer)
    locations = db.relationship("Inventory")

    def add(book_name, book_price, book_author, book_isbn):
        new_book = Book(book_name=book_name, book_price=book_price, book_author=book_author, book_isbn=book_isbn)
        db.session.add(new_book)
        db.session.commit()

    def get_inventory(self):
        return Book.query.all()

    def get_book(name):
        return Book.query.filter_by(book_name=name).first()

    def is_available(book_name, pincode):
        result = db.session.execute(
            'SELECT inv_loc.quantity, inv_loc.i_id, inv_loc.l_id from inventory,inv_loc,location where '
            'inventory.book_name= :book and location.pincode= :pincode and location.l_id=inv_loc.l_id and '
            'inventory.i_id=inv_loc.i_id',
            {'book': book_name, 'pincode': pincode}).first()
        return result


class Location(db.Model):
    pincode = db.Column(db.Integer, primary_key=True)

    def get_loc(self):
        return Location.query.all()

    def add_loc(pincode):
        loc = Location(pincode=pincode)
        db.session.add(loc)
        db.session.commit()


class Inventory(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('book.book_id'))
    pincode = db.Column(db.Integer, db.ForeignKey('location.pincode'))
    quantity = db.Column(db.Integer)


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80))
    email = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)
    mobile_no = db.Column(db.Integer)
    address = db.Column(db.Text)
    pincode = db.Column(db.Integer, db.ForeignKey('location.pincode'))
    token = db.Column(db.String(50), index=True, unique=True)
    token_expiration = db.Column(db.DateTime)
    orders = db.relationship('Orders', backref='user', lazy='dynamic')

    def user_pass_match(_username, _password):
        user = User.query.filter_by(username=_username).filter_by(password=_password).first()
        if user is None:
            return False
        else:
            return user

    def getAllUsers(self):
        return User.query.all()

    def get_orders(id):
        orders = Orders.query.filter_by(user_id=id).order_by(Orders.o_id).all()
        return orders

    def createUser(_username, _password):
        new_user = User(username=_username, password_hash=_password)
        db.session.add(new_user)
        db.session.commit()

    def get_token(self, expires_in=3600):
        now = datetime.utcnow()
        if self.token and self.token_expiration > now + timedelta(seconds=60):
            return self.token
        self.token = base64.b64encode(os.urandom(24)).decode('utf-8')
        self.token_expiration = now + timedelta(seconds=expires_in)
        db.session.add(self)
        return self.token

    def revoke_token(self):
        self.token_expiration = datetime.utcnow() - timedelta(seconds=1)

    @staticmethod
    def check_token(token):
        user = User.query.filter_by(token=token).first()
        if user is None or user.token_expiration < datetime.utcnow():
            return None
        return user


class Orders(db.Model):
    o_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    book_name = db.Column(db.String, nullable=False)
    qty = db.Column(db.Integer)
    total_amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.DateTime)
    pincode = db.Column(db.Integer, db.ForeignKey('location.pincode'))

    def get_all_orders(self):
        pass

    def get_order(id):
        order = Orders.query.filter_by(o_id=id).first()
        return order

    def place_order(user_id, book_name, qty, price, pincode):
        data = Book.is_available(book_name, pincode)
        new_qty = int(data.quantity) - int(qty)
        db.session.execute('update inv_loc set quantity=:qty where i_id=:iid and l_id=:lid',
                           {'qty': new_qty, 'iid': data.i_id, 'lid': data.l_id})
        new_order = Orders(user_id=user_id, book_name=book_name, qty=qty, total_amount=float(price) * float(qty),
                           date=datetime.utcnow(), pincode=pincode)
        db.session.add(new_order)
        db.session.commit()


class InventorySchema(ma.ModelSchema):
    class Meta:
        model = Book
        sqla_session = db.session


class LocationSchema(ma.ModelSchema):
    class Meta:
        model = Location
        sqla_session = db.session


class UserSchema(ma.ModelSchema):
    class Meta:
        model = User
        sqla_session = db.session


class OrderSchema(ma.ModelSchema):
    class Meta:
        model = Orders
        sqla_session = db.session


db.create_all()

# class Book(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String(80))
#     price = db.Column(db.Float)
#     isbn = db.Column(db.Integer)
#
#     def add_book(_name, _price, _isbn):
#         new_book = Book(name=_name, price=_price, isbn=_isbn)
#         db.session.add(new_book)
#         db.session.commit()
#
#     def get_all_books(self):
#         return Book.query.all()
#
#     def get_book(_isbn):
#         return Book.query.filter_by(isbn=_isbn).first()
#
#     def delete_book(_isbn):
#         is_sucessful = Book.query.filter_by(isbn=_isbn).delete()
#         db.session.commit()
#         return bool(is_sucessful)
#
#     def update_book_price(_isbn, _price):
#         book_to_update = Book.query.filter_by(isbn=_isbn).first()
#         book_to_update.price = _price
#         db.session.add(book_to_update)
#         db.session.commit()
#
#     def update_book_name(_isbn, _name):
#         book_to_update = Book.query.filter_by(isbn=_isbn).first()
#         book_to_update.name = _name
#         db.session.add(book_to_update)
#         db.session.commit()
#
#     def __repr__(self):
#         book_object = {
#             'name': self.name,
#             'price': self.price,
#             'isbn': self.isbn
#         }
#         return json.dumps(book_object)