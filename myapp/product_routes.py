from flask import Blueprint, jsonify, request, abort
from .models import Product, Category, Order, OrderItem, ProductVariant, db
from .utils import upload_image
from datetime import datetime
from dotenv import load_dotenv
import json
import requests
import base64
import os

load_dotenv()

product_bp = Blueprint('products', __name__)

# GET all products with variants
@product_bp.route('/products', methods=['GET'])
def get_products():
    # Get query parameters for limit and sort
    limit = request.args.get('limit', type=int)  # Optional limit
    sort = request.args.get('sort', default='created_at_desc')  # Default sort by 'created_at' descending

    # Define sorting logic
    if sort == 'created_at_asc':
        sort_column = Product.created_at.asc()
    else:  # Default to descending
        sort_column = Product.created_at.desc()

    # Query the products, applying sorting
    query = Product.query.order_by(sort_column)

    # Apply limit if provided
    if limit:
        query = query.limit(limit)

    products = query.all()

    # Serialize products with their variants
    products_data = []
    for product in products:
        variants = [{
            "id": variant.id,
            "size": variant.size,
            "edition": variant.edition,
            "stock": variant.stock
        } for variant in product.variants]

        products_data.append({
            "id": product.id,
            "name": product.name,
            "description": product.description,
            "price": product.price,
            "category_id": product.category_id, 
            "category": product.category.name,  
            "image_url": product.image_url,
            "created_at": product.created_at.isoformat(),
            "variants": variants
        })

    return jsonify(products_data)

# GET a single product by ID with variants
@product_bp.route('/products/<int:id>', methods=['GET'])
def get_product(id):
    product = Product.query.get_or_404(id)
    
    variants = [{
        "id": variant.id,
        "size": variant.size,
        "edition": variant.edition,
        "stock": variant.stock
    } for variant in product.variants]
    
    return jsonify({
        "id": product.id,
        "name": product.name,
        "description": product.description,
        "price": product.price,
        "category": {
            "id": product.category.id,
            "name": product.category.name
        },
        "image_url": product.image_url,
        "created_at": product.created_at.isoformat(),
        "variants": variants  # Include variants in the response
    })

# POST a new product with variants
@product_bp.route('/products', methods=['POST'])
def add_product():
    data = request.json

    # Validate required fields
    required_fields = ['name', 'description', 'price', 'category_id', 'variants']
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"'{field}' is required."}), 400

    # Validate variants
    variants = data.get('variants', [])
    if not isinstance(variants, list) or not variants:
        return jsonify({"error": "'variants' must be a non-empty list."}), 400

    for variant in variants:
        if not all(k in variant for k in ('size', 'edition', 'stock')):
            return jsonify({"error": "Each variant must include 'size', 'edition', and 'stock'."}), 400
        if not isinstance(variant['stock'], int) or variant['stock'] < 0:
            return jsonify({"error": "Variant 'stock' must be a non-negative integer."}), 400

    # Handle image upload if image_url is not provided
    image_url = data.get('imageUrl')
    if not image_url:
        image = request.files.get('image')
        if image:
            upload_result = upload_image(image)
            if upload_result and 'url' in upload_result:
                image_url = upload_result['url']
            else:
                return jsonify({"error": "Image upload failed."}), 500
        else:
            return jsonify({"error": "'imageUrl' or 'image' file is required."}), 400

    # Create the product
    new_product = Product(
        name=data['name'],
        description=data['description'],
        price=data['price'],
        category_id=data['category_id'],
        image_url=image_url,
        created_at=datetime.utcnow()
    )
    db.session.add(new_product)
    db.session.commit()  # Commit to get the product ID

    # Create product variants
    product_variants = []
    for variant in variants:
        product_variant = ProductVariant(
            product_id=new_product.id,
            size=variant['size'],
            edition=variant['edition'],
            stock=variant['stock'],
            created_at=datetime.utcnow()
        )
        product_variants.append(product_variant)

    db.session.bulk_save_objects(product_variants)
    db.session.commit()

    return jsonify({
        "message": "Product added successfully!",
        "product_id": new_product.id
    }), 201

