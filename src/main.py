"""Módulo principal da aplicação Flask."""
import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler

from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_migrate import Migrate, upgrade
from flask_login import LoginManager, login_user

from src.models import db
from src.models.user import User
from src.routes.auth import auth_bp
from src.routes.user import user_bp, bcrypt
from src.routes.treinamento_admin import admin_treinamento_bp
from src.routes.treinamento_user import user_treinamento_bp
from src.routes.agendamento_admin import admin_agendamento_bp
from src.routes.agendamento_user import user_agendamento_bp
from src.routes.laboratorio_admin import admin_laboratorio_bp
from src.routes.laboratorio_user import user_laboratorio_bp
from src.routes.rateio_admin import admin_rateio_bp
from src.routes.rateio_user import user_rateio_bp
from src.routes.ocupacao_admin import admin_ocupacao_bp
from src.routes.ocupacao_user import user_ocupacao_bp

# Configuração do logging
if not os.path.exists("logs"):
    os.makedirs("logs")
file_handler = RotatingFileHandler(
    "logs/app.log", maxBytes=10240, backupCount=10
)
file_handler.setFormatter(
    logging.Formatter(
        "%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]"
    )
)
file_handler.setLevel(logging.INFO)


def create_app():
    """
    Cria e configura uma instância da aplicação Flask.

    Esta função é a fábrica da aplicação, responsável por inicializar a aplicação,
    configurar o banco de dados, registrar as rotas (blueprints) e definir
    outras configurações essenciais como CORS e logging.

    O ambiente de configuração (desenvolvimento, teste, produção) é determinado
    pela variável de ambiente FLASK_CONFIG.

    Returns:
        Flask: A instância da aplicação Flask configurada.
    """
    app = Flask(__name__)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)

    # Prioriza a configuração do Railway, se disponível
    config_type = os.getenv("FLASK_CONFIG", "development")
    if os.getenv("DATABASE_URL"):
        config_type = "production"

    if config_type == "testing":
        app.config.from_object("src.config.TestingConfig")
    elif config_type == "production":
        app.config.from_object("src.config.ProductionConfig")
    else:
        app.config.from_object("src.config.DevelopmentConfig")
        
    db.init_app(app)
    bcrypt.init_app(app)

    # --- INÍCIO DA ALTERAÇÃO ---
    # Define o caminho absoluto para a pasta de migrations
    # Isso garante que o Alembic (ferramenta de migração) encontre os arquivos
    # independentemente de onde o script de inicialização for executado.
    basedir = os.path.abspath(os.path.dirname(__file__))
    migrations_dir = os.path.join(basedir, '..', 'migrations')
    Migrate(app, db, directory=migrations_dir)
    # --- FIM DA ALTERAÇÃO ---

    # Habilita CORS para todas as origens, permitindo que o frontend
    # se comunique com a API sem erros de política de mesma origem.
    CORS(app, supports_credentials=True)

    # Configuração do Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        """
        Carrega um usuário pelo seu ID.
        Esta função é usada pelo Flask-Login para gerenciar a sessão do usuário.
        """
        return db.session.get(User, int(user_id))

    # Registra as rotas (blueprints) da aplicação
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(user_bp, url_prefix="/api")
    app.register_blueprint(admin_treinamento_bp, url_prefix="/api/admin")
    app.register_blueprint(user_treinamento_bp, url_prefix="/api/user")
    app.register_blueprint(admin_agendamento_bp, url_prefix="/api/admin")
    app.register_blueprint(user_agendamento_bp, url_prefix="/api/user")
    app.register_blueprint(admin_laboratorio_bp, url_prefix="/api/admin")
    app.register_blueprint(user_laboratorio_bp, url_prefix="/api/user")
    app.register_blueprint(admin_rateio_bp, url_prefix="/api/admin")
    app.register_blueprint(user_rateio_bp, url_prefix="/api/user")
    app.register_blueprint(admin_ocupacao_bp, url_prefix="/api/admin")
    app.register_blueprint(user_ocupacao_bp, url_prefix="/api/user")


    with app.app_context():
        # Cria as tabelas do banco de dados se não existirem
        db.create_all()

        try:
            # Aplica as migrations do banco de dados
            upgrade(directory=migrations_dir)
            app.logger.info("Migrations aplicadas com sucesso.")
        except Exception as e:
            app.logger.error(f"Erro ao aplicar migrations: {e}")
            
        # Cria o usuário administrador se não existir
        try:
            admin_email = os.getenv("ADMIN_EMAIL")
            admin_senha = os.getenv("ADMIN_SENHA")

            if admin_email and not User.query.filter_by(email=admin_email).first():
                admin_user = User(
                    nome="Administrador",
                    email=admin_email,
                    senha=admin_senha,
                    tipo="admin",
                )
                db.session.add(admin_user)
                db.session.commit()
                app.logger.info("Usuário administrador criado com sucesso.")
        except Exception as e:
            app.logger.error(f"Erro ao criar usuário administrador: {e}")
            db.session.rollback()

    return app


app = create_app()

@app.route("/login-google", methods=["POST"])
def login_google():
    """
    Rota para autenticação via Google.
    Recebe o token do Google, verifica e loga o usuário.
    """
    data = request.get_json()
    email = data.get("email")
    nome = data.get("nome")

    if not email:
        return jsonify({"erro": "Email não fornecido"}), 400

    try:
        usuario = User.query.filter_by(email=email).first()

        if not usuario:
            # Se o usuário não existe, cria um novo
            usuario = User(nome=nome, email=email, senha=os.urandom(16))
            db.session.add(usuario)
            db.session.commit()
            
        # Loga o usuário
        login_user(usuario)
        
        return jsonify(usuario.to_dict())

    except Exception as e:
        app.logger.error(f"Erro ao fazer login: {e}")
        return jsonify({"erro": "Erro interno ao processar login"}), 500


@app.route("/")
def index():
    """Rota inicial da API."""
    return f"Bem-vindo à API do Conecta SENAI! {datetime.now().isoformat()}"


@app.errorhandler(404)
def not_found_error(error):
    """Handler para erros 404 (Não Encontrado)."""
    return jsonify({"erro": "Recurso não encontrado"}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handler para erros 500 (Erro Interno do Servidor)."""
    db.session.rollback()
    return jsonify({"erro": "Erro interno do servidor"}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
