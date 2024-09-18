from flask import Flask, session, render_template, request, redirect, url_for, flash, Response, g
import sqlite3
import csv
import io
import json
import os
from PIL import Image
import datetime
import threading

app = Flask(__name__)
app.secret_key = 'HeyTab'   

DATABASE = 'new_data.db'

current_sport_statuses = {
    'cricket': 'yes',
    'football': 'yes',
    'volleyball': 'yes',
    'basketball': 'no',
    'badminton': 'yes',
}

# Predefined dataset of game months and corresponding sports
game_data = [
    {'month': 3, 'sport': 'Football'},
    {'month': 5, 'sport': 'Basketball'},
    {'month': 8, 'sport': 'Soccer'},
    {'month': 10, 'sport': 'Cricket'}
]
month_l=['January','February','March','April','May','June','July','August','September','October','November','December']
s_coordinator_db = {'Rohan': 'Cricket'}
coordinator_db = {'Cd vala master': 'Arts'}

def create_tables():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS registrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sport TEXT,
            teamname TEXT,
            captain_name TEXT,
            vice_captain_name TEXT,
            phone TEXT,
            email TEXT,
            student_id TEXT,
            course TEXT,
            year TEXT,
            players_json TEXT
        )
    ''')

    conn.commit()
    conn.close()

create_tables()

admin_credentials = [{'username': 'admin', 'password': 'pass@123'}]

@app.route('/')
def home():
    image_paths = get_uploaded_image_paths()
    conn_event = sqlite3.connect(DATABASE_N)
    cursor_event = conn_event.cursor()
    cursor_event.execute('SELECT update_text FROM event_updates ORDER BY timestamp DESC LIMIT 3')
    event_updates = cursor_event.fetchall()
    conn_event.close()

    conn_event = sqlite3.connect(DATABASE_N)
    cursor_event = conn_event.cursor()
    cursor_event.execute('SELECT update_text FROM event_updates ORDER BY timestamp DESC LIMIT 10')
    event_updates01 = cursor_event.fetchall()
    conn_event.close()

    current_time = datetime.datetime.now()
    next_game_month, next_sport, time_to_next_game = calculate_next_game(current_time)
    current_month = current_time.month
    current_sport = get_sport_for_current_month(current_month, game_data)
    return render_template('index.html', game_data=game_data,current_sport=current_sport,month_l=month_l, next_game_month=next_game_month, next_sport=next_sport, time_to_next_game=time_to_next_game, current_time=current_time, image_paths=image_paths, event_updates=event_updates, event_updates01=event_updates01, coordinators=coordinator_db, s_coordinators=s_coordinator_db)

def get_sport_for_current_month(current_month, game_data):
    for game in game_data:
        if game['month'] == current_month:
            return game['sport']
    return "Sport not found"  
def calculate_next_game(current_time):
    next_game_month = None
    next_sport = None
    time_to_next_game = None

    for i, game in enumerate(game_data):
        if current_time.month < game['month']:
            next_game_month = game['month']
            next_sport = game['sport']
            time_to_next_game = game_data[(i + 1) % len(game_data)]['month']
            break

    if next_game_month is None:
        next_game_month = game_data[0]['month']
        next_sport = game_data[0]['sport']
        time_to_next_game = game_data[1]['month']

    return next_game_month, next_sport, time_to_next_game

@app.route('/add_month', methods=['POST'])
def add_month():
    new_month = int(request.form['new_month'])
    new_sport = request.form['new_sport']
    if new_month and new_sport:
        game_data.append({'month': new_month, 'sport': new_sport})
    return redirect(url_for('admin'))

@app.route('/delete_month', methods=['POST'])
def delete_month():
    month_to_delete = int(request.form['month_to_delete'])
    game_data[:] = [game for game in game_data if game['month'] != month_to_delete]
    return redirect(url_for('admin'))

def fetch_data_for_sport(conn, sport):
    cursor = conn.cursor()
    cursor.execute('''
        SELECT *, (teamname || ' - ' || players_json) AS team_player
        FROM registrations
        WHERE sport = ?
        GROUP BY team_player
        ORDER BY team_player
    ''', (sport,))
    return cursor.fetchall()


# ...
app.config['ADMIN_SESSION'] = False


@app.route('/admin_logout', methods=['GET'])
def admin_logout():
    app.config['ADMIN_SESSION'] = False
    return redirect(url_for('home'))


@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if any(cred['username'] == username and cred['password'] == password for cred in admin_credentials):
            session['logged_in'] = True
            app.config['ADMIN_SESSION'] = True
            flash("Login successful!", 'success')
            return redirect(url_for('admin'))
        else:
            flash("Login failed. Please try again.", 'danger')

    return render_template('Login_Page.html')


def timeout_session():
    app.config['ADMIN_SESSION'] = False
   

def start_session_timer():
    timer = threading.Timer(300, timeout_session)  # 300 seconds = 5 minutes
    timer.start()


@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if not app.config['ADMIN_SESSION']:
        return redirect(url_for('admin_login'))
    else:
        start_session_timer()

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        admin_credentials.append({"username": username, "password": password})

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute('SELECT DISTINCT sport FROM registrations')
    sports = [row[0] for row in cursor.fetchall()]

    all_data = {}
    all_data = {sport: fetch_data_for_sport(conn, sport) for sport in sports}

    conn.close()
    conn_event = sqlite3.connect(DATABASE_N)
    cursor_event = conn_event.cursor()
    cursor_event.execute('SELECT * FROM event_updates ORDER BY timestamp DESC LIMIT 20')
    event_updates = cursor_event.fetchall()
    conn_event.close()
      
    image_filenames = get_uploaded_image_filenames()
    current_time = datetime.datetime.now()
    next_game_month, next_sport, time_to_next_game = calculate_next_game(current_time)
    return render_template('admin.html', game_data=game_data, next_game_month=next_game_month,
                           next_sport=next_sport, current_sport_statuses=current_sport_statuses, time_to_next_game=time_to_next_game, admins=admin_credentials,coordinators=coordinator_db,s_coordinators=s_coordinator_db, event_updates=event_updates, all_data=all_data, image_filenames=image_filenames)
    


@app.route('/add_admin', methods=['POST'])
def add_admin():
    if not app.config['ADMIN_SESSION']:
        return redirect(url_for('admin_login'))
    new_username = request.form['new_username']
    new_password = request.form['new_password']
    
    admin_credentials.append({'username': new_username, 'password': new_password})
    
    flash(f"Admin '{new_username}' has been added.", 'success')
    return redirect(url_for('admin'))

@app.route('/delete_admin', methods=['POST'])
def delete_admin():
    if not app.config['ADMIN_SESSION']:
        return redirect(url_for('admin_login'))  # Redirect to admin login if admin session is not active

    del_username = request.form['del_username']
    
    admin_to_delete = next((move for move in admin_credentials if move['username'] == del_username), None)
    
    if admin_to_delete:
        admin_credentials.remove(admin_to_delete)
        flash(f"Admin '{del_username}' has been deleted.", 'success')
    else:
        flash(f"Admin '{del_username}' not found.", 'danger')
    
    return redirect(url_for('admin'))

def extract_team_data(request):
    teamname = request.form['teamname']
    captain_name = request.form['captain_name']
    vice_captain_name = request.form['vice_captain_name']
    phone = request.form['phone']
    email = request.form['email']
    student_id = request.form['student_id']
    year = request.form['year']
    course = request.form['course']

    players = request.form['players']
    """[{"player_name": request.form[f'player{i}']} for i in range(1, 14) if request.form.get(f'player{i}')]
"""
    return (
        teamname,
        captain_name,
        vice_captain_name,
        phone,
        email,
        student_id,
        course,
        year,
        players
    )

def extract_t_data(request):
    teamname = request.form['teamname']
    captain_name = request.form['teamname']
    vice_captain_name = request.form['teamname']
    phone = request.form['phone']
    email = request.form['email']
    student_id = request.form['student_id']
    year = request.form['year']
    course = request.form['course']

    players =request.form['players']
    """ [{"player_name": request.form[f'player{i}']} for i in range(1, 14) if request.form.get(f'player{i}')]"""

    return (
        teamname,
        captain_name,
        vice_captain_name,
        phone,
        email,
        student_id,
        course,
        year,
        players
    )

@app.route('/cricket_registration', methods=['GET', 'POST'])
def cricket_registration():
    if not sports_check('cricket'):
        return render_template('error.html')
    if request.method == 'POST':
        team_data = extract_team_data(request)
        if register_team('Cricket', *team_data):
            return render_template('registration_confirmation.html', registration_data=team_data)
        else:
            flash("Failed to register the team. Please try again.", 'danger')
            return render_template('registration_confirmation.html', registration_data=team_data)

    return render_template('cricket2.2.html')

# Route for football registration
@app.route('/football_registration', methods=['GET', 'POST'])
def football_registration():
    if not sports_check('football'):
        return render_template('error.html')
    if request.method == 'POST':
        team_data = extract_team_data(request)
        if register_team('Football', *team_data ):
            return render_template('registration_confirmation.html', registration_data=team_data)
        else:
            flash("Failed to register the team. Please try again.", 'danger')
            return redirect('registration_confirmation.html', registration_data=team_data)

    return render_template('football_form.html')

"""
@app.route('/tabletennis_registration', methods=['GET', 'POST'])
def tabletennis_registration():
    if request.method == 'POST':
        team_data = extract_team_data(request)
        registration_data = register_team(
            'Table Tennis', *team_data  # Use the unpacking operator to pass individual arguments
        )  #
         
        if registration_data:
            return render_template('registration_confirmation.html', registration_data=registration_data)
        else:
            flash("Failed to register the team. Please try again.", 'danger')
            return redirect(url_for('tabletennis_registration'))

    return render_template('form_table_tennis.html')

"""
@app.route('/volleyball_registration', methods=['GET', 'POST'])
def volleyball_registration():
    if not sports_check('volleyball'):
        return render_template('error.html')
    if request.method == 'POST':
        team_data = extract_team_data(request)
        if register_team('Volley Ball', *team_data):
            return render_template('registration_confirmation.html', registration_data=team_data)
        else:
            flash("Failed to register the team. Please try again.", 'danger')
            return render_template('registration_confirmation.html', registration_data=team_data)
    return render_template('vollyball_form.html')

# Route for badminton registration
@app.route('/badminton_registration', methods=['GET', 'POST'])
def badminton_registration():
    if not sports_check('badmintion'):
        return render_template('error.html')
    if request.method == 'POST':
        team_data = extract_team_data(request)
        if register_team('Badminton', *team_data):
            return render_template('registration_confirmation.html', registration_data=team_data)
        else:
            flash("Failed to register the team. Please try again.", 'danger')
            return render_template('registration_confirmation.html', registration_data=team_data)

    return render_template('Badmintion_form.html')

# Route for basketball registration
@app.route('/basketball_registration', methods=['GET', 'POST'])
def basketball_registration():
    if request.method == 'POST':
        team_data = extract_team_data(request)
        if register_team('Basket Ball', *team_data):
            return render_template('registration_confirmation.html', registration_data=team_data)
        else:
            flash("Failed to register the team. Please try again.", 'danger')
            return render_template('registration_confirmation.html', registration_data=team_data)

    return render_template('Basketball_form.html')
"""
# Route for carrom registration
@app.route('/carrom_registration', methods=['GET', 'POST'])
def carrom_registration():
    if request.method == 'POST':
        team_data = extract_t_data(request)
        registration_data = register_team(
            'Carrom', *team_data  # Use the unpacking operator to pass individual arguments
        )  #
        if registration_data:
            return render_template('registration_confirmation.html', registration_data=registration_data)
        else:
            flash("Failed to register the team. Please try again.", 'danger')
            return redirect(url_for('carrom_registration'))

    return render_template('form_Carrom.html')

# Route for chess registration
@app.route('/chess_registration', methods=['GET', 'POST'])
def chess_registration():
    if request.method == 'POST':
        team_data = extract_t_data(request)
        registration_data = register_team(
            'Chess', *team_data  # Use the unpacking operator to pass individual arguments
        )  #
        if registration_data:
            return render_template('registration_confirmation.html', registration_data=registration_data)
        else:
            flash("Failed to register the team. Please try again.", 'danger')
            return redirect(url_for('chess_registration'))

    return render_template('form_Chess.html')
"""

@app.route('/view_all_data', methods=['GET'])
def download_all_data():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM registrations')
    data = cursor.fetchall()
    conn.close()

    # Create a CSV file in memory
    output = io.StringIO()
    csv_writer = csv.writer(output)
    csv_writer.writerow([
        'ID', 'Sport', 'Team Name', 'Captain Name', 'Vice Captain Name', 'Phone', 'Email',
        'Student ID', 'Course', 'Year', 'Players JSON'
    ])
    csv_writer.writerows(data)

    # Create a response with the CSV data for download
    response = Response(output.getvalue(), content_type='text/csv')
    response.headers['Content-Disposition'] = 'attachment; filename=all_data.csv'
    return response

@app.route('/registration_confirmation')
def registration_confirmation():
    return render_template('registration_confirmation.html', registration_data=None)

def register_team(sport, teamname, captain_name, vice_captain_name, phone, email, student_id, course, year, players=None, registration_date=None):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    try:
        # Convert the 'players' list to a JSON string
        players_json = json.dumps(players) if players is not None else None

        # Include the current timestamp in the INSERT query
        cursor.execute('''
            INSERT INTO registrations (
                sport, teamname, captain_name, vice_captain_name, phone, email, student_id,
                course, year, players_json, registration_date
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (sport, teamname, captain_name, vice_captain_name, phone, email, student_id, course, year, players_json, registration_date))

        conn.commit()
        flash(f"{teamname} registration successful for {sport}!", 'success')
    except sqlite3.IntegrityError as e:
        conn.rollback()
        flash("Registration failed. Please check if the team name or student ID is already in use.", 'danger')
    except Exception as e:
        conn.rollback()
        flash(f"An error occurred: {str(e)}", 'danger')
        # Log the exception for debugging
        app.logger.error(str(e))
    finally:
        conn.close()



