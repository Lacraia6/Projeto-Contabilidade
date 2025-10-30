"""
Configuração de Logging Estruturado
"""

import logging
import json
from datetime import datetime
from flask import request, session


class StructuredFormatter(logging.Formatter):
    """Formata logs em JSON estruturado"""
    
    def format(self, record):
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
        }
        
        # Adicionar contexto da requisição se disponível
        if hasattr(request, 'method'):
            log_entry['context'] = {
                'method': request.method,
                'path': request.path,
                'remote_addr': request.remote_addr,
            }
        
        # Adicionar user_id se disponível
        if hasattr(session, 'get') and session.get('user_id'):
            log_entry['user_id'] = session.get('user_id')
            log_entry['user_tipo'] = session.get('user_tipo')
        
        # Adicionar exception info se houver
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_entry, ensure_ascii=False, default=str)


def setup_logging(app):
    """
    Configura logging estruturado para a aplicação
    
    Args:
        app: Instância da aplicação Flask
    """
    # Remover handlers padrão
    app.logger.handlers.clear()
    
    # Configurar nível de log
    app.logger.setLevel(logging.INFO)
    
    # Console handler com formatação estruturada
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(StructuredFormatter())
    app.logger.addHandler(console_handler)
    
    # File handler com formatação tradicional
    from logging.handlers import RotatingFileHandler
    import os
    
    if not os.path.exists('logs'):
        os.mkdir('logs')
    
    file_handler = RotatingFileHandler(
        'logs/contabilidade.log',
        maxBytes=10240000,  # 10MB
        backupCount=10
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    ))
    app.logger.addHandler(file_handler)


def log_action(action, user_id=None, **kwargs):
    """
    Loga uma ação do usuário
    
    Args:
        action: Nome da ação
        user_id: ID do usuário
        **kwargs: Dados adicionais
    """
    logger = logging.getLogger(__name__)
    
    log_data = {
        'action': action,
        'timestamp': datetime.now().isoformat(),
    }
    
    if user_id:
        log_data['user_id'] = user_id
    
    log_data.update(kwargs)
    
    logger.info(json.dumps(log_data, ensure_ascii=False))


def log_error(error, user_id=None, **kwargs):
    """
    Loga um erro
    
    Args:
        error: Exceção ou mensagem de erro
        user_id: ID do usuário
        **kwargs: Dados adicionais
    """
    logger = logging.getLogger(__name__)
    
    log_data = {
        'error': str(error),
        'type': type(error).__name__,
        'timestamp': datetime.now().isoformat(),
    }
    
    if user_id:
        log_data['user_id'] = user_id
    
    log_data.update(kwargs)
    
    logger.error(json.dumps(log_data, ensure_ascii=False, default=str))

