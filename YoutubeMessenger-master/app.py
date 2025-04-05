from flask import Flask, render_template, url_for, redirect, flash, request
from flask_sqlalchemy import SQLAlchemy
from forms import UserForm, LoginForm, UpdateForm, ChatForm, MailForm
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_migrate import Migrate
from flask_login import LoginManager, UserMixin, current_user, login_user, logout_user, login_required
from flask_mail import Mail, Message
import os

app = Flask(__name__)
app.debug = True
app.config['SECRET_KEY'] = "e0ra5894rhbeivki8r"
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///site.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Extensions
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)

app.config['MAIL_SERVER'] = 'smtp.googlemail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'gritsenko.cooperation@gmail.com'  # замените на вашу почту
app.config['MAIL_DEFAULT_SENDER'] = 'gritsenko.cooperation@gmail.com'  # и это тоже
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASS', 'Your password')  # замените или задайте переменную окружения
mail = Mail(app)


@login_manager.user_loader
def load_user(id):
    return db.session.query(UserModel).get(id)


# === ROUTES ===

@app.route("/")
def MainForAnon():
    if current_user.is_authenticated:
        return redirect(url_for("MainPage"))
    return render_template("main_anon.html")


@app.route("/info_user/<int:id>")
@login_required
def infoUserId(id):
    user = db.session.query(UserModel).get(id)
    created = user.created_on.strftime('%Y-%m-%d %H:%M:%S')
    date, time = created.split(' ')
    y, m, d = date.split('-')
    h, mi, s = time.split(':')

    return render_template("info_user_id.html", user=user,
                           date={'year': y, 'month': m, 'day': d},
                           time={'hour': h, 'minute': mi, 'second': s})


@app.route("/support/", methods=['POST', 'GET'])
def Support():
    form = MailForm()
    if form.validate_on_submit():
        msg = Message("Grits Messenger Support", recipients=["gritsenkoevg@yandex.kz"])
        msg.body = f"""Пользователь ({form.sender.data}) отправил сообщение:\n\n{form.message.data}"""
        mail.send(msg)
        flash("Сообщение успешно отправлено!")
    return render_template("support.html", form=form)


@app.route("/info_users/")
def infoUser():
    All = db.session.query(UserModel).all()
    return render_template("info_user.html", all=All)


@app.route("/main/", methods=['GET', 'POST'])
@login_required
def MainPage():
    AllUsers = db.session.query(UserModel).all()
    return render_template("main_page.html", all=AllUsers)


@app.route("/update_acc/<int:id>/", methods=["POST", "GET"])
@login_required
def UpdateAcc(id):
    form = UpdateForm()
    this_user = db.session.query(UserModel).get(id)
    All = db.session.query(UserModel.nick).all()
    all_nicks = [j for i in All for j in i if j != current_user.nick]

    if form.validate_on_submit() and current_user.id == id:
        new_nick = form.upd_nick.data
        new_pass = form.upd_password.data

        if new_nick and new_nick not in all_nicks:
            if 4 <= len(new_nick) <= 16:
                this_user.nick = new_nick
                flash("Ник обновлен")
            else:
                flash("Ник должен быть от 4 до 16 символов")

        elif new_nick:
            flash("Пользователь с таким ником уже существует")

        if new_pass:
            if 5 <= len(new_pass) <= 50:
                this_user.set_password(new_pass)
                flash("Пароль обновлен")
            else:
                flash("Пароль должен быть от 5 до 50 символов")

        db.session.commit()
    elif current_user.id != id:
        flash("Нельзя изменять чужие данные!")

    return render_template("upd_acc.html", form=form)


@app.route("/delete_acc/<int:id>/")
@login_required
def DeleteAcc(id):
    this_user = db.session.query(UserModel).get(id)
    if current_user.id == id:
        try:
            db.session.delete(this_user)
            db.session.commit()
            flash("Аккаунт удален")
        except:
            flash("Ошибка удаления аккаунта")
    else:
        flash("Нельзя удалить чужой аккаунт!")
    return render_template("del_acc.html")


@app.route("/chat/", methods=["GET", "POST"])
@login_required
def Chat():
    form = ChatForm()
    data = db.session.query(MessagesModel).order_by(-MessagesModel.id_message)
    TimeData = [{'id': m.id_message,
                 'timeHour': m.send_to_str.split()[1].split(".")[0],
                 'timeDay': m.send_to_str.split()[0]} for m in data]

    if form.validate_on_submit():
        msg = MessagesModel(message=form.message.data, user_nick=current_user.nick)
        db.session.add(msg)
        db.session.commit()
        return redirect(url_for("Chat"))

    return render_template("chat.html", form=form, data=data, TimeData=TimeData)


@app.route("/registration/", methods=['POST', 'GET'])
def Reg():
    if current_user.is_authenticated:
        return redirect(url_for("MainPage"))

    form = UserForm()
    all_nicks = [j.lower() for i in db.session.query(UserModel.nick).all() for j in i]

    if form.validate_on_submit():
        nick = form.nick.data
        password = form.password.data

        if nick.lower() not in all_nicks:
            new_user = UserModel(nick=nick)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for('Login'))
        else:
            flash("Аккаунт уже существует")
            return redirect(url_for('Login'))

    return render_template("registration.html", form=form)


@app.route("/login/", methods=["POST", "GET"])
def Login():
    form = LoginForm()

    if current_user.is_authenticated:
        return redirect(url_for("MainPage"))

    all_nicks = [j.lower() for i in db.session.query(UserModel.nick).all() for j in i]

    if form.validate_on_submit():
        nick = form.check_nick.data.lower()
        if nick in all_nicks:
            user = db.session.query(UserModel).filter_by(nick=form.check_nick.data).first()
            if user and user.check_password(form.check_pass.data):
                login_user(user)
                return redirect(url_for("MainPage"))
        else:
            flash("Пользователь не зарегистрирован!")

    return render_template("login.html", form=form)


@app.route("/logout_user/")
def LogOut():
    logout_user()
    return redirect("/login")


@app.errorhandler(401)
def NotAuthorised(error):
    return render_template("NotAuthorised.html")


@app.errorhandler(404)
def NotFound(error):
    return render_template("error404.html")


# === MODELS ===

class UserModel(db.Model, UserMixin):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    nick = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(200), nullable=False)
    created_on = db.Column(db.DateTime(), default=datetime.now)
    admin = db.Column(db.Boolean, default=False)
    admin_level = db.Column(db.Integer, default=0)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def __repr__(self):
        return f"<id:{self.id}>, <nick:{self.nick}>"


class MessagesModel(db.Model):
    __tablename__ = 'messages'
    id_message = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.Text)
    user_nick = db.Column(db.String(100))
    send_to = db.Column(db.DateTime, default=datetime.utcnow)
    send_to_str = db.Column(db.String(100), default=datetime.utcnow)

    def __repr__(self):
        return f'{self.id_message}, {self.message}'


# === RUN ===

if __name__ == "__main__":
    app.run(debug=True)
