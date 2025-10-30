from datetime import datetime, date
from dateutil.relativedelta import relativedelta


def get_previous_period():
    """
    Retorna o período anterior ao atual no formato MM/AAAA
    Exemplo: Se estamos em 10/2025, retorna '09/2025'
    """
    today = date.today()
    previous_month = today - relativedelta(months=1)
    return previous_month.strftime('%m/%Y')


def get_previous_period_label():
    """
    Retorna o período anterior ao atual no formato YYYY-MM
    Exemplo: Se estamos em 10/2025, retorna '2025-09'
    """
    today = date.today()
    previous_month = today - relativedelta(months=1)
    return previous_month.strftime('%Y-%m')


def get_current_period():
    """
    Retorna o período atual no formato MM/AAAA
    """
    today = date.today()
    return today.strftime('%m/%Y')


def get_current_period_label():
    """
    Retorna o período atual no formato YYYY-MM
    """
    today = date.today()
    return today.strftime('%Y-%m')


def convert_period_to_label(period):
    """
    Converte período de MM/AAAA para YYYY-MM
    """
    if '/' in period:
        month, year = period.split('/')
        return f"{year}-{month.zfill(2)}"
    return period


def convert_label_to_period(period_label):
    """
    Converte período de YYYY-MM para MM/AAAA
    """
    if '-' in period_label:
        year, month = period_label.split('-')
        return f"{month.zfill(2)}/{year}"
    return period_label


def validate_period_format(period):
    """
    Valida se o período está no formato correto (MM/AAAA)
    """
    import re
    pattern = r'^(0[1-9]|1[0-2])/(20[0-9]{2})$'
    return re.match(pattern, period) is not None


def get_period_display_name(period):
    """
    Retorna o nome do período para exibição
    Exemplo: '09/2025' -> 'Setembro/2025'
    """
    if not period or '/' not in period:
        return period
    
    month, year = period.split('/')
    month_names = {
        '01': 'Janeiro', '02': 'Fevereiro', '03': 'Março', '04': 'Abril',
        '05': 'Maio', '06': 'Junho', '07': 'Julho', '08': 'Agosto',
        '09': 'Setembro', '10': 'Outubro', '11': 'Novembro', '12': 'Dezembro'
    }
    
    month_name = month_names.get(month, month)
    return f"{month_name}/{year}"


def should_show_task_by_type(tarefa_tipo, periodo_label, tarefa_periodo_label=None):
    """
    Determina se uma tarefa deve ser exibida baseado no seu tipo e período
    
    Args:
        tarefa_tipo (str): Tipo da tarefa (Mensal, Trimestral, Anual)
        periodo_label (str): Período filtrado pelo usuário (YYYY-MM)
        tarefa_periodo_label (str): Período da tarefa específica (YYYY-MM ou YYYY-TQ)
    
    Returns:
        bool: True se a tarefa deve ser exibida, False caso contrário
    """
    if tarefa_tipo == 'Mensal':
        return True  # Tarefas mensais aparecem todo mês
    
    elif tarefa_tipo == 'Trimestral':
        if not periodo_label or not tarefa_periodo_label:
            return False
        
        # Mapear trimestres para o mês final de cada trimestre
        trimestre_para_mes_final = {
            'T1': 3,   # Primeiro trimestre -> Março
            'T2': 6,   # Segundo trimestre -> Junho
            'T3': 9,   # Terceiro trimestre -> Setembro
            'T4': 12   # Quarto trimestre -> Dezembro
        }
        
        try:
            # Extrair mês do período filtrado pelo usuário
            if len(periodo_label) >= 7 and '-' in periodo_label:
                mes_filtro = int(periodo_label.split('-')[1])
                
                # Extrair trimestre da tarefa (ex: 2025-T3 -> T3)
                if tarefa_periodo_label and 'T' in tarefa_periodo_label:
                    trimestre_tarefa = tarefa_periodo_label.split('-')[-1]
                    
                    # Verificar se o mês filtrado é o mês final do trimestre da tarefa
                    mes_final_trimestre = trimestre_para_mes_final.get(trimestre_tarefa)
                    if mes_final_trimestre and mes_filtro == mes_final_trimestre:
                        return True
                
                return False
                
        except (ValueError, IndexError):
            return False
    
    elif tarefa_tipo == 'Anual':
        # Tarefas anuais aparecem o ano todo
        return True
    
    return True  # Por padrão, mostrar a tarefa


def gerar_periodo_label(ano, mes):
    """Gera o label do período no formato YYYY-MM"""
    return f"{ano}-{mes:02d}"


def calcular_datas_periodo(ano, mes, tipo_tarefa):
    """Calcula as datas de início e fim baseado no tipo da tarefa"""
    import calendar
    
    if tipo_tarefa == 'Mensal':
        inicio = date(ano, mes, 1)
        fim = date(ano, mes, calendar.monthrange(ano, mes)[1])
        return inicio, fim, gerar_periodo_label(ano, mes)
    
    elif tipo_tarefa == 'Trimestral':
        # Determina o trimestre
        trimestre = (mes - 1) // 3 + 1
        mes_inicio = (trimestre - 1) * 3 + 1
        mes_fim = trimestre * 3
        inicio = date(ano, mes_inicio, 1)
        fim = date(ano, mes_fim, calendar.monthrange(ano, mes_fim)[1])
        return inicio, fim, f"{ano}-T{trimestre}"
    
    elif tipo_tarefa == 'Anual':
        inicio = date(ano, 1, 1)
        fim = date(ano, 12, 31)
        return inicio, fim, f"{ano}-Anual"
    
    # Fallback
    inicio = date(ano, mes, 1)
    fim = date(ano, mes, calendar.monthrange(ano, mes)[1])
    return inicio, fim, gerar_periodo_label(ano, mes)