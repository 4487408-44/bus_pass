import http.server
import socketserver
import sqlite3
import json
import hashlib
import os

os.chdir(os.path.dirname(__file__))
PORT = int(os.environ.get("PORT", 8082))

# Define our two separate database files
DB_USERS = "users.db"
DB_PASSES = "passes.db"

# Initialize both SQLite Databases
def init_db():
    # 1. Initialize Users Database
    conn_users = sqlite3.connect(DB_USERS)
    cursor_users = conn_users.cursor()
    cursor_users.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    ''')
    conn_users.commit()
    conn_users.close()
    
    # 2. Initialize Passes Database
    conn_passes = sqlite3.connect(DB_PASSES)
    cursor_passes = conn_passes.cursor()
    cursor_passes.execute('''
        CREATE TABLE IF NOT EXISTS passes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            pass_type TEXT NOT NULL,
            bus_number TEXT NOT NULL,
            issue_date TEXT NOT NULL,
            expiry_date TEXT NOT NULL
        )
    ''')
    conn_passes.commit()
    conn_passes.close()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

class AuthHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.path = '/login.html'
        return http.server.SimpleHTTPRequestHandler.do_GET(self)

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data.decode('utf-8'))

        if self.path == '/register':
            username = data.get("username")
            email = data.get("email")
            password = data.get("password")
            
            if not username or not email or not password:
                return self.send_json_response(400, {"error": "Missing username, email or password"})
                
            with sqlite3.connect(DB_USERS) as conn:
                cursor = conn.cursor()
                try:
                    cursor.execute('INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)', 
                                   (username, email, hash_password(password)))
                    conn.commit()
                    return self.send_json_response(201, {"message": "User registered successfully!"})
                except sqlite3.IntegrityError:
                    return self.send_json_response(409, {"error": "User already exists!"})
                
        elif self.path == '/login':
            email = data.get("email")
            password = data.get("password")
            
            if not email or not password:
                return self.send_json_response(400, {"error": "Missing email or password"})
                
            with sqlite3.connect(DB_USERS) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT id, password_hash FROM users WHERE email = ?', (email,))
                user = cursor.fetchone()
                
                if user and user[1] == hash_password(password):
                    return self.send_json_response(200, {"message": "Login successful!", "user_id": user[0]})
                elif user:
                    return self.send_json_response(401, {"error": "Invalid password."})
                else:
                    return self.send_json_response(404, {"error": "No login found. Please register as a new user!"})
                
        elif self.path == '/add_pass':
            user_id = data.get("user_id")
            pass_type = data.get("pass_type")
            bus_number = data.get("bus_number")
            issue_date = data.get("issue_date")
            expiry_date = data.get("expiry_date")
            
            if not all([user_id, pass_type, bus_number, issue_date, expiry_date]):
                return self.send_json_response(400, {"error": "Missing pass details"})
                
            # Connect to the passes database instead of the users database
            with sqlite3.connect(DB_PASSES) as conn:
                cursor = conn.cursor()
                cursor.execute('''INSERT INTO passes (user_id, pass_type, bus_number, issue_date, expiry_date) 
                                  VALUES (?, ?, ?, ?, ?)''', 
                               (user_id, pass_type, bus_number, issue_date, expiry_date))
                conn.commit()
                return self.send_json_response(201, {"message": "Pass stored successfully!"})
            
        elif self.path == '/get_passes':
            user_id = data.get("user_id")
            
            if not user_id:
                return self.send_json_response(400, {"error": "Missing user_id"})
                
            with sqlite3.connect(DB_PASSES) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT pass_type, bus_number, issue_date, expiry_date FROM passes WHERE user_id = ?', (user_id,))
                passes = [{"pass_type": row[0], "bus_number": row[1], "issue_date": row[2], "expiry_date": row[3]} for row in cursor.fetchall()]
                
                return self.send_json_response(200, {"passes": passes})
            
        else:
            return self.send_json_response(404, {"error": "Not found"})
            
    # Helper method to keep the code clean
    def send_json_response(self, status_code, response_dict):
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*') 
        self.end_headers()
        self.wfile.write(json.dumps(response_dict).encode())

if __name__ == "__main__":
    init_db()
    with socketserver.TCPServer(("0.0.0.0", PORT), AuthHandler) as httpd:
        print(f"Serving at http://0.0.0.0:{PORT}")
        httpd.serve_forever()
