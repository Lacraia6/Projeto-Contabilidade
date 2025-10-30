"""
Schemas de Validação para Empresa
"""

from marshmallow import Schema, fields, validate, ValidationError


class EmpresaSchema(Schema):
    """Schema para serialização de empresa"""
    id = fields.Int(dump_only=True)
    codigo = fields.Str(required=True, validate=validate.Length(min=2, max=10))
    nome = fields.Str(required=True, validate=validate.Length(min=3, max=255))
    tributacao_id = fields.Int(allow_none=True)
    ativo = fields.Bool(missing=True)
    criado_em = fields.DateTime(dump_only=True)
    atualizado_em = fields.DateTime(dump_only=True)


class EmpresaCreateSchema(Schema):
    """Schema para criação de empresa"""
    codigo = fields.Str(required=True, validate=validate.Length(min=2, max=10))
    nome = fields.Str(required=True, validate=validate.Length(min=3, max=255))
    tributacao_id = fields.Int(required=True)
    
    @validate('codigo')
    def validate_codigo(self, value):
        """Valida que código não é vazio"""
        if not value or not value.strip():
            raise ValidationError('Código é obrigatório')
        return value.strip().upper()


class EmpresaUpdateSchema(Schema):
    """Schema para atualização de empresa"""
    nome = fields.Str(validate=validate.Length(min=3, max=255))
    codigo = fields.Str(validate=validate.Length(min=2, max=10))
    tributacao_id = fields.Int(allow_none=True)
    ativo = fields.Bool()

