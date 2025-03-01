from flask import Flask, Blueprint, jsonify, request, abort
from myapp.models import Product, Category, Order, OrderItem, ProductVariant, db
from flask import current_app


from .utils import upload_image
from datetime import datetime
from dotenv import load_dotenv
import json
import requests
import base64
import os
from requests.auth import HTTPBasicAuth
from flask_cors import CORS
from flask import send_from_directory
from werkzeug.utils import secure_filename
import cloudinary
import cloudinary.uploader

load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Apply CORS to the app globally
CORS(app, resources={r"/*": {"origins": ["https://dickson4954.github.io", "http://localhost:3000"]}}, supports_credentials=True)


# 🔴 Force CORS Headers on Every Response
@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "https://dickson4954.github.io"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    return response

# cloudinary.config(
#     cloud_name=app.config['CLOUDINARY_CLOUD_NAME'],
#     api_key=app.config['CLOUDINARY_API_KEY'],
#     api_secret=app.config['CLOUDINARY_API_SECRET']
# )

product_bp = Blueprint('products', __name__)




@product_bp.route('/products', methods=['GET'])
def get_products():
    limit = request.args.get('limit', type=int)  
    sort = request.args.get('sort', default='created_at_desc') 
    sort_column = Product.created_at.asc() if sort == 'created_at_asc' else Product.created_at.desc()

    query = Product.query.order_by(sort_column)
    if limit:
        query = query.limit(limit)

    products = query.all()

    products_data = []
    for product in products:
        variants = [{
            "id": variant.id,
            "size": variant.size,
            "edition": variant.edition,
            "stock": variant.stock
        } for variant in product.variants]

        # ✅ Fixed: Only mark as sold out if there are variants AND all have 0 stock
        is_sold_out = len(variants) > 0 and all(variant["stock"] == 0 for variant in variants)

        products_data.append({
            "id": product.id,
            "name": product.name,
            "description": product.description,
            "price": product.price,
            "category_id": product.category_id, 
            "category": product.category.name,  
            "image_url": product.image_url,
            "created_at": product.created_at.isoformat(),
            "variants": variants,
            "sold_out": is_sold_out  # ✅ Corrected logic
        })

    return jsonify(products_data)

@product_bp.route('/products/<int:id>', methods=['GET'])
def get_product(id):
    product = Product.query.get_or_404(id)
    
    # Extract all variants for this product
    variants = [{
        "id": variant.id,
        "size": variant.size,
        "edition": variant.edition,
        "stock": variant.stock
    } for variant in product.variants]

    # Extract unique editions
    editions = list({variant.edition for variant in product.variants if variant.edition})

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
        "variants": variants,
        "editions": editions  # Ensure editions is always a list
    })

