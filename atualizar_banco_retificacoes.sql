-- Script para atualizar o banco de dados com as novas colunas de retificação
-- Execute este script no MySQL para adicionar as funcionalidades de retificação

USE contabilidade;

-- Adicionar colunas de retificação na tabela periodos
ALTER TABLE periodos 
ADD COLUMN data_retificacao DATE NULL COMMENT 'Data da última retificação',
ADD COLUMN contador_retificacoes INT DEFAULT 0 COMMENT 'Número de retificações realizadas';

-- Verificar se as colunas foram adicionadas
DESCRIBE periodos;

-- Verificar se a tabela retificacoes existe (já deve existir)
SHOW TABLES LIKE 'retificacoes';

-- Se a tabela retificacoes não existir, criá-la
CREATE TABLE IF NOT EXISTS retificacoes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    periodo_id INT NOT NULL,
    usuario_id INT NOT NULL,
    motivo TEXT,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (periodo_id) REFERENCES periodos(id) ON DELETE CASCADE,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Verificar a estrutura da tabela retificacoes
DESCRIBE retificacoes;

-- Mostrar estatísticas das tabelas
SELECT 
    'periodos' as tabela,
    COUNT(*) as total_registros
FROM periodos
UNION ALL
SELECT 
    'retificacoes' as tabela,
    COUNT(*) as total_registros
FROM retificacoes
UNION ALL
SELECT 
    'relacionamento_tarefas' as tabela,
    COUNT(*) as total_registros
FROM relacionamento_tarefas;

-- Mensagem de sucesso
SELECT 'Banco de dados atualizado com sucesso! As funcionalidades de retificação estão prontas para uso.' as status;
