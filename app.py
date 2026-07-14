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
    role = db.Column(db.String(10), nullable=False, default='trekker')
    status = db.Column(db.String(15), default='Active')
    full_name = db.Column(db.String(120))
    phone_number = db.Column(db.String(20), default="")
    gender = db.Column(db.String(10))
    date_of_birth = db.Column(db.Date)
    city = db.Column(db.String(50))
    state = db.Column(db.String(50))
    bio = db.Column(db.Text, default="")

    staff_profile = db.relationship('StaffProfile', backref='user', uselist=False, cascade="all, delete-orphan")
    bookings = db.relationship('Booking', backref='user', lazy=True)

class StaffProfile(db.Model):
    __tablename__ = 'trekmate_staff'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('trekmate_user.id'), nullable=False)
    status = db.Column(db.String(15), default='pending')

    # Assigned Treks
    treks = db.relationship('Trek', backref='staff', lazy=True)

class Trek(db.Model):
    __tablename__ = 'trekmate_treks'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(50), nullable=False)
    country = db.Column(db.String(50), nullable=False, default='India')
    description = db.Column(db.Text, nullable=True) 
    duration = db.Column(db.Integer, nullable=False) 
    difficulty = db.Column(db.String(20), nullable=False)
    available_slots = db.Column(db.Integer, nullable=False)
    requested_slots = db.Column(db.Integer, nullable=True)
    price = db.Column(db.Float, nullable=False, default=0.0)
    status = db.Column(db.String(15), nullable=False, default='Upcoming')
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)

    staff_id = db.Column(db.Integer, db.ForeignKey('trekmate_staff.id'))
    
    bookings = db.relationship('Booking', backref='trek', lazy=True)


