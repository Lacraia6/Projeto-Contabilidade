-- =====================================================
-- MIGRAÇÃO: SISTEMA MELHORADO DE TAREFAS
-- =====================================================

-- 1. Criar tabela para controle de versão de vinculações
CREATE TABLE IF NOT EXISTS vinculacao_empresa_tributacao (
    id INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id INT NOT NULL,
    tributacao_id INT NOT NULL,
    data_inicio DATE NOT NULL,
    data_fim DATE NULL,
    ativo BOOLEAN DEFAULT TRUE,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (empresa_id) REFERENCES empresas(id) ON DELETE CASCADE,
    FOREIGN KEY (tributacao_id) REFERENCES tributacoes(id) ON DELETE CASCADE,
    
    INDEX idx_empresa_tributacao (empresa_id, tributacao_id),
    INDEX idx_data_inicio (data_inicio),
    INDEX idx_ativo (ativo)
);

-- 2. Criar tabela para tarefas por tributação (muitos para muitos)
CREATE TABLE IF NOT EXISTS tarefa_tributacao (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tarefa_id INT NOT NULL,
    tributacao_id INT NOT NULL,
    obrigatoria BOOLEAN DEFAULT TRUE,
    ordem INT DEFAULT 0,
    ativo BOOLEAN DEFAULT TRUE,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (tarefa_id) REFERENCES tarefas(id) ON DELETE CASCADE,
    FOREIGN KEY (tributacao_id) REFERENCES tributacoes(id) ON DELETE CASCADE,
    
    UNIQUE KEY unique_tarefa_tributacao (tarefa_id, tributacao_id),
    INDEX idx_tributacao (tributacao_id),
    INDEX idx_ordem (ordem)
);

-- 3. Criar tabela para responsáveis padrão por setor/tributação
CREATE TABLE IF NOT EXISTS configuracao_responsavel_padrao (
    id INT AUTO_INCREMENT PRIMARY KEY,
    setor_id INT NOT NULL,
    tributacao_id INT NOT NULL,
    responsavel_id INT NOT NULL,
    ativo BOOLEAN DEFAULT TRUE,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (setor_id) REFERENCES setores(id) ON DELETE CASCADE,
    FOREIGN KEY (tributacao_id) REFERENCES tributacoes(id) ON DELETE CASCADE,
    FOREIGN KEY (responsavel_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    
    UNIQUE KEY unique_setor_tributacao (setor_id, tributacao_id),
    INDEX idx_setor (setor_id),
    INDEX idx_tributacao (tributacao_id)
);

-- 4. Adicionar campos ao relacionamento_tarefas
ALTER TABLE relacionamento_tarefas 
ADD COLUMN IF NOT EXISTS vinculacao_id INT NULL,
ADD COLUMN IF NOT EXISTS data_inicio DATE NULL,
ADD COLUMN IF NOT EXISTS data_fim DATE NULL,
ADD COLUMN IF NOT EXISTS versao_atual BOOLEAN DEFAULT TRUE,
ADD COLUMN IF NOT EXISTS motivo_desativacao TEXT NULL;

-- 5. Adicionar índices para melhor performance
ALTER TABLE relacionamento_tarefas 
ADD INDEX IF NOT EXISTS idx_vinculacao (vinculacao_id),
ADD INDEX IF NOT EXISTS idx_versao_atual (versao_atual),
ADD INDEX IF NOT EXISTS idx_data_inicio (data_inicio),
ADD INDEX IF NOT EXISTS idx_data_fim (data_fim);

-- 6. Adicionar campo para controlar se a tarefa é comum (ambas tributações)
ALTER TABLE tarefas 
ADD COLUMN IF NOT EXISTS tarefa_comum BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS condicoes_especiais TEXT NULL;

-- 7. Migrar dados existentes
-- Criar vinculações atuais para todas as empresas
INSERT INTO vinculacao_empresa_tributacao (empresa_id, tributacao_id, data_inicio, ativo)
SELECT DISTINCT 
    e.id as empresa_id,
    e.tributacao_id,
    COALESCE(e.criado_em, CURDATE()) as data_inicio,
    TRUE as ativo
FROM empresas e 
WHERE e.ativo = TRUE 
AND e.tributacao_id IS NOT NULL
ON DUPLICATE KEY UPDATE 
    data_inicio = VALUES(data_inicio),
    ativo = TRUE;

-- Atualizar relacionamentos existentes com vinculação_id
UPDATE relacionamento_tarefas rt
JOIN empresas e ON rt.empresa_id = e.id
JOIN vinculacao_empresa_tributacao vet ON e.id = vet.empresa_id AND e.tributacao_id = vet.tributacao_id
SET rt.vinculacao_id = vet.id,
    rt.data_inicio = vet.data_inicio,
    rt.versao_atual = TRUE
WHERE rt.vinculacao_id IS NULL;

-- Criar relacionamentos tarefa-tributação baseados nos relacionamentos existentes
INSERT INTO tarefa_tributacao (tarefa_id, tributacao_id, obrigatoria, ordem)
SELECT DISTINCT 
    rt.tarefa_id,
    e.tributacao_id,
    TRUE as obrigatoria,
    ROW_NUMBER() OVER (PARTITION BY e.tributacao_id ORDER BY t.nome) as ordem
FROM relacionamento_tarefas rt
JOIN empresas e ON rt.empresa_id = e.id
JOIN tarefas t ON rt.tarefa_id = t.id
WHERE e.tributacao_id IS NOT NULL
ON DUPLICATE KEY UPDATE 
    obrigatoria = TRUE,
    ordem = VALUES(ordem);

-- 8. Atualizar tarefas comuns (que aparecem em ambas as tributações)
UPDATE tarefas 
SET tarefa_comum = TRUE 
WHERE id IN (
    SELECT tarefa_id 
    FROM tarefa_tributacao 
    GROUP BY tarefa_id 
    HAVING COUNT(DISTINCT tributacao_id) > 1
);

-- 9. Comentários para documentação
ALTER TABLE vinculacao_empresa_tributacao COMMENT = 'Controla o histórico de vinculações entre empresas e tributações';
ALTER TABLE tarefa_tributacao COMMENT = 'Define quais tarefas são obrigatórias para cada tributação';
ALTER TABLE configuracao_responsavel_padrao COMMENT = 'Responsáveis padrão por setor e tributação';

-- 10. Verificar integridade dos dados
SELECT 'Verificação de dados migrados:' as status;
SELECT COUNT(*) as total_vinculacoes FROM vinculacao_empresa_tributacao;
SELECT COUNT(*) as total_tarefa_tributacao FROM tarefa_tributacao;
SELECT COUNT(*) as relacionamentos_atualizados FROM relacionamento_tarefas WHERE vinculacao_id IS NOT NULL;
SELECT COUNT(*) as tarefas_comuns FROM tarefas WHERE tarefa_comum = TRUE;


