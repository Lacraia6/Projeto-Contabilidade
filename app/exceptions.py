"""
Exceções Personalizadas
Sistema centralizado de tratamento de erros
"""


class APIError(Exception):
    """Exceção base para erros da API"""
    
    def __init__(self, message, status_code=400, details=None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details or {}
    
    def to_dict(self):
        """Converte exceção para dicionário"""
        return {
            'success': False,
            'message': self.message,
            'details': self.details
        }


class NotFoundError(APIError):
    """Erro quando recurso não encontrado"""
    
    def __init__(self, resource_name="Recurso"):
        super().__init__(
            message=f"{resource_name} não encontrado",
            status_code=404
        )


class ValidationError(APIError):
    """Erro de validação de dados"""
    
    def __init__(self, message="Dados inválidos", details=None):
        super().__init__(
            message=message,
            status_code=400,
            details=details
        )


class UnauthorizedError(APIError):
    """Erro de autenticação"""
    
    def __init__(self, message="Não autorizado"):
        super().__init__(
            message=message,
            status_code=401
        )


class ForbiddenError(APIError):
    """Erro de permissão"""
    
    def __init__(self, message="Sem permissão para realizar esta ação"):
        super().__init__(
            message=message,
            status_code=403
        )


class ConflictError(APIError):
    """Erro de conflito (ex: recurso já existe)"""
    
    def __init__(self, message="Conflito com recurso existente"):
        super().__init__(
            message=message,
            status_code=409
        )


class BusinessLogicError(APIError):
    """Erro de lógica de negócio"""
    
    def __init__(self, message, details=None):
        super().__init__(
            message=message,
            status_code=422,
            details=details
        )

