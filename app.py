from flask import Flask, request, render_template, redirect
from flask_mysqldb import MySQL
from flask_cors import CORS
import bcrypt
import random
from config import Config

app = Flask(__name__)
CORS(app)

# -----------------------------
# MySQL Configuration
# -----------------------------
app.config['MYSQL_HOST'] = Config.MYSQL_HOST
app.config['MYSQL_USER'] = Config.MYSQL_USER
app.config['MYSQL_PASSWORD'] = Config.MYSQL_PASSWORD
app.config['MYSQL_DB'] = Config.MYSQL_DB
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)

# -----------------------------
# HOME
# -----------------------------
@app.route('/')
def home():
    return render_template('index.html')

# -----------------------------
# REGISTER
# -----------------------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')

    data = request.form
    fullname = data['fullname']
    email = data['email']
    password = data['password']
    confirm_password = data['confirm_password']
    phone = data['phone']
    account_type = data['account_type']

    if password != confirm_password:
        return render_template('register.html', error="Passwords do not match")

    cur = mysql.connection.cursor()

    # Check existing user
    cur.execute("SELECT * FROM clients WHERE email=%s", (email,))
    if cur.fetchone():
        cur.close()
        return render_template('register.html', error="User already exists")

    # Hash password
    hashed_password = bcrypt.hashpw(
        password.encode('utf-8'),
        bcrypt.gensalt()
    ).decode('utf-8')

    # Insert client
    cur.execute("""
        INSERT INTO clients (fullname, email, password, phone)
        VALUES (%s, %s, %s, %s)
    """, (fullname, email, hashed_password, phone))

    mysql.connection.commit()
    user_id = cur.lastrowid

    # ✅ FIXED ACCOUNT INSERT
    account_number = "AC" + str(random.randint(10000, 99999))

    cur.execute("""
        INSERT INTO accounts (client_id, account_number, account_type, balance)
        VALUES (%s, %s, %s, %s)
    """, (user_id, account_number, account_type, 0))

    mysql.connection.commit()
    cur.close()

    return redirect('/login')

# -----------------------------
# LOGIN
# -----------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    email = request.form['email']
    password = request.form['password']

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM clients WHERE email=%s", (email,))
    user = cur.fetchone()
    cur.close()

    if user and bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
        return redirect('/dashboard')
    else:
        return render_template('login.html', error="Invalid email or password")

# -----------------------------
# DASHBOARD
# -----------------------------
@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

# -----------------------------
# ACCOUNTS
# -----------------------------
@app.route('/accounts')
def accounts():
    cur = mysql.connection.cursor()

    cur.execute("SELECT * FROM accounts")
    accounts = cur.fetchall()

    cur.close()

    return render_template('accounts.html', accounts=accounts)

# -----------------------------
# TRANSACTIONS
# -----------------------------
@app.route('/transactions')
def transactions():
    return render_template('transactions.html')

# -----------------------------
# LOANS
# -----------------------------
@app.route('/loans', methods=['GET', 'POST'])
def loans():
    if request.method == 'GET':
        return render_template('loans.html')

    try:
        data = request.form
        user_email = data.get('user_email', 'test@example.com')

        loan_type = data['loan_type']
        amount = float(data['loan_amount'])
        duration = int(data['loan_duration'])
        annual_income = float(data['annual_income'])

        cur = mysql.connection.cursor()

        # Get user id
        cur.execute("SELECT id FROM clients WHERE email=%s", (user_email,))
        user = cur.fetchone()

        if not user:
            cur.close()
            return render_template('loans.html', error="User not found")

        client_id = user['id']

        # Insert loan
        cur.execute("""
            INSERT INTO loans 
            (client_id, loan_type, amount, duration_years, annual_income, status)
            VALUES (%s,%s,%s,%s,%s,%s)
        """, (client_id, loan_type, amount, duration, annual_income, 'Pending'))

        mysql.connection.commit()
        cur.close()

        return render_template('loans.html', success="Loan applied successfully")

    except Exception as e:
        print("Loan Error:", e)
        return render_template('loans.html', error="Something went wrong")

# -----------------------------
# RUN APP
# -----------------------------
if __name__ == "__main__":
    app.run(debug=True)