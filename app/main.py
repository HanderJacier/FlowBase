import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.models.base import Base, Product, User
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import uuid

app = Flask(__name__)
app.secret_key = 'flowbase-secret-key-2024'

# Database
engine = create_engine("sqlite:///stash_forge.db")
Base.metadata.create_all(engine)

def ensure_db_schema():
    with engine.connect() as conn:
        result = conn.execute(text("PRAGMA table_info(products)"))
        existing_columns = [row[1] for row in result.fetchall()]
        if 'employee' not in existing_columns:
            conn.execute(text("ALTER TABLE products ADD COLUMN employee VARCHAR DEFAULT ''"))
        if 'position' not in existing_columns:
            conn.execute(text("ALTER TABLE products ADD COLUMN position VARCHAR DEFAULT ''"))
        conn.commit()

ensure_db_schema()

Session = sessionmaker(bind=engine)

def get_db_session():
    return Session()

# Helper function for CSRF token
def generate_csrf_token():
    if 'csrf_token' not in session:
        session['csrf_token'] = str(uuid.uuid4())
    return session['csrf_token']

app.jinja_env.globals['csrf_token'] = generate_csrf_token

def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        return func(*args, **kwargs)
    return wrapper

def validate_csrf():
    token = request.form.get('csrf_token') or request.headers.get('X-CSRFToken')
    return token and token == session.get('csrf_token')

# Routes
@app.route('/')
@login_required
def index():
    session_db = get_db_session()
    products = session_db.query(Product).all()
    session_db.close()
    return render_template('index.html', products=products)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user' in session:
        return redirect(url_for('index'))

    if request.method == 'POST':
        if not validate_csrf():
            return render_template('login.html', error='Token CSRF không hợp lệ')

        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        if not username or not password:
            return render_template('login.html', error='Vui lòng nhập đầy đủ thông tin')

        session_db = get_db_session()
        user = session_db.query(User).filter_by(username=username).first()
        session_db.close()

        if user and check_password_hash(user.password_hash, password):
            session['user'] = user.username
            return redirect(url_for('index'))
        return render_template('login.html', error='Tên đăng nhập hoặc mật khẩu không đúng')

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user' in session:
        return redirect(url_for('index'))

    if request.method == 'POST':
        if not validate_csrf():
            return render_template('register.html', error='Token CSRF không hợp lệ')

        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()

        if not username or not password or not confirm_password:
            return render_template('register.html', error='Vui lòng nhập đầy đủ thông tin')
        if password != confirm_password:
            return render_template('register.html', error='Mật khẩu xác nhận không khớp')

        session_db = get_db_session()
        if session_db.query(User).filter_by(username=username).first():
            session_db.close()
            return render_template('register.html', error='Tên đăng nhập đã tồn tại')

        password_hash = generate_password_hash(password)
        new_user = User(username=username, password_hash=password_hash)
        session_db.add(new_user)
        session_db.commit()
        session_db.close()
        session['user'] = username
        return redirect(url_for('index'))

    return render_template('register.html')

@app.route('/api/tasks')
@login_required
def api_tasks():
    session_db = get_db_session()
    products = session_db.query(Product).all()
    tasks = [
        {
            'id': p.id,
            'name': p.name,
            'employee': p.employee,
            'position': p.position,
            'done': p.quantity > 0
        }
        for p in products
    ]
    session_db.close()
    return jsonify({'tasks': tasks})

@app.route('/add', methods=['POST'])
@login_required
def add_task():
    name = request.form.get('name')
    employee = request.form.get('employee', '')
    position = request.form.get('position', '')
    if name:
        session_db = get_db_session()
        new_product = Product(
            name=name,
            sku=str(uuid.uuid4()),
            quantity=0,
            employee=employee,
            position=position
        )
        session_db.add(new_product)
        session_db.commit()
        session_db.close()
    return redirect(url_for('index'))

@app.route('/edit/<int:task_id>', methods=['POST'])
@login_required
def edit_task(task_id):
    name = request.form.get('name')
    employee = request.form.get('employee', '')
    position = request.form.get('position', '')
    status = request.form.get('status', 'pending')
    session_db = get_db_session()
    product = session_db.query(Product).get(task_id)
    if product and name:
        product.name = name
        product.employee = employee
        product.position = position
        product.quantity = 1 if status == 'completed' else 0
        session_db.commit()
    session_db.close()
    return jsonify({'success': True})

@app.route('/toggle/<int:task_id>')
@login_required
def toggle_task(task_id):
    session_db = get_db_session()
    product = session_db.query(Product).get(task_id)
    if product:
        product.quantity = 1 if product.quantity == 0 else 0
        session_db.commit()
    session_db.close()
    return redirect(url_for('index'))

@app.route('/delete/<int:task_id>', methods=['POST'])
@login_required
def delete_task(task_id):
    session_db = get_db_session()
    product = session_db.query(Product).get(task_id)
    if product:
        session_db.delete(product)
        session_db.commit()
    session_db.close()
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

@app.route('/csrf_token')
def csrf_token():
    return jsonify({'token': generate_csrf_token()})

if __name__ == '__main__':
    print("🚀 Chạy ứng dụng FlowBase tại: http://127.0.0.1:5000")
    app.run(debug=True, port=5000)