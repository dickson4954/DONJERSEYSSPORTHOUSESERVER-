from flask import Blueprint, jsonify, request, abort
from .models import Product, Category, Order, OrderItem, ProductVariant, db
from .utils import upload_image
from datetime import datetime
from dotenv import load_dotenv
import json
import requests
import base64
import os
from requests.auth import HTTPBasicAuth
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
@product_bp.route('/categories', methods=['GET'])
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
@product_bp.route('/categories/<int:category_id>', methods=['GET'])
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

@product_bp.route('/categories/<int:id>', methods=['DELETE'])
def delete_category(id):
    # Retrieve the category using the correct model
    category = Category.query.get_or_404(id)

    # Delete the category
    db.session.delete(category)
    db.session.commit()

    return jsonify({"message": "Category deleted successfully!"})



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

    # Check if cart or delivery details are missing
    if not cart or not delivery_details:
        return jsonify({'success': False, 'message': 'Cart or delivery details are missing.'}), 400

    # Extract delivery details
    name = delivery_details.get('name')
    email = delivery_details.get('email')
    phone = delivery_details.get('phone')
    location = delivery_details.get('location')

    # Validate required delivery details
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
    db.session.commit()  # Commit to generate the order ID

    # Add each item as an OrderItem linked to the Order
    order_items = []
    for item in cart:
        variant_id = item.get('variant_id')
        quantity = item.get('quantity', 1)

        # Check if variant_id is provided
        if not variant_id:
            return jsonify({'success': False, 'message': 'Variant ID is required for each cart item.'}), 400

        # Fetch product variant from the database
        variant = ProductVariant.query.get(variant_id)
        if not variant:
            return jsonify({'success': False, 'message': f"Variant with ID {variant_id} not found."}), 404

        # Check if stock is available
        if quantity > variant.stock:
            return jsonify({'success': False, 'message': f"Quantity for variant ID {variant_id} exceeds stock."}), 400

        # Deduct stock from the product variant
        variant.stock -= quantity

        # Create OrderItem instance
        order_item = OrderItem(
            order_id=order.id,
            product_variant_id=variant.id,
            quantity=quantity,
            unit_price=variant.product.price,
            size=variant.size,
            edition=variant.edition
        )
        order_items.append(order_item)

    # Bulk save order items and commit to the database
    db.session.bulk_save_objects(order_items)
    db.session.commit()

    return jsonify({'success': True, 'order_id': order.id}), 201


    # Initiate M-Pesa payment if required
    # Uncomment the following lines if you want to initiate payment immediately
    # payment_result = initiate_mpesa_payment(phone, total_price)
    # if payment_result['success']:
    #     order.payment_status = 'Payment Initiated'
    #     order.checkout_request_id = payment_result.get('checkout_request_id')
    #     db.session.commit()
    # else:
    #     return jsonify({'success': False, 'message': 'Payment initiation failed.', 'details': payment_result}), 500

    # return jsonify({'success': True, 'order_id': order.id}), 201


def get_mpesa_access_token():
    consumer_key = 'Pg578muqGU0hxW8gzaRGkczrGyquSOOQLd4XvnWUNBqHnsjQ'
    consumer_secret = 'UDQHV6hY2cpo5JGQhfBKZOgXLSHNX6jNRd6UPB5ZmxU7QfhcAG9YIZvCRAptXVAw'
    api_url = 'https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'
    response = requests.get(api_url, auth=HTTPBasicAuth(consumer_key, consumer_secret))
    print("Access Token Response:", response.text)  # Debugging line
    token = response.json().get('access_token')
    if not token:
        raise Exception("Failed to obtain access token")
    
    return token
    

# Function to initiate payment
def initiate_payment(phone_number, amount):
    try:
        access_token = get_mpesa_access_token()
        api_url = 'https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest'
        headers = {'Authorization': f'Bearer {access_token}'}
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        short_code = '8904818'
        passkey = 'bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919'
        password = base64.b64encode(f'{short_code}{passkey}{timestamp}'.encode()).decode()

        # Ensure the phone number is in the correct format
        phone_number = phone_number.strip()
        if phone_number.startswith("0"):
            phone_number = "254" + phone_number[1:]
        elif not phone_number.startswith("254"):
            return {'error': 'Invalid phone number format'}

        payload = {
            'BusinessShortCode': short_code,
            'Password': password,
            'Timestamp': timestamp,
            'TransactionType': 'CustomerPayBillOnline',
            'Amount': amount,
            'PartyA': phone_number,
            'PartyB': short_code,
            'PhoneNumber': phone_number,
            'CallBackURL': 'https://6da8-105-163-156-47.ngrok-free.app/callback',  # Update this with your callback URL
            'AccountReference': phone_number,
            'TransactionDesc': 'Payment for service',
        }

        response = requests.post(api_url, headers=headers, json=payload)
        response.raise_for_status()  # This will raise an exception if the status code is not 2xx

        if 'CheckoutRequestID' not in response.json():
            return {'error': 'Failed to initiate payment', 'details': response.json()}

        return response.json()

    except requests.exceptions.RequestException as e:
        return {'error': 'Failed to initiate payment', 'details': str(e)}


# Route to handle payment initiation
# Route to handle payment initiation
@product_bp.route('/pay', methods=['POST'])
def pay():
    try:
        # Get data from the request body
        data = request.get_json()

        # Ensure that both phone_number and amount are provided
        phone_number = data.get('phone_number')
        amount = data.get('amount')

        if not phone_number or not amount:
            return jsonify({'error': 'Phone number and amount are required'}), 400

        # Initiate payment
        response = initiate_payment(phone_number, amount)

        # Check if the response from initiate_payment contains 'CheckoutRequestID'
        if 'CheckoutRequestID' not in response:
            return jsonify({'error': 'Failed to initiate payment', 'details': response}), 500

        # Return response containing CheckoutRequestID
        return jsonify(response)

    except Exception as e:
        print(f"Error in /pay route: {str(e)}")  # Debugging line
        return jsonify({'error': 'Internal server error'}), 500
