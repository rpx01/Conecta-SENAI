import os
import sys
from datetime import datetime, timedelta
import jwt

os.environ['ADMIN_EMAIL'] = 'admin@example.com'
os.environ['ADMIN_USERNAME'] = 'admin'
os.environ['DISABLE_REDIS'] = '1'

import pytest
from flask import Flask

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.models import db
from src.models.user import User
from src.models.sala import Sala
from src.routes.user import user_bp, gerar_token_acesso, gerar_refresh_token
from src.routes.sala import sala_bp
from src.routes.turma import turma_bp
from src.routes.agendamento import agendamento_bp
from src.routes.instrutor import instrutor_bp
from src.routes.treinamento import treinamento_bp

@pytest.fixture
def app():
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'test'
    db.init_app(app)
    app.register_blueprint(user_bp, url_prefix='/api')
    app.register_blueprint(sala_bp, url_prefix='/api')
    app.register_blueprint(turma_bp, url_prefix='/api')
    app.register_blueprint(agendamento_bp, url_prefix='/api')
    app.register_blueprint(instrutor_bp, url_prefix='/api')
    app.register_blueprint(treinamento_bp, url_prefix='/api')

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
        db.session.commit()
    return app

@pytest.fixture
def client(app):
    return app.test_client()


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
