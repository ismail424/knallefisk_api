import sqlite3

class Product:
    def __init__(self, title, price, sale_price=None, on_sale=False, image=None):
        self.title = title
        self.price = price
        self.sale_price = sale_price
        self.on_sale = on_sale
        self.image = image
    
    @classmethod
    def from_dict(cls, data_dict):
        return cls(
            title=data_dict['title'],
            price=data_dict['price'],
            sale_price=data_dict.get('sale_price'),
            on_sale=data_dict.get('on_sale', False),
            image=data_dict.get('image')
        )

    @staticmethod
    def get_all(conn):
        cur = conn.cursor()
        cur.execute('''SELECT * FROM products''')
        rows = cur.fetchall()
        cur.close()
        return rows
    
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
            image TEXT
        )''')
        conn.commit()
        cur.close()
    
    def save(self, conn):
        cur = conn.cursor()
        cur.execute('''INSERT INTO products (
            title, price, sale_price, on_sale, image
        ) VALUES (?, ?, ?, ?, ?)''', (
            self.title,
            self.price,
            self.sale_price,
            int(self.on_sale),
            self.image
        ))
        conn.commit()
        cur.close()
