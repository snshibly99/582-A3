from flask import Flask, request, redirect, session, render_template, url_for, flash
from flask_mysqldb import MySQL

app = Flask(__name__)
app.secret_key = 'change_this_to_random_secret_key_123'

# MySQL Config - CHANGE THESE TO MATCH YOUR SETUP
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '12345678'  # Change to your MySQL password
app.config['MYSQL_DB'] = 'flask_app'

mysql = MySQL(app)

# Home route - Just shows the page, no filtering
@app.route('/')
@app.route('/index.html')
def home():
    cursor = mysql.connection.cursor()
    
    # Get photos for carousel
    cursor.execute('SELECT * FROM photos ORDER BY id')
    photos = cursor.fetchall()
    cursor.close()
    
    # Check if user is logged in
    username = session.get('username')
    
    return render_template('index.html', 
                         username=username,
                         photos=photos)

# Results page - Shows filtered photographers
@app.route('/results', methods=['GET', 'POST'])
def results():
    cursor = mysql.connection.cursor()
    
    # Get filter parameters from form or URL
    if request.method == 'POST':
        category = request.form.get('category', 'Portrait')
        price_range = request.form.get('price_range', '<$200')
        location = request.form.get('location', 'Queensland')
        search_query = request.form.get('search', '')
    else:
        category = request.args.get('category', 'Portrait')
        price_range = request.args.get('price_range', '<$200')
        location = request.args.get('location', 'Queensland')
        search_query = request.args.get('search', '')
    
    # Build query for filtered photographers
    query = 'SELECT * FROM photographers WHERE 1=1'
    params = []
    
    if category:
        query += ' AND category = %s'
        params.append(category)
    
    if price_range:
        query += ' AND price_range = %s'
        params.append(price_range)
    
    if location:
        query += ' AND location = %s'
        params.append(location)
    
    if search_query:
        query += ' AND (name LIKE %s OR description LIKE %s)'
        params.extend([f'%{search_query}%', f'%{search_query}%'])
    
    cursor.execute(query, params)
    photographers = cursor.fetchall()
    cursor.close()
    
    # Check if user is logged in
    username = session.get('username')
    
    return render_template('results.html', 
                         username=username,
                         photographers=photographers,
                         selected_category=category,
                         selected_price=price_range,
                         selected_location=location,
                         search_query=search_query)

# Search route (handles search form submission from navbar)
# This searches ONLY by name/description, ignoring filters
@app.route('/search', methods=['POST'])
def search():
    search_query = request.form.get('search', '')
    
    cursor = mysql.connection.cursor()
    
    # Search only by name and description
    if search_query:
        query = 'SELECT * FROM photographers WHERE name LIKE %s OR description LIKE %s'
        params = [f'%{search_query}%', f'%{search_query}%']
        cursor.execute(query, params)
    else:
        # If empty search, show all photographers
        cursor.execute('SELECT * FROM photographers')
    
    photographers = cursor.fetchall()
    cursor.close()
    
    username = session.get('username')
    
    # Render results page with search results only
    return render_template('results.html',
                         username=username,
                         photographers=photographers,
                         search_query=search_query,
                         is_search_only=True)

# Photographer listing page
@app.route('/photographer')
@app.route('/photographer.html')
def photographer():
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT * FROM photographers')
    photographers = cursor.fetchall()
    cursor.close()
    
    username = session.get('username')
    return render_template('photographer.html', 
                         photographers=photographers,
                         username=username)

# Checkout page
@app.route('/checkout')
@app.route('/checkout.html')
def checkout():
    username = session.get('username')
    return render_template('checkout.html', username=username)

# Registration route
@app.route('/register', methods=['GET', 'POST'])
def register():
    msg = ''
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')
        
        if not username or not password:
            msg = 'Please fill out the form completely!'
        else:
            cursor = mysql.connection.cursor()
            cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
            account = cursor.fetchone()
            
            if account:
                msg = 'Account already exists!'
                cursor.close()
            else:
                cursor.execute('INSERT INTO users (username, password, email) VALUES (%s, %s, %s)',
                             (username, password, email))
                mysql.connection.commit()
                cursor.close()
                flash('You have successfully registered! Please login.', 'success')
                return redirect(url_for('login'))
    
    return render_template('register.html', msg=msg)

# Login route
@app.route('/login', methods=['GET', 'POST'])
@app.route('/vendor.html', methods=['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
        account = cursor.fetchone()
        cursor.close()
        
        if account and account[3] == password:
            # Login successful
            session['loggedin'] = True
            session['id'] = account[0]
            session['username'] = account[1]
            flash('Login successful!', 'success')
            return redirect(url_for('home'))
        else:
            msg = 'Incorrect username or password!'
    
    return render_template('login.html', msg=msg)

# Logout route
@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))

# Profile route
@app.route('/profile')
def profile():
    if 'loggedin' in session:
        username = session['username']
        return render_template('profile.html', username=username)
    flash('Please login to view your profile.', 'warning')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)