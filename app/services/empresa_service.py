"""
Serviço de Empresas
Lógica de negócio para gerenciamento de empresas
"""

from app.db import db
from app.models import Empresa, RelacionamentoTarefa, Tarefa


class EmpresaService:
    """Serviço para operações relacionadas a empresas"""
    
    @staticmethod
    def get_empresas_por_usuario(user_id, setor_id=None):
        """
        Busca empresas relacionadas a um usuário
        
        Args:
            user_id: ID do usuário
            setor_id: ID do setor (opcional, para filtro)
        
        Returns:
            Lista de empresas
        """
        query = db.session.query(Empresa).join(
            RelacionamentoTarefa, Empresa.id == RelacionamentoTarefa.empresa_id
        ).filter(RelacionamentoTarefa.responsavel_id == user_id).distinct()
        
        # Filtro adicional por setor
        if setor_id:
            query = query.join(Tarefa, RelacionamentoTarefa.tarefa_id == Tarefa.id)
            query = query.filter(Tarefa.setor_id == setor_id)
        
        empresas = query.order_by(Empresa.nome).all()
        
        return empresas
    
    @staticmethod
    def get_empresas_ativas():
        """
        Busca todas as empresas ativas
        
        Returns:
            Lista de empresas ativas
        """
        empresas = Empresa.query.filter(Empresa.ativo == True).order_by(Empresa.nome).all()
        return empresas
    
    @staticmethod
    def criar_empresa(codigo, nome, tributacao_id):
        """
        Cria uma nova empresa
        
        Args:
            codigo: Código da empresa
            nome: Nome da empresa
            tributacao_id: ID da tributação
        
        Returns:
            Empresa criada
        
        Raises:
            ValueError: Se empresa com mesmo código já existe
        """
        # Verificar se já existe empresa com esse código
        existente = Empresa.query.filter_by(codigo=codigo).first()
        if existente:
            raise ValueError(f"Empresa com código '{codigo}' já existe")
        
        empresa = Empresa(
            codigo=codigo,
            nome=nome,
            tributacao_id=tributacao_id,
            ativo=True
        )
        
        db.session.add(empresa)
        db.session.commit()
        
        return empresa
    
    @staticmethod
    def atualizar_empresa(empresa_id, **kwargs):
        """
        Atualiza uma empresa
        
        Args:
            empresa_id: ID da empresa
            **kwargs: Campos para atualizar
        
        Returns:
            Empresa atualizada
        
        Raises:
            ValueError: Se empresa não encontrada
        """
        empresa = Empresa.query.get(empresa_id)
        
        if not empresa:
            raise ValueError("Empresa não encontrada")
        
        # Atualizar campos permitidos
        campos_permitidos = ['nome', 'codigo', 'tributacao_id', 'ativo']
        for campo, valor in kwargs.items():
            if campo in campos_permitidos:
                setattr(empresa, campo, valor)
        
        db.session.commit()
        
        return empresa
    
    @staticmethod
    def desativar_empresa(empresa_id):
        """
        Desativa uma empresa
        
        Args:
            empresa_id: ID da empresa
        
        Returns:
            bool: True se desativada com sucesso
        
        Raises:
            ValueError: Se empresa não encontrada
        """
        empresa = Empresa.query.get(empresa_id)
        
        if not empresa:
            raise ValueError("Empresa não encontrada")
        
        empresa.ativo = False
        db.session.commit()
        
        return True

