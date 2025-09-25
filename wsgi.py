import sys
import os
sys.dont_write_bytecode = True
from waitress import serve
from run import app
import logging
from werkzeug.middleware.proxy_fix import ProxyFix
from flask import request
import socket
import webbrowser



@app.before_request
def log_request_info():
    app.logger.info(f"Request: {request.method} {request.url}")
    
@app.after_request
def log_response_info(response):
        app.logger.info(f"{request.method} {request.url} -> {response.status_code}")
        return response
    

if __name__ == "__main__":
    port = 5600
    logging.basicConfig(level=logging.INFO)
    app.wsgi_app = ProxyFix(app.wsgi_app)
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    os.system("cls")
    print(f"Server rodando em:")
    print(f"Local: http://{hostname}:{port}")
    print(f"Rede:  http://{local_ip}:{port}")
    webbrowser.open(f"http://{local_ip}:{port}")
    serve(app, host="0.0.0.0", port=port)