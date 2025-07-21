"""Rotas para gerenciamento de usuarios."""

from flask import Blueprint, request, jsonify, current_app, g, redirect
import os

from src.limiter import limiter
import re
from datetime import datetime, timedelta
import jwt
import uuid
from src.models import db
from src.models.user import User
from src.models.refresh_token import RefreshToken
import hashlib
from src.redis_client import redis_conn
from sqlalchemy.exc import SQLAlchemyError
import requests
from werkzeug.security import check_password_hash
from src.utils.error_handler import handle_internal_error
from src.auth import (
    verificar_autenticacao,  # noqa: F401 - reexportado para outros módulos
    verificar_admin,
    login_required,
    admin_required,
)

user_bp = Blueprint("user", __name__)

# chaves do Google reCAPTCHA
RECAPTCHA_SITE_KEY = os.getenv("RECAPTCHA_SITE_KEY") or os.getenv("SITE_KEY")
RECAPTCHA_SECRET_KEY = (
    os.getenv("RECAPTCHA_SECRET_KEY")
    or os.getenv("CAPTCHA_SECRET_KEY")
    or os.getenv("SECRET_KEY")
)
RECAPTCHA_THRESHOLD = float(os.getenv("RECAPTCHA_THRESHOLD", "0.5"))


@user_bp.route("/recaptcha/site-key", methods=["GET"])
def obter_site_key():
    """Retorna a site key pública do reCAPTCHA."""
    return jsonify({"site_key": RECAPTCHA_SITE_KEY or ""})


PASSWORD_REGEX = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).{8,}$")

# Funções auxiliares para geração de tokens


