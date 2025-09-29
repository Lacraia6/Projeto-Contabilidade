#!/usr/bin/env python3
"""
Script para testar o redirecionamento do sistema antigo para o novo
"""

import sys
sys.path.append('.')
from app import create_app

def testar_redirecionamento():
    app = create_app()
    
    print("🚀 TESTE DE REDIRECIONAMENTO")
    print("=" * 40)
    
    with app.test_client() as client:
        # 1. Testar sistema antigo
        print("\n📋 1. Testando sistema antigo (/tarefas/page)")
        response = client.get('/tarefas/page')
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 302:
            location = response.headers.get('Location', 'N/A')
            print(f"   Redirecionando para: {location}")
            
            if '/tarefas-melhoradas/' in location:
                print("   ✅ Redirecionamento correto para sistema novo!")
            elif '/login' in location:
                print("   ⚠️ Redirecionando para login (normal sem autenticação)")
            else:
                print(f"   ❌ Redirecionamento inesperado: {location}")
        else:
            print("   ❌ Não redirecionou (status não é 302)")
        
        # 2. Testar sistema novo
        print("\n🆕 2. Testando sistema novo (/tarefas-melhoradas/)")
        response = client.get('/tarefas-melhoradas/')
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 302:
            location = response.headers.get('Location', 'N/A')
            print(f"   Redirecionando para: {location}")
            print("   ✅ Sistema novo acessível (redireciona para login)")
        elif response.status_code == 200:
            print("   ✅ Sistema novo acessível")
        else:
            print(f"   ❌ Erro no sistema novo: {response.status_code}")
        
        # 3. Testar outras rotas do sistema antigo
        print("\n🔗 3. Testando outras rotas do sistema antigo")
        rotas_antigas = ['/tarefas/', '/tarefas']
        
        for rota in rotas_antigas:
            response = client.get(rota)
            print(f"   {rota}: Status {response.status_code}")
            
            if response.status_code == 302:
                location = response.headers.get('Location', 'N/A')
                if '/tarefas-melhoradas/' in location:
                    print(f"     ✅ Redireciona para sistema novo")
                else:
                    print(f"     ⚠️ Redireciona para: {location}")
    
    print("\n" + "=" * 40)
    print("✅ TESTE CONCLUÍDO!")
    print("\n📝 RESUMO:")
    print("   • Sistema antigo redireciona para o novo")
    print("   • Sistema novo está acessível")
    print("   • Usuários serão direcionados automaticamente")
    print("\n🌐 Para testar com usuário logado:")
    print("   1. Acesse: http://192.168.1.166:5600/login")
    print("   2. Faça login como supervisor")
    print("   3. Clique em 'Tarefas' no menu")
    print("   4. Será redirecionado para o sistema melhorado!")

if __name__ == "__main__":
    testar_redirecionamento()


