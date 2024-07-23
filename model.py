import sqlite3

class Product:
    def __init__(self, title, price, sale_price=None, on_sale=False, image=None, is_visible=True):
        self.title = title
        self.price = price
        self.sale_price = sale_price
        self.on_sale = on_sale
        self.image = image
        self.is_visible = is_visible
    
    @classmethod
    def from_dict(cls, data_dict):
        return cls(
            title=data_dict['title'],
            price=data_dict['price'],
            sale_price=data_dict.get('sale_price'),
            on_sale=data_dict.get('on_sale', False),
            image=data_dict.get('image'),
            is_visible=data_dict.get('is_visible', True)
        )

    @staticmethod
    def get_all(conn):
        cur = conn.cursor()
        cur.execute('''SELECT * FROM products''')
        rows = cur.fetchall()
        cur.close()
        
        tmp_rows = []
        # Convert to integer and boolean, i dont want decimals, remove decimal from price and sale price
        for row in rows:
            tmp_rows.append({
                "id": row[0],
                "title": row[1],
                "price": int(row[2]),
                "sale_price": int(row[3]) if row[3] else None,
                "on_sale": bool(row[4]),
                "image": row[5],
                "is_visible": bool(row[6])
            })
        return tmp_rows
    
    @staticmethod
    def get_by_id(conn, id):
        cur = conn.cursor()
        cur.execute('''SELECT * FROM products WHERE id=?''', (id,))
        row = cur.fetchone()
        cur.close()
        return row
    
    
    @staticmethod
    def create_table(conn):
        cur = conn.cursor()
        cur.execute('''CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY,
            title TEXT,
            price REAL,
            sale_price REAL,
            on_sale INTEGER,
            image TEXT,
            is_visible INTEGER
        )''')
        conn.commit()
        cur.close()
    
    def save(self, conn):
        cur = conn.cursor()
        cur.execute('''INSERT INTO products (
            title, price, sale_price, on_sale, image, is_visible
        ) VALUES (?, ?, ?, ?, ?, ?)''', (
            self.title,
            self.price,
            self.sale_price,
            int(self.on_sale),
            self.image,
            int(self.is_visible)
        ))
        conn.commit()
        cur.close()

    def update(self, conn, id):
        cur = conn.cursor()
        cur.execute('''UPDATE products SET 
            title = ?, 
            price = ?, 
            sale_price = ?, 
            on_sale = ?, 
            image = ?, 
            is_visible = ? 
        WHERE id = ?''', (
            self.title,
            self.price,
            self.sale_price,
            int(self.on_sale),
            self.image,
            int(self.is_visible),
            id
        ))
        conn.commit()
        cur.close()
