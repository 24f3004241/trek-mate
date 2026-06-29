from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from datetime import date, datetime
app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///trekmate.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class User(db.Model):
    __tablename__ = 'trekmate_user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(60), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), default="")
    role = db.Column(db.String(10), nullable=False, default='user')
    bio = db.Column(db.Text, default="")

    staff_profile = db.relationship('StaffProfile', backref='user', uselist=False)
    bookings = db.relationship('Booking', backref='user', lazy=True)

class StaffProfile(db.Model):
    __tablename__ = 'trekmate_staff_profile'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('trekmate_user.id'), nullable=False)
    contact_details = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(15), default='pending')
    
    # Assigned Treks
    treks = db.relationship('Trek', backref='staff', lazy=True)

class Trek(db.Model):
    __tablename__ = 'trekmate_treks'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    duration = db.Column(db.Integer, nullable=False) 
    difficulty = db.Column(db.String(20), nullable=False)
    slots = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(15), nullable=False, default='upcoming')
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)

    staff_id = db.Column(db.Integer, db.ForeignKey('trekmate_staff_profile.id'), nullable=False)
    
    bookings = db.relationship('Booking', backref='trek', lazy=True)


class Booking(db.Model):
    __tablename__ = 'trekmate_booking'
    id = db.Column(db.Integer, primary_key=True)
    trek_id = db.Column(db.Integer, db.ForeignKey('trekmate_treks.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('trekmate_user.id'), nullable=False)
    booking_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(15), nullable=False, default='Booked')  # Status can be 'Booked', 'Cancelled', or 'Completed'

with app.app_context():
    db.create_all()

@app.route('/')
def home():
    return "Welcome to TrekMate!"

if __name__ == '__main__':
    app.run(debug=True)
