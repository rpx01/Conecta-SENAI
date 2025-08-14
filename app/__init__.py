from flask import Flask
from app.planejamento import bp as planejamento_bp

app = Flask(__name__, static_folder="static", template_folder="templates")
app.register_blueprint(planejamento_bp, url_prefix="/planejamento")

__all__ = ["app"]
