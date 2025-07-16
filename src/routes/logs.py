from flask import Blueprint, request, jsonify
from src.models.log import Log
from src.auth import admin_required

logs_bp = Blueprint('logs', __name__)


@logs_bp.route('/logs', methods=['GET'])
@admin_required
def get_logs():
    modelo = request.args.get('modelo')
    if not modelo:
        return jsonify({'erro': 'O parâmetro "modelo" é obrigatório'}), 400

    query = Log.query.filter_by(modelo_alvo=modelo)
    logs = query.order_by(Log.data_hora.desc()).limit(200).all()
    return jsonify([log.to_dict() for log in logs])

