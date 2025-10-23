"""Rotas para abertura e acompanhamento de chamados pelos usuários."""
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

from src.auth import verificar_autenticacao, verificar_admin
from src.extensions import db
from src.models.chamados import Chamado, MensagemChamado, StatusChamado, TipoProblema


chamados_bp = Blueprint("chamados", __name__, url_prefix="/chamados")


def login_required_page(func):
    """Decorator que garante que o usuário esteja autenticado via JWT."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        autenticado, user = verificar_autenticacao(request)
        if not autenticado or user is None:
            flash("Por favor, faça login para acessar os chamados.", "danger")
            return redirect("/admin/login.html")
        g.current_user = user
        return func(*args, **kwargs)

    return wrapper


@chamados_bp.route("/abrir", methods=["GET", "POST"])
@login_required_page
def abrir_chamado():
    """Permite que um usuário abra um novo chamado de suporte."""

    tipos_problema = TipoProblema.query.order_by(TipoProblema.nome).all()

    if request.method == "POST":
        titulo = (request.form.get("titulo") or "").strip()
        descricao = (request.form.get("descricao") or "").strip()
        tipo_problema_id = request.form.get("tipo_problema_id")

        if not titulo or not descricao or not tipo_problema_id:
            flash("Por favor, preencha todos os campos obrigatórios.", "danger")
            return render_template(
                "chamados/abrir.html",
                tipos_problema=tipos_problema,
                current_user=g.current_user,
            )

        novo_chamado = Chamado(
            titulo=titulo,
            descricao=descricao,
            status=StatusChamado.ABERTO,
            solicitante_id=g.current_user.id,
            tipo_problema_id=int(tipo_problema_id),
        )

        db.session.add(novo_chamado)
        db.session.commit()

        flash("Chamado aberto com sucesso!", "success")
        return redirect(url_for("chamados.ver_chamado", chamado_id=novo_chamado.id))

    return render_template(
        "chamados/abrir.html",
        tipos_problema=tipos_problema,
        current_user=g.current_user,
    )


@chamados_bp.route("/meus_chamados")
@login_required_page
def meus_chamados():
    """Lista todos os chamados criados pelo usuário autenticado."""

    chamados_do_usuario = (
        Chamado.query.filter_by(solicitante_id=g.current_user.id)
        .order_by(Chamado.data_abertura.desc())
        .all()
    )

    return render_template(
        "chamados/meus_chamados.html",
        chamados=chamados_do_usuario,
        current_user=g.current_user,
    )


@chamados_bp.route("/ver/<int:chamado_id>", methods=["GET", "POST"])
@login_required_page
def ver_chamado(chamado_id: int):
    """Exibe os detalhes de um chamado específico para o solicitante."""

    chamado = Chamado.query.get_or_404(chamado_id)

    if chamado.solicitante_id != g.current_user.id and not verificar_admin(g.current_user):
        abort(403)

    if request.method == "POST":
        texto_mensagem = (request.form.get("texto_mensagem") or "").strip()

        if not texto_mensagem:
            flash("A mensagem não pode estar vazia.", "danger")
        else:
            nova_mensagem = MensagemChamado(
                texto=texto_mensagem,
                chamado_id=chamado.id,
                usuario_id=g.current_user.id,
            )
            db.session.add(nova_mensagem)

            if chamado.status == StatusChamado.AGUARDANDO_USUARIO:
                chamado.status = StatusChamado.EM_ANDAMENTO
                db.session.add(chamado)

            db.session.commit()
            flash("Mensagem enviada.", "success")

        return redirect(url_for("chamados.ver_chamado", chamado_id=chamado.id))

    mensagens = (
        MensagemChamado.query.filter_by(chamado_id=chamado.id)
        .order_by(MensagemChamado.data_envio.asc())
        .all()
    )

    return render_template(
        "chamados/ver_chamado.html",
        chamado=chamado,
        mensagens=mensagens,
        current_user=g.current_user,
    )
