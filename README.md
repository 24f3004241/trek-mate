# Trek Mate

This is my MAD-1 project for a Trekking Management Application. It is a web application where users can find and book treks, and admins can manage the whole system. 

## Features
* **Role-Based Login:** There are 3 types of users - Admin, Staff (Guide), and Trekker (Normal User).
* **Trekker Panel:** Users can register, book seats for a trek, cancel bookings, and view their trekking history.
* **Admin Panel:** Admin can add new treks, delete treks, approve staff, and block users.
* **Staff Panel:** Guides can manage their assigned treks, update trek status (like Ongoing or Completed), and request more slots.
* **Dynamic Database:** Used SQLAlchemy to automatically calculate total seats, pricing, and active status.

## Technologies Used
* **Backend:** Python, Flask
* **Database:** SQLite (Flask-SQLAlchemy)
* **Frontend:** HTML, Bootstrap 5, Jinja2 Templates

## How to Run This Project
If you want to run this project on your system, follow these simple steps:

1. Open the project folder in VS Code or your terminal.
2. Install the required python libraries by running this command:
   `pip install -r requirements.txt`
3. Start the server by running:
   `python app.py`
4. Open your web browser and go to this link: `http://127.0.0.1:5000`

## Default Admin Details
To check the admin dashboard, you can use these login details:
* **Username:** admin
* **Password:** admin123