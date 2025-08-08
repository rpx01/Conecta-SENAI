"""
Inicializa a aplicacao Flask e registra os blueprints.
"""
import os
import logging
import traceback
import sys
from flask import Flask, redirect
from flask_migrate import Migrate
from src.limiter import limiter
from src.redis_client import init_redis

logging.basicConfig(stream=sys.stdout, level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

from src.models import db
from src.routes.laboratorios import agendamento_bp, laboratorio_bp
from src.routes.notificacao import notificacao_bp
from src.routes.ocupacao import ocupacao_bp, sala_bp, instrutor_bp
from src.routes.user import user_bp
from src.routes.rateio import rateio_bp
from src.routes.treinamentos import treinamento_bp, turma_bp

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

def create_admin(app):
    """Cria o usuário administrador padrão de forma idempotente."""
    from src.models.user import User
    from sqlalchemy.exc import SQLAlchemyError
    with app.app_context():
        try:
            admin_email = os.environ.get('ADMIN_EMAIL')
            admin_password = os.environ.get('ADMIN_PASSWORD')
            admin_username = os.environ.get('ADMIN_USERNAME')
            if not admin_email or not admin_password:
                logging.error(
                    "ADMIN_EMAIL e ADMIN_PASSWORD precisam estar definidos para criar o usuário administrador"
                )
                return

            if admin_email in {"admin@example.com", "<definir_em_producao>"} or \
               admin_password in {"senha-segura", "<definir_em_producao>"}:
                logging.error(
                    "ADMIN_EMAIL e ADMIN_PASSWORD não podem usar os valores padrão"
                )
                return

            admin_username = admin_username or admin_email.split('@')[0]

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
    from src.models.recurso import Recurso

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
    app = Flask(__name__, static_url_path='', static_folder='static')

    migrations_dir = os.path.join(project_root, 'migrations')

    db_uri = os.getenv("DATABASE_URL", "sqlite:///agenda_laboratorio.db").strip()
    if db_uri.startswith('postgres://'):
        db_uri = db_uri.replace('postgres://', 'postgresql://', 1)

    app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['REDIS_URL'] = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

    secret_key = (os.getenv('SECRET_KEY') or os.getenv('FLASK_SECRET_KEY') or '').strip()
    if not secret_key or secret_key.lower() == 'changeme':
        raise RuntimeError(
            "SECRET_KEY environment variable must be set to a secure value for JWT signing"
        )
    app.config['SECRET_KEY'] = secret_key

    db.init_app(app)
    Migrate(app, db, directory=migrations_dir)
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

    @app.route('/')
    def index():
        return redirect('/admin/login.html')

    @app.route('/<path:path>')
    def static_file(path):
        return app.send_static_file(path)

    @app.route('/health')
    def health_check():
        """Endpoint usado para verificacao de saude da aplicacao."""
        return "OK", 200

    # A inicializacao do banco (migracoes e dados padrao) deve ser executada
    # separadamente durante o processo de deploy.

    return app


try:
    logging.info("Iniciando a criação da aplicação Flask...")
    app = create_app()
    logging.info("Aplicação Flask criada com sucesso.")
except Exception as e:
    logging.error("!!!!!! FALHA CRÍTICA AO INICIAR A APLICAÇÃO !!!!!!")
    logging.error(f"Erro: {e}")
    logging.error(f"Traceback: {traceback.format_exc()}")
    raise e

if __name__ == '__main__':
    debug = os.getenv('FLASK_DEBUG', '0').lower() in ('1', 'true', 't', 'yes')
    port = int(os.getenv('PORT', '5000'))
    app.run(debug=debug, host='127.0.0.1', port=port)
