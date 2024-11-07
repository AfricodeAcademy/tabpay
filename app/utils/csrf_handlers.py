from flask import redirect, url_for, request, abort
from flask_wtf.csrf import CSRFError
from flask import current_app
from flask_wtf.csrf import validate_csrf

def init_csrf_handlers(app):
    # CSRF Error Handler
    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        return redirect(url_for('security.login'))

    # CSRF Protection Middleware
    @app.before_request
    def csrf_protect():
        if request.method == "POST":
            token = request.form.get('csrf_token')
            if not token or not validate_csrf(token):
                abort(400, "CSRF validation failed")

    # CSRF Failure Monitoring
    @app.after_request
    def log_csrf_errors(response):
        if response.status_code == 400 and 'CSRF' in str(response.data):
            current_app.logger.warning(f'CSRF validation failed for {request.url}')
        return response