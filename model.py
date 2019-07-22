import base64
import json
import os
from datetime import datetime, timedelta
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from settings import *

db = SQLAlchemy(app)


class Book(db.Model):
    book_id = db.Column(db.Integer, primary_key=True)
    book_name = db.Column(db.String(30))
    book_price = db.Column(db.Float)
    book_author = db.Column(db.String(30))
    book_isbn = db.Column(db.Integer)
    book_cover = db.Column(db.String(100))
    locations = db.relationship("Inventory  ")

    def add(book_name, book_price, book_author, book_isbn):
        new_book = Book(book_name=book_name, book_price=book_price, book_author=book_author, book_isbn=book_isbn)
        db.session.add(new_book)
        db.session.commit()

    def get_inventory(self):
        return Book.query.all()

    def get_book(name):
        return Book.query.filter_by(book_name=name).first()

    def __repr__(self):
        book_object = {
            'id': self.book_id,
            'name': self.book_name,
            'price': self.book_price,
            'author': self.book_author,
            'isbn': self.book_isbn
        }
        return json.dumps(book_object)


class Location(db.Model):
    pincode = db.Column(db.Integer, primary_key=True)

    def get_loc(self):
        return Location.query.all()

    def add_loc(pincode):
        loc = Location(pincode=pincode)
        db.session.add(loc)
        db.session.commit()

    def __repr__(self):
        location_object = {
            'pincode': self.pincode
        }
        return location_object


class Inventory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('book.book_id'))
    pincode = db.Column(db.Integer, db.ForeignKey('location.pincode'))
    quantity = db.Column(db.Integer)

    def is_available(book_name, pincode):
        result = db.session.query(Inventory.quantity, Inventory.book_id).filter(Book.book_name == book_name).filter(
            Location.pincode == pincode).filter(Book.book_id == Inventory.book_id).filter(
            Location.pincode == Inventory.pincode).first()
        return result

    def __repr__(self):
        inventory_object = {
            'id': self.id,
            'book_id': self.book_id,
            'pincode': self.pincode,
            'quantity': self.quantity
        }
        return inventory_object


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

    def user_pass_match(email, _password):
        user = User.query.filter_by(email=email).first()
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
        db.session.commit()
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
        orders = Orders.query.all()
        return orders

    def get_order(id):
        order = Orders.query.filter_by(o_id=id).first()
        return order

    def place_order(user_id, book_name, qty, price, pincode):
        data = Inventory.is_available(book_name, pincode)
        new_qty = int(data.quantity) - int(qty)
        db.session.query(Inventory).filter(Inventory.book_id == data.book_id).filter(
            Inventory.pincode == pincode).update({"quantity": new_qty})
        new_order = Orders(user_id=user_id, book_name=book_name, qty=qty, total_amount=float(price) * float(qty),
                           date=datetime.utcnow(), pincode=pincode)
        db.session.add(new_order)
        db.session.commit()
        return True


class BookSchema(ma.ModelSchema):
    class Meta:
        model = Book
        sqla_session = db.session


class InventorySchema(ma.ModelSchema):
    class Meta:
        model = Inventory
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