@app.route('/products/<int:product_id>/update-stock', methods=['POST'])
def update_stock(product_id):
    data = request.json
    size = data.get('size')
    quantity = data.get('quantity')

    # Find the variant by product_id and size (ignore edition)
    variant = ProductVariant.query.filter_by(
        product_id=product_id,
        size=size
    ).first()

    if not variant:
        return jsonify({"error": "Variant not found"}), 404

    if variant.stock < quantity:
        return jsonify({"error": "Not enough stock"}), 400

    # Update the stock
    variant.stock -= quantity
    db.session.commit()

    return jsonify({"success": True})

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
        if not all(k in variant for k in ('size', 'stock')):
            return jsonify({"error": "Each variant must include 'size' and 'stock'."}), 400
        if not isinstance(variant['stock'], int) or variant['stock'] < 0:
            return jsonify({"error": "Variant 'stock' must be a non-negative integer."}), 400

    # Handle image upload if image_url is not provided
    image_url = data.get('imageUrl')
    if not image_url:
        image = request.files.get('image')  # Use request.files for images
        if image:
            # Process the uploaded image
            upload_result = upload_image(image)  # Ensure this function accepts image as parameter
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

    # Add variants
    for variant in variants:
        sizes = variant['size']
        if isinstance(sizes, str):  
            sizes = [size.strip() for size in sizes.split(',')]  # Split sizes

        for size in sizes:
            # Check if the variant already exists
            existing_variant = ProductVariant.query.filter_by(
                product_id=new_product.id,
                size=size
            ).first()

            if existing_variant:
                # If exists, update stock instead of adding a duplicate
                existing_variant.stock += variant['stock']
            else:
                # If not exists, create a new variant
                product_variant = ProductVariant(
                    product_id=new_product.id,
                    size=size,
                    edition=variant.get('edition', ''),  # Optional: Include edition if needed
                    stock=variant['stock'],
                    created_at=datetime.utcnow()
                )
                db.session.add(product_variant)

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
    image_url = data.get('imageUrl')
    if not image_url:
        image = request.files.get('image')  # Use request.files for images
        if image:
            # Process the uploaded image
            upload_result = upload_image(image)  # Ensure this function accepts image as parameter
            if upload_result and 'url' in upload_result:
                image_url = upload_result['url']
            else:
                return jsonify({"error": "Image upload failed."}), 500
        else:
            return jsonify({"error": "'imageUrl' or 'image' file is required."}), 400

    # Update the image URL
    product.image_url = image_url

    # Handle variants update
    variants = data.get('variants', [])
    if variants:
        if not isinstance(variants, list):
            return jsonify({"error": "'variants' must be a list."}), 400

        for variant_data in variants:
            sizes = [size.strip() for size in variant_data.get('size', '').split(',')]  # ✅ Split sizes
            for size in sizes:
                variant_id = variant_data.get('id')

                if variant_id:
                    # ✅ Update existing variant if it exists
                    variant = ProductVariant.query.filter_by(
                        id=variant_id,
                        product_id=id
                    ).first()
                    if variant:
                        variant.size = size
                        variant.edition = variant_data.get('edition', variant.edition)
                        variant.stock = variant_data.get('stock', variant.stock)
                else:
                    # ✅ Create a new variant if size does not exist
                    new_variant = ProductVariant(
                        product_id=id,
                        size=size,
                        edition=variant_data['edition'],
                        stock=variant_data['stock'],
                        created_at=datetime.utcnow()
                    )
                    db.session.add(new_variant)

    db.session.commit()
    return jsonify({"message": "Product updated successfully!"})

