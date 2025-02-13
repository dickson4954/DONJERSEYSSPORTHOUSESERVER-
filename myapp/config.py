import os
from dotenv import load_dotenv
from datetime import timedelta

load_dotenv()

class Config:
    # General configurations
    SECRET_KEY = os.getenv('SECRET_KEY', '6ce880509867e095b667acbf863b5a987a647c196ed246a7')
    SQLALCHEMY_DATABASE_URI = "postgresql://don_jersey_app_user:p7qjdBF0lvH1CrlQL4iZ7DtCU6DSEKDy@dpg-cumtood2ng1s739qc4j0-a.oregon-postgres.render.com:5432/don_jersey_app"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    CLOUDINARY_CLOUD_NAME = 'dfdqp6bdl'
    CLOUDINARY_API_KEY = '838486655244728'
    CLOUDINARY_API_SECRET = 'IBzLj9TiA8FK9hlz5jtne2fYclU'

    # JWT configurations
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'fb7735a66fa196e5ed0eb045e3f00f12e6722f88b1793840fb273c4b37dc1d5a') 
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    JWT_TOKEN_LOCATION = ['headers', 'cookies']  
    JWT_COOKIE_SECURE = True 
    JWT_COOKIE_CSRF_PROTECT = True 

    # MPESA configurations for Lipa Na Mpesa Online (STK Push)
    MPESA_CONSUMER_KEY = os.getenv('MPESA_CONSUMER_KEY', 'FyWfrTK6hvup3TdzGGgs24SmGjigaAG0n1JHmIhvpcnOTA9m')
    MPESA_CONSUMER_SECRET = os.getenv('MPESA_CONSUMER_SECRET', 'Z7HrRwF2WE9OhDk9GQTGxo8dxeFqAmybETUFAM16IS1iUAwuGtlwCDFTsQWsdjiD')
    
    # Sandbox shortcode for testing Lipa Na Mpesa Buy Goods & Services
    MPESA_SHORTCODE = os.getenv('MPESA_SHORTCODE', '174379')  
    
    # Passkey for the Lipa Na Mpesa Online (STK Push) integration
    MPESA_PASSKEY = os.getenv('MPESA_PASSKEY', 'bfb279f9aa9bdbcf113b1d62f174b4c2')
    
    # 'sandbox' for testing and 'production' for live environment
    MPESA_ENVIRONMENT = os.getenv('MPESA_ENVIRONMENT', 'sandbox')
    
    # Your personal phone number to receive payments
    MY_PHONE_NUMBER = os.getenv('MY_PHONE_NUMBER','0757386259')
