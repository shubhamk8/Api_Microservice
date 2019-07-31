from flask import render_template, url_for, flash, redirect, request
from flask_login import login_user, logout_user, current_user, login_required

from settings import app, login_manager
from app import *
from api import * #needed or not?
from model import db, User, Book, Cart, Orders
from auth_forms import LoginForm, SignupForm, EditUserForm, AddressForm, PaymentForm
from order_forms import OrderBookForm, UpdateCartForm

import requests
import json



#DEMO FUNCTIONS

@app.route('/')
def index():
    # with open('books_inventory.json') as books_json:
    #    books = json.load(books_json)
    r = requests.get('http://localhost:5000/api/inventory')
    books = json.loads(r.text)
    return render_template('index.html', books=books)

@app.route('/cart/<int:user_id>')
def show_cart(user_id):
    # with open('shopping_cart.json') as cart_json:
    #    cart = json.load(cart_json)
    total = 0
    empty = False
    if current_user.id != user_id:
        abort(403)
    else:
        cart = Cart.view_cart(user_id)
        if cart is None:
            cart = []
            empty = True
        else:
            cart = json.loads(cart)
            for i in cart:
                total += i["total"]
        return render_template("shopping_cart.html", cart=cart, total=total, empty=empty)


def InCart(title):
    user = current_user
    cart = Cart.view_cart(user.id)
    if cart is not None:
        cart = json.loads(cart)
        for book in cart:
            if title == book["book_name"]:
                return True
        else:
            return False
    else:
        return False


@app.route('/cart/add <title>')
def AddToCart(title):
    if Cart.view_cart(current_user.id) is not None:
        cart = json.loads(Cart.view_cart(current_user.id))
    else:
        cart = {}
    if InCart(title):
        for book in cart:
            if book['book_name'] == title:
                book['quantity'] += 1
    else:
        Cart.add_to_cart(current_user.id, title, 1)
        flash('{} added to Cart'.format(title))
    return redirect(url_for('index'))

@app.route('/cart/remove <title>')
def RemoveFromCart(title):
    if InCart(title):
        Cart.delete_from_cart(title, current_user.id)
        return redirect(request.args.get('next') or url_for('show_cart', user_id=current_user.id))
    else:
        flash('{} not present in Cart'.format(title))
        return redirect(url_for('show_cart', user_id=current_user.id))

@app.route('/cart/update <title>', methods=['POST', 'GET'])
def UpdateCart(title):
    cart = Cart.view_cart(current_user.id)
    if cart is None:
        pass
    else:
        if request.method == 'POST':
            cart = json.loads(cart)
            for book in cart:
                print(book)
                print(request.form.get('quantity'))
                Cart.update_cart(book['cart_id'], request.form.get('quantity'))
                print(book)
                flash('Cart updated Successfully!')
    return redirect(url_for('show_cart', user_id=current_user.id))



@app.route('/order-memo/<int:user_id>')
def orderMemo(user_id):
    total = 0
    empty = False
    if user_id != current_user.id:
        abort(403)
    else:
        orders = User.get_orders(current_user.id)
        for book in orders:
            total += (book.total_amount * book.qty)
        if total == 0:
            empty = True
        return render_template("order_memo.html", order=orders, total=total, empty=empty)



@app.route('/confirm-order-demo/<int:user_id>)')
@login_required
def place_order_demo(user_id):
    total = 0
    cart = Cart.view_cart(user_id)
    if cart is None:
        pass
    else:
        cart = json.loads(cart)
        if current_user.address is not None:

                # url = "http://localhost:5000/api/user/cart/order"
                # rp = requests.get(url=url, params=str(current_user))
                Cart.cart_order(current_user.id)
                # params = {'id':current_user.id}
                #url = "http://localhost:5000/user/{}/orders".format(current_user.id)
                #rg = requests.get(url=url)
                # order = json.loads(rg.text)
                orders = User.get_orders(current_user.id)
                for book in orders:
                    total += (book.total_amount*book.qty)
                return render_template("order_memo.html", order=orders, total=total)
        else:
            flash("Enter delivery address")
            return redirect(url_for('address_form'))

# return render_template("confirm_order.html", cart=cart, total=total)


@app.route('/templates/address_form.html', methods=["GET", "POST"])
@login_required
def address_form():
    form = AddressForm()
    if form.validate_on_submit():
        user = current_user
        user.address = form.HouseNumber.data + ", " + form.SocietyName.data + ", " + form.Area.data + ", " + form.City.data + ", " + form.Pincode.data + ", " + form.State.data
        db.session.add(user)
        db.session.commit()
        flash('Address added successfully')
        return redirect(request.args.get('next') or url_for('user', user_id=current_user.id))
    return render_template("address_form.html", form=form)


@app.route('/book/<title>')
def view_book(title):
    book = Book.get_book(title)
    return render_template("view_book.html", book=book, incart=InCart(title))


@app.route('/add-payment-mode', methods=["GET","POST"])
def obtain_paymentmode():
    form = PaymentForm()
    if form.validate_on_submit():
        user = current_user
        user.mode_of_payment = form.ModeOfPayment.data
        db.session.add(user)
        db.session.commit()
        flash('Payment Mode added successfully')
        return redirect(url_for('user', user_id=current_user.id))
    return render_template("payment_method_form.html", form=form)


# ---End of Demo Functions---


@login_required
@app.route('/user-profile/<int:user_id>')
def user(user_id):
    user = User.query.filter_by(id=user_id).first_or_404()
    return render_template('user.html', user=user)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is not None: #and user.check_password(form.password.data)
            login_user(user, form.remember_me.data)
            flash("Logged in successfully as {}.".format(user.name))
            return redirect(request.args.get('next') or url_for('index'))
        flash('Incorrect Email or Password')
    return render_template("login.html", form=form)


@app.route('/logout')
def logout():
    logout_user()
    print("You have successfully logged out.")
    return redirect(url_for('index'))


@app.route("/signup", methods=["GET", "POST"])
def signup():
    form = SignupForm()
    if form.validate_on_submit():
        user = User(name=form.name.data, email=form.email.data, mobile_no=form.mobile_no.data,
                    password=form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Welcome! Please Log In~')
        return redirect(url_for('login'))
    return render_template("signup_1.html", form=form, title="Sign Up :)")


@app.route('/edit/<int:user_id>', methods=["GET", "POST"])
@login_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    form = EditUserForm(obj=user)
    if form.validate_on_submit():
        form.populate_obj(user)
        db.session.commit()
        flash("Updated your profile successfully!")
        return redirect(url_for('user', user_id=current_user.id))
    return render_template('signup_1.html', form=form, title="Edit Profile")


# Error Handling Views

@app.errorhandler(401)
def token_error(e):
    return render_template('401.html'), 401


@app.errorhandler(403)
def forbidden(e):
    return render_template('403.html'), 403


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500


if __name__ == '__main__':
    app.run(debug=True)