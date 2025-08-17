from flask import Blueprint, jsonify
from src.auth import login_required

basedados_bp = Blueprint('basedados', __name__)

# Dados que atualmente são estáticos, mas agora servidos via API.
# No futuro, podem ser movidos para o banco de dados.
DADOS = {
    "horario": [
        '08:00 - 12:00',
        '13:00 - 17:00',
        '18:00 - 22:00',
    ],
    "carga_horaria": [
        '4 horas',
        '8 horas',
        '16 horas',
        '24 horas',
        '40 horas',
    ],
    "modalidade": ['Semipresencial', 'Presencial', 'Online'],
    "local": [
        'ONLINE/HOME OFFICE',
        'CMD',
        'TRANSMISSÃO ONLINE',
        'SJB',
    ],
    "publico_alvo": ['Empregados Anglo American', 'Comunidade'],
}


@basedados_bp.route('/planejamento/basedados', methods=['GET'])
@login_required
def get_base_dados():
    """Retorna listas de opções para os formulários de planejamento."""
    return jsonify(DADOS)
