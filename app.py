from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.secret_key = "ogms_secret_key"

# ---------------- Database Setup ----------------
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# ---------------- Login Manager -----------------
login_manager = LoginManager(app)
login_manager.login_view = 'login'


# ---------------- User Model --------------------
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    contact = db.Column(db.String(15))
    role = db.Column(db.String(10), default='User')  # User / Admin


# ---------------- Grievance Model ----------------
class Grievance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    name = db.Column(db.String(100))
    email = db.Column(db.String(100))
    category = db.Column(db.String(50))
    complaint = db.Column(db.Text)
    status = db.Column(db.String(50), default='Pending')
    priority = db.Column(db.String(20), default='Normal')
    admin_remark = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ---------------- ROUTES ----------------

@app.route('/')
def home():
    return render_template('home.html', active_page='home')


# -------- Register --------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        contact = request.form['contact']
        role = request.form['role']

        if User.query.filter_by(email=email).first():
            flash("Email already exists!", "danger")
            return redirect(url_for('register'))

        new_user = User(name=name, email=email, password=password, contact=contact, role=role)
        db.session.add(new_user)
        db.session.commit()

        flash("Account created successfully! Please login.", "success")
        return redirect(url_for('login'))

    return render_template('register.html', active_page='register')


# -------- Login --------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            flash("Login successful!", "success")
            if user.role == 'Admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('user_dashboard'))
        else:
            flash("Invalid email or password!", "danger")
            return redirect(url_for('login'))

    return render_template('login.html', active_page='login')


# -------- Logout --------
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Logged out successfully.", "info")
    return redirect(url_for('login'))


# -------- Submit Grievance --------
@app.route('/grievance', methods=['GET', 'POST'])
@login_required
def grievance():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        category = request.form['category']
        complaint = request.form['complaint']
        priority = request.form.get('priority', 'Normal')

        new_grievance = Grievance(user_id=current_user.id, name=name, email=email,
                                  category=category, complaint=complaint, priority=priority)
        db.session.add(new_grievance)
        db.session.commit()

        flash("✅ Your grievance has been submitted successfully!", "success")
        return redirect(url_for('grievance'))

    return render_template('grievance.html', active_page='grievance')


# -------- User Dashboard --------
@app.route('/user_dashboard')
@login_required
def user_dashboard():
    grievances = Grievance.query.filter_by(user_id=current_user.id).order_by(Grievance.created_at.desc()).all()
    stats = {
        'total': len(grievances),
        'pending': sum(1 for g in grievances if g.status == 'Pending'),
        'resolved': sum(1 for g in grievances if g.status == 'Resolved')
    }
    return render_template('user_dashboard.html', grievances=grievances, stats=stats, active_page='user_dashboard')


# -------- Admin Dashboard --------
@app.route('/admin_dashboard')
@login_required
def admin_dashboard():
    if current_user.role != 'Admin':
        flash("Access denied!", "danger")
        return redirect(url_for('home'))

    grievances = Grievance.query.order_by(Grievance.created_at.desc()).all()
    stats = {
        'total': len(grievances),
        'pending': sum(1 for g in grievances if g.status == 'Pending'),
        'in_progress': sum(1 for g in grievances if g.status == 'In Progress'),
        'resolved': sum(1 for g in grievances if g.status == 'Resolved')
    }
    return render_template('admin_dashboard.html', grievances=grievances, stats=stats, active_page='admin_dashboard')


# -------- Update Status (Admin Only) --------
@app.route('/update_status/<int:id>', methods=['POST'])
@login_required
def update_status(id):
    if current_user.role != 'Admin':
        flash("Access denied!", "danger")
        return redirect(url_for('home'))

    grievance = Grievance.query.get_or_404(id)
    grievance.status = request.form.get('status', 'Pending')
    grievance.admin_remark = request.form.get('admin_remark', '')
    db.session.commit()
    flash("Grievance updated successfully!", "success")
    return redirect(url_for('admin_dashboard'))


# -------- Run the App --------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
