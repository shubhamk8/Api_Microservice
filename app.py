from flask import Flask, jsonify, request, Response
from datetime import datetime, timedelta
from settings import *
from flask_login import login_required, login_user, current_user
from model import *
import json
from functools import wraps


@login_manager.user_loader
def load_user(userid):
    return User.query.get(int(userid))


def token_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        token = request.args.get('token')
        try:
            jwt.decode(token, current_user.get_token())
            return f(*args, **kwargs)
        except:
            return jsonify({'error': 'Need a valid token to view this page'}), 401

    return wrapper


@app.route('/inventory')
def get_inventory():
    books = Inventory.get_inventory('self')
    books_schema = InventorySchema(many=True)
    response = Response(books_schema.dumps(books).data, status=201, mimetype="application/json")
    return response


@app.route('/login', methods=['POST'])
def get_token():
    request_data = request.get_json()
    username = str(request_data['username'])
    password = str(request_data['password'])
    user = User.user_pass_match(username, password)
    if user is not None:
        login_user(user, remember=False)
        expiration_date = datetime.utcnow() + timedelta(seconds=3600)
        token = jwt.encode({'exp': expiration_date}, user.get_token(), algorithm='HS256')
        return token
    else:
        return Response('', status=401, mimetype='application/json')


def validate(bookObject):
    if "name" in bookObject and "price" in bookObject and "ïsbn" in bookObject and "author" in bookObject:
        return True
    else:
        return True


@app.route('/inventory', methods=['POST'])
def add_book():
    request_data = request.get_json()
    if validate(request_data):
        Inventory.add(request_data['name'], request_data['price'], request_data['author'], request_data['isbn'])
        resp = Response("", status=201, mimetype='application/json')
        resp.headers['Location'] = "/inventory/" + str(request_data['name'])
        return resp
    else:
        invalidBookObjectError = {
            "error": "Invalid book object passed in request",
            "helpString": "Data is passed is similar to this {'name':'bookname', 'price':299, 'isbn':123453423}"
        }
        response = Response(jsonify(invalidBookObjectError), status=400, mimetype='application/json')
        return response


@app.route('/inventory/<string:name>')
def get_book_isbn(name):
    book = Inventory.get_book(name)
    if book is None:
        invalidBookMsg = {
            "error": "Book with provided Name is not found"
        }
        response = Response(json.dumps(invalidBookMsg), status=404, mimetype="application/json")
        return response
    else:
        bookSchema = InventorySchema()
        response = Response(bookSchema.dumps(book).data, status=201, mimetype='application/json')
        return response


@app.route('/inventory/<string:name>/locations')
def get_book_location(name):
    locations = db.session.execute(
        'select location.pincode from inventory,location,inv_loc where book_name= :name and location.l_id=inv_loc.l_id and inventory.i_id=inv_loc.i_id',
        {'name': name})
    locationSchema = LocationSchema(many=True)
    response = Response(locationSchema.dumps(locations).data, status=201, mimetype='application/json')
    return response


@app.route('/inventory/<string:name>/<int:pincode>/order')
def order(name, pincode):
    if Inventory.is_available(name, pincode):
        message = {
            "msg": "This Book is available for ordering"
        }
        response = Response(json.dumps(message), status=200, mimetype='application/json')
        return response
    else:
        message = {
            "msg": "Sorry!!.. This Book is not available at your location"
        }
        response = Response(json.dumps(message), status=200, mimetype='application/json')
        return response


@app.route('/user')
def get_users():
    user = User.getAllUsers('self')
    user_schema = UserSchema(many=True)
    response = Response(user_schema.dumps(user).data, status=201, mimetype='application/json')
    return response


@app.route('/user', methods=['POST'])
def add_user():
    request_data = request.get_json()
    new_user = User.createUser(request_data['username'], request_data['password'])
    db.session.add(new_user)
    db.session.commit()


@app.route('/user/<int:id>')
def get_user(id):
    user = User.query.filter_by(id=id).first()
    user_schema = UserSchema()
    response = Response(user_schema.dumps(user).data, status=201, mimetype='application/json')
    return response

@app.route('/user/<int:id>/orders')
def get_user_orders(id):
    orders = User.get_orders()
    order = OrderSchema(many=True)
    return Response(order.dumps(orders).data,status=201,mimetype='application/json')


@app.route('/books/<int:isbn>', methods=['PUT'])
def replace_book(isbn):
    request_data = request.get_json()
    if not validate(request_data):
        invalidBookObjectErrorMsg = {
            "error": "Valid Book object must be passed in the request",
            "helpString": "Data passed in similar to this {'name':'bookname','price':299}"
        }
        response = Response(jsonify(invalidBookObjectErrorMsg), status=400, mimetype='application/json')
        return response
    Book.replace_book(isbn, request_data['name'], request_data['price'])
    response = Response("", status=204)
    return response


@app.route('/books/<int:isbn>', methods={'PATCH'})
def update_book(isbn):
    request_data = request.get_json()
    if "name" in request_data:
        Book.update_book_name(isbn, request_data['name'])
    if "price" in request_data:
        Book.update_book_price(isbn, request_data['price'])
    response = Response("", status=204)
    response.headers['Location'] = "/books/" + str(isbn)
    return response


@app.route('/books/<int:isbn>', methods=['DELETE'])
def delete_book(isbn):
    if Book.delete_book(isbn):
        response = Response("", status=200, mimetype="application/json")
        return response
    else:
        invalidBookMsg = {
            "error": "Book with provided isbn number is not found"
        }

        response = Response(json.dumps(invalidBookMsg), status=404, mimetype="application/json")
        return response


if __name__ == '__main__':
    app.run(debug=True)
