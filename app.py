from api import bp as api_bp
from model import *

app.register_blueprint(api_bp, url_prefix='/api')


if __name__ == '__main__':
    app.run(debug=True)
