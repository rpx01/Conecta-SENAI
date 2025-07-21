import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from alembic.config import Config
from alembic import command

from .models import db
from .models.user import User

logging.basicConfig(level=logging.INFO)

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("A vari\u00e1vel de ambiente DATABASE_URL n\u00e3o foi definida.")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Inicializa o banco de dados e aplica as migra\u00e7\u00f5es do Alembic."""
    try:
        alembic_cfg_path = '/app/migrations/alembic.ini'
        alembic_cfg = Config(alembic_cfg_path)

        logging.info("Configurando a URL do banco de dados para o Alembic...")
        alembic_cfg.set_main_option('sqlalchemy.url', DATABASE_URL)

        logging.info("Aplicando migra\u00e7\u00f5es do banco de dados (upgrade head)...")
        command.upgrade(alembic_cfg, "head")
        logging.info("Migra\u00e7\u00f5es aplicadas com sucesso.")

    except Exception as e:
        logging.error(f"Ocorreu um erro ao aplicar as migra\u00e7\u00f5es: {e}")
        raise


def create_admin_user():
    """Cria um usu\u00e1rio administrador se ele ainda n\u00e3o existir."""
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.username == "admin").first()
        if not admin:
            admin_user = User(
                nome="Administrador",
                username="admin",
                email="admin@example.com",
                senha="admin",
                tipo="admin",
            )
            db.add(admin_user)
            db.commit()
            logging.info("Usu\u00e1rio administrador criado com sucesso.")
        else:
            logging.info("Usu\u00e1rio administrador j\u00e1 existe.")
    except Exception as e:
        logging.error(
            f"Erro ao verificar ou criar o usuário administrador: {e}"
        )
        db.rollback()
    finally:
        db.close()
