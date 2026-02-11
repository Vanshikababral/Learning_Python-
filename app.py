from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
import base64 

app = Flask(__name__)
app.secret_key = 'your-secret-key'  # Required for sessions

# Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blogger.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

# --- MODELS ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)

class Blogs(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    author = db.Column(db.String(100), nullable=False)
    owner_id = db.Column(db.Integer, nullable=False)
    image = db.Column(db.LargeBinary, nullable=True)

with app.app_context():
    db.create_all()

# --- ROUTES ---

# 1. REGISTER (Home Page)
@app.route('/', methods=['GET', 'POST'])
def register():
    error = None 
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user_existing = User.query.filter_by(username=username).first()

        if user_existing:
            error = "User already existing. Please use another username."
        else:
            hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
            new_user = User(username=username, password=hashed_password)
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for('login'))

    return render_template('register.html', error=error)

# 2. LOGIN
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        existing_user = User.query.filter_by(username=username).first()

        if existing_user and bcrypt.check_password_hash(existing_user.password, password):
            session['user_id'] = existing_user.id
            session['username'] = existing_user.username
            return redirect(url_for('index'))
        else:
            error = "Invalid username or password"
            
    return render_template('login.html', error=error)

# 3. LOGOUT
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# 4. CREATE BLOG
@app.route('/create', methods=['GET', 'POST'])
def create_blog():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        author = request.form['author']
        owner_id = session['user_id']
        
        image_file = request.files['image'] 
        if image_file:
            image_data = image_file.read()
        else:
            image_data = None

        new_blog = Blogs(
            title=title, 
            content=content, 
            author=author, 
            owner_id=owner_id, 
            image=image_data
        )
        db.session.add(new_blog)
        db.session.commit()
        return redirect(url_for('index'))
    
    return render_template('create_blog.html')

# 5. VIEW ALL BLOGS
@app.route('/blogs')
def index():
    all_blogs = Blogs.query.all()
  
    for blog in all_blogs:
        if blog.image:
            blog.image_b64 = base64.b64encode(blog.image).decode('utf-8')
        else:
            blog.image_b64 = None

    return render_template('index.html', blogs=all_blogs)

# 6. UPDATE BLOG
@app.route('/update/<int:id>', methods=['GET', 'POST'])  # Changed 'sno' to 'id'
def update(id):
    if 'user_id' not in session:
        return redirect('/login')

    # Fetch blog by ID
    blog = Blogs.query.get_or_404(id)

    # Check ownership
    if blog.owner_id != session['user_id']:
        return "You are not authorized to edit this blog!"

    if request.method == 'POST':
        blog.title = request.form['title']
        blog.content = request.form['content']
        blog.author = request.form['author']
        
        file = request.files['image']
        if file:
            blog.image = file.read()

        db.session.commit()
        return redirect(url_for('index'))

    return render_template('update.html', blog=blog)

# 7. DELETE BLOG
@app.route('/delete/<int:id>', methods=['POST']) # Changed 'sno' to 'id'
def delete(id):
    if 'user_id' not in session:
        return redirect('/login')

    blog = Blogs.query.get_or_404(id)

    if blog.owner_id != session['user_id']:
        return "Unauthorized"

    db.session.delete(blog)
    db.session.commit()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)