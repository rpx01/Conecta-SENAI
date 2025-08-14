"""Endpoints de API para o módulo de planejamento."""
from datetime import date

from flask import jsonify, request, abort
from sqlalchemy import extract

from app.auth import require_roles, ROLE_ADMIN, ROLE_GESTOR, ROLE_USER
from app.extensions import db
from app.planejamento import bp
from app.planejamento.models import Planejamento


@bp.get("/api/planejamento")
@require_roles(ROLE_ADMIN, ROLE_GESTOR, ROLE_USER)
def api_list():
    """Lista itens de planejamento com filtros simples."""
    mes = request.args.get("mes")  # YYYY-MM
    q = Planejamento.query
    if mes:
        try:
            y, m = mes.split("-")
            q = q.filter(
                extract("year", Planejamento.data) == int(y),
                extract("month", Planejamento.data) == int(m),
            )
        except ValueError:
            abort(400, "Formato de mês inválido. Use YYYY-MM")
    itens = q.order_by(Planejamento.data.asc()).all()
    return jsonify([
        {
            "id": p.id,
            "data": p.data.isoformat(),
            "turno": p.turno,
            "carga_horas": p.carga_horas,
            "modalidade": p.modalidade,
            "treinamento": p.treinamento,
            "instrutor_id": p.instrutor_id,
            "instrutor": p.instrutor.nome if p.instrutor else None,
            "local": p.local,
            "cliente": p.cliente,
            "observacao": p.observacao,
            "status": p.status,
        }
        for p in itens
    ])


@bp.post("/api/planejamento")
@require_roles(ROLE_ADMIN, ROLE_GESTOR)
def api_create():
    """Cria um novo item de planejamento."""
    data = request.get_json() or {}
    p = Planejamento(
        data=data["data"],
        turno=data["turno"],
        carga_horas=data.get("carga_horas"),
        modalidade=data.get("modalidade"),
        treinamento=data["treinamento"],
        instrutor_id=data["instrutor_id"],
        local=data.get("local"),
        cliente=data.get("cliente"),
        observacao=data.get("observacao"),
        status=data.get("status", "Planejado"),
        origem=data.get("origem", "Manual"),
    )
    db.session.add(p)
    db.session.commit()
    return jsonify({"id": p.id}), 201


@bp.put("/api/planejamento/<int:pid>")
@require_roles(ROLE_ADMIN, ROLE_GESTOR)
def api_update(pid: int):
    """Atualiza um item de planejamento existente."""
    p = Planejamento.query.get_or_404(pid)
    data = request.get_json() or {}
    for f in [
        "data",
        "turno",
        "carga_horas",
        "modalidade",
        "treinamento",
        "instrutor_id",
        "local",
        "cliente",
        "observacao",
        "status",
    ]:
        if f in data:
            setattr(p, f, data[f])
    db.session.commit()
    return jsonify({"ok": True})


@bp.delete("/api/planejamento/<int:pid>")
@require_roles(ROLE_ADMIN, ROLE_GESTOR)
def api_delete(pid: int):
    """Remove um item de planejamento."""
    p = Planejamento.query.get_or_404(pid)
    db.session.delete(p)
    db.session.commit()
    return jsonify({"ok": True})
