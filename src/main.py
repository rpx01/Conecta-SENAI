# flake8: noqa
"""Inicializa a aplicacao Flask e registra os blueprints."""
import os
import logging
import traceback
import sys
from flask import Flask, redirect
from flasgger import Swagger
from flask_wtf.csrf import CSRFProtect
from flask_migrate import Migrate
from src.limiter import limiter
from src.redis_client import init_redis
from src.config import DevConfig, ProdConfig, TestConfig
from src.repositories.user_repository import UserRepository
from src.extensions import mail

logging.basicConfig(stream=sys.stdout, level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

from src.models import db
from src.routes.laboratorios import agendamento_bp, laboratorio_bp
from src.routes.notificacao import notificacao_bp
from src.routes.ocupacao import ocupacao_bp, sala_bp, instrutor_bp
from src.routes.user import user_bp
from src.routes.rateio import rateio_bp
from src.routes.treinamentos import treinamento_bp, turma_bp
from src.routes.planejamento import basedados_bp, planejamento_bp
from src.routes.inscricoes_treinamento import bp as inscricoes_treinamento_bp
from src.blueprints.auth_reset import auth_reset_bp
from src.blueprints.auth import auth_bp
from apscheduler.schedulers.background import BackgroundScheduler
from src.services.notificacao_service import criar_notificacoes_agendamentos_proximos

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

csrf = CSRFProtect()

# Scheduler global para evitar múltiplas instâncias
scheduler = None

swagger_template = {
    "components": {
        "schemas": {
            "User": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "nome": {"type": "string"},
                    "email": {"type": "string"},
                    "tipo": {"type": "string"},
                },
            },
            "UserCreate": {
                "type": "object",
                "properties": {
                    "nome": {"type": "string"},
                    "email": {"type": "string"},
                    "senha": {"type": "string"},
                    "tipo": {"type": "string"},
                },
                "required": ["nome", "email", "senha"],
            },
            "Notification": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "mensagem": {"type": "string"},
                    "lida": {"type": "boolean"},
                    "criada_em": {"type": "string", "format": "date-time"},
                },
            },
        }
    }
}

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

            admin = UserRepository.get_by_email(admin_email)
            if not admin:
                admin = User(
                    nome='Administrador',
                    email=admin_email,
                    senha=admin_password,
                    tipo='admin',
                    username=admin_username
                )
                UserRepository.add(admin)
                logging.info("Usuário administrador criado com sucesso!")
            else:
                logging.info("Usuário administrador já existe.")
        except SQLAlchemyError as e:
            UserRepository.rollback()
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

    env = os.getenv('FLASK_ENV', 'development').lower()
    config_map = {
        'production': ProdConfig,
        'testing': TestConfig,
    }
    config_class = config_map.get(env, DevConfig)
    app.config.from_object(config_class)
    logging.getLogger().setLevel(app.config.get('LOG_LEVEL', logging.INFO))

    migrations_dir = os.path.join(project_root, 'migrations')

    db_uri = os.getenv("DATABASE_URL", "sqlite:///agenda_laboratorio.db").strip()
    if db_uri.startswith('postgres://'):
        db_uri = db_uri.replace('postgres://', 'postgresql://', 1)

    app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
    app.config['REDIS_URL'] = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

    secret_key = (os.getenv('SECRET_KEY') or os.getenv('FLASK_SECRET_KEY') or '').strip()
    if not secret_key or secret_key.lower() == 'changeme':
        raise RuntimeError(
            "SECRET_KEY environment variable must be set to a secure value for JWT signing"
        )
    app.config['SECRET_KEY'] = secret_key
    app.config.update(
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=not app.config.get('DEBUG', False),
        WTF_CSRF_TIME_LIMIT=3600,
    )

    cookie_secure_env = os.getenv('COOKIE_SECURE')
    if cookie_secure_env is None:
        cookie_secure = not app.config.get('DEBUG', False)
    else:
        cookie_secure = cookie_secure_env.lower() in ('true', '1', 't')
    cookie_samesite = os.getenv('COOKIE_SAMESITE', 'Strict' if cookie_secure else 'Lax')
    app.config['COOKIE_SECURE'] = cookie_secure
    app.config['COOKIE_SAMESITE'] = cookie_samesite

    db.init_app(app)
    Migrate(app, db, directory=migrations_dir)
    init_redis(app)
    limiter.init_app(app)
    app.config['WTF_CSRF_CHECK_DEFAULT'] = False
    csrf.init_app(app)
    mail.init_app(app)

    app.config['SWAGGER'] = {
        'title': 'Conecta SENAI API',
        'uiversion': 3,
    }

    swagger_config = {
        "headers": [],
        "specs": [
            {
                "endpoint": "apispec_1",
                "route": "/apispec_1.json",
                "rule_filter": lambda rule: True,
                "model_filter": lambda tag: True,
            }
        ],
        "static_url_path": "/flasgger_static",
        "swagger_ui": True,
        "specs_route": "/docs",
    }

    Swagger(app, config=swagger_config, template=swagger_template)

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
    app.register_blueprint(basedados_bp, url_prefix='/api/planejamento-basedados')
    app.register_blueprint(planejamento_bp, url_prefix='/api')
    app.register_blueprint(inscricoes_treinamento_bp)
    app.register_blueprint(auth_reset_bp)
    app.register_blueprint(auth_bp)

    # Inicia scheduler para notificações
    iniciar_scheduler(app)

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


def iniciar_scheduler(app):
    """Configura scheduler para geração periódica de notificações."""
    global scheduler
    if scheduler and scheduler.running:
        logging.debug("Scheduler já está em execução; ignorando nova inicialização")
        return

    scheduler = BackgroundScheduler()

    def job():
        with app.app_context():
            criar_notificacoes_agendamentos_proximos()

    intervalo = int(os.getenv('NOTIFICACAO_INTERVALO_MINUTOS', '60'))
    scheduler.add_job(job, 'interval', minutes=intervalo, id='notificacoes_agendamentos')
    scheduler.start()


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
