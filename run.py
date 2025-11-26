import os

from app import create_app


def _resolve_env() -> str | None:
	return os.getenv('APP_ENV') or os.getenv('FLASK_ENV')


app = create_app(_resolve_env())


if __name__ == '__main__':
	host = os.getenv('HOST', '0.0.0.0')
	port = int(os.getenv('PORT', '5600'))
	debug = bool(app.config.get('DEBUG', True))
	app.run(host=host, port=port, debug=debug)
