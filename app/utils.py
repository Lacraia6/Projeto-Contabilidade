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
