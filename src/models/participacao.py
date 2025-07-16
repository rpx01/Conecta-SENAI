from src.models import db

class Inscricao(db.Model):
    __tablename__ = 'inscricoes'
    id = db.Column(db.Integer, primary_key=True)
    turma_id = db.Column(db.Integer, db.ForeignKey('turmas_treinamento.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)

    turma = db.relationship('TurmaTreinamento', backref='inscricoes')
    usuario = db.relationship('User', backref='inscricoes_treinamentos')

    def to_dict(self):
        return {
            'id': self.id,
            'turma_id': self.turma_id,
            'usuario_id': self.usuario_id,
        }

class Presenca(db.Model):
    __tablename__ = 'presencas'
    id = db.Column(db.Integer, primary_key=True)
    inscricao_id = db.Column(db.Integer, db.ForeignKey('inscricoes.id'), nullable=False)
    data = db.Column(db.Date, nullable=False)
    presente = db.Column(db.Boolean, default=False, nullable=False)

    inscricao = db.relationship('Inscricao', backref='lista_presenca')

    def to_dict(self):
        return {
            'id': self.id,
            'inscricao_id': self.inscricao_id,
            'data': self.data.isoformat() if self.data else None,
            'presente': self.presente,
        }
