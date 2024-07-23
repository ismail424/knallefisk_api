from flask import Flask, flash, g, session, render_template, redirect, request
from flask_cors import CORS
from flask_session import Session
from werkzeug.utils import secure_filename
from model import Product
from PIL import Image
import os
import json
import sqlite3
from datetime import timedelta

UPLOAD_FOLDER = os.path.join(os.getcwd(), 'static', 'uploads')
DATABASE = "database.db"

app = Flask(__name__)
CORS(app)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=365)

Session(app)

from dotenv import load_dotenv
load_dotenv()

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    cursor = db.cursor()
    return db, cursor

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

@app.before_first_request
def startup():
    db, cursor = get_db()
    print("Creating products table...")
    Product.create_table(db)


@app.route("/")
def index():
    if "username" not in session:
        return redirect("/login")
    
    username = session["username"]
    db, cursor = get_db()
    products = Product.get_all(db)
    return render_template("index.html", products=products)

@app.route("/add", methods=["GET", "POST"])
def add():
    if "username" not in session:
        return redirect("/login")

    if request.method == 'POST':
        title = request.form['title']
        price = request.form['price']
        sale_price = request.form['sale_price'] if 'on_sale' in request.form else None
        on_sale = 'on_sale' in request.form
        is_visible = 'is_visible' in request.form
        image = request.files['image'] if 'image' in request.files and request.files['image'].filename != "" else None
        
        if image:
            filename = secure_filename(image.filename)
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            image.save(filepath)
            img = Image.open(filepath)
            img.save(filepath, optimize=True, quality=70)
            image_filename = filename
        else:
            image_filename = None

                    
        # Create a new Product object and save it to the database
        new_product = Product(
            title=title,
            price=price,
            sale_price=sale_price,
            on_sale=on_sale,
            is_visible=is_visible,
            image=image_filename
        )        
        db, cursor = get_db()
        new_product.save(db)
        
        return redirect("/")
    
    return render_template("create.html")

@app.route("/delete/<int:id>", methods=["POST"])
def delete(id):
    if "username" not in session:
        return redirect("/login")
    
    db, cursor = get_db()
    cursor.execute("DELETE FROM products WHERE id=?", (id,))
    db.commit()
    cursor.close()
    
    flash(f"Product with ID {id} has been deleted.", "success")
    return redirect("/")

@app.route("/edit/<int:product_id>", methods=["GET", "POST"])
def edit(product_id):
    if "username" not in session:
        return redirect("/login")

    db, cursor = get_db()
    product = Product.get_by_id(db, product_id)

    if not product:
        return "Product not found"

    if request.method == 'POST':
        title = request.form['title']
        price = request.form['price']
        sale_price = request.form['sale_price'] if 'on_sale' in request.form else None
        on_sale = 'on_sale' in request.form
        is_visible = 'is_visible' in request.form
        image = request.files['image'] if 'image' in request.files and request.files['image'].filename != "" else None
        
        # If a new image is uploaded, delete the old one and save the new one
        if image:
            if product['image']:
                old_image_path = os.path.join(app.config["UPLOAD_FOLDER"], product['image'])
                if os.path.exists(old_image_path):
                    os.remove(old_image_path)
            
            # Save the new image to disk
            image_path = os.path.join(app.config["UPLOAD_FOLDER"], image.filename)
            image.save(image_path)
            new_image_filename = image.filename
        else:
            new_image_filename = product['image']
        
        # Update the product with or without changing the image path
        cur = db.cursor()
        cur.execute(
            '''UPDATE products SET title = ?, price = ?, sale_price = ?, on_sale = ?, is_visible = ?, image = ? 
            WHERE id = ?''',
            (title, price, sale_price, int(on_sale), int(is_visible), new_image_filename, product_id)
        )
        db.commit()

        return redirect("/")

    return render_template("edit.html", product=product)



@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        username_env = os.environ.get("APP_USERNAME")
        password_env = os.environ.get("APP_PASSWORD")
        # Check if the username and password are correct, ignore case
        if username.lower() == username_env.lower() and password == password_env:
            session["username"] = username_env
            session.permanent = True
            return redirect("/")
        else:
            return render_template("login.html", error="Invalid username or password.")
    return render_template("login.html")

@app.route("/logout", methods=["GET", "POST"])
def logout():
    session.pop("username", None)
    return redirect("/")

# API routes
@app.route("/api/products")
def get_all_products():
    try:
        db, cur = get_db()
        cur.execute("SELECT * FROM products")
        rows = cur.fetchall()
        return  json.dumps(Product.get_all(db))
    except Exception as e:
        print(e)
        return []
    
if __name__ == "__main__":
    app.secret_key = os.environ.get("SECRET_KEY")
    app.run(debug=True, port=5000)