@product_bp.route('/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    try:
        product = Product.query.get(product_id)
        if not product:
            return jsonify({"message": "Product not found"}), 404

        # Delete all variants linked to this product first
        ProductVariant.query.filter_by(product_id=product_id).delete()

        # Now delete the product
        db.session.delete(product)
        db.session.commit()

        return jsonify({"message": "Product and its variants deleted successfully!"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

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

    # If the category has an associated image, delete it from Cloudinary
    if category.image_url:  # Assuming `image_url` is the field storing the Cloudinary URL
        try:
            # Extract the public ID from the Cloudinary URL
            public_id = category.image_url.split('/')[-1].split('.')[0]

            # Delete the image from Cloudinary
            cloudinary.uploader.destroy(public_id)
        except Exception as e:
            print(f"Error deleting image from Cloudinary: {str(e)}")
            return jsonify({"error": "Failed to delete associated image from Cloudinary"}), 500

    # Delete the category from the database
    db.session.delete(category)
    db.session.commit()

    return jsonify({"message": "Category deleted successfully!"})


@product_bp.route('/upload', methods=['POST'])
def upload_image():
    print("Upload route hit")  # Log when the route is accessed
    try:
        if 'file' not in request.files:
            print("No file part in the request")
            return jsonify({"error": "No file part in the request"}), 400

        image = request.files['file']
        if image.filename == '':
            return jsonify({"error": "No selected file"}), 400

        # Upload the image to Cloudinary
        upload_result = cloudinary.uploader.upload(image)

        # Get the secure URL of the uploaded image
        image_url = upload_result.get('secure_url')
        if not image_url:
            return jsonify({"error": "Failed to upload image to Cloudinary"}), 500

        return jsonify({"image_url": image_url})  # Return the URL of the uploaded image

    except Exception as e:
        print("Error:", str(e))
        return jsonify({"error": str(e)}), 500
# @product_bp.route('/uploads/<filename>')
# def uploaded_file(filename):
#     return send_from_directory(UPLOAD_FOLDER, filename)


# GET all orders
@product_bp.route('/orders', methods=['GET'])
def get_orders():
    try:
        orders = Order.query.all()
        if not orders:
            return jsonify([]), 200

        orders_data = []
        for order in orders:
            try:
                order_items = [{
                    "id": item.id,
                    "quantity": item.quantity,
                    "unit_price": item.unit_price,
                    "size": item.size,
                    "edition": item.edition,
                    "custom_name": item.custom_name,
                    "custom_number": item.custom_number,
                    "badge": item.badge,
                    "font_type": item.font_type
                } for item in order.items]

                orders_data.append({
                    "id": order.id,
                    "user_id": order.user_id,
                    "name": order.name,
                    "phone": order.phone,
                    "location": order.location,
                    "region": order.region or 'N/A',
                    "total_price": order.total_price,
                    "payment_status": order.payment_status,
                    "created_at": order.created_at.isoformat() if order.created_at else None,
                    "items": order_items
                })
            except Exception as order_error:
                current_app.logger.error(f"Error processing order {order.id}: {str(order_error)}")

        return jsonify(orders_data), 200
    except Exception as e:
        current_app.logger.error(f"Error fetching orders: {str(e)}")
        return jsonify({'success': False, 'message': 'Internal server error.'}), 500
# GET a single order by ID
@product_bp.route('/orders/<int:id>', methods=['GET'])
def get_order_by_id(id):
    # Fetch the order by ID or return a 404 error if not found
    order = Order.query.get_or_404(id)

    # Fetch order items with product details
    order_items = []
    for item in order.items:
        # Fetch the associated product for the current order item
        product = Product.query.get(item.product_id)
        
        # Build the order item dictionary with product details
        order_item_data = {
            "id": item.id,
            "quantity": item.quantity,
            "unit_price": item.unit_price,
            "size": item.size,
            "edition": item.edition,
            "custom_name": item.custom_name,
            "custom_number": item.custom_number,
            "badge": item.badge,
            "font_type": item.font_type,
            "product": {
                "name": product.name if product else 'N/A',  # Include product name
                "description": product.description if product else 'N/A'  # Include product description
            }
        }
        order_items.append(order_item_data)

    # Build the order data dictionary
    order_data = {
        "id": order.id,
        "user_id": order.user_id,
        "name": order.name,
        "phone": order.phone,
        "location": order.location,
        "region": order.region or 'N/A',
        "total_price": order.total_price,
        "payment_status": order.payment_status,
        "created_at": order.created_at.isoformat(),
        "items": order_items  # Include order items with product details
    }

    return jsonify(order_data)
@product_bp.route('/orders', methods=['POST'])
def create_order():
    try:
        data = request.json
        print("Received Order Data:", data)

        if not data:
            print("Error: No data received.")
            return jsonify({'success': False, 'message': 'No data received.'}), 400

        cart = data.get('cart', [])
        shipping_details = data.get('shipping_details', {})
        total_price = data.get('total_price', 0)

        if not cart or not shipping_details:
            print("Error: Missing cart or shipping details.")
            return jsonify({'success': False, 'message': 'Cart or shipping details are missing.'}), 400

        # Validate required fields in shipping_details
        required_shipping_fields = ['name', 'phone', 'location', 'region']
        missing_fields = [field for field in required_shipping_fields if field not in shipping_details]
        if missing_fields:
            print(f"Error: Missing shipping fields: {missing_fields}")
            return jsonify({'success': False, 'message': f'Missing shipping fields: {", ".join(missing_fields)}'}), 400

        # Check total_price validity
        if not isinstance(total_price, (int, float)) or total_price <= 0:
            print("Error: Invalid total_price.")
            return jsonify({'success': False, 'message': 'Invalid total_price. It must be a positive number.'}), 400

        # Validate cart items
        for item in cart:
            if 'quantity' not in item or 'price' not in item or 'name' not in item or 'size' not in item:
                print(f"Error: Missing required fields in cart item: {item}")
                return jsonify({'success': False, 'message': 'Each cart item must include quantity, price, name, and size.'}), 400

        # If everything is correct, proceed to create order
        print("Creating order...")
        order = Order(
            user_id=None,
            name=shipping_details['name'],
            phone=shipping_details['phone'],
            location=shipping_details['location'],
            region=shipping_details['region'],
            total_price=total_price,
            payment_status='Pending'
        )

        db.session.add(order)
        db.session.commit()  # Commit to get the order ID

        # Create order items & update stock
        for item in cart:
            print(f"Processing item: {item.get('name', 'Unnamed Item')}")

            # Fetch the product by name
            product = Product.query.filter_by(name=item['name']).first()
            if not product:
                print(f"Error: Product '{item['name']}' not found.")
                db.session.rollback()
                return jsonify({'success': False, 'message': f"Product '{item['name']}' not found."}), 404

            # Fetch the correct variant based on size (ignore edition)
            variant = ProductVariant.query.filter_by(
                product_id=product.id,
                size=item.get('size')).first()
            if not variant:
                print(f"Error: Product variant for size '{item.get('size')}' not found.")
                db.session.rollback()
                return jsonify({'success': False, 'message': f"Product variant for size '{item.get('size')}' not found."}), 404

            # Check stock availability
            if variant.stock < item['quantity']:
                print(f"Error: Not enough stock for {product.name} size {variant.size}")
                db.session.rollback()
                return jsonify({'success': False, 'message': f"Not enough stock for {product.name} size {variant.size}"}), 400

            # Reduce stock
            variant.stock -= item['quantity']
            db.session.add(variant)  # Update stock in the database

            # Create order item
            order_item = OrderItem(
                order_id=order.id,  # Link to the order
                product_id=product.id,  # Include the product_id
                quantity=item['quantity'],
                unit_price=item['price'],
                size=item.get('size', 'N/A'),
                edition=item.get('edition', 'N/A'),  # Optional: Include edition if needed
                custom_name=item.get('customName', ''),
                custom_number=item.get('customNumber', None) if item.get('customNumber') else None,  # Convert empty string to None
                badge=item.get('badge', ''),
                font_type=item.get('fontType', '')
            )
            db.session.add(order_item)

        db.session.commit()  # Commit the order items and stock update

        print("Order created successfully:", order.id)
        return jsonify({'success': True, 'order_id': order.id}), 201

    except Exception as e:
        print("Error creating order:", str(e))  # Debugging log
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Internal server error.'}), 500

# DELETE an order
@app.route('/orders/<int:order_id>', methods=['DELETE'])
def delete_order(order_id):
    order = Order.query.get(order_id)
    if not order:
        return jsonify({'message': 'Order not found'}), 404

    try:
        db.session.delete(order)
        db.session.commit()
        return jsonify({'message': 'Order deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error deleting order: {str(e)}'}), 500






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
    consumer_key = 'SjVJTzVgkJnNxNG8CllAcPcMj4W7I4pKNPJcArcrniD5D3Mm'
    consumer_secret = 'uH7v3PjjZkw8DsrejlETeCUsja07csu3PHnStFJIE4bA8fA4rhSwdwF9YQGoPgAU'
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
        short_code = '174379'
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
            'CallBackURL': 'https://donjerseyssporthouseserver-5-cmus.onrender.com/callback',  # Update this with your callback URL
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

        # Validate required fields
        if not data or 'phone_number' not in data or 'amount' not in data:
            return jsonify({'error': 'Phone number and amount are required'}), 400

        phone_number = data['phone_number']
        amount = data['amount']

        # Validate phone number format
        if not phone_number.startswith('254') and not phone_number.startswith('0'):
            return jsonify({'error': 'Invalid phone number format. Use 254 or 0 prefix.'}), 400

        # Convert phone number to 254 format if it starts with 0
        if phone_number.startswith('0'):
            phone_number = '254' + phone_number[1:]

        # Validate amount
        if not isinstance(amount, (int, float)) or amount <= 0:
            return jsonify({'error': 'Amount must be a positive number.'}), 400

        # Initiate payment
        response = initiate_payment(phone_number, amount)

        # Check if the response contains 'CheckoutRequestID'
        if 'CheckoutRequestID' not in response:
            return jsonify({'error': 'Failed to initiate payment', 'details': response}), 500

        # Return response containing CheckoutRequestID
        return jsonify({'CheckoutRequestID': response['CheckoutRequestID']}), 200

    except Exception as e:
        print("Error initiating payment:", str(e))  # Debugging log
        return jsonify({'error': str(e)}), 500
if __name__ == "__main__":
    app.run(debug=True)  # Enable debug mode
