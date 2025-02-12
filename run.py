from myapp import create_app

app = create_app()  # Create Flask app instance

# Function to list available routes (optional, useful for debugging)
def list_routes(app):
    print("\nAvailable Routes:")
    for rule in app.url_map.iter_rules():
        methods = ','.join(sorted(rule.methods))
        print(f"{rule.endpoint:30s} {methods:20s} {rule}")
    print("\n")

# Ensure this script works both locally and in production
if __name__ == '__main__':
    list_routes(app)
    app.run(debug=True)  # For local testing
