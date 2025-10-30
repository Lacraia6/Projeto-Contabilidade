"""
Schemas de Validação para Tarefa
"""

from marshmallow import Schema, fields, validate


class TarefaSchema(Schema):
    """Schema para serialização de tarefa"""
    id = fields.Int(dump_only=True)
    nome = fields.Str(required=True, validate=validate.Length(min=3, max=255))
    tipo = fields.Str(required=True, validate=validate.OneOf(['Mensal', 'Trimestral', 'Anual']))
    descricao = fields.Str(allow_none=True)
    tributacao_id = fields.Int(allow_none=True)
    setor_id = fields.Int(allow_none=True)
    tarefa_comum = fields.Bool(missing=False)
    condicoes_especiais = fields.Str(allow_none=True)
    criado_em = fields.DateTime(dump_only=True)
    atualizado_em = fields.DateTime(dump_only=True)


class TarefaCreateSchema(Schema):
    """Schema para criação de tarefa"""
    nome = fields.Str(required=True, validate=validate.Length(min=3, max=255))
    tipo = fields.Str(required=True, validate=validate.OneOf(['Mensal', 'Trimestral', 'Anual']))
    descricao = fields.Str(allow_none=True)
    tributacao_id = fields.Int(allow_none=True)
    setor_id = fields.Int(required=True)
    tarefa_comum = fields.Bool(missing=False)
    condicoes_especiais = fields.Str(allow_none=True)

