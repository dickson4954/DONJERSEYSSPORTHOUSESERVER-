# utils.py
import cloudinary.uploader

def upload_image(image):
    try:
        result = cloudinary.uploader.upload(image)
        print("Upload Result:", result)  
        return result  
    except Exception as e:
        print(f"Error uploading image: {e}")
        return None
