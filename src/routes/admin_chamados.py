"""Rotas de administração para gerenciamento de chamados."""
from datetime import datetime
from functools import wraps

from flask import (
    Blueprint,
    abort,
    flash,
    g,
    redirect,
    render_template,
    request,
    url_for,
)

from src.auth import verificar_admin, verificar_autenticacao
from src.extensions import db
from src.models.chamados import Chamado, MensagemChamado, StatusChamado, TipoProblema
from src.models.user import User


admin_chamados_bp = Blueprint(
    "admin_chamados", __name__, url_prefix="/admin/chamados"
)


def login_required_page(func):
    """Garante que o usuário esteja autenticado antes de acessar a rota."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        autenticado, user = verificar_autenticacao(request)
        if not autenticado or user is None:
            flash("Por favor, faça login para acessar o painel administrativo.", "danger")
            return redirect("/admin/login.html")
        g.current_user = user
        return func(*args, **kwargs)

    return wrapper


def admin_required_page(func):
    """Garante que apenas administradores tenham acesso à rota."""

    @wraps(func)
    @login_required_page
    def wrapper(*args, **kwargs):
        if not verificar_admin(g.current_user):
            abort(403)
        return func(*args, **kwargs)

    return wrapper


@admin_chamados_bp.route("/dashboard")
@admin_required_page
def dashboard():
    """Exibe o painel de chamados para administradores."""

    f_status = request.args.get("status")
    f_solicitante_id = request.args.get("solicitante_id")
    f_tipo_id = request.args.get("tipo_id")

    query = Chamado.query.filter(Chamado.status != StatusChamado.FECHADO)

    if f_status:
        try:
            query = query.filter(Chamado.status == StatusChamado[f_status])
        except KeyError:
            flash("Status selecionado inválido.", "warning")
    if f_solicitante_id:
        query = query.filter(Chamado.solicitante_id == int(f_solicitante_id))
    if f_tipo_id:
        query = query.filter(Chamado.tipo_problema_id == int(f_tipo_id))

    chamados = query.order_by(Chamado.data_abertura.asc()).all()

    solicitantes = User.query.order_by(User.nome).all()
    tipos_problema = TipoProblema.query.order_by(TipoProblema.nome).all()
    status_disponiveis = [s for s in StatusChamado if s != StatusChamado.FECHADO]

    return render_template(
        "admin/chamados/dashboard.html",
        chamados=chamados,
        solicitantes=solicitantes,
        tipos_problema=tipos_problema,
        status_disponiveis=status_disponiveis,
        filtros=request.args,
        current_user=g.current_user,
    )


@admin_chamados_bp.route("/indicadores")
@admin_required_page
def indicadores():
    """Exibe indicadores e gráficos sobre os chamados."""

    total_abertos = (
        Chamado.query.filter(Chamado.status != StatusChamado.FECHADO).count()
    )

    query_status = (
        db.session.query(Chamado.status, db.func.count(Chamado.id))
        .group_by(Chamado.status)
        .all()
    )
    dados_status = {
        "labels": [s.name.replace("_", " ").title() for s, _ in query_status],
        "data": [count for _, count in query_status],
    }

    query_tipo = (
        db.session.query(TipoProblema.nome, db.func.count(Chamado.id))
        .join(Chamado.tipo_problema)
        .group_by(TipoProblema.nome)
        .order_by(TipoProblema.nome)
        .all()
    )
    dados_tipo = {
        "labels": [nome for nome, _ in query_tipo],
        "data": [count for _, count in query_tipo],
    }

    chamados_fechados = Chamado.query.filter(
        Chamado.status == StatusChamado.FECHADO,
        Chamado.data_fechamento.isnot(None),
    ).all()

    tempo_medio_dias = 0
    if chamados_fechados:
        total_dias = 0
        for chamado in chamados_fechados:
            diferenca = chamado.data_fechamento - chamado.data_abertura
            total_dias += diferenca.days
        tempo_medio_dias = round(total_dias / len(chamados_fechados), 1)

    return render_template(
        "admin/chamados/indicadores.html",
        total_abertos=total_abertos,
        dados_status=dados_status,
        dados_tipo=dados_tipo,
        tempo_medio_dias=tempo_medio_dias,
        current_user=g.current_user,
    )


@admin_chamados_bp.route("/tipos_problema", methods=["GET"])
@admin_required_page
def tipos_problema():
    """Lista todos os tipos de problema cadastrados."""

    tipos = TipoProblema.query.order_by(TipoProblema.nome).all()
    return render_template(
        "admin/chamados/tipos_problema.html",
        tipos=tipos,
        current_user=g.current_user,
    )


@admin_chamados_bp.route("/tipos_problema/salvar", methods=["POST"])
@admin_required_page
def tipos_problema_salvar():
    """Cria ou atualiza tipos de problema."""

    tipo_id = request.form.get("id")
    nome = (request.form.get("nome") or "").strip()
    descricao = (request.form.get("descricao") or "").strip() or None

    if not nome:
        flash('O campo "Nome" é obrigatório.', "danger")
        return redirect(url_for("admin_chamados.tipos_problema"))

    if tipo_id:
        tipo = TipoProblema.query.get_or_404(tipo_id)
        tipo.nome = nome
        tipo.descricao = descricao
        flash("Tipo de problema atualizado com sucesso.", "success")
    else:
        if TipoProblema.query.filter_by(nome=nome).first():
            flash("Este nome de tipo de problema já existe.", "danger")
            return redirect(url_for("admin_chamados.tipos_problema"))
        tipo = TipoProblema(nome=nome, descricao=descricao)
        db.session.add(tipo)
        flash("Tipo de problema criado com sucesso.", "success")

    db.session.commit()
    return redirect(url_for("admin_chamados.tipos_problema"))


@admin_chamados_bp.route("/tipos_problema/deletar/<int:tipo_id>", methods=["POST"])
@admin_required_page
def tipos_problema_deletar(tipo_id: int):
    """Remove um tipo de problema, se possível."""

    tipo = TipoProblema.query.get_or_404(tipo_id)

    if Chamado.query.filter_by(tipo_problema_id=tipo_id).first():
        flash(
            "Não é possível deletar este tipo, pois já está associado a chamados existentes.",
            "danger",
        )
        return redirect(url_for("admin_chamados.tipos_problema"))

    db.session.delete(tipo)
    db.session.commit()
    flash("Tipo de problema deletado com sucesso.", "success")
    return redirect(url_for("admin_chamados.tipos_problema"))


@admin_chamados_bp.route("/ver/<int:chamado_id>", methods=["GET", "POST"])
@admin_required_page
def ver_chamado_admin(chamado_id: int):
    """Exibe e permite administrar um chamado específico."""

    chamado = Chamado.query.get_or_404(chamado_id)

    if request.method == "POST":
        texto_mensagem = request.form.get("texto_mensagem")
        novo_status_str = request.form.get("novo_status")
        novo_admin_id = request.form.get("admin_responsavel_id")

        if texto_mensagem:
            nova_mensagem = MensagemChamado(
                texto=texto_mensagem.strip(),
                chamado_id=chamado.id,
                usuario_id=g.current_user.id,
            )
            db.session.add(nova_mensagem)
            flash("Mensagem enviada.", "success")

        if novo_status_str:
            try:
                novo_status = StatusChamado[novo_status_str]
            except KeyError:
                flash("Status inválido selecionado.", "danger")
                return redirect(
                    url_for("admin_chamados.ver_chamado_admin", chamado_id=chamado.id)
                )

            if chamado.status != novo_status:
                chamado.status = novo_status
                if novo_status == StatusChamado.FECHADO:
                    chamado.data_fechamento = datetime.utcnow()
                else:
                    chamado.data_fechamento = None
                flash(
                    f'Status do chamado alterado para "{novo_status.value}".',
                    "info",
                )

        if novo_admin_id is not None:
            if novo_admin_id in {"0", "", "None"}:
                if chamado.admin_responsavel_id is not None:
                    chamado.admin_responsavel_id = None
                    flash("Chamado não está mais atribuído a um responsável.", "info")
            else:
                try:
                    novo_admin_int = int(novo_admin_id)
                except ValueError:
                    flash("Administrador selecionado inválido.", "danger")
                else:
                    admin_usuario = User.query.get(novo_admin_int)
                    if not admin_usuario or admin_usuario.tipo not in {"admin", "secretaria"}:
                        flash("Administrador selecionado inválido.", "danger")
                    elif chamado.admin_responsavel_id != novo_admin_int:
                        chamado.admin_responsavel_id = novo_admin_int
                        flash(
                            f"Chamado atribuído a {admin_usuario.nome}.",
                            "info",
                        )

        db.session.add(chamado)
        db.session.commit()
        return redirect(url_for("admin_chamados.ver_chamado_admin", chamado_id=chamado.id))

    mensagens = (
        MensagemChamado.query.filter_by(chamado_id=chamado.id)
        .order_by(MensagemChamado.data_envio.asc())
        .all()
    )
    admins = (
        User.query.filter(User.tipo.in_(["admin", "secretaria"]))
        .order_by(User.nome)
        .all()
    )
    status_list = list(StatusChamado)

    return render_template(
        "admin/chamados/ver_chamado.html",
        chamado=chamado,
        mensagens=mensagens,
        admins_list=admins,
        status_list=status_list,
        current_user=g.current_user,
    )
