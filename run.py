from myapp import create_app

app = create_app()


def list_routes(app):
    print("\nAvailable Routes:")
    for rule in app.url_map.iter_rules():
        methods = ','.join(sorted(rule.methods))
        print(f"{rule.endpoint:30s} {methods:20s} {rule}")
    print("\n")


if __name__ == '__main__':
    
    list_routes(app)
    app.run(debug=True)
