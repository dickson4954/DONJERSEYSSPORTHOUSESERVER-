from werkzeug.security import generate_password_hash
from myapp import create_app
from myapp.models import User, Category, Product, ProductVariant, Order, OrderItem
from myapp.extensions import db
from datetime import datetime

def seed_data():
    # Clear existing data in reverse order to avoid foreign key constraints
    db.session.query(OrderItem).delete()
    db.session.query(Order).delete()
    db.session.query(ProductVariant).delete()
    db.session.query(Product).delete()
    db.session.query(Category).delete()
    db.session.query(User).delete()
    db.session.commit()

    # Create admin and regular users
    users = [
        User(username="admin", email="admin@gmail.com", password_hash=generate_password_hash("admin123"), is_admin=True),
        User(username="john_doe", email="john@gmail.com", password_hash=generate_password_hash("password")),
        User(username="jane_doe", email="jane@gmail.com", password_hash=generate_password_hash("password")),
    ]

    # Add categories
    categories = [
        Category(name="Jerseys"),
        Category(name="Sportswear"),
        Category(name="Gym Equipment"),
    ]

    # Add products
    products = [
        Product(name="Arsenal Home Jersey 2024", description="Latest Arsenal home jersey.", price=1500, category_id=1, image_url="https://i1.adis.ws/i/ArsenalDirect/mit6141_f?&$plpImages$"),
        Product(name="Arsenal Away Jersey 2024", description="Latest Arsenal away jersey.", price=1500, category_id=1, image_url="https://i1.adis.ws/i/ArsenalDirect/mit6148_f?&$plpImages$"),
        Product(name="Arsenal Third Jersey 2024", description="Latest Arsenal third jersey.", price=1500, category_id=1, image_url="https://i1.adis.ws/i/ArsenalDirect/miz0114_f?&$plpImages$"),
        Product(name="Man Utd Home Jersey 2024", description="Latest Manchester United home jersey.", price=1500, category_id=1, image_url="https://mufc-live.cdn.scayle.cloud/images/032465a23bed509d050589e6439809a2.jpg"),
        Product(name="Chelsea Home Jersey 2024", description="Latest Chelsea home jersey.", price=1500, category_id=1, image_url="https://havencraft.co.ke/wp-content/uploads/2024/08/chelsea-nike-home-stadium-shirt-2024-25_ss5_p-200851164pv-2u-canixtzkdetrqr6ldmyhv-urvlapfisvffp6cea3w2-700x700-1.png"),
        Product(name="Barcelona Home Jersey 2024", description="Latest Barcelona home jersey.", price=1500, category_id=1, image_url="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTqhWo1_9LhNxXRSHdAJFODH0VsI0cluQjedkjIvSR6Ik5lqQXcfoO9GZQ3qCdHuu1sGAo&usqp=CAU"),
        Product(name="Running Shoes", description="Comfortable running shoes.", price=2000, category_id=2, image_url="https://cdn.thewirecutter.com/wp-content/media/2023/09/running-shoes-2048px-5960.jpg"),
        Product(name="Yoga Pants", description="Flexible yoga pants.", price=750, category_id=2, image_url="https://images-na.ssl-images-amazon.com/images/I/41JkukHbj2L._UL500_.jpg"),
        Product(name="Treadmill", description="Electric treadmill with multiple speed settings.", price=200000, category_id=3, image_url="https://i1.wp.com/www.alphafitness.co.ke/wp-content/uploads/2021/11/HRS-TREADMILL-1.jpg?fit=736%2C527&ssl=1"),
        Product(name="Dumbbells", description="Set of adjustable dumbbells.", price=20000, category_id=3, image_url="https://m.media-amazon.com/images/I/61T7+l4TdwL.jpg"),
    ]
    
    # Add product variants for sizes and editions
    product_variants = [
        ProductVariant(product_id=1, size="L", edition="Fan Edition", stock=50),
        ProductVariant(product_id=1, size="XL", edition="Player Edition", stock=30),
        ProductVariant(product_id=2, size="M", edition="Fan Edition", stock=40),
        ProductVariant(product_id=3, size="S", edition="Player Edition", stock=25),
        ProductVariant(product_id=4, size="L", edition="Fan Edition", stock=60),
        ProductVariant(product_id=5, size="XL", edition="Player Edition", stock=45),
        ProductVariant(product_id=6, size="S", edition="Fan Edition", stock=70),
        ProductVariant(product_id=7, size="42", edition="Standard", stock=200),
        ProductVariant(product_id=8, size="L", edition="Standard", stock=120),
        ProductVariant(product_id=9, size="Standard", edition="Deluxe", stock=10),
        ProductVariant(product_id=10, size="Standard", edition="Standard", stock=100),
    ]

    # Add users, categories, products, and variants to the session
    db.session.bulk_save_objects(users)
    db.session.bulk_save_objects(categories)
    db.session.bulk_save_objects(products)
    db.session.bulk_save_objects(product_variants)
    db.session.commit()

    # Creating sample orders
    orders = [
        Order(user_id=2, name="John Doe", email="john@gmail.com", phone="1234567890", location="123 Main St", total_price=3000.0, created_at=datetime.utcnow()),
        Order(user_id=3, name="Jane Doe", email="jane@gmail.com", phone="0987654321", location="456 Elm St", total_price=1500.0, created_at=datetime.utcnow()),
    ]

    # Commit orders
    db.session.bulk_save_objects(orders)
    db.session.commit()

    # Add order items linked to the orders
    order_items = [
        OrderItem(order_id=1, product_variant_id=1, quantity=2, unit_price=1500, size="L", edition="Fan Edition"),
        OrderItem(order_id=1, product_variant_id=7, quantity=1, unit_price=2000, size="42", edition="Standard"),
        OrderItem(order_id=2, product_variant_id=3, quantity=1, unit_price=1500, size="S", edition="Fan Edition"),
    ]

    # Save order items
    db.session.bulk_save_objects(order_items)
    db.session.commit()

    print("Database seeded successfully!")

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        db.create_all()
        seed_data()
