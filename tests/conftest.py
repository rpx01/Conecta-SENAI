import os
import sys
from datetime import datetime, timedelta
import jwt

os.environ['ADMIN_EMAIL'] = 'admin@example.com'
os.environ['ADMIN_USERNAME'] = 'admin'
os.environ['DISABLE_REDIS'] = '1'
os.environ['REDIS_URL'] = 'memory://'

import pytest
from flask import Flask
from flask_wtf.csrf import CSRFProtect

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.models import db
from src.models.user import User
from src.models.sala import Sala
from src.models.log_rateio import LogLancamentoRateio
from src.extensions import limiter
from src.routes.user import user_bp, gerar_token_acesso, gerar_refresh_token
from src.routes.ocupacao import sala_bp, instrutor_bp, ocupacao_bp
from src.routes.treinamentos import turma_bp, treinamento_bp
from src.routes.laboratorios import agendamento_bp, laboratorio_bp
from src.routes.rateio.rateio import rateio_bp
from src.routes.noticias import api_noticias_bp
from src.routes.support import support_bp
from src.routes.horario import horario_bp
from src.blueprints.auth import auth_bp
from src.routes.treinamentos.basedados import (
    secretaria_bp as treinamentos_basedados_bp,
)

@pytest.fixture
def app():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    app = Flask(
        __name__,
        template_folder=os.path.join(base_dir, 'src', 'templates'),
        static_folder=os.path.join(base_dir, 'src', 'static')
    )
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'test'
    app.config['WTF_CSRF_CHECK_DEFAULT'] = False
    db.init_app(app)
    limiter.init_app(app)
    CSRFProtect(app)
    app.register_blueprint(user_bp, url_prefix='/api')
    app.register_blueprint(sala_bp, url_prefix='/api')
    app.register_blueprint(turma_bp, url_prefix='/api')
    app.register_blueprint(agendamento_bp, url_prefix='/api')
    app.register_blueprint(instrutor_bp, url_prefix='/api')
    app.register_blueprint(treinamento_bp, url_prefix='/api')
    app.register_blueprint(ocupacao_bp, url_prefix='/api')
    app.register_blueprint(laboratorio_bp, url_prefix='/api')
    app.register_blueprint(rateio_bp, url_prefix='/api')
    app.register_blueprint(api_noticias_bp, url_prefix='/api')
    app.register_blueprint(support_bp, url_prefix='/api')
    app.register_blueprint(horario_bp, url_prefix='/api')
    app.register_blueprint(
        treinamentos_basedados_bp, url_prefix='/api/treinamentos/secretaria'
    )
    app.register_blueprint(auth_bp)

    with app.app_context():
        db.create_all()
        admin = User(
            nome='Admin',
            email='admin@example.com',
            senha='Password1!',
            tipo='admin'
        )
        db.session.add(admin)
        comum = User(
            nome='Usuario',
            email='usuario@example.com',
            senha='Password1!',
            tipo='comum'
        )
        db.session.add(comum)
        sala = Sala(nome='Sala Teste', capacidade=10)
        db.session.add(sala)
        for i in range(15):
            log = LogLancamentoRateio(
                acao='create',
                usuario='Admin',
                instrutor=f'Instrutor {i}',
                filial='F',
                uo='U',
                cr='CR',
                classe_valor='CL',
                percentual=10,
            )
            db.session.add(log)
        db.session.commit()
    return app

@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def csrf_token(client):
    resp = client.get('/api/csrf-token')
    return resp.get_json()['csrf_token']


@pytest.fixture
def non_admin_auth_headers(app):
    with app.app_context():
        user = User.query.filter_by(email='usuario@example.com').first()
        token = jwt.encode({
            'user_id': user.id,
            'nome': user.nome,
            'perfil': user.tipo,
            'exp': datetime.utcnow() + timedelta(hours=1)
        }, app.config['SECRET_KEY'], algorithm='HS256')
        return {'Authorization': f'Bearer {token}'}


@pytest.fixture
def login_admin():
    def _login(client):
        with client.application.app_context():
            user = User.query.filter_by(email='admin@example.com').first()
            token = gerar_token_acesso(user)
            refresh = gerar_refresh_token(user)
        return token, refresh

    return _login
