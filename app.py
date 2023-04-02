from flask import Flask, flash, g, session, render_template, redirect, request
from flask_cors import CORS
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from model import Product
from PIL import Image
import os
import json
import sqlite3

UPLOAD_FOLDER = os.path.join(os.getcwd(), 'static', 'uploads')
DATABASE = "database.db"

app = Flask(__name__)
CORS(app)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

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

    if request.method == "POST":
        title = request.form["title"]
        price = request.form["price"]
        sale_price = request.form.get("sale_price")
        on_sale = bool(request.form.get("on_sale"))
        if "image" in request.files:
            image = request.files["image"]
        else:
            image = None
            
        if not title or not price or not image:
            error = "Title, price, and image are required"
            return render_template("create.html", error=error)
        
        if image.filename != "":
            filename = secure_filename(image.filename)
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            image.save(filepath)
            img = Image.open(filepath)
            img.save(filepath, optimize=True, quality=70)
                    
        # Create a new Product object and save it to the database
        product = Product(title=title, price=price, sale_price=sale_price, on_sale=on_sale, image=filename)
        db, cursor = get_db()
        product.save(db)
        
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

    db, cur = get_db()
    product =  Product.get_by_id(db, product_id)

    if not product:
        return "Product not found"

    if request.method == "POST":
        # Update the product with the new data
        title = request.form.get("title")
        price = request.form.get("price")
        sale_price = request.form.get("sale_price")
        on_sale = request.form.get("on_sale") == "on"

        image = request.files.get("image")
        filename = secure_filename(image.filename)

        if filename:

            # Delete the old image
            old_image_path = os.path.join(app.config["UPLOAD_FOLDER"], product["image"])
            os.remove(old_image_path)
            
            # Save the image to disk
            image_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            image.save(image_path)

            # Update the product with the new image path
            cur.execute(
                "UPDATE products SET title = ?, price = ?, sale_price = ?, on_sale = ?, image = ? WHERE id = ?",
                (title, price, sale_price, on_sale, filename, product_id),
            )
            
        else:
            # Update the product without changing the image path
            cur.execute(
                "UPDATE products SET title = ?, price = ?, sale_price = ?, on_sale = ? WHERE id = ?",
                (title, price, sale_price, on_sale, product_id),
            )

        db.commit()

        return redirect("/")

    return render_template("edit.html", product=product)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        username_env = os.environ.get("USERNAME")
        password_env = os.environ.get("PASSWORD")

        if username == username_env and password == password_env:
            session["username"] = username
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

        products = []
        for row in rows:
            product = {
                "id": row["id"],
                "title": row["title"],
                "price": row["price"],
                "sale_price": row["sale_price"],
                "on_sale": row["on_sale"],
                "image": row["image"]
            }
            products.append(product)

        return  json.dumps(products)
    except Exception as e:
        print(e)
        return []
    
if __name__ == "__main__":
    app.secret_key = os.environ.get("SECRET_KEY")
    app.run(debug=True, port=5000)
