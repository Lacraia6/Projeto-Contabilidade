"""
Serviço de Tarefas
Lógica de negócio para gerenciamento de tarefas
"""

from app.db import db
from app.models import Tarefa, RelacionamentoTarefa, Periodo, Empresa, Usuario
from app.utils import gerar_periodo_label, calcular_datas_periodo
from sqlalchemy.orm import joinedload
from datetime import date


class TarefaService:
    """Serviço para operações relacionadas a tarefas"""
    
    @staticmethod
    def get_tarefas_por_usuario(user_id, setor_id=None):
        """
        Busca todas as tarefas relacionadas a um usuário
        
        Args:
            user_id: ID do usuário
            setor_id: ID do setor (opcional, para filtro)
        
        Returns:
            Lista de tarefas
        """
        query = Tarefa.query.join(RelacionamentoTarefa)
        
        if setor_id:
            query = query.filter(Tarefa.setor_id == setor_id)
        
        # Aplicar filtro de responsável
        tarefas = query.filter(
            RelacionamentoTarefa.responsavel_id == user_id
        ).distinct().order_by(Tarefa.nome).all()
        
        return tarefas
    
    @staticmethod
    def get_periodos_por_usuario(user_id, periodo_label, empresa_id=None, tarefa_id=None):
        """
        Busca períodos filtrados por usuário e critérios
        
        Args:
            user_id: ID do usuário
            periodo_label: Label do período (YYYY-MM)
            empresa_id: ID da empresa (opcional)
            tarefa_id: ID da tarefa (opcional)
        
        Returns:
            Lista de períodos formatados
        """
        query = db.session.query(Periodo).join(RelacionamentoTarefa).join(Tarefa).join(Empresa)
        
        # Filtros
        if periodo_label:
            query = query.filter(Periodo.periodo_label == periodo_label)
        if empresa_id:
            query = query.filter(RelacionamentoTarefa.empresa_id == empresa_id)
        if user_id:
            query = query.filter(RelacionamentoTarefa.responsavel_id == user_id)
        if tarefa_id:
            query = query.filter(RelacionamentoTarefa.tarefa_id == tarefa_id)
        
        # Carregar relacionamentos de uma vez (evita N+1)
        periodos = query.options(
            joinedload(Periodo.relacionamento_tarefa).joinedload(RelacionamentoTarefa.tarefa),
            joinedload(Periodo.relacionamento_tarefa).joinedload(RelacionamentoTarefa.empresa)
        ).all()
        
        # Formatar resultados
        itens = []
        for periodo in periodos:
            rel = periodo.relacionamento_tarefa
            tarefa = rel.tarefa
            empresa = rel.empresa
            
            itens.append({
                "periodo_id": periodo.id,
                "nome": tarefa.nome,
                "tipo": tarefa.tipo,
                "status": periodo.status or 'pendente',
                "vencimento": periodo.fim.strftime('%d/%m/%Y') if periodo.fim else None,
                "empresa_ativa": bool(getattr(empresa, 'ativo', True)),
                "empresa_nome": empresa.nome,
                "data_conclusao": periodo.data_conclusao.strftime('%d/%m/%Y') if periodo.data_conclusao else None,
                "data_retificacao": periodo.data_retificacao.strftime('%d/%m/%Y') if periodo.data_retificacao else None,
                "contador_retificacoes": periodo.contador_retificacoes or 0,
                "periodo_label": periodo.periodo_label
            })
        
        return itens
    
    @staticmethod
    def concluir_periodo(periodo_id, user_id):
        """
        Conclui um período/tarefa
        
        Args:
            periodo_id: ID do período
            user_id: ID do usuário
        
        Returns:
            bool: True se concluído com sucesso
        
        Raises:
            ValueError: Se período não encontrado
        """
        periodo = Periodo.query.get(periodo_id)
        
        if not periodo:
            raise ValueError("Período não encontrado")
        
        periodo.status = 'concluida'
        periodo.data_conclusao = date.today()
        
        db.session.commit()
        return True
    
    @staticmethod
    def retificar_periodo(periodo_id, user_id, motivo=None):
        """
        Retifica um período/tarefa
        
        Args:
            periodo_id: ID do período
            user_id: ID do usuário
            motivo: Motivo da retificação (opcional)
        
        Returns:
            bool: True se retificado com sucesso
        
        Raises:
            ValueError: Se período não encontrado
        """
        from app.models import Retificacao
        from datetime import datetime
        
        periodo = Periodo.query.get(periodo_id)
        
        if not periodo:
            raise ValueError("Período não encontrado")
        
        periodo.status = 'retificada'
        periodo.data_retificacao = date.today()
        periodo.contador_retificacoes = (periodo.contador_retificacoes or 0) + 1
        
        # Criar registro de retificação
        retificacao = Retificacao(
            periodo_id=periodo_id,
            usuario_id=user_id,
            motivo=motivo,
            criado_em=datetime.now()
        )
        db.session.add(retificacao)
        db.session.commit()
        
        return True

