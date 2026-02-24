from flask import Flask, render_template
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

app = Flask(__name__, static_url_path='/static')


"""
Configure Flask using environment variables
"""
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-key')

"""
Home page
"""
@app.route('/')
def index():
    return render_template('main/index.html')

"""
Blueprint registration
"""
from portal.views import portal_blueprint
app.register_blueprint(portal_blueprint)

"""
Error handlers
"""
@app.errorhandler(500)
def internal_error(error):
    return render_template('error/500.html'), 500

@app.errorhandler(503)
def service_unavailable_error(error):
    return render_template('error/503.html'), 503

@app.errorhandler(400)
def bad_request_error(error):
    return render_template('error/400.html'), 400

@app.errorhandler(403)
def forbidden_error(error):
    return render_template('error/403.html'), 403


if __name__ == "__main__":
    app.run(debug=True)