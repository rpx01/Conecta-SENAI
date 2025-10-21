from src.models import db
from src.models.user import User
from src.models.refresh_token import RefreshToken


class UserRepository:
    """Encapsula operações de banco relacionadas a usuários."""

    @staticmethod
    def get_by_email(email: str):
        return User.query.filter_by(email=email).first()

    @staticmethod
    def get_by_id(user_id: int):
        return db.session.get(User, user_id)

    @staticmethod
    def add(user: User):
        db.session.add(user)
        db.session.commit()
        return user

    @staticmethod
    def paginate(page: int, per_page: int):
        return User.query.paginate(page=page, per_page=per_page, error_out=False)

    @staticmethod
    def delete(user: User):
        """Remove um usuário e seus registros dependentes."""

        if user.id is not None:
            RefreshToken.query.filter_by(user_id=user.id).delete(
                synchronize_session=False
            )

        db.session.delete(user)
        db.session.commit()

    @staticmethod
    def commit():
        db.session.commit()

    @staticmethod
    def rollback():
        db.session.rollback()
