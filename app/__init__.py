from flask import Flask


def create_app():
    app = Flask(__name__)
    app.url_map.strict_slashes = False
    
    from .routes import gateway_bp
    app.register_blueprint(gateway_bp)
    
    @app.errorhandler(Exception)
    def handle_exception(e):
        if hasattr(e, "code"):
            print(f"Error: {e}, Code: {e.code}")
            if hasattr(e, "description"):
                return {"error": e.description}, e.code
            return {"error": "An error occurred"}, e.code
        return {"error": "Internal Server Error", "message": str(e)}, 500

    return app

import os

def get_env_variable(name, cast_type=str):
    """
    Retrieves an environment variable. 
    Raises a Detailed RuntimeError if the variable is missing.
    """
    
    value = os.getenv(name)
    if name is None:
        raise RuntimeError(f"CRITICAL ERROR: Environment variable '{name}' is not set.")
    try:
        return cast_type(value)
    except ValueError:
        raise RuntimeError(f"CRITICAL ERROR: Variable '{name}' must be of type {cast_type.__name__}.")