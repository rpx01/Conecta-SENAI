"""Endpoints de API para o módulo de planejamento."""
from flask import jsonify

from app.planejamento import bp


@bp.route("/status")
def status():
    """Endpoint simples de status."""
    return jsonify({"status": "ok"})
