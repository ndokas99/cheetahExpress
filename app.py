from flask import Flask, render_template, request, flash, redirect
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError, OperationalError
from os import path

app = Flask(__name__)
settings = {
    "SECRET_KEY": 'HGJR7489GJF93U5N577G',
    "SQLALCHEMY_DATABASE_URI": 'sqlite:///database.db',
    "SQLALCHEMY_TRACK_MODIFICATIONS": False,
}
app.config.update(settings)
db = SQLAlchemy(app)


class CargoDetails(db.Model):
    trackNumber = db.Column(db.Text, primary_key=True)
    nameOfSender = db.Column(db.Text, nullable=False)
    nameOfReceiver = db.Column(db.Text, nullable=False)
    weight = db.Column(db.Text, nullable=False)
    dimensions = db.Column(db.Text, nullable=False)
    costOfShipment = db.Column(db.Text, nullable=False)
    freightCost = db.Column(db.Text, nullable=False)
    dutyCost = db.Column(db.Text, nullable=False)
    vatCost = db.Column(db.Text, nullable=False)
    control = db.Column(db.Text, nullable=False)


@app.route('/')
def track():
    return render_template('index.html')


@app.route('/result', methods=['POST'])
def result():
    trackingNumber = request.form['trackingNumber']
    order = CargoDetails.query.filter_by(trackNumber=trackingNumber).first()
    if order:
        results = {
            'Name of Sender': order.nameOfSender,
            'Name of Receiver': order.nameOfReceiver,
            'Weight': order.weight,
            'Dimensions': order.dimensions,
            'Cost of Equipment': order.costOfShipment,
            'Freight Cost': order.freightCost,
            'Duty': order.dutyCost,
            'VAT': order.vatCost,
            'Control': order.control
        }
        return render_template('results.html', trackingNumber=trackingNumber, results=results)
    else:
        flash("Tracking number not found", category="failure")
        return redirect('/')


@app.route('/login')
def login():
    return render_template('login.html')


@app.route("/create", methods=['POST'])
def create():
    if request.form['username'] == 'admin':
        if request.form['password'] == 'admin101':
            return render_template('create.html')
    flash("Invalid credentials", category="failure")
    return redirect('/login')


@app.route("/createOrder", methods=['POST'])
def create_order():
    data = request.form
    order = CargoDetails(
        trackNumber=data['tno'],
        nameOfSender=data['nos'],
        nameOfReceiver=data['nor'],
        weight=data['wgt'],
        dimensions=data['dims'],
        costOfShipment=data['coe'],
        freightCost=data['fcost'],
        dutyCost=data['duty'],
        vatCost=data['vat'],
        control=data['ctrl']
    )
    db.session.add(order)
    db.session.commit()

    flash("Order created successfully", category="success")
    return render_template('create.html')


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
    app.run('0.0.0.0')
