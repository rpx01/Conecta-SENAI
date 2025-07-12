from flask import Blueprint, jsonify
from src.auth import admin_required

rateio_bp = Blueprint('rateio', __name__)

@rateio_bp.route('/rateio/relatorio', methods=['GET'])
@admin_required
def gerar_relatorio():
    return jsonify({'relatorio': []})
