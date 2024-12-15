import os
from flask import Flask, send_from_directory, abort

from blueprints.api_bluep.endpoint import endpoint as api_bluep
from blueprints.web_bluep.endpoint import endpoint as web_bluep
import settings


app = Flask('obo-space-web')

app.config['SECRET_KEY'] = settings.SECRET_KEY
# app.config['UPLOAD_FOLDER'] = 'uploads'
# app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'webm'}

@app.route('/static/<path:filename>')
def serve_static(filename):
    """Serve static files securely."""
    safe_path = os.path.join(app.static_folder, filename)
    if os.path.isfile(safe_path):
        return send_from_directory(app.static_folder, filename)
    else:
        abort(404)

app.register_blueprint(api_bluep)
app.register_blueprint(web_bluep)

if __name__ == '__main__':
    app.run(debug=True)
