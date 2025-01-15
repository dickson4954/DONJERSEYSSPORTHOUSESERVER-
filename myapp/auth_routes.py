from flask import Blueprint, request, jsonify
from werkzeug.security import check_password_hash, generate_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from .models import User, db

auth_bp = Blueprint('auth', __name__)

# Route for user signup
@auth_bp.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()

    # Basic validation for required fields
    if not data.get('username') or not data.get('email') or not data.get('password'):
        return jsonify({"message": "Missing required fields"}), 400

    # Check if the username or email already exists
    if User.query.filter_by(username=data['username']).first():
        return jsonify({"message": "Username already exists"}), 400

    if User.query.filter_by(email=data['email']).first():
        return jsonify({"message": "Email already exists"}), 400

    # Hash the password and create a new user
    hashed_password = generate_password_hash(data['password'], method='pbkdf2:sha256')
    new_user = User(username=data['username'], email=data['email'], password_hash=hashed_password)

    # Save the user to the database
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "User registered successfully"}), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    if not data.get('identifier') or not data.get('password'):
        return jsonify({"message": "Missing username/email or password"}), 400

    # Find user by username or email
    user = User.query.filter((User.username == data['identifier']) | (User.email == data['identifier'])).first()

    if not user:
        return jsonify({"message": "User not found"}), 404

    if not check_password_hash(user.password_hash, data['password']):
        return jsonify({"message": "Invalid password"}), 401

    # Generate JWT access token with user role
    access_token = create_access_token(identity={"id": user.id, "username": user.username, "is_admin": user.is_admin})

    return jsonify({
        "message": "Login successful",
        "access_token": access_token,
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "is_admin": user.is_admin  # Add admin status in response
        }
    }), 200


# Route to get the current user details (Protected)
@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    current_user = get_jwt_identity()
    
    user = User.query.get(current_user['id'])
    if not user:
        return jsonify({"message": "User not found"}), 404

    return jsonify({
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "is_admin": user.is_admin
    }), 200

# Route for users to update their profile (Protected)
@auth_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    current_user = get_jwt_identity()
    user = User.query.get(current_user['id'])

    if not user:
        return jsonify({"message": "User not found"}), 404

    data = request.get_json()
    user.username = data.get('username', user.username)
    user.email = data.get('email', user.email)

    # Optionally update the password
    if data.get('password'):
        user.password_hash = generate_password_hash(data['password'], method='pbkdf2:sha256')

    db.session.commit()

    return jsonify({"message": "Profile updated successfully"}), 200

# Route for user logout (if using JWT Blacklisting, optional)
@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    # Implement blacklisting if necessary, otherwise token expires automatically
    return jsonify({"message": "Logout successful"}), 200
