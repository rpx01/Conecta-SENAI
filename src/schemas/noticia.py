"""Schemas Marshmallow para serialização de notícias."""

from marshmallow import Schema, fields


class ImagemNoticiaSchema(Schema):
    """Serializa instâncias do modelo :class:`ImagemNoticia`."""

    id = fields.Int()
    nome_arquivo = fields.Str()
    caminho_relativo = fields.Str()
    url = fields.Str(attribute="url_publica", allow_none=True)


class NoticiaSchema(Schema):
    """Serializa instâncias do modelo :class:`Noticia`."""

    id = fields.Int()
    titulo = fields.Str(required=True)
    resumo = fields.Str(allow_none=True)
    conteudo = fields.Str(required=True)
    autor = fields.Str(allow_none=True)
    imagem_url = fields.Method("get_imagem_url")
    imagem = fields.Nested(ImagemNoticiaSchema, allow_none=True)
    destaque = fields.Bool()
    ativo = fields.Bool()
    data_publicacao = fields.DateTime(allow_none=True)
    criado_em = fields.DateTime()
    atualizado_em = fields.DateTime()

    @staticmethod
    def get_imagem_url(obj):
        imagem = getattr(obj, "imagem", None)
        if imagem is not None:
            return getattr(imagem, "url_publica", None)
        return getattr(obj, "imagem_url", None)
