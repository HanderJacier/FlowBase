import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.base import Base, Product
import uuid

app = Flask(__name__)
app.secret_key = 'flowbase-secret-key-2024'

# Database
engine = create_engine("sqlite:///stash_forge.db")
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

def get_db_session():
    return Session()

# Helper function for CSRF token
def generate_csrf_token():
    if 'csrf_token' not in session:
        session['csrf_token'] = str(uuid.uuid4())
    return session['csrf_token']

app.jinja_env.globals['csrf_token'] = generate_csrf_token

# Routes
@app.route('/')
def index():
    session_db = get_db_session()
    products = session_db.query(Product).all()
    session_db.close()
    return render_template('index.html', products=products)

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/api/tasks')
def api_tasks():
    session_db = get_db_session()
    products = session_db.query(Product).all()
    tasks = [{'id': p.id, 'name': p.name, 'done': p.quantity > 0} for p in products]
    session_db.close()
    return jsonify({'tasks': tasks})

@app.route('/add', methods=['POST'])
def add_task():
    name = request.form.get('name')
    if name:
        session_db = get_db_session()
        new_product = Product(name=name, sku='', quantity=0)
        session_db.add(new_product)
        session_db.commit()
        session_db.close()
    return redirect(url_for('index'))

@app.route('/toggle/<int:task_id>')
def toggle_task(task_id):
    session_db = get_db_session()
    product = session_db.query(Product).get(task_id)
    if product:
        product.quantity = 1 if product.quantity == 0 else 0
        session_db.commit()
    session_db.close()
    return redirect(url_for('index'))

@app.route('/delete/<int:task_id>', methods=['POST'])
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
    return redirect(url_for('login'))

@app.route('/csrf_token')
def csrf_token():
    return jsonify({'token': generate_csrf_token()})

if __name__ == '__main__':
    print("🚀 Chạy ứng dụng FlowBase tại: http://127.0.0.1:5000")
    app.run(debug=True, port=5000)