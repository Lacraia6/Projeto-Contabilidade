"""
Serviço de Autenticação
Lógica de negócio para autenticação e gerenciamento de usuários
"""

from werkzeug.security import generate_password_hash, check_password_hash
from app.db import db
from app.models import Usuario


class AuthService:
    """Serviço para operações relacionadas a autenticação"""
    
    @staticmethod
    def verificar_login(login, senha):
        """
        Verifica credenciais de login
        
        Args:
            login: Login do usuário
            senha: Senha em texto plano
        
        Returns:
            Usuario: Usuário autenticado ou None
        """
        usuario = Usuario.query.filter_by(login=login, ativo=True).first()
        
        if not usuario:
            return None
        
        # Verificar senha
        # Suporte para senhas antigas (texto plano) e novas (hash)
        if usuario.senha.startswith('pbkdf2:'):
            # Senha com hash
            if check_password_hash(usuario.senha, senha):
                return usuario
        else:
            # Senha antiga (texto plano) - compatibilidade retroativa
            if usuario.senha == senha:
                # Migrar para hash automaticamente
                AuthService.migrar_senha_para_hash(usuario.id)
                return usuario
        
        return None
    
    @staticmethod
    def migrar_senha_para_hash(usuario_id, senha_nova=None):
        """
        Migra senha de texto plano para hash
        
        Args:
            usuario_id: ID do usuário
            senha_nova: Nova senha (se None, mantém a atual)
        
        Returns:
            bool: True se migrada com sucesso
        """
        usuario = Usuario.query.get(usuario_id)
        
        if not usuario:
            return False
        
        # Se já tem hash, não faz nada
        if usuario.senha.startswith('pbkdf2:'):
            return True
        
        # Criar hash
        senha = senha_nova if senha_nova else usuario.senha
        usuario.senha = generate_password_hash(senha)
        
        db.session.commit()
        return True
    
    @staticmethod
    def criar_usuario(nome, login, senha, tipo, setor_id):
        """
        Cria um novo usuário com senha hash
        
        Args:
            nome: Nome do usuário
            login: Login do usuário
            senha: Senha em texto plano
            tipo: Tipo do usuário (normal, gerente, admin)
            setor_id: ID do setor
        
        Returns:
            Usuario: Usuário criado
        
        Raises:
            ValueError: Se login já existe
        """
        # Verificar se login já existe
        existente = Usuario.query.filter_by(login=login).first()
        if existente:
            raise ValueError(f"Login '{login}' já existe")
        
        # Criar hash da senha
        senha_hash = generate_password_hash(senha)
        
        usuario = Usuario(
            nome=nome,
            login=login,
            senha=senha_hash,
            tipo=tipo,
            setor_id=setor_id,
            ativo=True
        )
        
        db.session.add(usuario)
        db.session.commit()
        
        return usuario
    
    @staticmethod
    def atualizar_senha(usuario_id, senha_antiga, senha_nova):
        """
        Atualiza senha do usuário
        
        Args:
            usuario_id: ID do usuário
            senha_antiga: Senha atual
            senha_nova: Nova senha
        
        Returns:
            bool: True se atualizada com sucesso
        
        Raises:
            ValueError: Se senha antiga incorreta
        """
        usuario = Usuario.query.get(usuario_id)
        
        if not usuario:
            raise ValueError("Usuário não encontrado")
        
        # Verificar senha antiga
        if usuario.senha.startswith('pbkdf2:'):
            if not check_password_hash(usuario.senha, senha_antiga):
                raise ValueError("Senha atual incorreta")
        else:
            if usuario.senha != senha_antiga:
                raise ValueError("Senha atual incorreta")
        
        # Atualizar com hash
        usuario.senha = generate_password_hash(senha_nova)
        db.session.commit()
        
        return True
    
    @staticmethod
    def redefinir_senha(usuario_id, senha_nova):
        """
        Redefine senha do usuário (admin only)
        
        Args:
            usuario_id: ID do usuário
            senha_nova: Nova senha
        
        Returns:
            bool: True se redefinida com sucesso
        """
        usuario = Usuario.query.get(usuario_id)
        
        if not usuario:
            raise ValueError("Usuário não encontrado")
        
        usuario.senha = generate_password_hash(senha_nova)
        db.session.commit()
        
        return True

