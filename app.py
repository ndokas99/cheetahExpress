from flask import Flask, render_template, redirect, request, session, flash, \
    make_response, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError, OperationalError
from werkzeug.security import generate_password_hash, check_password_hash
from os import path
from geopy.exc import GeocoderUnavailable
from geopy.geocoders import Nominatim
from geopy.distance import geodesic as GD


app = Flask(__name__)
settings = {
    "SECRET_KEY": 'H211233JG88DJRTI5PP',
    "SQLALCHEMY_DATABASE_URI": 'sqlite:///database.db',
    "SQLALCHEMY_TRACK_MODIFICATIONS": False,
}
app.config.update(settings)
db = SQLAlchemy(app)
geolocator = Nominatim(user_agent=__name__)


class Database(db.Model):
    studentReg = db.Column(db.Text, primary_key=True)
    studentId = db.Column(db.Text, unique=True, nullable=False)
    studentPassword = db.Column(db.Text, nullable=False)
    studentName = db.Column(db.Text, nullable=False)
    studentSurname = db.Column(db.Text, nullable=False)
    studentAddress = db.Column(db.Text, nullable=False)
    studentEmail = db.Column(db.Text, nullable=False)
    studentCity = db.Column(db.Text, nullable=False)
    studentBlacklisted = db.Column(db.Integer, nullable=False)
    studentNumber = db.Column(db.Text, nullable=False)
    studentGrade = db.Column(db.Text, nullable=False)
    studentAcmStatus = db.Column(db.Integer, nullable=False)
    studentProgram = db.Column(db.Text, nullable=False)
    studentDistance = db.Column(db.Float, nullable=False)


class Accommodation(db.Model):
    reg = db.Column(db.Text, primary_key=True)
    hostel = db.Column(db.Text, nullable=False)
    room = db.Column(db.Text, nullable=False)
    loc = db.Column(db.Text, nullable=False)
    status = db.Column(db.Text, nullable=False)


@app.route('/')
def login():
    session["rights"] = "non-elevated"
    session["state"] = "logged out"
    return render_template("login.html")


@app.route('/dashboard', methods=['POST'])
def dashboard():
    if request.method == "POST":
        reg = request.form['regnumber'].upper()
        password = request.form['password']

        if reg == "ADMIN":
            adminPass = "sha1$8uTuf2zM485ON06y$c8d3b579d9b05fbddc83b94a11e1a099fa18f6fb"
            if check_password_hash(adminPass, password):
                session["rights"] = "elevated"
                return redirect("_admin")

        std = Database.query.filter_by(studentReg=reg).first()
        if std:
            if check_password_hash(std.studentPassword, password):
                session['state'] = "logged in"
                session['user'] = reg
                return redirect("/user_dashboard")

    flash("Account does not exist", category="error")
    return redirect("/")


@app.route('/user_dashboard')
def user_dash():
    if session["state"] == "logged out":
        flash("You are currently logged out", category="error")
        return redirect("/")
    std = Database.query.filter_by(studentReg=session['user']).first()
    return render_template("user_dashboard.html", student=std)


@app.route('/accommodation')
def accommodation():
    if session["state"] == "logged out":
        flash("You are currently logged out", category="error")
        return redirect("/")
    acc = Accommodation.query.filter_by(reg=session['user']).first()
    return render_template("accommodation_status.html", acc=acc)


@app.route("/apply", methods=["POST"])
def apply():
    std = Database.query.filter_by(studentReg=session['user']).first()
    acc = Accommodation.query.filter_by(reg=session['user']).first()
    if std.studentBlacklisted == 0:
        std.studentAcmStatus = 1
        acc.status = "Pending"
        db.session.commit()
        return make_response(jsonify({"response": "yes"}))
    else:
        std.studentAcmStatus = 0
        acc.status = "Rejected"
        db.session.commit()
        return make_response(jsonify({"response": "no"}))


@app.route("/_admin")
def admin():
    if session["rights"] != "elevated":
        flash("You do not have permission to access this page", category="error")
        return redirect("/")
    else:
        return render_template("manage_students.html")


