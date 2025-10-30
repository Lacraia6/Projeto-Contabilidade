-- =====================================================
-- ÍNDICES DE BANCO DE DADOS PARA OTIMIZAÇÃO
-- =====================================================
-- Este arquivo contém índices para melhorar performance
-- das queries mais frequentes do sistema
-- Compatível com MySQL/MariaDB
-- =====================================================

-- ÍNDICES PARA RELACIONAMENTO_TAREFAS
-- Otimiza buscas por responsável, empresa e status
CREATE INDEX idx_relacionamento_tarefa_responsavel 
ON relacionamento_tarefas(responsavel_id, empresa_id, status);

-- Otimiza buscas por empresa e tarefa
CREATE INDEX idx_relacionamento_tarefa_empresa 
ON relacionamento_tarefas(empresa_id, tarefa_id);

-- Otimiza filtros por status e versão atual
CREATE INDEX idx_relacionamento_tarefa_ativo 
ON relacionamento_tarefas(status, versao_atual);

-- ÍNDICES PARA PERIODOS
-- Otimiza buscas por relacionamento e período
CREATE INDEX idx_periodo_relacionamento_status 
ON periodos(relacionamento_tarefa_id, periodo_label, status);

-- Otimiza buscas por período e status
CREATE INDEX idx_periodo_label_status 
ON periodos(periodo_label, status);

-- Otimiza buscas por datas
CREATE INDEX idx_periodo_datas 
ON periodos(inicio, fim);

-- ÍNDICES PARA EMPRESAS
-- Otimiza buscas por ativa e tributação
CREATE INDEX idx_empresa_ativo 
ON empresas(ativo, tributacao_id);

-- Otimiza buscas por código (busca rápida)
CREATE INDEX idx_empresa_codigo 
ON empresas(codigo);

-- ÍNDICES PARA USUARIOS
-- Otimiza login
CREATE INDEX idx_usuario_login 
ON usuarios(login);

-- Otimiza buscas por setor
CREATE INDEX idx_usuario_setor_ativo 
ON usuarios(setor_id, ativo);

-- ÍNDICES PARA TAREFAS
-- Otimiza buscas por tipo e setor
CREATE INDEX idx_tarefa_tipo_setor 
ON tarefas(tipo, setor_id);

-- Otimiza tarefas comuns
CREATE INDEX idx_tarefa_comum 
ON tarefas(tarefa_comum);

-- ÍNDICES PARA VINCULACAO_EMPRESA_TRIBUTACAO
-- Otimiza buscas por empresa e tributação ativa
CREATE INDEX idx_vinculacao_empresa_tributacao_ativa 
ON vinculacao_empresa_tributacao(empresa_id, ativo, data_fim);

-- Otimiza buscas por data
CREATE INDEX idx_vinculacao_empresa_tributacao_data 
ON vinculacao_empresa_tributacao(data_inicio, data_fim);

-- ÍNDICES PARA CHECKLIST
-- Otimiza buscas por empresa
CREATE INDEX idx_checklist_empresa 
ON checklists(empresa_id, ativo);

-- Otimiza buscas por criador
CREATE INDEX idx_checklist_criado_por 
ON checklists(criado_por, criado_em);

-- ÍNDICES PARA ATRIBUICOES_TAREFAS
-- Otimiza buscas por responsável e status
CREATE INDEX idx_atribuicao_responsavel_status 
ON atribuicoes_tarefas(responsavel_id, status);

-- Otimiza buscas por período de execução
CREATE INDEX idx_atribuicao_periodo_execucao 
ON atribuicoes_tarefas(periodo_execucao_id, status);

-- Otimiza buscas por empresa e tarefa
CREATE INDEX idx_atribuicao_empresa_tarefa 
ON atribuicoes_tarefas(empresa_id, tarefa_id, status);

-- =====================================================
-- ESTATÍSTICAS
-- =====================================================
-- MySQL/MariaDB atualiza estatísticas automaticamente
-- Não é necessário executar ANALYZE manualmente
-- =====================================================

-- =====================================================
-- NOTAS:
-- =====================================================
-- 1. Execute este script no banco de dados de produção
--    durante janela de manutenção
-- 2. MySQL/MariaDB não suporta índices parciais com WHERE
--    Todos os índices foram criados sem filtros
-- 3. Monitore o uso dos índices com:
--    SHOW INDEX FROM tabela;
-- 4. Se necessário, remova índices não utilizados:
--    DROP INDEX idx_nome ON tabela;
-- 5. Se o índice já existir, ocorrerá erro - ignore
-- =====================================================

