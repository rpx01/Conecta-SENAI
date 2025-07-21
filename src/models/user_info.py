from src.models import db

class UserInfo(db.Model):
    """Informações opcionais adicionais dos usuários."""

    __tablename__ = 'usuarios_info'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False, unique=True)
    cpf = db.Column(db.String(14))
    data_nascimento = db.Column(db.Date)
    empresa = db.Column(db.String(150))

    user = db.relationship('User', back_populates='info')

    def to_dict(self):
        return {
            'cpf': self.cpf,
            'data_nascimento': self.data_nascimento.isoformat() if self.data_nascimento else None,
            'empresa': self.empresa,
        }
