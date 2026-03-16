from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime
from functools import wraps
from pdfminer.high_level import extract_text
import os

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        # Check if Authorization header exists
        if "Authorization" in request.headers:
            token = request.headers["Authorization"]

        if not token:
            return jsonify({"error": "Token is missing"}), 401

        try:
            # Remove "Bearer " if you send it that way
            if token.startswith("Bearer "):
                token = token.split(" ")[1]

            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = User.query.get(data["user_id"])

        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401

        return f(current_user, *args, **kwargs)

    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(current_user, *args, **kwargs):
        if current_user.role != "admin":
            return jsonify({"error": "Admin access required"}), 403
        return f(current_user, *args, **kwargs)
    return decorated

app = Flask(__name__)

app.config['SECRET_KEY'] = 'supersecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="candidate")
class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    skills_required = db.Column(db.String(300), nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    job_id = db.Column(db.Integer, db.ForeignKey('job.id'))
    status = db.Column(db.String(20), default="applied")
    resume_path = db.Column(db.String(200))

from pdfminer.high_level import extract_text

def calculate_match(resume_path, job_skills):

    resume_text = extract_text(resume_path).lower()

    skills = [s.strip().lower() for s in job_skills.split(",")]

    matched = []
    missing = []

    for skill in skills:
        if skill in resume_text:
            matched.append(skill)
        else:
            missing.append(skill)

    score = int((len(matched) / len(skills)) * 100) if skills else 0

    return {
        "score": score,
        "matched": matched,
        "missing": missing
    }

@app.route("/")
def home():
    return jsonify({"message": "ATS Backend is Running"})

@app.route("/admin-dashboard", methods=["GET"])
@token_required
@admin_required
def admin_dashboard(current_user):
    return jsonify({
        "message": "Welcome Admin",
        "username": current_user.username
    })

# Register Route (JSON API)
@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()

    username = data.get("username")
    password = data.get("password")
    role = data.get("role", "candidate")  # default candidate

    if not username or not password:
        return jsonify({"error": "Username and password required"}), 400

    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        return jsonify({"error": "User already exists"}), 400

    hashed_password = generate_password_hash(password)

    new_user = User(
        username=username,
        password=hashed_password,
        role=role
    )

    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "User registered successfully"}), 201

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()

    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "Username and password required"}), 400

    user = User.query.filter_by(username=username).first()

    if not user:
        return jsonify({"error": "User not found"}), 404

    if not check_password_hash(user.password, password):
        return jsonify({"error": "Invalid password"}), 401

    # Create JWT token
    token = jwt.encode({
        "user_id": user.id,
        "role": user.role,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=30)
    }, app.config['SECRET_KEY'], algorithm="HS256")

    return jsonify({
        "message": "Login successful",
        "token": token
    }), 200

@app.route("/profile", methods=["GET"])
@token_required
def profile(current_user):
    return jsonify({
        "message": "Access granted",
        "username": current_user.username
    })

@app.route("/create-job", methods=["POST"])
@token_required
@admin_required
def create_job(current_user):

    data = request.get_json()

    title = data.get("title")
    description = data.get("description")
    skills = data.get("skills_required")

    if not title or not description:
        return jsonify({"error": "Title and description required"}), 400

    new_job = Job(
        title=title,
        description=description,
        skills_required=skills,
        created_by=current_user.id
    )

    db.session.add(new_job)
    db.session.commit()

    return jsonify({"message": "Job created successfully"}), 201

@app.route("/apply-job/<int:job_id>", methods=["POST"])
@token_required
def apply_job(current_user, job_id):

    if current_user.role != "candidate":
        return jsonify({"error": "Only candidates can apply"}), 403

    job = Job.query.get(job_id)

    if not job:
        return jsonify({"error": "Job not found"}), 404

    if "resume" not in request.files:
        return jsonify({"error": "Resume required"}), 400

    file = request.files["resume"]

    filepath = os.path.join("resumes", file.filename)
    file.save(filepath)

    application = Application(
        user_id=current_user.id,
        job_id=job_id,
        resume_path=filepath
    )

    db.session.add(application)
    db.session.commit()

    return jsonify({"message": "Application submitted"})

@app.route("/applications", methods=["GET"])
@token_required
@admin_required
def view_applications(current_user):

    applications = Application.query.all()

    result = []

    for app in applications:
        user = User.query.get(app.user_id)
        job = Job.query.get(app.job_id)

        result.append({
            "candidate": user.username,
            "job": job.title,
            "status": app.status
        })

    return jsonify(result)

UPLOAD_FOLDER = "resumes"

@app.route("/upload-resume", methods=["POST"])
@token_required
def upload_resume(current_user):

    if current_user.role != "candidate":
        return jsonify({"error": "Only candidates can upload resumes"}), 403

    if "resume" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["resume"]

    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)

    text = extract_text(filepath)

    return jsonify({
        "message": "Resume uploaded successfully",
        "preview": text[:500]
    })

@app.route("/job-applications/<int:job_id>", methods=["GET"])
@token_required
@admin_required
def view_job_applications(current_user, job_id):

    applications = Application.query.filter_by(job_id=job_id).all()

    results = []

    job = Job.query.get(job_id)

    for app in applications:

        match = calculate_match(app.resume_path, job.skills_required)

        user = User.query.get(app.user_id)

        results.append({
            "candidate": user.username,
            "score": match["score"],
            "matched_skills": match["matched"],
            "missing_skills": match["missing"]
        })

    return jsonify(results)


if __name__ == "__main__":
    app.run(debug=True)