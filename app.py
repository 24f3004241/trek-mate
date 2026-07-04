from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from datetime import date, datetime

app = Flask(__name__)

app.config['SECRET_KEY'] = 'trek_mate_super_secret_key_123'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///trekmate.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class User(db.Model):
    __tablename__ = 'trekmate_user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(60), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(10), nullable=False, default='trekker')  # 'trekker' or 'staff'

    full_name = db.Column(db.String(120))
    phone_number = db.Column(db.String(20), default="")
    gender = db.Column(db.String(10))
    date_of_birth = db.Column(db.Date)
    city = db.Column(db.String(50))
    state = db.Column(db.String(50))
    bio = db.Column(db.Text, default="")

    staff_profile = db.relationship('StaffProfile', backref='user', uselist=False)
    bookings = db.relationship('Booking', backref='user', lazy=True)

class StaffProfile(db.Model):
    __tablename__ = 'trekmate_staff'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('trekmate_user.id'), nullable=False)
    contact_details = db.Column(db.String(100))
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
    available_slots = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(15), nullable=False, default='upcoming')
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)

    staff_id = db.Column(db.Integer, db.ForeignKey('trekmate_staff.id'), nullable=False)
    
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

    admin_exists = User.query.filter_by(role='admin').first()
    if admin_exists == None:
        sec_pass = generate_password_hash("admin123")
        default_admin = User(username="admin", email="admin@trekmate.com", password=sec_pass, role="admin")
        db.session.add(default_admin)
        db.session.commit()
        print("Default admin user created!")

@app.route('/')
def home():
    return redirect('/login')

@app.route("/register", methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        #  Extract form data
        u_name = request.form.get('username')
        u_email = request.form.get('email')
        u_pass = request.form.get('password')
        u_confirm_pass = request.form.get('confirm_password')
        u_role = request.form.get('role')

        #  Validation: Check if username already exists
        check_user = User.query.filter_by(username=u_name).first()
        if check_user != None:
            flash("Username already exists. Please choose a different username.", "error")
            return redirect(url_for('register'))

        #  Validation: Check if passwords match
        if u_pass != u_confirm_pass:
            flash("Passwords do not match. Please try again.", "error")
            return redirect(url_for('register'))
        
        check_email = User.query.filter_by(email=u_email).first()
        if check_email != None:
            flash("Email already registered. Please use a different email.", "error")
            return redirect(url_for('register'))

        #  Password hashing
        sec_password = generate_password_hash(u_pass)

        #  Create new user and save to database
        new_user = User(username=u_name, email=u_email, password=sec_password, role=u_role)
        db.session.add(new_user)
        db.session.commit()

        #  If the user is a staff, create a StaffProfile entry
        if u_role == 'staff':
            new_staff_profile = StaffProfile(user_id=new_user.id)
            db.session.add(new_staff_profile)
            db.session.commit()

        flash("Registration successful!! You can log in now.", "success")
        return redirect(url_for('login'))

    # If GET request, render the registration form
    return render_template("register.html")

@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        input_name = request.form.get('username')
        input_pass = request.form.get('password')

        #  Fetch user from database based on username
        user = User.query.filter_by(username=input_name).first()

        #  Check if user exists and password is correct
        if user and check_password_hash(user.password, input_pass):
            # Save user info in session for later use
            session['user_id'] = user.id
            session['role'] = user.role
            
            # Redirect to dashboard based on user role
            if user.role == 'admin':
                return "Welcome Admin! (Admin Dashboard - Manage Users, Treks, Bookings)"
            elif user.role == 'staff':
                return "Welcome Staff! (Staff Dashboard - Manage Assigned Treks)"
            else:
                return "Welcome Trekker! (User Dashboard - View Available Treks, Bookings)"
        else:
            flash("Invalid username or password. Please try again.", "error")
            return redirect(url_for('login'))

    return render_template("login.html")

# Trekker Dashboard route
@app.route("/trekker_dashboard")
def trekker_dashboard():
    # Security check: 
    if  session.get('user_id') == None or session.get('role') != 'trekker':
        flash("Please log in to access the trekker dashboard.", "error")
        return redirect(url_for('login'))
    
    return render_template("trekker_dash.html")

# Logout route to clear session and redirect to login
@app.route("/logout")
def logout():
    session.clear() # Clear all session data
    flash("You have been logged out successfully.", "success")
    return redirect(url_for('login')) # Redirect to login page after logout


if __name__ == '__main__':
    app.run(debug=True)
