"""
Inicializa a aplicacao Flask e registra os blueprints.
"""
import os
import logging
from flask import Flask, redirect
from flask_migrate import Migrate, upgrade, init, migrate as migrate_cmd
from src.limiter import limiter
from src.redis_client import init_redis

from src.models import db
from src.routes.agendamento import agendamento_bp
from src.routes.instrutor import instrutor_bp
from src.routes.laboratorio import laboratorio_bp
from src.routes.notificacao import notificacao_bp
from src.routes.ocupacao import ocupacao_bp
from src.routes.sala import sala_bp
from src.routes.turma import turma_bp
from src.routes.user import user_bp
from src.routes.rateio import rateio_bp
from src.routes.treinamento import treinamento_bp
from src.routes.treinamento_admin import admin_treinamento_bp
from src.routes.treinamento_user import user_treinamento_bp
from src.models.recurso import Recurso
import sqlalchemy as sa

MIGRATIONS_DIR = os.path.join(os.path.dirname(__file__), '..', 'migrations')
migrate = Migrate(directory=MIGRATIONS_DIR)

def create_admin(app):
    """Cria o usuário administrador padrão de forma idempotente."""
    from src.models.user import User
    from sqlalchemy.exc import SQLAlchemyError
    with app.app_context():
        try:
            admin_email = os.environ.get('ADMIN_EMAIL')
            admin_password = os.environ.get('ADMIN_PASSWORD')
            admin_username = os.environ.get('ADMIN_USERNAME') or admin_email.split('@')[0]
            if not admin_email or not admin_password:
                logging.error(
                    "ADMIN_EMAIL e ADMIN_PASSWORD precisam estar definidos para criar o usuário administrador"
                )
                return

            admin = User.query.filter_by(email=admin_email).first()
            if not admin:
                admin = User(
                    nome='Administrador',
                    email=admin_email,
                    senha=admin_password,
                    tipo='admin',
                    username=admin_username
                )
                db.session.add(admin)
                db.session.commit()
                logging.info("Usuário administrador criado com sucesso!")
            else:
                logging.info("Usuário administrador já existe.")
        except SQLAlchemyError as e:
            db.session.rollback()
            logging.error("Erro ao criar usuário administrador: %s", str(e))


def create_default_recursos(app):
    """Garante que os recursos padrao existam de forma idempotente."""
    with app.app_context():
        padrao = [
            "tv",
            "projetor",
            "quadro_branco",
            "climatizacao",
            "computadores",
            "wifi",
            "bancadas",
            "armarios",
            "tomadas",
        ]
        for nome in padrao:
            if not Recurso.query.filter_by(nome=nome).first():
                db.session.add(Recurso(nome=nome))
        db.session.commit()




def create_app():
    """Fábrica de aplicação usada pelo Flask."""
    logging.basicConfig(level=logging.INFO)
    app = Flask(__name__, static_url_path='', static_folder='static')

    db_uri = os.getenv("DATABASE_URL", "sqlite:///agenda_laboratorio.db").strip()
    if db_uri.startswith('postgres://'):
        db_uri = db_uri.replace('postgres://', 'postgresql://', 1)

    app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['REDIS_URL'] = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

    secret_key = os.getenv('SECRET_KEY') or os.getenv('FLASK_SECRET_KEY')
    if not secret_key:
        raise RuntimeError(
            "SECRET_KEY environment variable must be set for JWT signing"
        )
    app.config['SECRET_KEY'] = secret_key

    db.init_app(app)
    migrate.init_app(app, db)
    init_redis(app)
    limiter.init_app(app)

    # Configura chaves do reCAPTCHA (opcional)
    app.config['RECAPTCHA_SITE_KEY'] = os.getenv('RECAPTCHA_SITE_KEY') or os.getenv('SITE_KEY')
    app.config['RECAPTCHA_SECRET_KEY'] = os.getenv('RECAPTCHA_SECRET_KEY') or os.getenv('CAPTCHA_SECRET_KEY') or os.getenv('SECRET_KEY')
    app.config['RECAPTCHA_THRESHOLD'] = float(os.getenv('RECAPTCHA_THRESHOLD', '0.5'))

    app.register_blueprint(user_bp, url_prefix='/api')
    app.register_blueprint(agendamento_bp, url_prefix='/api')
    app.register_blueprint(notificacao_bp, url_prefix='/api')
    app.register_blueprint(laboratorio_bp, url_prefix='/api')
    app.register_blueprint(turma_bp, url_prefix='/api')
    app.register_blueprint(sala_bp, url_prefix='/api')
    app.register_blueprint(instrutor_bp, url_prefix='/api')
    app.register_blueprint(ocupacao_bp, url_prefix='/api')
    app.register_blueprint(rateio_bp, url_prefix='/api')
    app.register_blueprint(treinamento_bp, url_prefix='/api')
    app.register_blueprint(admin_treinamento_bp, url_prefix='/api/admin')
    app.register_blueprint(
        user_treinamento_bp,
        url_prefix='/api/user',
        name='treinamento_user',
    )

    @app.route('/')
    def index():
        return redirect('/admin-login.html')

    @app.route('/<path:path>')
    def static_file(path):
        return app.send_static_file(path)

    with app.app_context():
        if not os.path.exists(MIGRATIONS_DIR):
            logging.info("Pasta de migrations nao encontrada, inicializando...")
            try:
                init(directory=MIGRATIONS_DIR)
                migrate_cmd(directory=MIGRATIONS_DIR)
            except Exception as e:  # pragma: no cover - primeira migracao opcional
                logging.error("Erro ao criar migrations: %s", str(e))

        versions_dir = os.path.join(MIGRATIONS_DIR, 'versions')
        if not os.path.exists(versions_dir) or not os.listdir(versions_dir):
            try:
                migrate_cmd(directory=MIGRATIONS_DIR)
            except Exception as e:  # pragma: no cover - geracao opcional
                logging.error("Erro ao gerar migrations: %s", str(e))

        db.create_all()
        try:
            upgrade(directory=MIGRATIONS_DIR)
        except Exception as e:  # pragma: no cover - migracao opcional
            logging.error("Erro ao aplicar migrations: %s", str(e))
        create_admin(app)
        create_default_recursos(app)

    return app


app = create_app()

if __name__ == '__main__':
    debug = os.getenv('FLASK_DEBUG', '0').lower() in ('1', 'true', 't', 'yes')
    port = int(os.getenv('PORT', '5000'))
    app.run(debug=debug, host='127.0.0.1', port=port)
