from api import bp as api_bp
from model import *
from flask import render_template
from views import *

app.register_blueprint(api_bp, url_prefix='/api')

if __name__ == '__main__':
    app.run(debug=True)
