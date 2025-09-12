from marshmallow import Schema, fields


class SecretariaTreinamentosSchema(Schema):
    id = fields.Int(dump_only=True)
    nome = fields.Str(required=False, allow_none=True)
    email = fields.Email(required=True)
    ativo = fields.Bool(dump_only=True)
