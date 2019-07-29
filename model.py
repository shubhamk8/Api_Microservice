import base64
import json
import os
from datetime import datetime, timedelta
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from settings import *
from flask import url_for

db = SQLAlchemy(app)


class PaginatedAPIMixin(object):
    @staticmethod
    def to_collection(query, page, per_page, endpoint, **kwargs):
        resources = query.paginate(page, per_page,
                                   False)  # WHAT IS FALSE - an error flag- when an out of range page is requested
        # If True, a 404 error will be automatically returned to the client.
        # If False, an empty list will be returned for out of range pages.
        data = {
            'items': [item.to_dict() for item in resources.items],
            '_meta': {
                'page': page,
                'per_page': per_page,
                'total_pages': resources.pages,
                'total_items': resources.total
            },
            '_links': {
                'self': url_for(endpoint, page=page, per_page=per_page, **kwargs),
                'next': url_for(endpoint, page=page + 1, per_page=per_page, **kwargs),
                'prev': url_for(endpoint, page=page - 1, per_page=per_page, **kwargs)
            }
        }
        return data


class Book(db.Model, PaginatedAPIMixin):
    book_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(30))
    price = db.Column(db.Float)
    author = db.Column(db.String(30))
    isbn = db.Column(db.Integer)
    imgsrc = db.Column(db.String)
    locations = db.relationship("Inventory  ")

    def add(title, price, author, isbn, imgsrc):
        new_book = Book(title=title, price=price, author=author, isbn=isbn, imgsrc=imgsrc)
        db.session.add(new_book)
        db.session.commit()

    def get_inventory(self):
        return Book.query.all()

    def get_book(title):
        return Book.query.filter_by(title=title).first()

    def __repr__(self):
        book_object = {
            'id': self.book_id,
            'title': self.title,
            'price': self.price,
            'author': self.author,
            'isbn': self.isbn
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

    def is_available(title, pincode):
        result = db.session.query(Inventory.quantity, Inventory.book_id).filter(Book.title == title).filter(
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
    user_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80))
    email = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)
    mobile_no = db.Column(db.Integer)
    address = db.Column(db.Text)
    pincode = db.Column(db.Integer, db.ForeignKey('location.pincode'))
    mode_of_payment = db.Column(db.String)
    token = db.Column(db.String(50), index=True, unique=True)
    token_expiration = db.Column(db.DateTime)
    orders = db.relationship('Orders', backref='user', lazy='dynamic')
    cart = db.relationship('Cart', backref='user', lazy='dynamic')

    def user_pass_match(email, _password):
        user = User.query.filter_by(email=email).first()
        if user is None:
            return False
        else:
            return user

    def get_id(self):
        return (self.user_id)

    def getAllUsers(self):
        return User.query.all()

    def get_orders(id):
        orders = Orders.query.filter_by(user_id=id).order_by(Orders.o_id).all()
        return orders

    def createUser(_name, _password):
        new_user = User(email=_name, password=_password)
        db.session.add(new_user)
        db.session.commit()

    def get_token(self, expires_in=3600):
        now = datetime.utcnow()
        if self.token and self.token_expiration > now + timedelta(seconds=60):
            return self.token
        self.token = create_access_token(self.user_id, expires_delta=timedelta(expires_in))
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
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
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

    def place_order(user_id, title, qty, price, pincode):
        data = Inventory.is_available(title, pincode)
        new_qty = int(data.quantity) - int(qty)
        db.session.query(Inventory).filter(Inventory.book_id == data.book_id).filter(
            Inventory.pincode == pincode).update({"quantity": new_qty})
        new_order = Orders(user_id=user_id, title=title, qty=qty, total_amount=float(price) * float(qty),
                           date=datetime.utcnow(), pincode=pincode)
        db.session.add(new_order)
        db.session.commit()
        return True


class Cart(db.Model):
    cart_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.ForeignKey('user.user_id'), nullable=False)
    book_name = db.Column(db.String)
    price = db.Column(db.Float)
    quantity = db.Column(db.Integer)
    total = db.Column(db.Float)

    def add_to_cart(user_id, book_name, quantity):
        price = db.session.query(Book.book_price).filter(Book.book_name == book_name).first()
        cart_tot = float(price[0]) * int(quantity)
        cart = Cart(user_id=user_id, book_name=book_name, price=float(price[0]), quantity=quantity, total=cart_tot)
        db.session.add(cart)
        db.session.commit()

    def delete_from_cart(book_name, user_id):
        Cart.query.filer_by(Cart.book_name == book_name).filter_by(Cart.user_id == user_id).delete()
        db.session.commit()

    def view_cart(user_id):
        cart = Cart.query.filter(Cart.user_id == user_id).all()
        if len(cart) is 0:
            return None
        res = CartSchema(many=True)
        return res.dumps(cart).data

    def cart_order(user_id):
        items = db.session.query(Cart).filter(Cart.user_id == user_id).all()
        for item in items:
            usr = db.session.query(User.pincode).filter(User.id == item.user_id).first()
            order = Orders(user_id=item.user_id, book_name=item.book_name, qty=item.quantity,
                           total_amount=item.cart_total, date=datetime.utcnow(), pincode=usr.pincode)
            db.session.add(order)
            db.session.commit()

    def update_cart(id, quantity):
        cart_to_update = Cart.query.filer_by(cart_id=id).first()
        cart_to_update.quantity = quantity
        db.session.add(cart_to_update)
        db.session.commit()


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


class CartSchema(ma.ModelSchema):
    class Meta:
        model = Cart
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