@app.route("/query", methods=["POST"])
def query():
    if session["rights"] != "elevated":
        flash("You do not have permission to access this page", category="error")
        return redirect("/")
    reg = request.get_json()["regno"].upper()
    std = Database.query.filter_by(studentReg=reg).first()

    if std:
        if std.studentBlacklisted == 0:
            blackls = "No"
        else:
            blackls = "Yes"

        response = {"result": 1,
                    "reg": std.studentReg,
                    "name": std.studentName,
                    "surname": std.studentSurname,
                    "prog": std.studentProgram,
                    "blackls": blackls}
    else:
        response = {"result": "0"}
    return make_response(jsonify(response))


@app.route("/blacklist", methods=["POST"])
def blacklist():
    if session["rights"] != "elevated":
        flash("You do not have permission to access this page", category="error")
        return redirect("/")
    reg = request.get_json()["regno"].upper()
    std = Database.query.filter_by(studentReg=reg).first()
    if std:
        std.studentBlacklisted = 1
        db.session.commit()
        response = {"result": 1}
    else:
        response = {"result": 0}
    return make_response(jsonify(response))


@app.route("/register")
def register():
    if session["rights"] != "elevated":
        flash("You do not have permission to access this page", category="error")
        return redirect("/")
    return render_template("register_student.html")


@app.route("/create", methods=["POST"])
def create():
    if session["rights"] != "elevated":
        flash("You do not have permission to access this page", category="error")
        return redirect("/")

    if request.method == "POST":
        data = request.form

        try:
            address = geolocator.geocode("Mount Pleasant, Harare")
            UzCoord = (address.latitude, address.longitude)
            loc = geolocator.geocode(data["city"])
            if not loc:
                flash("City not located, try again!", category="error")
                return redirect("/register")
        except GeocoderUnavailable:
            flash("Network error, Try again!", category="error")
            return redirect("/register")

        dist = GD(UzCoord, (loc.latitude, loc.longitude)).kilometers

        std = Database(
            studentReg=data['reg'].upper(),
            studentPassword=generate_password_hash(data['reg'].upper(), method="sha1"),
            studentId=data['natId'],
            studentName=data['name'],
            studentSurname=data['sname'],
            studentAddress=data['addr'],
            studentEmail=data['email'],
            studentCity=data['city'],
            studentBlacklisted=0,
            studentNumber=data['num'],
            studentGrade=data['level'],
            studentAcmStatus=0,
            studentProgram=data['prog'],
            studentDistance=dist
        )
        acc = Accommodation(
            reg=data['reg'].upper(),
            loc="Null",
            room="Null",
            hostel="Null",
            status="Unapplied"
        )
        db.session.add(std)
        db.session.add(acc)
        db.session.commit()

    flash("Registration complete", category="success")
    return redirect("/_admin")


@app.route("/allocate", methods=["POST"])
def allocate():
    applicants = []
    for (reg_number, dist, blacklisted, acm) in Database.query.with_entities(
            Database.studentReg, Database.studentDistance, Database.studentBlacklisted, Database.studentAcmStatus
    ):
        if blacklisted == 0:
            if acm == 1:
                applicants.append((reg_number, dist))

    applicants.sort(key=lambda x: x[1])

    for (num, students) in enumerate(applicants[:10]):
        reg = students[0]
        std = Database.query.filter_by(studentReg=reg).first()
        acc = Accommodation.query.filter_by(reg=reg).first()
        std.studentAcmStatus = 2
        acc.hostel = "Manfred"
        acc.room = f"R{num+1}"
        acc.loc = "Main Campus"
        acc.status = "Allocated"
        db.session.commit()

    return make_response(jsonify({}))


def create_database():
    if not path.exists("/instance/database.db"):
        try:
            db.create_all()
        except IntegrityError:
            pass
        except OperationalError:
            pass


with app.app_context():
    create_database()

if __name__ == '__main__':
    app.run(port=5001, debug=True)
