import logging
import os
import socket
import sys
import webbrowser

from flask import request
from waitress import serve
from werkzeug.middleware.proxy_fix import ProxyFix

from app import create_app

sys.dont_write_bytecode = True


def _create_app():
	"""Instantiate the Flask application with environment-aware config."""
	env_name = os.getenv('APP_ENV') or os.getenv('FLASK_ENV')
	application = create_app(env_name)
	application.wsgi_app = ProxyFix(application.wsgi_app)
	return application


app = _create_app()


@app.before_request
def log_request_info():
	app.logger.info(f"Request: {request.method} {request.url}")


@app.after_request
def log_response_info(response):
	app.logger.info(f"{request.method} {request.url} -> {response.status_code}")
	return response


if __name__ == "__main__":
	port = int(os.getenv('PORT', '5600'))
	host = os.getenv('HOST', '0.0.0.0')
	logging.basicConfig(level=logging.INFO)
	hostname = socket.gethostname()
	local_ip = socket.gethostbyname(hostname)
	if os.name == 'nt':
		os.system('cls')
	print("Server rodando em:")
	print(f"Local: http://{hostname}:{port}")
	print(f"Rede:  http://{local_ip}:{port}")
	if os.getenv('AUTO_OPEN_BROWSER', '1') == '1':
		webbrowser.open(f"http://{local_ip}:{port}")
	serve(app, host=host, port=port)