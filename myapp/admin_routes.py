from flask import request, jsonify, Blueprint
from myapp.utils import upload_image
from myapp import db
from werkzeug.security import check_password_hash, generate_password_hash
from myapp.models import Product, Category, User

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/admin/add_product', methods=['POST'])
def add_product():
    if 'image' not in request.files:
        return jsonify({'error': 'No image file uploaded'}), 400

    image = request.files['image']
    name = request.form['name']
    description = request.form['description']
    price = float(request.form['price'])
    category_id = int(request.form['category_id'])
    stock = int(request.form['stock'])

    # Upload image to Cloudinary
    upload_result = upload_image(image)
    if not upload_result:
        return jsonify({'error': 'Image upload failed'}), 500

    # Save the product with image URL
    new_product = Product(
        name=name,
        description=description,
        price=price,
        category_id=category_id,
        image_url=upload_result['url'],
        stock=stock
    )
    
    db.session.add(new_product)
    db.session.commit()

    return jsonify({'message': 'Product added successfully!'}), 201

from werkzeug.security import generate_password_hash

@admin_bp.route('/admin/register', methods=['POST'])
def register_admin():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    # Validate inputs
    if not username or not email or not password:
        return jsonify({"message": "All fields are required"}), 400

    # Check if user already exists
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({"message": "User with this email already exists"}), 400

    # Create a new admin user
    hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
    new_admin = User(username=username, email=email, password_hash=hashed_password, is_admin=True)

    # Save to the database
    db.session.add(new_admin)
    db.session.commit()

    return jsonify({"message": "New admin registered successfully"}), 201

