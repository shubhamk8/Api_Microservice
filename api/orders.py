from api import bp
from model import *
from flask import jsonify


@bp.route('/orders')
def get_orders():
    orders = Orders.get_all_orders()
    result = OrderSchema(many=True)
    return jsonify(result.dumps(orders).data)


@bp.route('/orders/<int:id>')
def get_order_id(id):
    order = Orders.get_order(id)
    result = OrderSchema
    return jsonify(result.dumps(order).data)
