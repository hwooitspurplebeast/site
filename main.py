from flask import Flask, render_template, request, redirect, session
import psycopg2
from datetime import datetime

app = Flask(__name__)

# Secret key for sessions
app.secret_key = 'your_secret_key'

# Database connection settings
DB_URI = 'postgresql://neondb_owner:EcI5aqLhX2Gd@ep-blue-lake-a5esrj33.us-east-2.aws.neon.tech/neondb?sslmode=require'

# Items and prices
items = [
    {"name": "500 Members", "cost": 4, "members": "500 Members"},
    {"name": "1000 Members", "cost": 7, "members": "1000 Members"},
    {"name": "2000 Members", "cost": 14, "members": "2000 Members"},
    {"name": "3000 Members", "cost": 18, "members": "3000 Members"},
    {"name": "4000 Members", "cost": 24, "members": "4000 Members"},
    {"name": "5000 Members", "cost": 27, "members": "5000 Members"},
    {"name": "7500 Members", "cost": 32, "members": "7500 Members"},
    {"name": "9000 Members", "cost": 36, "members": "9000 Members"}
]

# Flag to ensure tables are created only once
tables_created = False

def get_db_connection():
    """Create and return a database connection."""
    conn = psycopg2.connect(DB_URI)
    return conn

def create_tables():
    """Create the necessary tables in the database if they don't exist."""
    conn = get_db_connection()
    cur = conn.cursor()

    # Create Orders table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id SERIAL PRIMARY KEY,
        user_name VARCHAR(100),
        discord_server VARCHAR(100),
        discord_username VARCHAR(100),
        email VARCHAR(100),
        social_media VARCHAR(100),
        ip_of_user VARCHAR(100),
        timestamp TIMESTAMP
    );
    """)

    # Create Items table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS items (
        id SERIAL PRIMARY KEY,
        name VARCHAR(100),
        cost INT,
        quantity INT,
        order_id INT,
        FOREIGN KEY (order_id) REFERENCES orders(id)
    );
    """)

    conn.commit()
    cur.close()
    conn.close()

@app.before_request
def initialize_db():
    """Run the table creation once, before the first request."""
    global tables_created
    if not tables_created:
        create_tables()
        tables_created = True

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        cart = {}
        for item in items:
            quantity = int(request.form.get(item['name'], 0))  # Get quantity from form input
            if quantity > 0:
                cart[item['name']] = quantity
        session['cart'] = cart  # Store cart in session
        return redirect('/order')
    return render_template('index.html', items=items)

@app.route('/order', methods=['GET', 'POST'])
def order():
    if request.method == 'POST':
        # Collect user information
        name = request.form['name']
        discord_server = request.form['discord_server']
        discord_username = request.form['discord_username']
        email = request.form['email']
        social_media = request.form['social_media']

        # Get items in cart from session
        items_in_cart = session.get('cart', {})

        # Prepare order data
        conn = get_db_connection()
        cur = conn.cursor()

        # Insert order details
        cur.execute("""
        INSERT INTO orders (user_name, discord_server, discord_username, email, social_media, ip_of_user, timestamp)
        VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id;
        """, (name, discord_server, discord_username, email, social_media, request.remote_addr, datetime.now()))

        order_id = cur.fetchone()[0]  # Get the generated order ID

        # Insert items into the items table
        for item, quantity in items_in_cart.items():
            item_cost = next(i['cost'] for i in items if i['name'] == item)
            cur.execute("""
            INSERT INTO items (name, cost, quantity, order_id)
            VALUES (%s, %s, %s, %s);
            """, (item, item_cost, quantity, order_id))

        conn.commit()
        cur.close()
        conn.close()

        # Clear the session cart after order is submitted
        session.pop('cart', None)

        return redirect('/thank_you')

    # Get the items in the cart (from session)
    items_in_cart = session.get('cart', {})

    # Calculate total cost
    total_cost = 0
    for item, quantity in items_in_cart.items():
        # Find the cost of each item
        item_cost = next(i['cost'] for i in items if i['name'] == item)
        total_cost += item_cost * quantity

    return render_template('order.html', items_in_cart=items_in_cart, total_cost=total_cost)

@app.route('/thank_you')
def thank_you():
    return render_template('thanks.html')

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8080, debug=True)
