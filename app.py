from flask import Flask, request, render_template, redirect, url_for, session, flash
import mysql.connector
from flask_mail import Mail, Message
from flask_socketio import SocketIO
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'

# Configure Flask-Mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('EMAIL_USER')
app.config['MAIL_PASSWORD'] = os.environ.get('EMAIL_PASS')

mail = Mail(app)
socketio = SocketIO(app)

# Database connection function
def get_db_connection():
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='',
        database='pyrosense'
    )

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM user WHERE email = %s AND password = %s", (email, password))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        if user:
            session['user_email'] = email
            return redirect(url_for('home'))
        else:
            flash('Invalid credentials')
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        location = request.form['location']
        password = request.form['password']
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM user WHERE email = %s", (email,))
        user = cursor.fetchone()
        if not user:
            cursor.execute("INSERT INTO user (name, email, phone, location, password) VALUES (%s, %s, %s, %s, %s)",
                           (name, email, phone, location, password))
            conn.commit()
            cursor.close()
            conn.close()
            return redirect(url_for('login'))
        else:
            flash('Email already registered')
            cursor.close()
            conn.close()
    return render_template('signup.html')

@app.route('/alert')
def alert():
    return render_template('alert.html')

def send_alert(user):
    location = user['location']
    google_maps_link = f"https://www.google.com/maps/search/?api=1&query={location}"

    socketio.emit('fire_alert', {'location': location, 'google_maps_link': google_maps_link}, namespace='/alert')

    # Send an email notification
    msg = Message('Fire Alert', sender='noreply@demo.com', recipients=[user['email']])
    msg.body = f'Fire detected at your house location: {location}. Please evacuate immediately!\nGoogle Maps link: {google_maps_link}'
    mail.send(msg)

    # Send the location to emergency services
    send_location_to_emergency_services(location, google_maps_link)

def send_location_to_emergency_services(location, google_maps_link):
    # Logic to send the location to emergency services (e.g., via SMS, social media, etc.)
    print(f"Sending location {location} to emergency services\nGoogle Maps link: {google_maps_link}")

@app.route('/detect_fire', methods=['POST'])
def detect_fire():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM user")
    users = cursor.fetchall()
    for user in users:
        send_alert(user)
    cursor.close()
    conn.close()
    return 'Alert sent to all users!'

if __name__ == '__main__':
    socketio.run(app, debug=True)
