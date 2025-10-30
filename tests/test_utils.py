"""
Testes para funções utilitárias
"""

import pytest
from app.utils import (
    get_previous_period,
    get_previous_period_label,
    get_current_period,
    get_current_period_label,
    convert_period_to_label,
    validate_period_format,
    should_show_task_by_type
)


class TestPeriodUtils:
    """Testes para funções de período"""
    
    def test_get_previous_period(self):
        """Testa geração de período anterior"""
        periodo = get_previous_period()
        # Formato esperado: MM/AAAA
        assert '/' in periodo
        parts = periodo.split('/')
        assert len(parts) == 2
        assert len(parts[0]) == 2  # Mês
        assert len(parts[1]) == 4  # Ano
    
    def test_get_previous_period_label(self):
        """Testa geração de label de período anterior"""
        label = get_previous_period_label()
        # Formato esperado: YYYY-MM
        assert '-' in label
        parts = label.split('-')
        assert len(parts) == 2
        assert len(parts[0]) == 4  # Ano
        assert len(parts[1]) == 2  # Mês
    
    def test_get_current_period(self):
        """Testa geração de período atual"""
        periodo = get_current_period()
        assert '/' in periodo
        parts = periodo.split('/')
        assert len(parts) == 2
    
    def test_get_current_period_label(self):
        """Testa geração de label de período atual"""
        label = get_current_period_label()
        assert '-' in label
        parts = label.split('-')
        assert len(parts) == 2
    
    def test_convert_period_to_label(self):
        """Testa conversão de período para label"""
        # Teste com formato válido
        assert convert_period_to_label('01/2025') == '2025-01'
        assert convert_period_to_label('12/2024') == '2024-12'
        assert convert_period_to_label('09/2025') == '2025-09'
    
    def test_validate_period_format(self):
        """Testa validação de formato de período"""
        # Formatos válidos
        assert validate_period_format('01/2025') == True
        assert validate_period_format('12/2024') == True
        assert validate_period_format('09/2025') == True
        
        # Formatos inválidos
        assert validate_period_format('2025/01') == False
        assert validate_period_format('1/2025') == False
        assert validate_period_format('01/25') == False
        assert validate_period_format('invalid') == False
        assert validate_period_format('') == False


class TestTaskUtils:
    """Testes para funções de tarefa"""
    
    def test_should_show_task_by_type_mensal(self):
        """Testa lógica de exibição de tarefa mensal"""
        # Tarefas mensais aparecem todo mês
        assert should_show_task_by_type('Mensal', '2025-01', None) == True
        assert should_show_task_by_type('Mensal', '2025-12', None) == True
    
    def test_should_show_task_by_type_anual(self):
        """Testa lógica de exibição de tarefa anual"""
        # Tarefas anuais aparecem o ano todo
        assert should_show_task_by_type('Anual', '2025-01', None) == True
        assert should_show_task_by_type('Anual', '2025-06', None) == True
        assert should_show_task_by_type('Anual', '2025-12', None) == True
    
    def test_should_show_task_by_type_trimestral(self):
        """Testa lógica de exibição de tarefa trimestral"""
        # Tarefas trimestrais aparecem apenas no mês final do trimestre
        assert should_show_task_by_type('Trimestral', '2025-03', '2025-T1') == True  # Março (T1)
        assert should_show_task_by_type('Trimestral', '2025-06', '2025-T2') == True  # Junho (T2)
        assert should_show_task_by_type('Trimestral', '2025-09', '2025-T3') == True  # Setembro (T3)
        assert should_show_task_by_type('Trimestral', '2025-12', '2025-T4') == True  # Dezembro (T4)
        
        # Não deve aparecer em outros meses
        assert should_show_task_by_type('Trimestral', '2025-01', '2025-T1') == False  # Janeiro (T1)
        assert should_show_task_by_type('Trimestral', '2025-05', '2025-T2') == False  # Maio (T2)

