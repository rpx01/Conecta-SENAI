"""Formulários para o módulo de planejamento."""
from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired


class PlanejamentoForm(FlaskForm):
    nome = StringField("Nome", validators=[DataRequired()])
