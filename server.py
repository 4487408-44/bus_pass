import http.server
import socketserver
import sqlite3
import json
import hashlib
import os
import razorpay
import json

client = razorpay.Client(auth=("YOUR_KEY_ID", "YOUR_KEY_SECRET"))

def create_order(amount):
    order = client.order.create({
        "amount": amount * 100,   # paise
        "currency": "INR",
        "payment_capture": 1
    })
    return order

from datetime import datetime, timedelta

os.chdir(os.path.dirname(__file__))
PORT = int(os.environ.get("PORT", 8082))

DB_NAME = "bus_pass.db"

# ================= DATABASE INIT =================
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            email TEXT UNIQUE,
            password_hash TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS routes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT,
            destination TEXT,
            distance INTEGER
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS buses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bus_number TEXT,
            route_id INTEGER,
            driver_name TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pass_types (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type_name TEXT,
            validity_days INTEGER,
            price REAL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS passes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            bus_id INTEGER,
            pass_type_id INTEGER,
            issue_date TEXT,
            expiry_date TEXT,
            status TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount REAL,
            payment_date TEXT,
            status TEXT
        )
    ''')

    conn.commit()
    conn.close()

# ================= HASH =================
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ================= HANDLER =================
class Handler(http.server.SimpleHTTPRequestHandler):

    # ✅ MOVE HERE (outside do_POST)
    def send_json(self, code, data):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def do_POST(self):
        try:
            content_length = int(self.headers['Content-Length'])
            raw_data = self.rfile.read(content_length).decode()
            data = json.loads(raw_data)
        except:
            return self.send_json(400, {"error": "Invalid JSON"})
            
        # ========= REGISTER =========
        if self.path == '/register':
            username = data.get("username")
            email = data.get("email")
            password = data.get("password")

            if not username or not email or not password:
                return self.send_json(400, {"error": "Missing fields"})

            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()

            try:
                cursor.execute(
                    "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
                    (username, email, hash_password(password))
                )
                conn.commit()
                return self.send_json(201, {"message": "Registered successfully"})
            except sqlite3.IntegrityError:
                return self.send_json(409, {"error": "User already exists"})

        # ========= LOGIN =========
        elif self.path == '/login':
            email = data.get("email")
            password = data.get("password")

            if not email or not password:
                return self.send_json(400, {"error": "Missing email or password"})

            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("SELECT id, password_hash FROM users WHERE email=?", (email,))
            user = cursor.fetchone()

            if user and user[1] == hash_password(password):
                return self.send_json(200, {"user_id": user[0]})
            elif user:
                return self.send_json(401, {"error": "Invalid password"})
            else:
                return self.send_json(404, {"error": "User not found"})

        # ========= ADD PASS =========
        elif self.path == '/add_pass':
            print("==== ADD PASS API CALLED ====")
            print("DATA RECEIVED:", data)
            
            user_id = data.get("user_id")
            bus_id = data.get("bus_id")
            pass_type_id = data.get("pass_type_id")

            if not all([user_id, bus_id, pass_type_id]):
                return self.send_json(400, {"error": "Missing pass details"})

            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()

            cursor.execute("SELECT validity_days, price FROM pass_types WHERE id=?", (pass_type_id,))
            pt = cursor.fetchone()

            if not pt:
                return self.send_json(400, {"error": "Invalid pass type"})

            validity_days, price = pt

            issue_date = datetime.now()
            expiry_date = issue_date + timedelta(days=validity_days)
            
            cursor.execute('''
                INSERT INTO passes (user_id, bus_id, pass_type_id, issue_date, expiry_date, status)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                bus_id,
                pass_type_id,
                issue_date.strftime("%Y-%m-%d"),
                expiry_date.strftime("%Y-%m-%d"),
                "Active"
            ))

            cursor.execute('''
                INSERT INTO payments (user_id, amount, payment_date, status)
                VALUES (?, ?, ?, ?)
            ''', (
                user_id,
                price,
                issue_date.strftime("%Y-%m-%d"),
                "Paid"
            ))
            
            print("PASS INSERTED SUCCESSFULLY")

            conn.commit()
            return self.send_json(201, {"message": "Pass created successfully"})

        # ========= GET PASSES =========
        elif self.path == '/get_passes':
           
            user_id = data.get("user_id")
            
            print("Fetching passes for user_id:", user_id)
            
            if not user_id:
                return self.send_json(400, {"error": "Missing user_id"})

            today = datetime.now().strftime("%Y-%m-%d")

            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()

            cursor.execute('''
                SELECT p.id, pt.type_name, b.bus_number, p.issue_date, p.expiry_date
                FROM passes p
                JOIN pass_types pt ON p.pass_type_id = pt.id
                JOIN buses b ON p.bus_id = b.id
                WHERE p.user_id = ? AND p.expiry_date >= ?
            ''', (user_id, today))

            rows = cursor.fetchall()

            passes = []
            for r in rows:
                passes.append({
                    "pass_id": r[0],
                    "type": r[1],
                    "bus": r[2],
                    "issue_date": r[3],
                    "expiry_date": r[4]
                })

            return self.send_json(200, {"passes": passes})

        elif self.path == "/create_order":
            amount = data.get("amount")

            if not amount:
                return self.send_json(400, {"error": "Missing amount"})

            order = create_order(amount)
            return self.send_json(200, order)

        else:
            return self.send_json(404, {"error": "Not found"})
        # ========= RESPONSE =========
        def send_json(self, code, data):
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(data).encode())

# ================= RUN =================
if __name__ == "__main__":
    init_db()
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("0.0.0.0", PORT), Handler) as server:
        print(f"Server running at http://localhost:{PORT}")
        server.serve_forever()