def gerar_token_acesso(usuario):
    """Gera um token JWT de acesso para o usuário."""
    payload = {
        "user_id": usuario.id,
        "nome": usuario.nome,
        "perfil": usuario.tipo,
        "exp": datetime.utcnow() + timedelta(minutes=15),
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(payload, current_app.config["SECRET_KEY"], algorithm="HS256")


def _hash_token(token: str) -> str:
    """Return SHA-256 hexadecimal hash for a token."""
    return hashlib.sha256(token.encode()).hexdigest()


def gerar_refresh_token(usuario):
    """Gera e persiste um refresh token para o usuário."""
    exp = datetime.utcnow() + timedelta(days=7)
    payload = {
        "user_id": usuario.id,
        "exp": exp,
        "type": "refresh",
        "jti": str(uuid.uuid4()),
    }
    token = jwt.encode(payload, current_app.config["SECRET_KEY"], algorithm="HS256")

    # Confirma que o usuário ainda existe antes de salvar o token
    if not db.session.get(User, usuario.id):
        current_app.logger.error("Usuário inválido ao gerar refresh token")
        raise ValueError("Usuário inválido")

    rt = RefreshToken(
        user_id=usuario.id,
        token_hash=_hash_token(token),
        expires_at=exp,
        created_at=datetime.utcnow(),
    )
    try:
        db.session.add(rt)
        db.session.commit()
    except Exception as e:  # pragma: no cover - proteção contra falhas de banco
        db.session.rollback()
        current_app.logger.error(f"Erro ao salvar refresh token: {str(e)}")
        raise

    return token


def verificar_refresh_token(token):
    """Valida um refresh token e retorna o usuário associado ou None."""
    try:
        dados = jwt.decode(
            token, current_app.config["SECRET_KEY"], algorithms=["HS256"]
        )
        if dados.get("type") != "refresh":
            return None
        rt = RefreshToken.query.filter_by(
            token_hash=_hash_token(token), revoked=False
        ).first()
        if not rt or rt.is_expired():
            return None
        usuario = db.session.get(User, dados.get("user_id"))
        return usuario
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


@user_bp.route("/usuarios", methods=["GET"])
@admin_required
def listar_usuarios():
    """Lista todos os usuários."""
    usuarios = User.query.all()
    return jsonify([u.to_dict() for u in usuarios])


@user_bp.route("/usuarios/<int:id>", methods=["GET"])
@login_required
def obter_usuario(id):
    """Obtém detalhes de um usuário específico."""
    user = g.current_user
    if not verificar_admin(user) and user.id != id:
        return jsonify({"erro": "Permissão negada"}), 403

    usuario = db.session.get(User, id)
    if not usuario:
        return jsonify({"erro": "Usuário não encontrado"}), 404

    return jsonify(usuario.to_dict())


@user_bp.route("/usuarios", methods=["POST"])
@limiter.limit("5 per minute")
def criar_usuario():
    """Cria um novo usuário.
    Usuários não autenticados podem criar apenas usuários comuns.
    Administradores podem criar qualquer tipo de usuário.
    """
    dados = request.get_json()

    email = dados.get("email", "").strip()
    nome = dados.get("nome")
    senha = dados.get("senha")
    username = dados.get("username") or email.split('@')[0]

    # Validação de dados
    if not all([nome, email, senha]):
        return jsonify({"erro": "Dados incompletos"}), 400

    # Para registro público não permitimos definir tipo

    # Verifica se o email já existe
    if User.query.filter_by(email=email).first():
        return jsonify({"erro": "Este e-mail já está registado"}), 400

    # Validação de senha
    if not PASSWORD_REGEX.match(senha):
        return (
            jsonify(
                {
                    "erro": "Senha deve ter ao menos 8 caracteres, incluindo letra maiúscula, letra minúscula, número e caractere especial"
                }
            ),
            400,
        )

    # Cria o usuário
    try:
        novo_usuario = User(
            nome=nome,
            email=email,
            senha=senha,
            tipo="comum",
            username=username,
        )
        db.session.add(novo_usuario)
        db.session.commit()
        return jsonify(novo_usuario.to_dict()), 201
    except SQLAlchemyError as e:
        db.session.rollback()
        return handle_internal_error(e)


@user_bp.route("/registrar", methods=["POST"])
def registrar_usuario():
    """Registra um usuário a partir de um formulário HTML."""
    nome = request.form.get("nome", "").strip()
    email = request.form.get("email", "").strip()
    senha = request.form.get("senha")
    username = request.form.get("username") or email.split('@')[0]
    confirmar = request.form.get("confirmarSenha")

    if not all([nome, email, senha, confirmar]):
        return jsonify({"erro": "Dados incompletos"}), 400

    if senha != confirmar:
        return jsonify({"erro": "As senhas não coincidem"}), 400

    if not PASSWORD_REGEX.match(senha):
        return (
            jsonify(
                {
                    "erro": "Senha deve ter ao menos 8 caracteres, incluindo letra maiúscula, letra minúscula, número e caractere especial"
                }
            ),
            400,
        )

    if User.query.filter_by(email=email).first():
        return jsonify({"erro": "Este e-mail já está registado"}), 400

    try:
        novo_usuario = User(
            nome=nome,
            email=email,
            senha=senha,
            tipo="comum",
            username=username,
        )
        db.session.add(novo_usuario)
        db.session.commit()
    except SQLAlchemyError as e:  # pragma: no cover
        db.session.rollback()
        return handle_internal_error(e)

    if "text/html" in request.accept_mimetypes:
        return redirect("/admin-login.html")
    return jsonify({"mensagem": "Usuário registrado com sucesso"}), 201


@user_bp.route("/usuarios/<int:id>", methods=["PUT"])
@login_required
def atualizar_usuario(id):
    """
    Atualiza um usuário existente.
    Usuários comuns só podem atualizar seus próprios dados.
    Administradores podem atualizar dados de qualquer usuário.
    """
    user = g.current_user

    # Verifica permissões
    if not verificar_admin(user) and user.id != id:
        return jsonify({"erro": "Permissão negada"}), 403

    usuario = db.session.get(User, id)
    if not usuario:
        return jsonify({"erro": "Usuário não encontrado"}), 404

    data = request.json

    # Atualiza os campos fornecidos
    if "nome" in data:
        usuario.nome = data["nome"]

    if "email" in data:
        # Verifica se o email já existe para outro usuário
        email_existente = User.query.filter_by(email=data["email"]).first()
        if email_existente and email_existente.id != id:
            return jsonify({"erro": "Email já cadastrado para outro usuário"}), 400
        usuario.email = data["email"]

    if "cpf" in data:
        usuario.cpf = data["cpf"]
    if "data_nascimento" in data and data.get("data_nascimento"):
        try:
            usuario.data_nascimento = datetime.strptime(data["data_nascimento"], '%Y-%m-%d').date()
        except (ValueError, TypeError):
            pass
    else:
        usuario.data_nascimento = None
    if "empresa" in data:
        usuario.empresa = data["empresa"]

    # Apenas administradores podem alterar o tipo de usuário
    if "tipo" in data and verificar_admin(user):
        if data["tipo"] not in ["comum", "admin"]:
            return jsonify({"erro": "Tipo de usuário inválido"}), 400

        novo_tipo = data["tipo"]

        # Evita que administradores comuns rebaixem outros administradores
        if usuario.tipo == "admin" and novo_tipo == "comum":
            admin_email = os.getenv("ADMIN_EMAIL")
            is_root = admin_email and user.email == admin_email

            if not is_root:
                return (
                    jsonify(
                        {
                            "erro": "Você não tem permissão para rebaixar um administrador"
                        }
                    ),
                    403,
                )

        usuario.tipo = novo_tipo

    # Atualiza a senha se fornecida
    if "senha" in data:
        senha_atual = data.get("senha_atual")

        # Se quem está alterando não é um administrador editando outro usuário,
        # exige a senha atual para confirmar a operação
        if not verificar_admin(user) or user.id == id:
            if not senha_atual:
                return jsonify({"erro": "Senha atual obrigatória"}), 400
            if not usuario.check_senha(senha_atual):
                return jsonify({"erro": "Senha atual incorreta"}), 403

        nova_senha = data["senha"]
        if not PASSWORD_REGEX.match(nova_senha):
            return (
                jsonify(
                    {
                        "erro": "Senha deve ter ao menos 8 caracteres, incluindo letra maiúscula, letra minúscula, número e caractere especial"
                    }
                ),
                400,
            )

        usuario.set_senha(nova_senha)

    try:
        db.session.commit()
        return jsonify(usuario.to_dict())
    except SQLAlchemyError as e:
        db.session.rollback()
        return handle_internal_error(e)


@user_bp.route("/usuarios/<int:id>", methods=["DELETE"])
@admin_required
def remover_usuario(id):
    """
    Remove um usuário.
    Apenas administradores podem remover usuários.
    Um usuário não pode remover a si mesmo.
    """
    user = g.current_user

    # Impede que um usuário remova a si mesmo
    if user.id == id:
        return jsonify({"erro": "Não é possível remover o próprio usuário"}), 400

    usuario = db.session.get(User, id)
    if not usuario:
        return jsonify({"erro": "Usuário não encontrado"}), 404

    try:
        db.session.delete(usuario)
        db.session.commit()
        return jsonify({"mensagem": "Usuário removido com sucesso"})
    except SQLAlchemyError as e:
        db.session.rollback()
        return handle_internal_error(e)


@user_bp.route("/login", methods=["POST"])
@limiter.limit("10 per minute")
def login():
    """Autentica um usuário e retorna tokens JWT."""
    try:
        dados = request.get_json(silent=True)

        if not dados:
            return jsonify(success=False, message="Corpo da requisição ausente"), 400

        email = dados.get("email", "").strip()
        senha = dados.get("senha")
        recaptcha_token = dados.get("recaptcha_token")

        # Valida reCAPTCHA caso a chave esteja configurada
        recaptcha_secret = current_app.config.get("RECAPTCHA_SECRET_KEY")
        if recaptcha_secret:
            if not recaptcha_token:
                return (
                    jsonify(success=False, message="Verificação reCAPTCHA obrigatória"),
                    400,
                )
            try:
                verify_resp = requests.post(
                    "https://www.google.com/recaptcha/api/siteverify",
                    data={"secret": recaptcha_secret, "response": recaptcha_token},
                    timeout=5,
                )
                verify_data = verify_resp.json()
                threshold = current_app.config.get("RECAPTCHA_THRESHOLD", 0.5)
                if (
                    not verify_data.get("success")
                    or verify_data.get("action") != "login"
                    or verify_data.get("score", 0) < threshold
                ):
                    return (
                        jsonify(
                            success=False,
                            message="Verificação reCAPTCHA falhou. Tente novamente.",
                        ),
                        400,
                    )
            except requests.RequestException:
                return (
                    jsonify(success=False, message="Falha ao verificar reCAPTCHA"),
                    400,
                )

        if not email or not senha:
            return jsonify(success=False, message="Email e senha são obrigatórios"), 400

        usuario = User.query.filter_by(email=email).first()

        try:
            senha_ok = usuario and check_password_hash(usuario.senha_hash, senha)
        except ValueError:
            senha_ok = False

        if not senha_ok:
            current_app.logger.warning(
                "Tentativa de login inválida para %s do IP %s",
                email,
                request.remote_addr,
            )
            return jsonify(success=False, message="Credenciais inválidas"), 401

        access_token = gerar_token_acesso(usuario)
        try:
            refresh_token = gerar_refresh_token(usuario)
        except Exception as e:
            current_app.logger.error(f"Erro ao salvar refresh token: {e}")
            return jsonify(success=False, message="Erro ao salvar token"), 500

        resp = jsonify(
            message="Login successful",
            token=access_token,
            refresh_token=refresh_token,
            usuario=usuario.to_dict(),
        )
        resp.set_cookie(
            "access_token",
            access_token,
            httponly=True,
            samesite="Lax",
        )
        resp.set_cookie(
            "refresh_token",
            refresh_token,
            httponly=True,
            samesite="Lax",
        )
        return resp, 200
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao fazer login: {e}")
        return jsonify(success=False, message="Erro interno no login"), 500
    except Exception as e:
        current_app.logger.error(f"Erro inesperado ao fazer login: {e}")
        return jsonify(success=False, message="Erro interno no login"), 500


@user_bp.route("/refresh", methods=["POST"])
def refresh_token():
    data = request.json or {}
    token = data.get("refresh_token") or request.cookies.get("refresh_token")
    if not token:
        return jsonify({"erro": "Refresh token obrigatório"}), 400
    usuario = verificar_refresh_token(token)
    if not usuario:
        return jsonify({"erro": "Refresh token inválido"}), 401
    novo_token = gerar_token_acesso(usuario)
    resp = jsonify({"token": novo_token})
    resp.set_cookie(
        "access_token",
        novo_token,
        httponly=True,
        samesite="Lax",
    )
    return resp


@user_bp.route("/logout", methods=["POST"])
def logout():
    """Revoga o token de acesso atual e/ou o refresh token."""
    auth_header = request.headers.get("Authorization")
    token = (
        auth_header.split(" ")[1]
        if auth_header
        else request.cookies.get("access_token")
    )

    if token:
        try:
            dados = jwt.decode(
                token,
                current_app.config["SECRET_KEY"],
                algorithms=["HS256"],
                options={"verify_exp": False},
            )
            jti = dados.get("jti")
            exp = datetime.utcfromtimestamp(dados["exp"])
            ttl = exp - datetime.utcnow()
            if ttl.total_seconds() > 0 and jti:
                redis_conn.setex(jti, ttl, "revoked")
        except jwt.InvalidTokenError:
            return jsonify({"erro": "Token inválido"}), 401

    data = request.json or {}
    refresh = data.get("refresh_token") or request.cookies.get("refresh_token")
    if refresh:
        rt = RefreshToken.query.filter_by(token_hash=_hash_token(refresh)).first()
        if rt:
            rt.revoked = True
            db.session.commit()

    if not token and not refresh:
        return jsonify({"erro": "Token obrigatório"}), 400

    resp = jsonify({"mensagem": "Logout realizado"})
    resp.set_cookie("access_token", "", expires=0)
    resp.set_cookie("refresh_token", "", expires=0)
    return resp
