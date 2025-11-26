#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para executar testes do frontend
"""

import os
import sys
import subprocess

# Configurar ambiente de teste
os.environ['APP_ENV'] = 'testing'
os.environ.setdefault('TEST_DATABASE_URL', 'sqlite:///:memory:')

def run_tests():
    """Executa todos os testes do frontend"""
    print("🧪 Executando testes do frontend...")
    print("=" * 60)
    
    # Testes de frontend
    test_files = [
        'tests/test_frontend.py',
        'tests/test_frontend_elements.py'
    ]
    
    # Argumentos do pytest
    pytest_args = [
        'pytest',
        '-v',
        '--tb=short',
        '--color=yes'
    ]
    
    # Adicionar arquivos de teste
    pytest_args.extend(test_files)
    
    # Executar testes
    result = subprocess.run(
        pytest_args,
        cwd=os.path.dirname(os.path.abspath(__file__))
    )
    
    return result.returncode

def run_all_tests():
    """Executa todos os testes (backend + frontend)"""
    print("🧪 Executando todos os testes...")
    print("=" * 60)
    
    pytest_args = [
        'pytest',
        '-v',
        '--tb=short',
        '--color=yes',
        'tests/'
    ]
    
    result = subprocess.run(
        pytest_args,
        cwd=os.path.dirname(os.path.abspath(__file__))
    )
    
    return result.returncode

def run_with_coverage():
    """Executa testes com cobertura"""
    print("🧪 Executando testes com cobertura...")
    print("=" * 60)
    
    pytest_args = [
        'pytest',
        '-v',
        '--tb=short',
        '--color=yes',
        '--cov=app',
        '--cov-report=html',
        '--cov-report=term',
        'tests/'
    ]
    
    result = subprocess.run(
        pytest_args,
        cwd=os.path.dirname(os.path.abspath(__file__))
    )
    
    return result.returncode

if __name__ == '__main__':
    if len(sys.argv) > 1:
        if sys.argv[1] == '--all':
            exit_code = run_all_tests()
        elif sys.argv[1] == '--coverage':
            exit_code = run_with_coverage()
        else:
            print("Uso: python run_tests_frontend.py [--all|--coverage]")
            exit_code = 1
    else:
        exit_code = run_tests()
    
    sys.exit(exit_code)