# PUT (update) an existing product and its variants
@product_bp.route('/products/<int:id>', methods=['PUT'])
def update_product(id):
    product = Product.query.get_or_404(id)
    data = request.json

    # Update product fields if provided
    product.name = data.get('name', product.name)
    product.description = data.get('description', product.description)
    product.price = data.get('price', product.price)
    product.category_id = data.get('category_id', product.category_id)

    # Handle image update
    if 'imageUrl' in data:
        product.image_url = data['imageUrl']
    elif 'image' in request.files:
        image = request.files.get('image')
        if image:
            upload_result = upload_image(image)
            if upload_result and 'url' in upload_result:
                product.image_url = upload_result['url']
            else:
                return jsonify({"error": "Image upload failed."}), 500

    # Handle variants update
    variants = data.get('variants')
    if variants:
        if not isinstance(variants, list):
            return jsonify({"error": "'variants' must be a list."}), 400
        for variant_data in variants:
            variant_id = variant_data.get('id')
            if variant_id:
                # Update existing variant
                variant = ProductVariant.query.filter_by(id=variant_id, product_id=id).first()
                if not variant:
                    return jsonify({"error": f"Variant with ID {variant_id} not found for this product."}), 404
                variant.size = variant_data.get('size', variant.size)
                variant.edition = variant_data.get('edition', variant.edition)
                variant.stock = variant_data.get('stock', variant.stock)
            else:
                # Create new variant
                if not all(k in variant_data for k in ('size', 'edition', 'stock')):
                    return jsonify({"error": "New variants must include 'size', 'edition', and 'stock'."}), 400
                new_variant = ProductVariant(
                    product_id=id,
                    size=variant_data['size'],
                    edition=variant_data['edition'],
                    stock=variant_data['stock'],
                    created_at=datetime.utcnow()
                )
                db.session.add(new_variant)

    db.session.commit()
    return jsonify({"message": "Product updated successfully!"})

# DELETE a product and its variants
@product_bp.route('/products/<int:id>', methods=['DELETE'])
def delete_product(id):
    product = Product.query.get_or_404(id)
    db.session.delete(product)
    db.session.commit()
    return jsonify({"message": "Product and its variants deleted successfully!"})

# Count products by category
@product_bp.route('/products/count-by-category', methods=['GET'])
def count_products_by_category():
    categories = db.session.query(
        Category.name,
        Category.id,
        db.func.count(Product.id).label('count')
    ).outerjoin(Product).group_by(Category.id).all()

    return jsonify([{
        'category_name': category.name,
        'category_id': category.id,
        'count': category.count
    } for category in categories])

# Get products by category with variants
@product_bp.route('/products/by-category/<int:category_id>', methods=['GET'])
def get_products_by_category(category_id):
    # Add query parameters for limit and sort
    limit = request.args.get('limit', default=6, type=int)
    sort = request.args.get('sort', default='created_at_desc')

    # Define sorting logic
    if sort == 'created_at_asc':
        sort_column = Product.created_at.asc()
    else:
        sort_column = Product.created_at.desc()

    # Query products filtered by category, sorted, and limited
    products = Product.query.filter_by(category_id=category_id).order_by(sort_column).limit(limit).all()

    # Serialize products with their variants
    products_data = []
    for product in products:
        variants = [{
            "id": variant.id,
            "size": variant.size,
            "edition": variant.edition,
            "stock": variant.stock
        } for variant in product.variants]

        products_data.append({
            "id": product.id,
            "name": product.name,
            "description": product.description,
            "price": product.price,
            "image_url": product.image_url,
            "variants": variants
        })

    return jsonify(products_data)

# POST image upload (no changes needed if already functional)
@product_bp.route('/upload', methods=['POST'])
def upload_image_route():  
    image = request.files.get('file')
    if image:
        result = upload_image(image)
        if result and 'url' in result:
            return jsonify({'image_url': result['url']}), 200
    return jsonify({"error": "Image upload failed"}), 500

