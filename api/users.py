from flask import request, Response
from flask_login import login_user, current_user, login_required, logout_user
from api import bp
from model import *
from flask import jsonify
from functools import wraps
import jwt


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def token_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        token = request.authorization.get()
        print(token)
        try:
            jwt.decode(token, current_user.get_token())
            jwt.decode()
            return f(*args, **kwargs)
        except:
            return jsonify({'error': 'Need a valid token to view this page'}), 401

    return wrapper


@bp.route('/login_token', methods=['POST'])
def get_token():
    request_data = request.get_json()
    email = str(request_data['email'])
    password = str(request_data['password'])
    user = User.user_pass_match(email, password)
    if user is not None:
        login_user(user, remember=False)
        token = user.get_token(3600)
        return Response(token, status=401, mimetype='application/json')
    else:
        return Response('', status=401, mimetype='application/json')


@bp.route('/users')
@jwt_required
def get_users():
    user = User.getAllUsers('self')
    user_schema = UserSchema(many=True)
    response = Response(user_schema.dumps(user).data, status=201, mimetype='application/json')
    return response


@bp.route('/user', methods=['POST'])
@jwt_required
def add_user():
    request_data = request.get_json()
    new_user = User.createUser(request_data['email'], request_data['password'])
    db.session.add(new_user)
    db.session.commit()


@bp.route('/user/<int:id>')
def get_user(id):
    user = User.query.filter_by(user_id=id).first()
    user_schema = UserSchema()
    response = Response(user_schema.dumps(user).data, status=201, mimetype='application/json')
    return response


@bp.route('/user/<int:id>/orders')
@login_required
def get_user_orders(id):
    orders = User.get_orders(id)
    result = OrderSchema(many=True)
    return Response(result.dumps(orders).data, status=201, mimetype='application/json')


@bp.route('/user/<int:id>/order', methods=['post'])
@token_required
def place_order(id):
    data = request.get_json()
    result = Orders.place_order(id, data['book_name'], data['qty'], data['price'], data['pincode'])
    if result is True:
        message = {"msg": "Order Placed Successfully! "}
        response = Response(json.dumps(message), status=201, mimetype='application/json')
        return response
    else:
        message = {"msg": "Sorry! This Book is currently not available at your location."}
        response = Response(json.dumps(message), status=500, mimetype='application/json')
        return response


@bp.route('/user/cart')
@token_required
def view_cart():
    cart = Cart.view_cart(current_user.user_id)
    if cart is not None:
        response = Response(cart, status=200, mimetype='application/json')
        return response
    else:
        message = {
            "msg": "Your Cart Is Empty!!"
        }
        return Response(json.dumps(message), status=200, mimetype='application/json')


@bp.route('/user/cart', methods=['post'])
@login_required
def add_to_cart():
    data = request.get_json()
    cart = Cart.add_to_cart(current_user.user_id, data['book_name'], data['quantity'])
    return Response('', status=201, mimetype='application/json')


@bp.route('/user/cart', methods=['delete'])
@login_required
def delete_from_cart():
    data = request.get_json()
    res = Cart.delete_from_cart(data['book_name'], current_user.id)
    return Response('', status=200, mimetype='application/json')


@bp.route('/user/cart/order')
@login_required
def order_cart():
    Cart.cart_order(current_user.user_id)
    return Response('', status=201, mimetype='application/json')


@bp.route('/logout')
def logout():
    logout_user()
    return Response('Logged Out Successfully...', status=200, mimetype='application/json')


@bp.route('/user/cart/<int:id>', methods=["put"])
def update_quantity(id):
    req = request.get_json()
    Cart.update_cart(id, req['quantity'])
    return Response('', status=200, mimetype='application/json')