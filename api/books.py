from api import bp
from flask_login import login_required
from model import *
from flask import jsonify, request, Response


def validate(bookObject):
    if "name" in bookObject and "price" in bookObject and "ïsbn" in bookObject and "author" in bookObject:
        return True
    else:
        return True


@bp.route('/inventory')
def get_inventory():
    books = Book.get_inventory('self')
    books_schema = BookSchema(many=True)
    response = Response(books_schema.dumps(books).data, status=201, mimetype="application/json")
    return response


@bp.route('/inventory', methods=['POST'])
@login_required
def add_book():
    request_data = request.get_json()
    if validate(request_data):
        Book.add(request_data['name'], request_data['price'], request_data['author'], request_data['isbn'])
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


@bp.route('/inventory/<string:name>')
def get_book_isbn(name):
    book = Book.get_book(name)
    if book is None:
        invalidBookMsg = {
            "error": "Book with provided Name is not found"
        }
        response = Response(json.dumps(invalidBookMsg), status=404, mimetype="application/json")
        return response
    else:
        bookSchema = BookSchema()
        response = Response(bookSchema.dumps(book).data, status=201, mimetype='application/json')
        return response


@bp.route('/inventory/<string:name>/locations')
def get_book_location(name):
    locations = db.session.query(Inventory.pincode).filter(Book.book_name == name).filter(
        Location.pincode == Inventory.pincode).filter(Inventory.book_id == Book.book_id).all()
    location_schema = LocationSchema(many=True)
    response = Response(location_schema.dumps(locations).data, status=201, mimetype='application/json')
    return response


@bp.route('/inventory/<string:name>/<int:pincode>')
def check_availability(name, pincode):
    result = Inventory.is_available(name, pincode)
    if result is not None:
        message = {
            "msg": "This Book is available for ordering"
        }
        response = Response(json.dumps(message), status=200, mimetype='application/json')
        return response
    else:
        message = {"msg": "Sorry!!.. This Book is not available at your location"}
        response = Response(json.dumps(message), status=200, mimetype='application/json')
        return response
