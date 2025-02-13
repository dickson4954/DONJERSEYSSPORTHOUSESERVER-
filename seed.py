from werkzeug.security import generate_password_hash
from myapp import create_app
from myapp.models import User, Category, Product, ProductVariant, Order, OrderItem
from myapp.extensions import db
from datetime import datetime
def seed_data():
    # Clear existing data to avoid foreign key violations
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
    db.session.bulk_save_objects(users)
    db.session.commit()

    # Fetch actual user IDs
    admin_user = User.query.filter_by(username="admin").first()
    john_user = User.query.filter_by(username="john_doe").first()
    jane_user = User.query.filter_by(username="jane_doe").first()

    # Add categories
    categories = [
        Category(name="Jerseys"),
        Category(name="Sportswear"),
        Category(name="Gym Equipment"),
    ]
    db.session.bulk_save_objects(categories)
    db.session.commit()

    # Fetch category IDs
    jerseys_category = Category.query.filter_by(name="Jerseys").first()
    sportswear_category = Category.query.filter_by(name="Sportswear").first()
    gym_category = Category.query.filter_by(name="Gym Equipment").first()

    # Add products
    products = [
        Product(name="Arsenal Home Jersey 2024", description="Latest Arsenal home jersey.", price=1500, category_id=jerseys_category.id, image_url="https://i1.adis.ws/i/ArsenalDirect/mit6141_f?&$plpImages$"),
        Product(name="Running Shoes", description="Comfortable running shoes.", price=2000, category_id=sportswear_category.id, image_url="https://cdn.thewirecutter.com/wp-content/media/2023/09/running-shoes-2048px-5960.jpg", size_type="number"),
        Product(name="Yoga Pants", description="Flexible yoga pants.", price=750, category_id=sportswear_category.id, image_url="https://images-na.ssl-images-amazon.com/images/I/41JkukHbj2L._UL500_.jpg"),
        Product(name="Treadmill", description="Electric treadmill with multiple speed settings.", price=200000, category_id=gym_category.id, image_url="https://i1.wp.com/www.alphafitness.co.ke/wp-content/uploads/2021/11/HRS-TREADMILL-1.jpg?fit=736%2C527&ssl=1"),
    ]
    db.session.bulk_save_objects(products)
    db.session.commit()

    # Fetch product IDs
    arsenal_jersey = Product.query.filter_by(name="Arsenal Home Jersey 2024").first()
    running_shoes = Product.query.filter_by(name="Running Shoes").first()
    yoga_pants = Product.query.filter_by(name="Yoga Pants").first()

    # Add product variants
    product_variants = [
        ProductVariant(product_id=arsenal_jersey.id, size="L", edition="Fan Edition", stock=50),
        ProductVariant(product_id=arsenal_jersey.id, size="XL", edition="Player Edition", stock=30),
        ProductVariant(product_id=yoga_pants.id, size="M", edition="Fan Edition", stock=40),
        ProductVariant(product_id=running_shoes.id, size="42", edition="Standard", stock=200),
        ProductVariant(product_id=running_shoes.id, size="43", edition="Standard", stock=150),
        ProductVariant(product_id=running_shoes.id, size="44", edition="Deluxe", stock=100),
    ]
    db.session.bulk_save_objects(product_variants)
    db.session.commit()

    # Fetch product variant IDs
    jersey_variant = ProductVariant.query.filter_by(product_id=arsenal_jersey.id, size="L").first()
    shoes_variant = ProductVariant.query.filter_by(product_id=running_shoes.id, size="42").first()
    yoga_variant = ProductVariant.query.filter_by(product_id=yoga_pants.id, size="M").first()

    # Create sample orders with correct user IDs
    orders = [
        Order(user_id=john_user.id, name="John Doe", email="john@gmail.com", phone="1234567890", location="123 Main St", total_price=3000.0, created_at=datetime.utcnow()),
        Order(user_id=jane_user.id, name="Jane Doe", email="jane@gmail.com", phone="0987654321", location="456 Elm St", total_price=1500.0, created_at=datetime.utcnow()),
    ]
    db.session.bulk_save_objects(orders)
    db.session.commit()

    # Fetch order IDs dynamically
    order1 = Order.query.filter_by(user_id=john_user.id).first()
    order2 = Order.query.filter_by(user_id=jane_user.id).first()

    # Add order items
    order_items = [
        OrderItem(order_id=order1.id, product_variant_id=jersey_variant.id, quantity=2, unit_price=1500, size="L", edition="Fan Edition"),
        OrderItem(order_id=order1.id, product_variant_id=shoes_variant.id, quantity=1, unit_price=2000, size="42", edition="Standard"),
        OrderItem(order_id=order2.id, product_variant_id=yoga_variant.id, quantity=1, unit_price=1500, size="M", edition="Fan Edition"),
    ]
    db.session.bulk_save_objects(order_items)
    db.session.commit()

    print("Database seeded successfully!")


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        seed_data()