# POST a new order with variants
@product_bp.route('/orders', methods=['POST'])
def create_order():
    data = request.json
    cart = data.get('cart', [])
    delivery_details = data.get('delivery_details', {})
    total_price = data.get('total_price', 0)

    if not cart or not delivery_details:
        return jsonify({'success': False, 'message': 'Cart or delivery details are missing.'}), 400

    # Extract delivery details
    name = delivery_details.get('name')
    email = delivery_details.get('email')
    phone = delivery_details.get('phone')
    location = delivery_details.get('location')

    if not all([name, phone, location]):
        return jsonify({'success': False, 'message': 'All delivery details are required.'}), 400

    # Create an Order instance
    order = Order(
        user_id=None,  # Update this if linking to authenticated users
        name=name,
        email=email,
        phone=phone,
        location=location,
        total_price=total_price,
        payment_status='Pending'  # Initial status
    )
    db.session.add(order)
    db.session.commit()

    # Add each item as an OrderItem linked to the Order
    order_items = []
    for item in cart:
        variant_id = item.get('variant_id')
        quantity = item.get('quantity', 1)

        if not variant_id:
            return jsonify({'success': False, 'message': 'Variant ID is required for each cart item.'}), 400

        variant = ProductVariant.query.get(variant_id)
        if not variant:
            return jsonify({'success': False, 'message': f"Variant with ID {variant_id} not found."}), 404

        if quantity > variant.stock:
            return jsonify({'success': False, 'message': f"Quantity for variant ID {variant_id} exceeds stock."}), 400

        # Deduct stock
        variant.stock -= quantity

        order_item = OrderItem(
            order_id=order.id,
            product_variant_id=variant.id,
            quantity=quantity,
            unit_price=variant.product.price,
            size=variant.size,
            edition=variant.edition
        )
        order_items.append(order_item)

    db.session.bulk_save_objects(order_items)
    db.session.commit()

    # Initiate M-Pesa payment if required
    # Uncomment the following lines if you want to initiate payment immediately
    # payment_result = initiate_mpesa_payment(phone, total_price)
    # if payment_result['success']:
    #     order.payment_status = 'Payment Initiated'
    #     order.checkout_request_id = payment_result.get('checkout_request_id')
    #     db.session.commit()
    # else:
    #     return jsonify({'success': False, 'message': 'Payment initiation failed.', 'details': payment_result}), 500

    return jsonify({'success': True, 'order_id': order.id}), 201

# Function to initiate M-Pesa STK Push (No changes needed unless modifying behavior)
def initiate_mpesa_payment(phone, total_price):
    shortcode = str(174379)
    consumer_key = os.getenv('MPESA_CONSUMER_KEY')
    consumer_secret = os.getenv('MPESA_CONSUMER_SECRET')
    environment = os.getenv('MPESA_ENVIRONMENT', 'sandbox')
    
    recipient_phone_number = os.getenv('MY_PHONE_NUMBER')  # Ensure this is set in your environment variables

    # Step 1: Get access token
    access_token = get_mpesa_access_token()
    print("Access Token:", access_token)  # Debugging access token
    if not access_token:
        return {'success': False, 'message': 'Failed to get access token.'}

    # Step 2: Prepare the password and timestamp for the request
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    password = base64.b64encode((shortcode + timestamp).encode()).decode('utf-8')

    # Step 3: Prepare STK Push request body
    stk_push_url = f'https://{environment}.safaricom.co.ke/mpesa/stkpush/v1/processrequest'
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    body = {
        "BusinessShortCode": shortcode,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline", 
        "Amount": total_price,
        "PartyA": phone,  
        "PartyB": shortcode,  
        "PhoneNumber": phone, 
        "CallBackURL": "https://yourdomain.com/mpesa/callback",  # Update with your actual callback URL
        "AccountReference": "Order Payment",
        "TransactionDesc": "Payment for Order"
    }

    # Step 4: Send the STK Push request
    response = requests.post(stk_push_url, json=body, headers=headers)
    response_data = response.json()
    print("STK Push Response:", response_data)  # Debugging response data

    if response.status_code == 200 and response_data.get('ResponseCode') == '0':
        return {
            'success': True,
            'message': 'STK Push sent successfully',
            'checkout_request_id': response_data.get('CheckoutRequestID')
        }
    else:
        return {
            'success': False,
            'message': 'STK Push request failed.',
            'details': response_data
        }

