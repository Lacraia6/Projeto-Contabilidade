"""
Schemas de Validação para Usuario
"""

from marshmallow import Schema, fields, validate


class UsuarioSchema(Schema):
    """Schema para serialização de usuário (sem senha)"""
    id = fields.Int(dump_only=True)
    nome = fields.Str(required=True, validate=validate.Length(min=3, max=255))
    login = fields.Str(required=True, validate=validate.Length(min=3, max=150))
    tipo = fields.Str(required=True, validate=validate.OneOf(['normal', 'gerente', 'admin']))
    setor_id = fields.Int(allow_none=True)
    ativo = fields.Bool(missing=True)
    criado_em = fields.DateTime(dump_only=True)
    atualizado_em = fields.DateTime(dump_only=True)


class UsuarioCreateSchema(Schema):
    """Schema para criação de usuário"""
    nome = fields.Str(required=True, validate=validate.Length(min=3, max=255))
    login = fields.Str(required=True, validate=validate.Length(min=3, max=150))
    senha = fields.Str(required=True, validate=validate.Length(min=6, max=255))
    tipo = fields.Str(required=True, validate=validate.OneOf(['normal', 'gerente', 'admin']))
    setor_id = fields.Int(allow_none=True)
    
    @validate('login')
    def validate_login(self, value):
        """Valida que login não é vazio"""
        if not value or not value.strip():
            from marshmallow import ValidationError
            raise ValidationError('Login é obrigatório')
        return value.strip().lower()

