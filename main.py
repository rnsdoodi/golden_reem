from flask import Flask, render_template, request, url_for, redirect, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, DateField
from wtforms.validators import DataRequired, length
import smtplib
# from wtforms.fields.html5 import DateField
import os

# Flask App
app = Flask(__name__)

OWN_EMAIL = "goldenreem2022@gmail.com"
ALAA_EMAIL = "goldenreem2022@gmail.com"
OWN_PASSWORD = "tesngdnzlskwmazd"

all_selections = []

app.config['SECRET_KEY'] = 'any secret key'
# CREATE DATABASE
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///customers.db"

# Optional: But it will silence the deprecation warning in the console.
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Bootstrap App
Bootstrap(app)

# Login Manager
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(Admin_id):
    return Admins.query.get(int(Admin_id))


# Creating Table in the DB to Add New Customer Request
class Customers(db.Model):
    __tablename__ = "customers"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), nullable=False)
    contact_No = db.Column(db.String(250), nullable=False)
    address = db.Column(db.String(1000), nullable=False)
    product_code = db.Column(db.String(250), nullable=False)
    quantity = db.Column(db.String(10), nullable=False)
    status = db.Column(db.String(500), nullable=False)
    notes = db.Column(db.String(1000), nullable=True)


# CREATE TABLE IN DB To save users login Data (Hashed & Salted)
class Admins(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(1000))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))


db.create_all()


#  Customer selection  Flask Form
class CustomerSelection(FlaskForm):
    name = StringField('الاسم ثلاثي  ', validators=[DataRequired(), length(max=100)])
    contact_No = StringField('رقم الجوال', validators=[DataRequired()], description='05xxxxxxxx : مثال')
    address = StringField('العنوان', validators=[DataRequired(), length(max=500)], description='اسم المدينة - اسم '
                                                                                               'الحي - اسم الشارع')
    product_code = StringField('رمز المنتج المطلوب', validators=[DataRequired()],
                               description='رمز المنتج موجود باللون الأحمر''على كل منتج')
    quantity = StringField('العدد', validators=[DataRequired(), length(max=500)], description='العدد المطلوب')
    submit = SubmitField(' أكـمـل عمـلـيـة الشـراء')


# Edit Form Follow up Flask Form
class Follow(FlaskForm):
    status = SelectField('حالة الطلب', choices=["تم استلام الطلب والتواصل مع العميل", "جاري تجهيز الطلب", "تم تجهيز الطلب",
                                                "جاري توصيل الطلب للعميل", "تم توصيل الطلب للعميل", "تم إغلاق الطلب",
                                                "تم إلغاء الطلب"])
    notes = StringField('ملاحظات', validators=[length(max=1000)], description='هل توجد اي ملاحظات على الطلب ؟')
    submit = SubmitField(' تـــحـديــث')


################################################################


@app.route('/')
def home():
    return render_template('index.html')


@app.route("/customer_selection", methods=["GET", "POST"])
def customer_selection():
    form = CustomerSelection()
    if form.validate_on_submit():
        new_selection = Customers(
            name=form.name.data,
            contact_No=form.contact_No.data,
            address=form.address.data,
            product_code=form.product_code.data,
            quantity=form.quantity.data
        )
        db.session.add(new_selection)
        db.session.commit()
        all_selections.append(new_selection)
        flash("تم إرسال الطلب بنجاح ✅ وجاري العمل لتجهيز طلبكم. سوف نقوم بالتواصل معكم في اقرب فرصة !!")
        return redirect(url_for('customer_selection'))
    return render_template("select.html", form=form)


@app.route("/contact", methods=["GET", "POST"])
def get_data():
    if request.method == "POST":
        name = request.form["full-name"]
        email = request.form["email"]
        phone = request.form["phone"]
        message = request.form["message"]

        send_email(name, email, phone, message)

        return redirect(url_for('get_data', msg_sent=False))
    return render_template("index.html", msg_sent=True)


def send_email(name, email, phone, message):
    email_message = f"Subject:New Message\n\nName: {name}\nEmail: {email}\nPhone: {phone}\nMessage:{message}."
    with smtplib.SMTP("smtp.gmail.com") as connection:
        connection.starttls()
        connection.login(OWN_EMAIL, OWN_PASSWORD)
        connection.sendmail(OWN_EMAIL, ALAA_EMAIL, email_message.encode("UTF-8"))


@app.route("/Report")
def Report():
    new_selection = Customers.query.all()
    return render_template("Report.html", selections=new_selection, name=current_user.name, logged_in=True)


@app.route("/follow")
def follow():
    new_selection = Customers.query.all()
    return render_template("follow.html", selections=new_selection, name=current_user.name, logged_in=True)


@app.route("/request_edit", methods=["GET", "POST"])
def request_edit():
    form = Follow()
    selection_id = request.args.get("id")
    updated_selection = Customers.query.get(selection_id)
    if form.validate_on_submit():
        updated_selection.status = form.status.data
        updated_selection.notes = form.notes.data

        db.session.commit()
        flash("تم تعديل حالة الطلب بنجاح✔")
        return redirect(url_for('request_edit'))
    return render_template("request_edit.html", form=form, selection=updated_selection)


@app.route("/delete")
def delete():
    selection_id = request.args.get("id")
    selection_to_delete = Customers.query.get(selection_id)
    db.session.delete(selection_to_delete)
    db.session.commit()
    flash("تم حذف بيانات العميل بنجاح✔")
    return redirect(url_for('follow'))


#######################################################################################################################
# Authentication Part for (Admins) :-


# @app.route("/")
# def landing():
#     return render_template("admin.html")

@app.route('/admins')
def sign():
    return render_template("main.html")


@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == "POST":

        if Admins.query.filter_by(email=request.form.get('email')).first():
            # User already exists
            flash("You've already signed up with that email, log in instead!")
            return redirect(url_for('login'))

        hash_and_salted_password = generate_password_hash(
            request.form.get('password'),
            method='pbkdf2:sha256',
            salt_length=8
        )
        new_admin = Admins(
            email=request.form.get('email'),
            name=request.form.get('name'),
            password=hash_and_salted_password,
        )
        db.session.add(new_admin)
        db.session.commit()
        login_user(new_admin)
        flash("تم التسجيل بنجاح, رجاءا قم بالعودة الى صفحة الدخول")
        return redirect(url_for("register"))

    return render_template("register.html", logged_in=current_user.is_authenticated)


@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get('email')
        password = request.form.get('password')

        admin = Admins.query.filter_by(email=email).first()
        # Email doesn't exist or password incorrect.
        if not admin:
            flash("That email does not exist, please try again.")
            return redirect(url_for('login'))
        elif not check_password_hash(admin.password, password):
            flash('Password incorrect, please try again.')
            return redirect(url_for('login'))
        else:
            login_user(admin)
            return redirect(url_for('admin'))

    return render_template("login.html", logged_in=current_user.is_authenticated)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('sign'))


@app.route('/admin')
@login_required
def admin():
    print(current_user.name)
    all_selections = Customers.query.all()
    return render_template("admin.html", selections=all_selections, logged_in=True, name=current_user.name)


##########################################################################


if __name__ == "__main__":
    app.run(debug=True)