# Create a route for deleting a student record
@app.route('/delete_student', methods=['POST'])
def delete_student():
    student_id = request.form.get('student_id')

    if not student_id:
        flash("Please provide a student ID for deletion.", 'danger')
        return redirect(request.referrer)

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    try:
        cursor.execute('DELETE FROM registrations WHERE id = ?', (student_id,))
        conn.commit()
        flash(f"Student record with ID {student_id} has been deleted.", 'success')
    except Exception as e:
        conn.rollback()
        flash(f"An error occurred while deleting the student record: {str(e)}", 'danger')
    finally:
        conn.close()

    return redirect(request.referrer)

# ... (Your existing code)

# Function to insert sample data into the registrations table
def insert_sample_data():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    sample_data = [
        # Sample data for Basketball registration
        ('Basketball', 'Team A', 'John Doe', 'Jane Smith', '1234567890', 'john@example.com', '12345', 'Computer Science', '2nd', '["Player 1", "Player 2", "Player 3"]'),
        
        # Sample data for Volleyball registration
        ('Volleyball', 'Team B', 'Mike Johnson', 'Emily Davis', '9876543210', 'mike@example.com', '54321', 'Business Administration', '3rd', '["Player 4", "Player 5", "Player 6"]'),

        # Sample data for Table Tennis registration
        ('Table Tennis', 'Team C', 'David Wilson', 'Sophia Brown', '5678901234', 'david@example.com', '67890', 'Engineering', '1st', '["Player 7", "Player 8", "Player 9"]'),

        # Add sample data for other sports registrations here
    ]

    try:
        cursor.executemany('''
            INSERT INTO registrations (
                sport, teamname, captain_name, vice_captain_name, phone, email, student_id,
                course, year, players_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', sample_data)

        conn.commit()
        print("Sample data inserted successfully.")
    except Exception as e:
        conn.rollback()
        print(f"An error occurred: {str(e)}")
    finally:
        conn.close()

# Uncomment the line below to insert the sample data when needed
# insert_sample_data()
DATABASE_N = 'event_updates.db'  # SQLite database file

def get_db_connection():
    conn = getattr(g, '_database', None)
    if conn is None:
        conn = g._database = sqlite3.connect(DATABASE_N)
    return conn

# Function to create the event_updates table if it doesn't exist
def create_event_updates_table():
    with app.app_context():  # Set up the application context
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS event_updates (
                id INTEGER PRIMARY KEY,
                update_text TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()

# Create the table before handling any requests
create_event_updates_table()

@app.route('/notify')
def event():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT update_text FROM event_updates ORDER BY timestamp DESC LIMIT 10')
    top_10_event_updates = cursor.fetchall()
    conn.close()
    return render_template('notification.html', event_updates=top_10_event_updates)

@app.route('/add_update', methods=['POST'])
def add_update():
    if request.method == 'POST':
        event_update = request.form['event_update']
        if event_update:
            event_update = event_update[:200]  # Limit update length to 200 characters

            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('INSERT INTO event_updates (update_text) VALUES (?)', (event_update,))
            conn.commit()
            conn.close()

            flash('Event update added successfully!', 'success')
        else:
            flash('Update cannot be empty!', 'danger')
    return redirect(url_for('admin'))

@app.route('/admin/delete_update', methods=['POST'])
def delete_update():
    if request.method == 'POST':
        update_id = request.form['update_id']
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM event_updates WHERE id = ?', (update_id,))
        conn.commit()
        conn.close()

        flash('Event update deleted successfully!', 'success')
    return redirect(url_for('admin'))
# ...

# Define a custom error handler for 404 Not Found Error
@app.errorhandler(404)
def not_found_error(error):
    return render_template('error.html'), 404

@app.errorhandler(405)
def not_found_error(error):
    return render_template('error.html'), 405


image_paths = ['image1.jpg', 'image2.jpg', 'image3.jpg']
current_image_index = 0

app.config['UPLOAD_FOLDER'] = 'static/uploads'


def get_uploaded_image_filenames():
    image_filenames = []
    image_folder = app.config['UPLOAD_FOLDER']

    for filename in os.listdir(image_folder):
        if filename.endswith(('png', 'jpg', 'jpeg', 'gif','JPG','PNG','JPEG','GIF')):
            image_filenames.append(filename)

    return image_filenames


def get_uploaded_image_paths():
    # Get a list of image file paths in the 'static/uploads' directory
    image_paths = []
    image_folder = app.config['UPLOAD_FOLDER']

    for filename in os.listdir(image_folder):
        if filename.endswith(('png', 'jpg', 'jpeg', 'gif','PNG','JPG','JPEG','GIF')):
            image_path = url_for('static', filename=f'uploads/{filename}')  # Updated path
            image_paths.append(image_path)

    return image_paths


@app.route('/gallery')
def gallery():
    image_paths = get_uploaded_image_paths()
    conn_event = sqlite3.connect(DATABASE_N)
    cursor_event = conn_event.cursor()
    cursor_event.execute('SELECT update_text FROM event_updates ORDER BY timestamp DESC LIMIT 3')
    event_updates = cursor_event.fetchall()
    conn_event.close()
    conn_event = sqlite3.connect(DATABASE_N)
    cursor_event = conn_event.cursor()
    cursor_event.execute('SELECT update_text FROM event_updates ORDER BY timestamp DESC LIMIT 10')
    event_updates01 = cursor_event.fetchall()
    conn_event.close()
    return render_template('news.html', image_paths=image_paths,event_updates=event_updates,event_updates01=event_updates01)

@app.route('/about')
def aboutit():
    conn_event = sqlite3.connect(DATABASE_N)
    cursor_event = conn_event.cursor()
    cursor_event.execute('SELECT update_text FROM event_updates ORDER BY timestamp DESC LIMIT 3')
    event_updates = cursor_event.fetchall()
    conn_event.close()
    conn_event = sqlite3.connect(DATABASE_N)
    cursor_event = conn_event.cursor()
    cursor_event.execute('SELECT update_text FROM event_updates ORDER BY timestamp DESC LIMIT 10')
    event_updates01 = cursor_event.fetchall()
    conn_event.close()
    return render_template('about.html',event_updates=event_updates,event_updates01=event_updates01)


@app.route('/upload', methods=['POST'])
def upload():
    uploaded_files = request.files.getlist('files[]')

    for file in uploaded_files:
        if file.filename != '':
            filename = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(filename)
            resize_image(filename)

    image_paths = get_uploaded_image_paths()
    return redirect(url_for('gallery'))


def resize_image(image_path):
    image = Image.open(image_path)
    new_width = 400
    new_height = 200
    resized_image = image.resize((new_width, new_height), Image.LANCZOS)
    resized_image.save(image_path)


@app.route('/delete', methods=['POST'])
def delete():
    selected_file = request.form.get('selected_file')

    if selected_file:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], selected_file)

        if os.path.exists(file_path):
            os.remove(file_path)

    image_paths = get_uploaded_image_paths()
    return redirect(url_for('gallery'))

@app.route('/get_image_paths')
def get_image_paths():
    image_paths = get_uploaded_image_paths()
    return jsonify(image_paths)

@app.route('/move_images', methods=['POST'])
def move_images():
    global current_image_index

    direction = request.form.get('direction')

    if direction == 'prev':
        current_image_index = (current_image_index - 1) % len(image_paths)
    elif direction == 'next':
        current_image_index = (current_image_index + 1) % len(image_paths)

    return redirect(url_for('index'))



@app.route('/add_coordinator', methods=['POST'])
def add_coordinator():
    coordinator_name = request.form['coordinator_name']
    sport_name = request.form['sport_name']
    coordinator_db[coordinator_name] = sport_name
    return redirect(url_for('admin'))

@app.route('/delete_coordinator', methods=['POST'])
def delete_coordinator():
    coordinator_name = request.form.get('coordinator_name')  # Get the coordinator name from the form
    if coordinator_name in coordinator_db:
        del coordinator_db[coordinator_name]  # Delete the coordinator if it exists
    return redirect(url_for('admin'))

@app.route('/add_student_coordinator', methods=['POST'])
def add_student_coordinator():
    coordinator_s_name = request.form['student_coordinator_name']
    sport_name = request.form['sport_name']
    s_coordinator_db[coordinator_s_name] = sport_name
    return redirect(url_for('admin'))

@app.route('/delete_student_coordinator',methods=['POST'])
def delete_student_coordinator():
    coordinator_name=request.form['student_coordinator_name']
    if coordinator_name in s_coordinator_db:
        del s_coordinator_db[coordinator_name]
    return redirect(url_for('admin'))


# Function to check the approval status of a specific sport
def sports_check(sport_name):
    return current_sport_statuses.get(sport_name, 'no') == 'yes'

@app.route('/admin_change_status', methods=['GET', 'POST'])
def admin_change_status():
    if request.method == 'POST':
        # Get the sport name and new status from the form input
        sport_name = request.form.get('sport_name')
        new_status = request.form.get('new_status')

        # Update the approval status in the dictionary
        if sport_name in current_sport_statuses:
            current_sport_statuses[sport_name] = new_status

    # Render the admin.html template with the sports approval status dictionary
    return redirect(url_for('admin'))





import logging

# Configure logging
app.logger.setLevel(logging.DEBUG)
handler = logging.FileHandler('error.log')
handler.setLevel(logging.ERROR)
app.logger.addHandler(handler)

if __name__ == '__main__':
    app.run(debug=True)