# Function to get M-Pesa access token (No changes needed unless modifying behavior)
def get_mpesa_access_token():
    url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
    consumer_key = os.getenv("MPESA_CONSUMER_KEY")
    consumer_secret = os.getenv("MPESA_CONSUMER_SECRET")

    if not consumer_key or not consumer_secret:
        print("Error: Missing M-Pesa consumer key or secret.")
        return None

    # Encode key and secret to base64
    auth_string = f"{consumer_key}:{consumer_secret}"
    auth_header = base64.b64encode(auth_string.encode()).decode()

    headers = {
        "Authorization": f"Basic {auth_header}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json().get("access_token")
        else:
            print("Response Status:", response.status_code)
            print("Response Body:", response.text)
            return None
    except requests.RequestException as e:
        print("Request error:", e)
        return None

# MPESA callback route to handle payment responses
@product_bp.route('/mpesa/callback', methods=['POST'])
def mpesa_callback():
    data = request.json
    result_code = data.get('Body', {}).get('stkCallback', {}).get('ResultCode')
    result_desc = data.get('Body', {}).get('stkCallback', {}).get('ResultDesc')
    checkout_request_id = data.get('Body', {}).get('stkCallback', {}).get('CheckoutRequestID')
    
    # Retrieve order by checkout_request_id if stored in Order table
    order = Order.query.filter_by(checkout_request_id=checkout_request_id).first()

    if order:
        if result_code == 0:
            # Payment successful
            order.payment_status = 'Completed'
            db.session.commit()
            return jsonify({'success': True, 'message': 'Payment successful.'})
        else:
            # Payment failed
            order.payment_status = 'Failed'
            db.session.commit()
            return jsonify({'success': False, 'message': f'Payment failed: {result_desc}.'})
    else:
        return jsonify({'success': False, 'message': 'Order not found.'}), 404

# Manage categories (no changes needed)
@product_bp.route('/categories', methods=['GET', 'POST'])
def manage_categories():
    if request.method == 'GET':
        # Fetch all categories
        categories = Category.query.all()
        return jsonify([{
            'id': category.id,
            'name': category.name
        } for category in categories]), 200

    elif request.method == 'POST':
        # Add a new category
        if not request.json or not 'name' in request.json:
            return jsonify({'error': 'Category name is required'}), 400

        category_name = request.json['name']
        new_category = Category(name=category_name)

        try:
            db.session.add(new_category)
            db.session.commit()
            return jsonify({'message': 'Category added successfully'}), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500

# GET all orders (admin)
@product_bp.route('/getorders', methods=['GET'])
def get_orders():
    orders = Order.query.all()
    orders_data = [
        {
            "id": order.id,
            "user": {
                "username": order.user.username if order.user else "Guest",
                "email": order.user.email if order.user else order.email  # Fallback to order email if no user is linked
            },
            "name": order.name,
            "phone": order.phone,
            "location": order.location,
            "total_price": order.total_price,
            "order_date": order.created_at.isoformat(),
            "payment_status": order.payment_status,
            "order_items": [
                {
                    "product_name": item.product_variant.product.name,
                    "description": item.product_variant.product.description,
                    "quantity": item.quantity,
                    "unit_price": item.unit_price,
                    "size": item.size,
                    "edition": item.edition,
                    "total_item_price": item.quantity * item.unit_price
                }
                for item in order.items 
            ]
        }
        for order in orders
    ]
    return jsonify(orders_data)



# Additional route to fetch variants for a specific product
@product_bp.route('/products/<int:id>/variants', methods=['GET'])
def get_product_variants(id):
    product = Product.query.get_or_404(id)
    variants = [{
        "id": variant.id,
        "size": variant.size,
        "edition": variant.edition,
        "stock": variant.stock
    } for variant in product.variants]
    
    return jsonify(variants), 200
