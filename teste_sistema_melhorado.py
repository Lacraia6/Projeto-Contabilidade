#!/usr/bin/env python3
"""
Script de teste para o Sistema Melhorado de Tarefas
Demonstra as principais funcionalidades implementadas
"""

import sys
sys.path.append('.')
from app import create_app
from app.db import db
from app.models import (
    Empresa, Tributacao, Usuario, Tarefa, RelacionamentoTarefa, Setor,
    VinculacaoEmpresaTributacao, TarefaTributacao, ConfiguracaoResponsavelPadrao
)
from datetime import date

def testar_sistema():
    app = create_app()
    with app.app_context():
        print("🚀 TESTE DO SISTEMA MELHORADO DE TAREFAS")
        print("=" * 50)
        
        # 1. Verificar estrutura de dados
        print("\n📊 1. VERIFICANDO ESTRUTURA DE DADOS")
        print("-" * 30)
        
        # Contar registros
        empresas = Empresa.query.filter_by(ativo=True).count()
        tributacoes = Tributacao.query.count()
        tarefas = Tarefa.query.count()
        vinculacoes = VinculacaoEmpresaTributacao.query.filter_by(ativo=True).count()
        relacionamentos = RelacionamentoTarefa.query.filter_by(versao_atual=True).count()
        
        print(f"✅ Empresas ativas: {empresas}")
        print(f"✅ Tributações: {tributacoes}")
        print(f"✅ Tarefas: {tarefas}")
        print(f"✅ Vinculações ativas: {vinculacoes}")
        print(f"✅ Relacionamentos atuais: {relacionamentos}")
        
        # 2. Demonstrar funcionalidade de vinculação empresa-tributação
        print("\n🏢 2. VINCULAÇÕES EMPRESA-TRIBUTAÇÃO")
        print("-" * 30)
        
        vinculacoes_ativas = VinculacaoEmpresaTributacao.query.filter_by(ativo=True).all()
        for vinc in vinculacoes_ativas:
            empresa = Empresa.query.get(vinc.empresa_id)
            tributacao = Tributacao.query.get(vinc.tributacao_id)
            print(f"📋 {empresa.nome} → {tributacao.nome} (desde {vinc.data_inicio})")
        
        # 3. Demonstrar tarefas por tributação
        print("\n📋 3. TAREFAS POR TRIBUTAÇÃO")
        print("-" * 30)
        
        for tributacao in Tributacao.query.all():
            tarefas_trib = TarefaTributacao.query.filter_by(
                tributacao_id=tributacao.id, ativo=True
            ).count()
            print(f"📊 {tributacao.nome}: {tarefas_trib} tarefas")
        
        # 4. Demonstrar tarefas comuns
        print("\n🔄 4. TAREFAS COMUNS (AMBAS TRIBUTAÇÕES)")
        print("-" * 30)
        
        tarefas_comuns = Tarefa.query.filter_by(tarefa_comum=True).all()
        for tarefa in tarefas_comuns:
            print(f"✅ {tarefa.nome} ({tarefa.tipo})")
        
        # 5. Demonstrar relacionamentos com controle de versão
        print("\n🔗 5. RELACIONAMENTOS COM CONTROLE DE VERSÃO")
        print("-" * 30)
        
        for empresa in Empresa.query.filter_by(ativo=True).limit(3).all():
            print(f"\n🏢 {empresa.nome}:")
            
            # Tarefas ativas
            tarefas_ativas = RelacionamentoTarefa.query.filter_by(
                empresa_id=empresa.id, versao_atual=True
            ).all()
            print(f"   📋 Tarefas ativas: {len(tarefas_ativas)}")
            
            # Tarefas históricas
            tarefas_historicas = RelacionamentoTarefa.query.filter_by(
                empresa_id=empresa.id, versao_atual=False
            ).all()
            print(f"   📚 Tarefas históricas: {len(tarefas_historicas)}")
        
        # 6. Simular mudança de tributação
        print("\n🔄 6. SIMULAÇÃO DE MUDANÇA DE TRIBUTAÇÃO")
        print("-" * 30)
        
        # Buscar uma empresa para simular
        empresa_teste = Empresa.query.filter_by(ativo=True).first()
        if empresa_teste:
            vinculacao_atual = VinculacaoEmpresaTributacao.query.filter_by(
                empresa_id=empresa_teste.id, ativo=True
            ).first()
            
            if vinculacao_atual:
                print(f"🏢 Empresa: {empresa_teste.nome}")
                print(f"📊 Tributação atual: {vinculacao_atual.tributacao.nome}")
                
                # Buscar outra tributação
                outra_tributacao = Tributacao.query.filter(
                    Tributacao.id != vinculacao_atual.tributacao_id
                ).first()
                
                if outra_tributacao:
                    print(f"🔄 Tributação alternativa: {outra_tributacao.nome}")
                    
                    # Contar tarefas que seriam afetadas
                    tarefas_atuais = RelacionamentoTarefa.query.filter_by(
                        empresa_id=empresa_teste.id, versao_atual=True
                    ).count()
                    
                    tarefas_nova = TarefaTributacao.query.filter_by(
                        tributacao_id=outra_tributacao.id, ativo=True
                    ).count()
                    
                    print(f"📋 Tarefas atuais: {tarefas_atuais}")
                    print(f"📋 Tarefas na nova tributação: {tarefas_nova}")
                    print("💡 Para aplicar a mudança, use o sistema web!")
        
        # 7. Demonstrar responsáveis padrão
        print("\n👥 7. RESPONSÁVEIS PADRÃO")
        print("-" * 30)
        
        responsaveis = ConfiguracaoResponsavelPadrao.query.filter_by(ativo=True).all()
        if responsaveis:
            for resp in responsaveis:
                setor = Setor.query.get(resp.setor_id)
                tributacao = Tributacao.query.get(resp.tributacao_id)
                usuario = Usuario.query.get(resp.responsavel_id)
                print(f"👤 {usuario.nome} → {setor.nome} ({tributacao.nome})")
        else:
            print("ℹ️ Nenhum responsável padrão configurado")
        
        print("\n" + "=" * 50)
        print("✅ TESTE CONCLUÍDO COM SUCESSO!")
        print("🌐 Acesse o sistema em: http://localhost:5000/tarefas-melhoradas/")
        print("=" * 50)

if __name__ == "__main__":
    testar_sistema()


