from flask_sqlalchemy import SQLAlchemy
from .extensions import db
from datetime import datetime


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    orders = db.relationship('Order', backref='user', lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "is_admin": self.is_admin,
            "orders": [order.to_dict() for order in self.orders]
        }

class Category(db.Model):
    __tablename__ = 'categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    products = db.relationship('Product', backref='category', lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "products": [product.to_dict() for product in self.products]
        }

class Product(db.Model):
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    image_url = db.Column(db.String(255), nullable=True)
    size_type = db.Column(db.String(50), nullable=False, default="standard")  # "standard" (S, M, L) or "number" (38, 39, 40)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    variants = db.relationship('ProductVariant', backref='product', lazy=True)
    order_items = db.relationship('OrderItem', backref='product', lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "price": self.price,
            "category_id": self.category_id,
            "image_url": self.image_url,
            "size_type": self.size_type,
            "created_at": self.created_at.isoformat(),
            "variants": [variant.to_dict() for variant in self.variants]
        }

class ProductVariant(db.Model):
    __tablename__ = 'product_variants'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    size = db.Column(db.String(20), nullable=False)  # Supports both number & standard sizes
    edition = db.Column(db.String(50), nullable=False)
    stock = db.Column(db.Integer, nullable=False)
    badge = db.Column(db.String(50), nullable=True)  # Optional field for badge type
    font_type = db.Column(db.String(50), nullable=True)  # Optional field for font type
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "product_id": self.product_id,
            "size": self.size,
            "edition": self.edition,
            "stock": self.stock,
            "badge": self.badge,
            "font_type": self.font_type
        }

class Order(db.Model):
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    name = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    location = db.Column(db.String(255), nullable=False)
    id_number = db.Column(db.String(50), nullable=True)  # New field for ID number
    region = db.Column(db.String(255), nullable=False)  # New field for Region
    total_price = db.Column(db.Float, nullable=False)
    payment_status = db.Column(db.String(50), nullable=False, default="Pending")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    items = db.relationship('OrderItem', backref='order', lazy='joined')

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "phone": self.phone,
            "location": self.location,
            "id_number": self.id_number,
            "region": self.region,
            "total_price": self.total_price,
            "payment_status": self.payment_status,
            "created_at": self.created_at.isoformat(),
            "items": [item.to_dict() for item in self.items]
        }

class OrderItem(db.Model):
    __tablename__ = 'order_items'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    size = db.Column(db.String(20), nullable=False)
    edition = db.Column(db.String(50), nullable=False)
    custom_name = db.Column(db.String(50), nullable=True)
    custom_number = db.Column(db.Integer, nullable=True)
    badge = db.Column(db.String(50), nullable=True)
    font_type = db.Column(db.String(50), nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "order_id": self.order_id,
            "product_id": self.product_id,
            "quantity": self.quantity,
            "unit_price": self.unit_price,
            "size": self.size,
            "edition": self.edition,
            "custom_name": self.custom_name,
            "custom_number": self.custom_number,
            "badge": self.badge,
            "font_type": self.font_type,
            "product": self.product.to_dict() if self.product else None
        }