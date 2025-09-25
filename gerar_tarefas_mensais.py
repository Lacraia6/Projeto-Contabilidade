#!/usr/bin/env python3
"""
Script para gerar tarefas mensais automaticamente
Execute este script no primeiro dia de cada mês
"""

import sys
import os
from datetime import datetime, date
import calendar

# Adicionar o diretório do projeto ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.db import db
from app.models import Usuario, Empresa, Tarefa, RelacionamentoTarefa, Periodo

def gerar_periodo_label(ano, mes):
    """Gera o label do período no formato YYYY-MM"""
    return f"{ano}-{mes:02d}"

def calcular_datas_periodo(ano, mes, tipo_tarefa):
    """Calcula as datas de início e fim baseado no tipo da tarefa"""
    if tipo_tarefa == 'Mensal':
        inicio = date(ano, mes, 1)
        fim = date(ano, mes, calendar.monthrange(ano, mes)[1])
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
    
    return inicio, fim, gerar_periodo_label(ano, mes)

def gerar_tarefas_mes(ano=None, mes=None):
    """Gera tarefas para o mês especificado ou atual"""
    app = create_app()
    
    with app.app_context():
        try:
            # Usar mês atual se não especificado
            if not ano or not mes:
                hoje = datetime.now()
                ano = ano or hoje.year
                mes = mes or hoje.month
            
            print(f"Gerando tarefas para {ano}-{mes:02d}...")
            
            # Verificar se já existem tarefas para este período
            periodo_label = gerar_periodo_label(ano, mes)
            periodos_existentes = Periodo.query.filter_by(periodo_label=periodo_label).count()
            
            if periodos_existentes > 0:
                print(f"⚠️  Tarefas para {periodo_label} já foram geradas ({periodos_existentes} períodos)")
                return False
            
            # Buscar todos os relacionamentos ativos
            relacionamentos = RelacionamentoTarefa.query.filter_by(status='ativa').all()
            print(f"📋 Encontrados {len(relacionamentos)} relacionamentos ativos")
            
            if len(relacionamentos) == 0:
                print("⚠️  Nenhum relacionamento ativo encontrado")
                return False
            
            tarefas_criadas = 0
            
            for rel in relacionamentos:
                tarefa = Tarefa.query.get(rel.tarefa_id)
                if not tarefa:
                    print(f"⚠️  Tarefa não encontrada para relacionamento {rel.id}")
                    continue
                
                # Calcular datas do período
                inicio, fim, periodo_label_tarefa = calcular_datas_periodo(ano, mes, tarefa.tipo)
                
                # Verificar se já existe período para este relacionamento
                periodo_existente = Periodo.query.filter_by(
                    relacionamento_tarefa_id=rel.id,
                    periodo_label=periodo_label_tarefa
                ).first()
                
                if periodo_existente:
                    print(f"⚠️  Período já existe para tarefa {tarefa.nome} ({periodo_label_tarefa})")
                    continue
                
                # Criar novo período
                novo_periodo = Periodo(
                    relacionamento_tarefa_id=rel.id,
                    inicio=inicio,
                    fim=fim,
                    periodo_label=periodo_label_tarefa,
                    status='pendente',
                    contador_retificacoes=0,
                    atualizado_em=datetime.now()
                )
                
                db.session.add(novo_periodo)
                tarefas_criadas += 1
                print(f"✅ Criado período para: {tarefa.nome} ({tarefa.tipo}) - {periodo_label_tarefa}")
            
            db.session.commit()
            
            print(f"🎉 Tarefas geradas com sucesso!")
            print(f"📊 Total de períodos criados: {tarefas_criadas}")
            print(f"📅 Período: {periodo_label}")
            
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Erro ao gerar tarefas: {str(e)}")
            return False

def verificar_geracao():
    """Verifica se as tarefas do mês atual foram geradas"""
    app = create_app()
    
    with app.app_context():
        try:
            hoje = datetime.now()
            periodo_atual = gerar_periodo_label(hoje.year, hoje.mes)
            
            periodos_existentes = Periodo.query.filter_by(periodo_label=periodo_atual).count()
            relacionamentos_ativos = RelacionamentoTarefa.query.filter_by(status='ativa').count()
            
            print(f"📅 Período atual: {periodo_atual}")
            print(f"📊 Períodos existentes: {periodos_existentes}")
            print(f"📋 Relacionamentos ativos: {relacionamentos_ativos}")
            print(f"🔍 Precisa gerar: {'Sim' if periodos_existentes == 0 and relacionamentos_ativos > 0 else 'Não'}")
            
            return periodos_existentes == 0 and relacionamentos_ativos > 0
            
        except Exception as e:
            print(f"❌ Erro ao verificar geração: {str(e)}")
            return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Gerar tarefas mensais automaticamente')
    parser.add_argument('--ano', type=int, help='Ano para gerar tarefas')
    parser.add_argument('--mes', type=int, help='Mês para gerar tarefas')
    parser.add_argument('--verificar', action='store_true', help='Apenas verificar se precisa gerar')
    
    args = parser.parse_args()
    
    if args.verificar:
        verificar_geracao()
    else:
        sucesso = gerar_tarefas_mes(args.ano, args.mes)
        sys.exit(0 if sucesso else 1)
