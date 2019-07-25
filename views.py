from flask import render_template, url_for, flash, redirect, request
from flask_login import login_user, logout_user, current_user, login_required

from settings import app, login_manager
from app import *
from api import * #needed or not?
from model import User, Book, db
from auth_forms import LoginForm, SignupForm, EditUserForm, AddressForm, PaymentForm

import json



#DEMO FUNCTIONS

@app.route('/')
def index():
    # with open('books_inventory.json') as books_json:
    #    books = json.load(books_json)
    r = requests.get('http:/localhost:5000/api/inventory')
    books = json.loads(r.text)
    return render_template('index.html', books=books)


@app.route('/order-memo')
def orderMemo():
    return render_template("order_memo.html")

@app.route('/confirm-order-demo#')
def place_order_demo():
    return render_template("confirm_order.html")

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
        return redirect(url_for('index'))
    return render_template("address_form.html", form=form)

@app.route('/book/<title>')
def view_book(title):
    with open('books_inventory.json') as books_json:
        books_list = json.load(books_json)
        for book in books_list:
            if book['title'] == title:
                book = book
                break
    return render_template("view_book.html", book=book)


@app.route('/add-payment-mode')
def obtain_paymentmode():
    form = PaymentForm()
    if form.validate_on_submit():
        user = current_user
        user.ModeOfPayment = form.ModeOfPayment.data
        db.session.add(user)
        db.session.commit()
        flash('Payment Mode added successfully')
        return redirect(url_for('index'))
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
