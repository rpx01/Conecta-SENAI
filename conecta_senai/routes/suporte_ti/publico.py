"""Rotas públicas (usuários autenticados e visitantes) do módulo de suporte de TI."""
from __future__ import annotations

import os
import re
import secrets
from datetime import datetime

from email_validator import EmailNotValidError, validate_email
from flask import (
    Blueprint,
    current_app,
    flash,
    g,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_wtf.csrf import CSRFError, generate_csrf, validate_csrf
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.utils import secure_filename

from conecta_senai.auth import login_required
from conecta_senai.models import User, db
from conecta_senai.models.suporte_anexo import SuporteAnexo
from conecta_senai.models.suporte_basedados import SuporteArea, SuporteTipoEquipamento
from conecta_senai.models.suporte_chamado import SuporteChamado
from conecta_senai.routes.suporte_ti.utils import ensure_tables_exist

suporte_ti_public_bp = Blueprint(
    "suporte_ti_publico",
    __name__,
    url_prefix="/api/suporte_ti",
)

suporte_ti_public_html_bp = Blueprint(
    "suporte_ti_public_html",
    __name__,
)

ALLOWED_URGENCIAS = {"Baixo", "Médio", "Medio", "Alto"}
_USERNAME_SANITIZE_RE = re.compile(r"[^a-z0-9]+")


def _render_public_form(
    areas: list[SuporteArea],
    tipos: list[SuporteTipoEquipamento],
    form_data: dict[str, str] | None = None,
    errors: list[str] | None = None,
    status_code: int = 200,
):
    """Renderiza o formulário público com os dados auxiliares necessários."""

    return (
        render_template(
            "suporte_ti/abertura_publica.html",
            csrf_token=generate_csrf(),
            areas=areas,
            tipos=tipos,
            form_data=form_data or {},
            form_errors=errors or [],
        ),
        status_code,
    )


def _gerar_username_base(email: str) -> str:
    """Gera um username base sanitizado a partir do e-mail informado."""

    local_part = (email.split("@", 1)[0] or "usuario").lower()
    base = _USERNAME_SANITIZE_RE.sub("-", local_part).strip("-") or "usuario"
    return base[:40]


def _obter_ou_criar_usuario_publico(nome: str, email: str) -> User:
    """Obtém o usuário relacionado ao e-mail ou cria um novo registro público."""

    email_normalizado = email.lower()
    usuario = User.query.filter(func.lower(User.email) == email_normalizado).first()
    if usuario:
        return usuario

    base_username = _gerar_username_base(email_normalizado)
    username = base_username
    sufixo = 1
    while User.query.filter_by(username=username).first():
        username = f"{base_username[:35]}-{sufixo}"
        sufixo += 1

    senha_temporaria = secrets.token_urlsafe(16)
    novo_usuario = User(
        nome=nome,
        email=email_normalizado,
        senha=senha_temporaria,
        username=username,
    )
    db.session.add(novo_usuario)
    db.session.flush()
    return novo_usuario


@suporte_ti_public_html_bp.route("/suporte/abrir-chamado", methods=["GET", "POST"])
def abrir_chamado_publico():
    """Disponibiliza um formulário público para abertura de chamados."""

    ensure_tables_exist([SuporteArea, SuporteTipoEquipamento, SuporteChamado])

    areas = SuporteArea.query.order_by(SuporteArea.nome.asc()).all()
    tipos = (
        SuporteTipoEquipamento.query.order_by(SuporteTipoEquipamento.nome.asc()).all()
    )

    if request.method == "GET":
        return _render_public_form(areas, tipos)

    form_data = {chave: (valor or "").strip() for chave, valor in request.form.items()}
    erros: list[str] = []

    try:
        validate_csrf(form_data.get("csrf_token"))
    except CSRFError:
        erros.append("Não conseguimos validar o token de segurança. Atualize a página e tente novamente.")

    nome = form_data.get("nome_completo", "")
    if not nome:
        erros.append("Informe seu nome completo.")

    email = form_data.get("email", "").lower()
    if not email:
        erros.append("Informe um e-mail para contato.")
    else:
        try:
            validate_email(email, check_deliverability=False)
        except EmailNotValidError:
            erros.append("E-mail informado é inválido.")

    descricao = form_data.get("descricao_problema", "")
    if not descricao:
        erros.append("Descreva o problema encontrado.")

    nivel_urgencia = (form_data.get("nivel_urgencia") or "").strip()
    if not nivel_urgencia:
        erros.append("Selecione o nível de urgência.")
    elif nivel_urgencia not in ALLOWED_URGENCIAS:
        erros.append("Nível de urgência inválido.")

    area_obj = None
    try:
        area_id = int(form_data.get("area_id", ""))
        area_obj = db.session.get(SuporteArea, area_id)
    except (TypeError, ValueError):
        area_obj = None
    if not area_obj:
        erros.append("Selecione uma área válida.")

    tipo_equipamento_obj = None
    try:
        tipo_id = int(form_data.get("tipo_equipamento_id", ""))
        tipo_equipamento_obj = db.session.get(SuporteTipoEquipamento, tipo_id)
    except (TypeError, ValueError):
        tipo_equipamento_obj = None
    if not tipo_equipamento_obj:
        erros.append("Selecione um tipo de equipamento válido.")

    if erros:
        return _render_public_form(areas, tipos, form_data=form_data, errors=erros, status_code=400)

    nivel_normalizado = "Médio" if nivel_urgencia == "Medio" else nivel_urgencia

    try:
        usuario = _obter_ou_criar_usuario_publico(nome, email)
        chamado = SuporteChamado(
            user_id=usuario.id,
            email=email,
            area=area_obj.nome,
            tipo_equipamento_id=tipo_equipamento_obj.id,
            patrimonio=form_data.get("patrimonio") or None,
            numero_serie=form_data.get("numero_serie") or None,
            descricao_problema=descricao,
            nivel_urgencia=nivel_normalizado,
            observacoes=form_data.get("local") or None,
            status="Aberto",
        )
        db.session.add(chamado)
        db.session.commit()
    except SQLAlchemyError:
        current_app.logger.exception("Falha ao salvar chamado público de suporte")
        db.session.rollback()
        flash(
            "Não foi possível registrar o chamado neste momento. Tente novamente em instantes.",
            "danger",
        )
        return _render_public_form(areas, tipos, form_data=form_data, status_code=500)

    flash("Chamado registrado com sucesso! Em breve nossa equipe entrará em contato.", "success")
    return redirect(url_for("suporte_ti_public_html.abrir_chamado_publico"))


def _serialize_chamado(chamado: SuporteChamado) -> dict:
    return {
        "id": chamado.id,
        "user_id": chamado.user_id,
        "nome": chamado.user.nome if chamado.user else None,
        "email": chamado.email,
        "area": chamado.area,
        "tipo_equipamento_id": chamado.tipo_equipamento_id,
        "tipo_equipamento_nome": (
            chamado.tipo_equipamento.nome if chamado.tipo_equipamento else None
        ),
        "patrimonio": chamado.patrimonio,
        "numero_serie": chamado.numero_serie,
        "descricao_problema": chamado.descricao_problema,
        "nivel_urgencia": chamado.nivel_urgencia,
        "status": chamado.status,
        "created_at": chamado.created_at.isoformat() if chamado.created_at else None,
        "updated_at": chamado.updated_at.isoformat() if chamado.updated_at else None,
        "observacoes": chamado.observacoes,
        "anexos": [anexo.file_path for anexo in chamado.anexos],
    }


@suporte_ti_public_bp.route("/novo_chamado", methods=["POST"])
@login_required
def criar_chamado():
    ensure_tables_exist(
        [SuporteArea, SuporteTipoEquipamento, SuporteChamado, SuporteAnexo]
    )

    usuario = g.current_user
    form = request.form

    area = (form.get("area") or "").strip()
    tipo_equipamento_id = form.get("tipo_equipamento_id") or form.get(
        "tipoEquipamentoId"
    )
    patrimonio = form.get("patrimonio") or None
    numero_serie = form.get("numero_serie") or form.get("numeroSerie") or None
    descricao = (form.get("descricao_problema") or form.get("descricaoProblema") or "").strip()
    nivel_urgencia = (form.get("nivel_urgencia") or form.get("nivelUrgencia") or "").strip()

    erros: list[str] = []

    if not area:
        erros.append("Área é obrigatória.")

    try:
        tipo_equipamento_id_int = int(tipo_equipamento_id)
    except (TypeError, ValueError):
        erros.append("Tipo de equipamento inválido.")
        tipo_equipamento_id_int = None

    if not descricao:
        erros.append("Descrição do problema é obrigatória.")

    if not nivel_urgencia:
        erros.append("Nível de urgência é obrigatório.")
    elif nivel_urgencia not in ALLOWED_URGENCIAS:
        erros.append("Nível de urgência inválido.")

    area_registro = None
    if area:
        area_registro = (
            SuporteArea.query.filter(func.lower(SuporteArea.nome) == area.lower())
            .first()
        )
        if not area_registro:
            erros.append("Área selecionada não está cadastrada.")

    if erros:
        return jsonify({"erro": erros}), 400

    tipo_equipamento = None
    if tipo_equipamento_id_int is not None:
        tipo_equipamento = db.session.get(
            SuporteTipoEquipamento, tipo_equipamento_id_int
        )
        if not tipo_equipamento:
            return jsonify({"erro": "Tipo de equipamento não encontrado."}), 404

    anexos = request.files.getlist("anexos") or request.files.getlist("fotos")
    anexos_validos = [arquivo for arquivo in anexos if arquivo and arquivo.filename]
    if len(anexos_validos) > 5:
        return jsonify({"erro": "É permitido anexar no máximo 5 arquivos."}), 400

    upload_folder = os.path.join(current_app.static_folder, "uploads", "suporte")
    os.makedirs(upload_folder, exist_ok=True)

    chamado = SuporteChamado(
        user_id=usuario.id,
        email=usuario.email,
        area=area_registro.nome if area_registro else area,
        tipo_equipamento_id=tipo_equipamento.id if tipo_equipamento else None,
        patrimonio=patrimonio or None,
        numero_serie=numero_serie or None,
        descricao_problema=descricao,
        nivel_urgencia="Médio" if nivel_urgencia == "Medio" else nivel_urgencia,
        status="Aberto",
    )

    arquivos_salvos: list[SuporteAnexo] = []
    for arquivo in anexos_validos:
        nome_seguro = secure_filename(arquivo.filename)
        if not nome_seguro:
            continue
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")
        nome_final = f"{timestamp}_{nome_seguro}"
        caminho_completo = os.path.join(upload_folder, nome_final)
        arquivo.save(caminho_completo)
        caminho_relativo = os.path.relpath(caminho_completo, current_app.static_folder)
        arquivos_salvos.append(
            SuporteAnexo(file_path=os.path.join("/", caminho_relativo).replace("\\", "/"))
        )

    if arquivos_salvos:
        chamado.anexos.extend(arquivos_salvos)

    try:
        db.session.add(chamado)
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        for anexo in arquivos_salvos:
            caminho_arquivo = anexo.file_path.lstrip("/")
            caminho_completo = os.path.join(current_app.static_folder, caminho_arquivo)
            if os.path.exists(caminho_completo):
                try:
                    os.remove(caminho_completo)
                except OSError:
                    pass
        return jsonify({"erro": "Não foi possível criar o chamado."}), 500

    return jsonify({"mensagem": "Chamado criado com sucesso.", "id": chamado.id}), 201


@suporte_ti_public_bp.route("/meus_chamados", methods=["GET"])
@login_required
def listar_meus_chamados():
    ensure_tables_exist([SuporteChamado])
    usuario = g.current_user
    chamados = (
        SuporteChamado.query.filter_by(user_id=usuario.id)
        .order_by(SuporteChamado.created_at.desc())
        .all()
    )
    return jsonify([_serialize_chamado(chamado) for chamado in chamados])


@suporte_ti_public_bp.route("/basedados_formulario", methods=["GET"])
@login_required
def obter_base_dados_formulario():
    ensure_tables_exist([SuporteTipoEquipamento, SuporteArea])

    tipos = (
        SuporteTipoEquipamento.query.order_by(SuporteTipoEquipamento.nome.asc()).all()
    )
    areas = SuporteArea.query.order_by(SuporteArea.nome.asc()).all()

    return jsonify(
        {
            "tipos_equipamento": [
                {"id": tipo.id, "nome": tipo.nome} for tipo in tipos
            ],
            "areas": [{"id": area.id, "nome": area.nome} for area in areas],
        }
    )
