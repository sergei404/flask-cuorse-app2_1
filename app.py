import flask_migrate
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, render_template, request
from flask_wtf import CSRFProtect
from form import BookingForm, RequestForm, SortTeacherForm


from utils import getGoals, getFilterTeachers, getTeacherGoals, weekdays, \
    getTeacher, practice


app: Flask = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tutors.db'
app.config['SQLALCHEMY_ECHO'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


db = SQLAlchemy(app)
migrate = flask_migrate.Migrate(app, db)
csrf = CSRFProtect(app)
SECRET_KEY = 'zxscdfg8uygfeplmzsw2'
app.config["SECRET_KEY"] = SECRET_KEY


class Tutor(db.Model):
    __tablename__ = 'tutors'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    about = db.Column(db.String)
    rating = db.Column(db.Float)
    picture = db.Column(db.String)
    price = db.Column(db.Integer)
    goals = db.Column(db.String)
    free = db.Column(db.String)
    reservations = db.relationship("Reservation", back_populates="tutor")


class Reservation(db.Model):
    __tablename__ = 'reservations'

    id = db.Column(db.Integer, primary_key=True)
    client_name = db.Column(db.String)
    client_phone = db.Column(db.String)
    class_day = db.Column(db.String)
    time = db.Column(db.String)
    tutor_id = db.Column(db.Integer, db.ForeignKey("tutors.id"))
    tutor = db.relationship("Tutor", back_populates="reservations")


class Selection(db.Model):
    __tablename__ = 'selections'

    id = db.Column(db.Integer, primary_key=True)
    time = db.Column(db.String)
    goal = db.Column(db.String)
    phone = db.Column(db.String)
    name = db.Column(db.String)


@app.route('/')
def render_main():
    # seed()
    teachers = db.session.query(Tutor).limit(3).all()
    return render_template('index.html', goals=getGoals(),
                           teachers=teachers)


@app.route('/all/', methods=["GET", "POST"])
def render_all():
    form = SortTeacherForm()
    teachers_sort = db.session.query(Tutor).all()
    if request.method == "POST":
        select = form.select.data
        if select == 'rating':
            teachers_sort.sort(key=lambda x: x["rating"], reverse=True)
        elif select == 'price_up':
            teachers_sort.sort(key=lambda x: x["price"], reverse=True)
        elif select == 'price_down':
            teachers_sort.sort(key=lambda x: x["price"])
        return render_template('all.html', form=form, teachers=teachers_sort)

    return render_template('all.html', teachers=teachers_sort, form=form)


@app.route('/request/')
def render_request():
    form = RequestForm()
    return render_template('request.html', form=form)


@app.route('/goal/<goal>/')
def render_goal(goal):
    teachers = db.session.query(Tutor).all()
    if not getGoals()[goal]:
        return render_not_found(
            f"{goal} - такой цели обучения нет.")

    return render_template('goal.html',
                           teachers=getFilterTeachers(teachers, goal),
                           goal=getGoals()[goal])


@app.route('/profiles/<int:teacher_id>/')
def render_teacher_profile(teacher_id):
    teachers = db.session.query(Tutor).all()
    teacher = getTeacher(teachers, teacher_id)
    goals = getTeacherGoals(getGoals(), teacher['goals'])
    if not teacher:
        return render_not_found(f"К сожалению, такого преподавателя нет")

    return render_template('profile.html', teacher=teacher, goals=goals,
                           weekdays=weekdays)


@app.route('/request_done/', methods=["GET", "POST"])
def render_request_done():
    form = RequestForm()
    if request.method == "POST" and form.validate_on_submit():
        selection = Selection(
            time=practice[form.practice_time.data],
            goal=form.goal.data,
            phone=form.phone.data,
            name=form.name.data
        )

        db.session.add(selection)
        db.session.commit()

        return render_template(
            "request_done.html", user=selection)

    return render_not_found("Для начала подайте заявку на подбор.")


@app.route('/booking/<int:id>/<day>/<time>/')
def render_booking(id, day, time):
    teachers = db.session.query(Tutor).all()
    form = BookingForm()
    day_ru = weekdays[day[:3]][0]
    teacher = getTeacher(teachers, id)
    if not teacher:
        return render_not_found(
            f"К сожалению, такого преподавателя не существует."
        )

    form.class_day.data = day
    form.time.data = time
    form.tutor_id.data = id
    return render_template('booking.html',
                           teacher=teacher, day=day_ru,
                           time=time, form=form)


@app.route('/booking_done/', methods=["GET", "POST"])
def render_booking_done():
    form = BookingForm()
    teachers = db.session.query(Tutor).all()
    if request.method == "POST" and form.validate_on_submit():
        selection = Reservation(
            client_name=form.name.data,
            client_phone=form.phone.data,
            class_day=form.class_day.data,
            time=form.time.data,
            tutor=getTeacher(teachers, form.tutor_id.data)
        )

        db.session.add_all(selection)
        db.session.commit()

    return render_template('booking_done.html', selection=selection)


@app.errorhandler(404)
def render_not_found(message="По вашему запросу ничего не найдено"):
    return render_template("error.html", message=message), 404


if __name__ == '__main__':
    app.run(debug=True)
