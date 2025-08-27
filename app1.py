from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import os, json, secrets
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

# AI imports
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
app.config['USER_DB'] = 'users.json'

# ----------------------
# AI Model Initialization
# ----------------------
MODEL_NAME = "HuggingFaceH4/zephyr-7b-beta"  # You can swap with mistralai/Mistral-7B-Instruct-v0.2
print(f"Loading model: {MODEL_NAME}...")

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForCausalLM.from_pretrained(MODEL_NAME)
model.to("cpu")


def generate_ai_response(user_message):
    """Generate AI chat response"""
    messages = [
        {"role": "system", "content": "You are CitizenAI, a helpful and responsible AI assistant."},
        {"role": "user", "content": user_message}
    ]
    inputs = tokenizer.apply_chat_template(
        messages,
        add_generation_prompt=True,
        tokenize=True,
        return_tensors="pt"
    ).to(model.device)

    outputs = model.generate(
        **inputs,
        max_new_tokens=256,
        temperature=0.7,
        top_p=0.9
    )

    return tokenizer.decode(outputs[0][inputs["input_ids"].shape[-1]:], skip_special_tokens=True)

# ----------------------
# User DB Helpers
# ----------------------
def init_user_db():
    if not os.path.exists(app.config['USER_DB']):
        with open(app.config['USER_DB'], 'w') as f:
            json.dump([], f)

def get_users():
    init_user_db()
    with open(app.config['USER_DB'], 'r') as f:
        return json.load(f)

def save_users(users):
    with open(app.config['USER_DB'], 'w') as f:
        json.dump(users, f, indent=2)

def find_user(email):
    for user in get_users():
        if user['email'] == email:
            return user
    return None

def register_user(email, password, first_name, last_name):
    if find_user(email):
        return False, "Email already registered"
    users = get_users()
    users.append({
        'email': email,
        'password': generate_password_hash(password),
        'first_name': first_name,
        'last_name': last_name,
        'created_at': datetime.now().isoformat()
    })
    save_users(users)
    return True, ""

def verify_user(email, password):
    user = find_user(email)
    if not user:
        return False, "User not found"
    if not check_password_hash(user['password'], password):
        return False, "Incorrect password"
    return True, user

# ----------------------
# Routes
# ----------------------
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/services')
def services():
    return render_template('services.html')

@app.route('/chat')
def chat():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('chat.html')

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    error = None
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        success, result = verify_user(email, password)
        if success:
            session['user'] = {
                'email': email,
                'first_name': result['first_name'],
                'last_name': result['last_name']
            }
            return redirect(url_for('dashboard'))
        else:
            error = result
    return render_template('login.html', error=error)

@app.route('/signup', methods=['POST'])
def signup():
    email = request.form.get('email')
    password = request.form.get('password')
    first_name = request.form.get('first_name')
    last_name = request.form.get('last_name')
    success, message = register_user(email, password, first_name, last_name)
    if success:
        session['user'] = {
            'email': email,
            'first_name': first_name,
            'last_name': last_name
        }
        return redirect(url_for('dashboard'))
    return render_template('login.html', signup_error=message, show_signup=True)

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('home'))

# ----------------------
# Chat API Endpoints
# ----------------------
@app.route('/send_message', methods=['POST'])
def send_message():
    if 'user' not in session:
        return jsonify({"error": "Not logged in"}), 401
    data = request.json
    user_message = data.get("message", "")
    if not user_message.strip():
        return jsonify({"error": "Message cannot be empty"}), 400
    ai_reply = generate_ai_response(user_message)
    return jsonify({"reply": ai_reply})

@app.route('/feedback', methods=['POST'])
def feedback():
    if 'user' not in session:
        return jsonify({"error": "Not logged in"}), 401
    data = request.json
    sentiment = data.get("sentiment")
    concern = data.get("concern")
    feedback_entry = {
        "user": session['user']['email'],
        "sentiment": sentiment,
        "concern": concern,
        "timestamp": datetime.now().isoformat()
    }
    with open("feedback.json", "a") as f:
        f.write(json.dumps(feedback_entry) + "\n")
    return jsonify({"status": "Feedback received"})

if __name__ == '__main__':
    app.run(debug=True, port=5001)