class Booking(db.Model):
    __tablename__ = 'trekmate_booking'
    id = db.Column(db.Integer, primary_key=True)
    trek_id = db.Column(db.Integer, db.ForeignKey('trekmate_treks.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('trekmate_user.id'), nullable=False)

    seats_booked = db.Column(db.Integer, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    booking_date = db.Column(db.DateTime, default=datetime.utcnow)

    booking_status = db.Column(db.String(15), default='Confirmed')


with app.app_context():
    db.create_all()

    admin_exists = User.query.filter_by(role='admin').first()
    if admin_exists == None:
        sec_pass = generate_password_hash("admin123")
        default_admin = User(username="admin", email="admin@trekmate.com", password=sec_pass, role="admin")
        db.session.add(default_admin)
        db.session.commit()

# Landing page
@app.route('/')
@app.route('/home')
def home():
    return render_template("home.html")


# Explore/Booking Page Route
@app.route('/explore')
def explore():
    # Get search and filter parameters from URL
    search_query = request.args.get('search', '').strip()
    difficulty_filter = request.args.get('difficulty', '')
    
    # Only show treks that haven't started yet
    query = Trek.query.filter(Trek.start_date >= date.today(), Trek.status == 'Upcoming')
    
    # Search Filter
    if search_query:
        query = query.filter(
            (Trek.name.ilike(f"%{search_query}%")) |
            (Trek.location.ilike(f"%{search_query}%")) |
            (Trek.state.ilike(f"%{search_query}%"))
        )
        
    # Apply Difficulty Filter
    if difficulty_filter:
        query = query.filter(Trek.difficulty == difficulty_filter)
        
    upcoming_treks = query.order_by(Trek.start_date.asc()).all()
    
    return render_template("explore.html", treks=upcoming_treks, search_query=search_query, difficulty_filter=difficulty_filter)

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
                return redirect(url_for('admin_dashboard'))
            elif user.role == 'staff':
                return redirect(url_for('staff_dashboard'))
            else:
                return redirect(url_for('trekker_dashboard'))
        else:
            flash("Invalid username or password. Please try again.", "error")
            return redirect(url_for('login'))

    return render_template("login.html")

# Trekker Dashboard route
@app.route("/trekker_dashboard")
def trekker_dashboard(): 
    if  session.get('user_id') == None or session.get('role') != 'trekker':
        flash("Please log in to access the trekker dashboard.", "warning")
        return redirect(url_for('login'))
    
    # Fetch current user from database
    user = User.query.get(session['user_id'])
   
    return render_template("trekker_dash.html", user=user)

# Edit Profile Route
@app.route("/edit_profile", methods=['GET', 'POST'])
def edit_profile():
    if session.get('user_id') == None:
        flash("Please log in first.", "danger")
        return redirect(url_for('login'))
        
    user = User.query.get(session['user_id'])
    
    if request.method == 'POST':
        user.full_name = request.form.get('full_name')
        user.phone_number = request.form.get('phone_number')
        user.gender = request.form.get('gender')
        
        dob_str = request.form.get('date_of_birth')
        if dob_str:
            user.date_of_birth = datetime.strptime(dob_str, '%Y-%m-%d').date()
            
        user.city = request.form.get('city')
        user.state = request.form.get('state')
        user.bio = request.form.get('bio')
        
        db.session.commit()
        flash("Profile updated successfully!", "success")
        
        # Return to dashboard
        if user.role == 'staff':
            return redirect(url_for('staff_dashboard'))
        return redirect(url_for('trekker_dashboard'))
        
    return render_template("edit_profile.html", user=user)

# Logout route to clear session and redirect to login
@app.route("/logout")
def logout():
    session.clear() # Clear all session data
    flash("You have been logged out successfully.", "success")
    return redirect(url_for('login'))


@app.route("/admin_dashboard")
def admin_dashboard():
    if session.get('user_id') == None or session.get('role') != 'admin':
        flash("Please log in to access the admin dashboard.", "error")
        return redirect(url_for('login'))
    
    # Extract counts but IGNORE Blocked Users, Blacklisted Staff, and Deleted Treks
    total_users = User.query.filter(User.role == 'trekker', User.status != 'Blocked').count()
    total_staff = User.query.filter(User.role == 'staff', User.status != 'Blacklisted').count()
    total_treks = Trek.query.filter(Trek.status != 'Deleted').count()
    
    total_bookings = Booking.query.count()
    
    # Fetch only active treks to display in the admin dashboard table (Hide deleted ones)
    all_treks = Trek.query.filter(Trek.status != 'Deleted').all() 

    # Send the counts and trek list to html template for rendering
    return render_template("admin_dash.html", 
                           t_users=total_users, 
                           t_staff=total_staff, 
                           t_treks=total_treks, 
                           t_bookings=total_bookings,
                           treks=all_treks,
                           today=date.today())
   
@app.route("/admin/add_trek", methods=['GET', 'POST'])
def add_trek():
    # Security Check 
    if session.get('user_id') == None or session.get('role') != 'admin':
        return redirect(url_for('login'))
    
    # Extract all approved staff from the database to show them in the dropdown in the form
    approved_staff = StaffProfile.query.filter_by(status='Approved').all()

    if request.method == 'POST':
        # Extract form data
        t_name = request.form.get('name')
        t_location = request.form.get('location')
        t_state = request.form.get('state')
        t_country = request.form.get('country')
        t_description = request.form.get('description')
        t_diff = request.form.get('difficulty')
        t_duration = request.form.get('duration')
        t_slots = request.form.get('available_slots')
        t_price = request.form.get('price')
        
        
        start_date_str = request.form.get('start_date')
        end_date_str = request.form.get('end_date')
        staff_id = request.form.get('staff_id') or None  # If no staff is selected, it will be None
        # Convert date strings to date objects for comparison
        start_obj = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_obj = datetime.strptime(end_date_str, '%Y-%m-%d').date()

        if end_obj < start_obj:
            flash("End date cannot be before start date!", "danger")
            return redirect(url_for('add_trek'))
        
        if staff_id:
            overlapping_trek = Trek.query.filter(
                Trek.staff_id == staff_id,
                Trek.start_date <= end_obj,
                Trek.end_date >= start_obj,
                Trek.status!='Cancelled',
                Trek.status!='Deleted'
            ).first()
            if overlapping_trek:
                flash("Selected staff is already assigned to another trek during the same period!", "danger")
                return redirect(url_for('add_trek'))

        new_trek = Trek(
            name=t_name, 
            location=t_location,
            state=t_state,
            country=t_country,
            description=t_description,
            difficulty=t_diff,
            duration=int(t_duration), 
            available_slots=int(t_slots), 
            price=float(t_price),
            start_date=start_obj, 
            end_date=end_obj,
            staff_id=staff_id # None if no staff is selected
        )
        db.session.add(new_trek)
        db.session.commit()

        flash("New trek added successfully!", "success")
        return redirect(url_for('manage_treks'))

    # If GET request, render the add trek form with the list of approved staff
    return render_template('add_trek.html', staff_list=approved_staff, today=date.today())



#  Manage Treks
@app.route("/admin/manage_treks")
def manage_treks():
    if session.get('user_id') == None or session.get('role') != 'admin':
        return redirect(url_for('login'))
    
    search_query = request.args.get('search', '').strip()
    query = Trek.query.filter(Trek.status != 'Deleted')
    
    if search_query:
        # Find staff users whose usernames match the search query
        matching_users = User.query.filter(User.username.ilike(f"%{search_query}%")).all()

        # Extract the staff IDs from the matching users and store them in a list
        matching_staff_ids = []
        for u in matching_users:
            if u.staff_profile:
                matching_staff_ids.append(u.staff_profile.id)

        # Now filter the treks based on the search query
        if search_query.isdigit():
            # If user types a number, we can check if it's a trek ID
            query = query.filter(Trek.id == int(search_query))
        else:
            # If user types a text, we can check for trek name, location, or assigned staff
            query = query.filter(
                (Trek.name.ilike(f"%{search_query}%")) |
                (Trek.location.ilike(f"%{search_query}%")) |
                (Trek.difficulty.ilike(f"%{search_query}%")) |
                (Trek.staff_id.in_(matching_staff_ids))
            )
    
    # Fetch all the treks from the database
    all_treks = query.all()
    today = date.today()
    return render_template("manage_treks.html", treks=all_treks, today=today, search_query=search_query)


#  View Trek Details Route
@app.route("/admin/trek_details/<int:trek_id>")
def trek_details(trek_id):
    if session.get('user_id') == None or session.get('role') != 'admin':
        return redirect(url_for('login'))
    
    # Search trek by ID in the database
    trek = Trek.query.get(trek_id)
    
    # If trek is not found, show an error message and redirect to manage treks page
    if trek == None:
        flash("Trek not found!", "error")
        return redirect(url_for('manage_treks'))
        
    return render_template("trek_details.html", trek=trek, today=date.today())


#  View Staff Profile Route
@app.route("/admin/staff_profile/<int:staff_id>")
def staff_profile(staff_id):
    if session.get('user_id') == None or session.get('role') != 'admin':
        return redirect(url_for('login'))
        
    # Search staff profile by ID in the database
    staff = StaffProfile.query.get(staff_id)
    
    if staff == None:
        flash("Staff profile not found!", "error")
        return redirect(url_for('manage_treks'))
        
    return render_template("staff_profile.html", staff=staff, today=date.today())


# Delete Trek
@app.route("/admin/delete_trek/<int:trek_id>")
def delete_trek(trek_id):
    if session.get('user_id') == None or session.get('role') != 'admin':
        return redirect(url_for('login'))
    
    # Search trek by ID in the database
    trek_to_delete = Trek.query.get(trek_id)
    
    if trek_to_delete:
        trek_to_delete.status = 'Deleted'
        trek_to_delete.staff=None
        db.session.commit()
        flash("Trek successfully deleted!", "success")
        
    return redirect(url_for('manage_treks'))


# Edit Trek (Show pre_filled data and update it)
@app.route("/admin/edit_trek/<int:trek_id>", methods=['GET', 'POST'])
def edit_trek(trek_id):
    if session.get('user_id') == None or session.get('role') != 'admin':
        return redirect(url_for('login'))
    
    # fetch the data of the clicked trek from the database using its ID
    trek = Trek.query.get(trek_id)

    # fetch all approved staff from the database to show them in the dropdown in the form
    approved_staff = StaffProfile.query.filter_by(status='Approved').all()
    
    # if admin submit the edited forn
    if request.method == 'POST':
        # replace old data with new data
        trek.name = request.form.get('name')
        trek.location = request.form.get('location')
        trek.state = request.form.get('state')
        trek.country = request.form.get('country')
        trek.description = request.form.get('description')
        trek.difficulty = request.form.get('difficulty')
        trek.duration = int(request.form.get('duration'))
        trek.available_slots = int(request.form.get('available_slots'))
        trek.price = float(request.form.get('price'))
        
        start_str = request.form.get('start_date')
        end_str = request.form.get('end_date')
        trek.start_date = datetime.strptime(start_str, '%Y-%m-%d').date()
        trek.end_date = datetime.strptime(end_str, '%Y-%m-%d').date()

        # Handle staff id
        staff_val = request.form.get('staff_id')
        if staff_val == "" or staff_val == None:
            trek.staff_id = None
        else:
            trek.staff_id = int(staff_val)

        if trek.end_date < trek.start_date:
            flash("End date cannot be before start date!", "danger")
            return redirect(url_for('edit_trek', trek_id=trek_id))
        
        if trek.staff_id:
            overlapping_trek = Trek.query.filter(
                Trek.staff_id == trek.staff_id,
                Trek.id != trek.id,  # Exclude the current trek which is edited now
                Trek.start_date <= trek.end_date,
                Trek.end_date >= trek.start_date
            ).first()
            if overlapping_trek:
                flash("Selected staff is already assigned to another trek during the same period!", "danger")
                return redirect(url_for('edit_trek', trek_id=trek_id))
        
        # Naya data add nahi karna (add()), sirf save (commit) karna hai kyunki ID same hai
        db.session.commit()
        
        flash("Trek details updated successfully!", "success")
        return redirect(url_for('manage_treks'))
        
    # Agar GET request hai, toh form dikhao aur usme purana data bhej do
    return render_template("edit_trek.html", trek=trek, staff_list=approved_staff, today=date.today())

# Approve Trek Slot Changes
@app.route("/admin/approve_slots/<int:trek_id>")
def admin_approve_slots(trek_id):
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
        
    trek = Trek.query.get(trek_id)
    if trek and trek.status == 'Pending Approval':
        if trek.requested_slots is not None:
            trek.available_slots = trek.requested_slots
            trek.requested_slots = None # request completed, set it to none

        trek.status = 'Upcoming'
        db.session.commit()
        flash("Trek slots approved and updated! Bookings re-opened!", "success")
        
    return redirect(url_for('manage_treks'))

# Reject Trek Slot Changes
@app.route("/admin/reject_slots/<int:trek_id>")
def admin_reject_slots(trek_id):
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
        
    trek = Trek.query.get(trek_id)
    if trek and trek.status == 'Pending Approval':
        trek.requested_slots = None # after request rejeted, set it to none
        trek.status = 'Upcoming'
        db.session.commit()
        flash(f"Slot request rejected for {trek.name}. Trek returned to normal status.", "danger")
    return redirect(url_for('manage_treks'))

# Manage Staff route
@app.route("/admin/manage_staff")
def manage_staff():
    if session.get('user_id') == None or session.get('role') != 'admin':
        return redirect(url_for('login'))
    
    search_query = request.args.get('search', '').strip()
    query = StaffProfile.query
    
    if search_query:
        # Search name or email in user table
        matching_users = User.query.filter(
            (User.username.ilike(f"%{search_query}%")) |
            (User.email.ilike(f"%{search_query}%"))
        ).all()

        # Store those matching user IDs in a list
        matching_user_ids = []
        for u in matching_users:
            matching_user_ids.append(u.id)

        # Now filter the staff profiles based on the matching user IDs
        query = query.filter(StaffProfile.user_id.in_(matching_user_ids))

    # fetch all the staff profiles from the database
    staff_list = query.all()
    
    return render_template("manage_staff.html", staff_list=staff_list, search_query=search_query)

#  Approve Staff Action
@app.route("/admin/approve/<int:staff_id>")
def approve_action(staff_id):
    if session.get('user_id') == None or session.get('role') != 'admin':
        return redirect(url_for('login'))
        
    staff = StaffProfile.query.get(staff_id)
    if staff != None:
        staff.status = 'Approved'
        db.session.commit()
        flash("Staff successfully approved!", "success")
        
    return redirect(url_for('manage_staff'))


#  Blacklist Staff Action
@app.route("/admin/blacklist/<int:staff_id>")
def blacklist_action(staff_id):
    if session.get('user_id') == None or session.get('role') != 'admin':
        return redirect(url_for('login'))
        
    staff = StaffProfile.query.get(staff_id)
    if staff != None:
        staff.status = 'Blacklisted'
        db.session.commit()
        flash("Staff has been blacklisted!", "danger")
        
    return redirect(url_for('manage_staff'))


#  users route
@app.route("/admin/manage_users")
def manage_users():
    if session.get('user_id') == None or session.get('role') != 'admin':
        return redirect(url_for('login'))
    
    search_query = request.args.get('search', '').strip()

    query = User.query.filter_by(role='trekker')  # Only fetch trekkers

    if search_query:
        if search_query.isdigit():
            query = query.filter(User.id == int(search_query))
        else:
            query = query.filter(
                (User.username.ilike(f"%{search_query}%"))
                | (User.email.ilike(f"%{search_query}%"))
            )

    all_trekkers = query.all()
    return render_template("manage_users.html", users=all_trekkers, search_query=search_query)

# Manage Bookings
@app.route("/admin/manage_bookings")
def manage_bookings():
    if session.get('user_id') == None or session.get('role') != 'admin':
        return redirect(url_for('login'))
    
    all_bookings = Booking.query.all()
    return render_template("manage_bookings.html", bookings=all_bookings)

# Block User (Trekker) Action
@app.route("/admin/block_user/<int:user_id>")
def block_user(user_id):
    # Security check
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
        
    # fetch user from database
    user = User.query.get(user_id)
    
    if user:
        # Status update
        user.status = 'Blocked'
        
        db.session.commit()
        
    return redirect(url_for('manage_users'))


@app.route("/admin/unblock_user/<int:user_id>")
def unblock_user(user_id):
    # Security Check
    if session.get('role') != 'admin':
        return redirect(url_for('login'))
        
    # fetch user from database
    user = User.query.get(user_id)
    
    if user:
        # Set status to active
        user.status = 'Active'
        
        db.session.commit()
        
    return redirect(url_for('manage_users'))


@app.route("/admin/view_user_profile/<int:user_id>")
def view_user_profile(user_id):
    # Security check
    if session.get('user_id') == None or session.get('role') != 'admin':
        return redirect(url_for('login'))
        
    # fetch id from database
    user = User.query.get(user_id)
    
    if user:
        return render_template("user_profile.html", user=user)# here we call user_profile and send users data
    else:
        flash("User not found !", "danger")
        return redirect(url_for('manage_users'))
    

@app.route("/trek/<int:id>")
def view_trek(id):
    trek = Trek.query.get_or_404(id)
    return render_template("view_trek.html", trek=trek)

@app.route("/book_trek/<int:trek_id>", methods=['GET', 'POST'])
def book_trek(trek_id):
    if 'user_id' not in session:
        flash("Please log in to book a trek.", "warning")
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    if user.status == 'Blocked':
        flash("Your account has been blocked by Admin. You cannot book new treks.","danger")
        return redirect(url_for('my_treks'))
        
    trek = Trek.query.get_or_404(trek_id)
    
    if request.method == 'POST':
        seats_to_book = int(request.form.get('seats_booked'))
        
        if seats_to_book <= 0:
            flash("Please select at least 1 seat.", "danger")
            return redirect(url_for('book_trek', trek_id=trek.id))
            
        if seats_to_book > trek.available_slots:
            flash(f"Sorry, only {trek.available_slots} seats are available.", "danger")
            return redirect(url_for('book_trek', trek_id=trek.id))

        existing_booking = Booking.query.filter_by(user_id=session['user_id'], trek_id=trek.id, booking_status='Confirmed').first()
        if existing_booking != None:
            flash("You have already booked this trek! Check your dashboard.", "warning")
            return redirect(url_for('view_trek', id=trek.id))
            
        total_price = trek.price * seats_to_book
        
        new_booking = Booking(
            user_id=session['user_id'], 
            trek_id=trek.id,
            seats_booked=seats_to_book,
            total_price=total_price,
            booking_status='Confirmed')
        
        trek.available_slots -= seats_to_book
        
        db.session.add(new_booking)
        db.session.commit()
        
        flash("Booking successful! Your adventure awaits.", "success")
        return redirect(url_for('my_treks'))
        
    return render_template("book_trek.html", trek=trek)


@app.route("/cancel_booking/<int:booking_id>")
def cancel_booking(booking_id):
    if 'user_id' not in session:
        flash("Please log in first.", "danger")
        return redirect(url_for('login'))

    booking = Booking.query.get_or_404(booking_id)

    if booking.user_id != session['user_id'] and session.get('role') != 'admin':
        flash("You cannot cancel someone else's booking!", "danger")
        return redirect(url_for('my_treks'))

    if booking.booking_status == 'Cancelled':
        flash("This booking is already cancelled.", "warning")
        return redirect(url_for('my_treks'))

    # change booking status
    booking.booking_status = 'Cancelled'

    # ReAdding the seats to slots
    booking.trek.available_slots += booking.seats_booked

    db.session.commit()
    flash("Booking cancelled successfully. Seats have been refunded.", "success")

    # if admin cancels redirect to admin manage booking page and else user's my treks page
    if session.get('role') == 'admin':
        return redirect(url_for('manage_bookings'))
    return redirect(url_for('my_treks'))

# My Treks (User's Trekking History & Active Treks)
@app.route("/my_treks")
def my_treks():
    if session.get('user_id') == None or session.get('role') != 'trekker':
        flash("Please log in first.", "danger")
        return redirect(url_for('login'))
        
    user = User.query.get(session['user_id'])
    today = date.today()
    
    # Lists for different- different tables
    upcoming_bookings = []
    current_bookings = []
    completed_bookings = []
    cancelled_bookings = []
    
    for booking in user.bookings:
        if booking.booking_status == 'Cancelled' or booking.trek.status == 'Deleted':
            cancelled_bookings.append(booking)
        elif booking.trek.status == 'Completed':
            completed_bookings.append(booking)
        elif booking.trek.status == 'Ongoing':
            current_bookings.append(booking)
        else:
            upcoming_bookings.append(booking)
            
    return render_template("my_treks.html", 
                           upcoming=upcoming_bookings, 
                           current=current_bookings, 
                           completed=completed_bookings, 
                           cancelled=cancelled_bookings)


# View Specific Booking Details
@app.route("/booking_details/<int:booking_id>")
def booking_details(booking_id):
    if session.get('user_id') == None or session.get('role') != 'trekker':
        flash("Please log in first.", "danger")
        return redirect(url_for('login'))
        
    booking = Booking.query.get_or_404(booking_id)
    
    # One user cannot see other user's detail
    if booking.user_id != session['user_id']:
        flash("Access Denied! You can only view your own bookings.", "danger")
        return redirect(url_for('my_treks'))
        
    return render_template("booking_details.html", booking=booking)


# Staff Dashboard Route
@app.route("/staff_dashboard")
def staff_dashboard():
    if session.get('user_id') == None or session.get('role') != 'staff':
        flash("Please log in as staff to access this page.", "warning")
        return redirect(url_for('login'))
    
    user = User.query.get(session.get('user_id'))
    staff_profile = user.staff_profile

    # for blacklisted staff
    if staff_profile and staff_profile.status == 'Blacklisted':
        flash("Your account has been blacklisted.", "danger")
    
    assigned_treks = []
    active_treks = []
    completed_treks = []
    total_participants = 0

    if staff_profile:
        assigned_treks = Trek.query.filter_by(staff_id=staff_profile.id).order_by(Trek.start_date.asc()).all()
        
        for trek in assigned_treks:
            if trek.status == 'Deleted':
                continue
            # Participants calculation
            for booking in trek.bookings:
                if booking.booking_status == 'Confirmed':
                    total_participants += booking.seats_booked
            
            # Differenciate Active and Completed treks
            if trek.status == 'Completed':
                completed_treks.append(trek)
            else:
                active_treks.append(trek)

    valid_assigned_count = len(active_treks) + len(completed_treks)

    return render_template("staff_dash.html", 
                           user=user, 
                           staff_profile=staff_profile, 
                           active_treks=active_treks,
                           completed_treks=completed_treks,
                           total_assigned=valid_assigned_count,
                           total_participants=total_participants,
                           total_completed=len(completed_treks))


# Staff Manage Trek
@app.route("/staff/manage_trek/<int:trek_id>", methods=['GET', 'POST'])
def staff_manage_trek(trek_id):
    if session.get('user_id') == None or session.get('role') != 'staff':
        flash("Access Denied. Please log in as staff.", "danger")
        return redirect(url_for('login'))
        
    user = User.query.get(session.get('user_id'))
    staff_profile = user.staff_profile

    # block blacklisted staff
    if staff_profile and staff_profile.status == 'Blacklisted':
        flash("Your account is blacklisted. You cannot manage treks.", "danger")
        return redirect(url_for('staff_dashboard'))

    trek = Trek.query.get(trek_id)
    
    if trek == None or trek.staff_id != staff_profile.id:
        flash("Unauthorized Access!", "danger")
        return redirect(url_for('staff_dashboard'))
        
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'edit_slots':
            new_slots = int(request.form.get('new_slots'))
            trek.requested_slots = new_slots
            trek.status = 'Pending Approval'
            flash("Slot change requested! Sent to Admin for approval. Bookings are now locked.", "info")
            
        elif action == 'close_booking':
            trek.status = 'Closed'
            flash("Bookings closed manually for this trek.", "warning")
            
        elif action == 'open_booking':
            trek.status = 'Upcoming'
            flash("Bookings are now open again.", "success")
            
        # staff can mark trek as started and completed
        elif action == 'start_trek':
            trek.status = 'Ongoing'
            flash("Trek has officially started! (Status: Ongoing)", "success")
            
        elif action == 'complete_trek':
            trek.status = 'Completed'
            flash("Trek marked as successfully completed!", "success")
            
        db.session.commit()
        return redirect(url_for('staff_manage_trek', trek_id=trek.id))
        
    # Fetch Participants full details
    participants = Booking.query.filter_by(trek_id=trek.id, booking_status='Confirmed').all()
    return render_template("staff_manage_trek.html", trek=trek, participants=participants)

if __name__ == '__main__':
    app.run(debug=True)
