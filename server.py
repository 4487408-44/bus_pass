import http.server
import socketserver
import sqlite3
import json
import hashlib
import os

PORT = int(os.environ.get("PORT", 8082))
DB_NAME = "users.db"

# Initialize SQLite Database
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

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

        username = data.get("username")
        email = data.get("email")
        password = data.get("password")

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        if self.path == '/register':
            if not username or not email or not password:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Missing username, email or password"}).encode())
                return
                
            try:
                cursor.execute('INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)', (username, email, hash_password(password)))
                conn.commit()
                response = {"message": "User registered successfully!"}
                status_code = 201
            except sqlite3.IntegrityError:
                response = {"error": "User already exists!"}
                status_code = 409
        elif self.path == '/login':
            if not email or not password:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Missing email or password"}).encode())
                return
            cursor.execute('SELECT id, password_hash FROM users WHERE email = ?', (email,))
            user = cursor.fetchone()
            
            if user:
                if user[1] == hash_password(password):
                    response = {"message": "Login successful!", "user_id": user[0]}
                    status_code = 200
                else:
                    response = {"error": "Invalid password."}
                    status_code = 401
            else:
                response = {"error": "No login found. Please register as a new user!"}
                status_code = 404
        else:
            response = {"error": "Not found"}
            status_code = 404
            
        conn.close()

        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode())

if __name__ == "__main__":
    init_db()
    import os
    PORT = int(os.environ.get("PORT", 8082))

    with socketserver.TCPServer(("0.0.0.0", PORT), AuthHandler) as httpd:
        print(f"Serving at http://0.0.0.0:{PORT}")
        httpd.serve_forever()