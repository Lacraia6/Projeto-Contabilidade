-- ========================================
-- SCRIPT SQL PARA CRIAÇÃO DA BASE DE DADOS
-- Sistema de Contabilidade e Tarefas
-- ========================================

-- Criar banco de dados (descomente se necessário)
-- CREATE DATABASE contabilidade_sistema;
-- USE contabilidade_sistema;

-- ========================================
-- CRIAÇÃO DAS TABELAS
-- ========================================

-- Tabela: setores
CREATE TABLE IF NOT EXISTS setores (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(255) NOT NULL,
    INDEX idx_setores_nome (nome)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabela: tributacoes
CREATE TABLE IF NOT EXISTS tributacoes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    INDEX idx_tributacoes_nome (nome)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabela: usuarios
CREATE TABLE IF NOT EXISTS usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(255) NOT NULL,
    login VARCHAR(150) UNIQUE NOT NULL,
    senha VARCHAR(255) NOT NULL,
    tipo VARCHAR(50) NOT NULL,
    setor_id INT,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    ativo BOOLEAN DEFAULT TRUE,
    INDEX idx_usuarios_login (login),
    INDEX idx_usuarios_tipo (tipo),
    INDEX idx_usuarios_setor (setor_id),
    INDEX idx_usuarios_ativo (ativo),
    FOREIGN KEY (setor_id) REFERENCES setores(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabela: empresas
CREATE TABLE IF NOT EXISTS empresas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    codigo VARCHAR(100) UNIQUE NOT NULL,
    nome VARCHAR(255) NOT NULL,
    tributacao_id INT,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    ativo BOOLEAN DEFAULT TRUE,
    INDEX idx_empresas_codigo (codigo),
    INDEX idx_empresas_nome (nome),
    INDEX idx_empresas_tributacao (tributacao_id),
    INDEX idx_empresas_ativo (ativo),
    FOREIGN KEY (tributacao_id) REFERENCES tributacoes(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabela: tarefas
CREATE TABLE IF NOT EXISTS tarefas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(255) NOT NULL,
    tipo VARCHAR(50) NOT NULL,
    descricao TEXT,
    tributacao_id INT,
    setor_id INT,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_tarefas_nome (nome),
    INDEX idx_tarefas_tipo (tipo),
    INDEX idx_tarefas_tributacao (tributacao_id),
    INDEX idx_tarefas_setor (setor_id),
    FOREIGN KEY (tributacao_id) REFERENCES tributacoes(id) ON DELETE SET NULL,
    FOREIGN KEY (setor_id) REFERENCES setores(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabela: relacionamento_tarefas
CREATE TABLE IF NOT EXISTS relacionamento_tarefas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tarefa_id INT NOT NULL,
    empresa_id INT NOT NULL,
    responsavel_id INT,
    status VARCHAR(50) DEFAULT 'ativa',
    dia_vencimento INT,
    prazo_especifico DATE,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_rel_tarefa (tarefa_id),
    INDEX idx_rel_empresa (empresa_id),
    INDEX idx_rel_responsavel (responsavel_id),
    INDEX idx_rel_status (status),
    UNIQUE KEY unique_tarefa_empresa (tarefa_id, empresa_id),
    FOREIGN KEY (tarefa_id) REFERENCES tarefas(id) ON DELETE CASCADE,
    FOREIGN KEY (empresa_id) REFERENCES empresas(id) ON DELETE CASCADE,
    FOREIGN KEY (responsavel_id) REFERENCES usuarios(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabela: periodos
CREATE TABLE IF NOT EXISTS periodos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    relacionamento_tarefa_id INT NOT NULL,
    inicio DATE NOT NULL,
    fim DATE NOT NULL,
    periodo_label VARCHAR(50) NOT NULL,
    status VARCHAR(50) DEFAULT 'pendente',
    data_conclusao DATE,
    data_retificacao DATE,
    contador_retificacoes INT DEFAULT 0,
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_periodos_relacionamento (relacionamento_tarefa_id),
    INDEX idx_periodos_label (periodo_label),
    INDEX idx_periodos_status (status),
    INDEX idx_periodos_inicio (inicio),
    INDEX idx_periodos_fim (fim),
    FOREIGN KEY (relacionamento_tarefa_id) REFERENCES relacionamento_tarefas(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabela: retificacoes
CREATE TABLE IF NOT EXISTS retificacoes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    periodo_id INT NOT NULL,
    usuario_id INT NOT NULL,
    motivo TEXT,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_retificacoes_periodo (periodo_id),
    INDEX idx_retificacoes_usuario (usuario_id),
    INDEX idx_retificacoes_criado (criado_em),
    FOREIGN KEY (periodo_id) REFERENCES periodos(id) ON DELETE CASCADE,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ========================================
-- DADOS INICIAIS (SEEDS)
-- ========================================

-- Inserir setores
INSERT IGNORE INTO setores (id, nome) VALUES
(1, 'Departamento Fiscal'),
(2, 'Departamento Pessoal'),
(3, 'Departamento Contábil');

-- Inserir tributacoes
INSERT IGNORE INTO tributacoes (id, nome) VALUES
(1, 'Simples Nacional'),
(2, 'Regime Normal'),
(3, 'Lucro Real'),
(4, 'Lucro Presumido');

-- Inserir usuários
INSERT IGNORE INTO usuarios (id, nome, login, senha, tipo, setor_id, ativo) VALUES
(1, 'Ana Gerente', 'ana', '123', 'gerente', 1, TRUE),
(2, 'Bruno Colaborador', 'bruno', '123', 'normal', 1, TRUE),
(3, 'Carla Colaboradora', 'carla', '123', 'normal', 3, TRUE),
(4, 'Gabriel Admin', 'gabriel', '123', 'admin', NULL, TRUE),
(5, 'Katia Ines', 'KATIA', '123', 'gerente', 1, TRUE),
(6, 'Priscila Marthinelli', 'PRISCILA', '123', 'gerente', 3, TRUE),
(7, 'Brigida Max', 'BRIGIDA', '123', 'gerente', 3, TRUE);

-- Inserir empresas
INSERT IGNORE INTO empresas (id, codigo, nome, tributacao_id, ativo) VALUES
(1, 'ALFA', 'Empresa Alfa', 1, TRUE),
(2, 'BETA', 'Empresa Beta', 2, TRUE),
(3, 'GAMA', 'Empresa Gama', 1, TRUE),
(4, '667', 'AL Comercio Varejista de Cosmeticos', 2, TRUE),
(5, 'HANFER', 'Hanfer Industria e Comercio', 2, TRUE),
(6, 'PIRIQUITO', 'Piriquito Ferro e Aço', 2, TRUE);

-- Inserir tarefas
INSERT IGNORE INTO tarefas (id, nome, tipo, descricao, tributacao_id, setor_id) VALUES
(1, 'Apuração ICMS', 'Mensal', 'Apuração e pagamento do ICMS mensal', 2, 1),
(2, 'Folha de Pagamento', 'Mensal', 'Processamento da folha de pagamento mensal', NULL, 2),
(3, 'SPED Contábil', 'Mensal', 'Escrituração contábil digital (SPED)', 2, 3),
(4, 'SPED CONTRIBUICOES', 'Mensal', 'SPED Contribuições mensal', 2, 1),
(5, 'Tarefa do Fiscal 1', 'Mensal', 'Tarefa específica do setor fiscal', 2, 1),
(6, 'Tarefa do Fiscal 2', 'Mensal', 'Outra tarefa específica do setor fiscal', 2, 1);

-- Inserir relacionamentos de tarefas
INSERT IGNORE INTO relacionamento_tarefas (id, tarefa_id, empresa_id, responsavel_id, status) VALUES
(1, 1, 1, 2, 'ativa'),
(2, 2, 1, 2, 'ativa'),
(3, 3, 2, 3, 'ativa'),
(4, 4, 2, 3, 'ativa'),
(5, 4, 4, 2, 'ativa'),
(6, 4, 5, 2, 'ativa'),
(7, 4, 1, 2, 'ativa'),
(8, 1, 6, 2, 'ativa'),
(9, 4, 6, 2, 'ativa'),
(10, 5, 1, 2, 'ativa'),
(11, 6, 1, 2, 'ativa'),
(12, 5, 6, 2, 'ativa'),
(13, 6, 6, 2, 'ativa');

-- Inserir períodos (exemplos para 2025-08 e 2025-09)
INSERT IGNORE INTO periodos (id, relacionamento_tarefa_id, inicio, fim, periodo_label, status, contador_retificacoes) VALUES
-- Período 2025-08
(1, 1, '2025-08-01', '2025-08-31', '2025-08', 'retificada', 1),
(2, 2, '2025-08-01', '2025-08-31', '2025-08', 'retificada', 1),
(3, 3, '2025-08-01', '2025-08-31', '2025-08', 'pendente', 0),
-- Período 2025-09
(4, 1, '2025-09-01', '2025-09-30', '2025-09', 'concluida', 0),
(5, 2, '2025-09-01', '2025-09-30', '2025-09', 'concluida', 0),
(6, 3, '2025-01-01', '2025-12-31', '2025-Anual', 'pendente', 0),
(7, 4, '2025-09-01', '2025-09-30', '2025-09', 'pendente', 0),
(8, 5, '2025-09-01', '2025-09-30', '2025-09', 'concluida', 0),
(9, 6, '2025-09-01', '2025-09-30', '2025-09', 'pendente', 0),
(10, 7, '2025-09-01', '2025-09-30', '2025-09', 'pendente', 0),
-- Períodos adicionais para demonstração
(11, 8, '2025-09-01', '2025-09-30', '2025-09', 'pendente', 0),
(12, 9, '2025-09-01', '2025-09-30', '2025-09', 'pendente', 0),
(13, 10, '2025-09-01', '2025-09-30', '2025-09', 'pendente', 0),
(14, 11, '2025-09-01', '2025-09-30', '2025-09', 'pendente', 0),
(15, 12, '2025-09-01', '2025-09-30', '2025-09', 'pendente', 0),
(16, 13, '2025-09-01', '2025-09-30', '2025-09', 'pendente', 0);

-- Inserir retificações (exemplos)
INSERT IGNORE INTO retificacoes (id, periodo_id, usuario_id, motivo, criado_em) VALUES
(1, 1, 2, 'Erro no cálculo do ICMS - correção necessária', '2025-08-15 10:30:00'),
(2, 2, 2, 'Ajuste na folha de pagamento - horas extras', '2025-08-20 14:15:00');

-- ========================================
-- VIEWS ÚTEIS
-- ========================================

-- View: resumo de tarefas por período
CREATE OR REPLACE VIEW v_resumo_tarefas_periodo AS
SELECT 
    p.periodo_label,
    COUNT(*) as total_tarefas,
    SUM(CASE WHEN p.status = 'pendente' THEN 1 ELSE 0 END) as pendentes,
    SUM(CASE WHEN p.status = 'fazendo' THEN 1 ELSE 0 END) as em_andamento,
    SUM(CASE WHEN p.status = 'concluida' THEN 1 ELSE 0 END) as concluidas,
    SUM(CASE WHEN p.status = 'retificada' THEN 1 ELSE 0 END) as retificadas,
    ROUND(
        (SUM(CASE WHEN p.status IN ('concluida', 'retificada') THEN 1 ELSE 0 END) * 100.0 / COUNT(*)), 2
    ) as taxa_conclusao
FROM periodos p
GROUP BY p.periodo_label
ORDER BY p.periodo_label DESC;

-- View: tarefas com informações completas
CREATE OR REPLACE VIEW v_tarefas_completas AS
SELECT 
    p.id as periodo_id,
    p.periodo_label,
    p.status,
    p.data_conclusao,
    p.data_retificacao,
    p.contador_retificacoes,
    t.nome as tarefa_nome,
    t.tipo as tarefa_tipo,
    e.nome as empresa_nome,
    e.codigo as empresa_codigo,
    u.nome as responsavel_nome,
    s.nome as setor_nome,
    tr.nome as tributacao_nome,
    rt.status as relacionamento_status,
    p.inicio,
    p.fim
FROM periodos p
JOIN relacionamento_tarefas rt ON p.relacionamento_tarefa_id = rt.id
JOIN tarefas t ON rt.tarefa_id = t.id
JOIN empresas e ON rt.empresa_id = e.id
LEFT JOIN usuarios u ON rt.responsavel_id = u.id
LEFT JOIN setores s ON t.setor_id = s.id
LEFT JOIN tributacoes tr ON e.tributacao_id = tr.id
ORDER BY p.periodo_label DESC, e.nome, t.nome;

-- ========================================
-- PROCEDURES ÚTEIS
-- ========================================

-- Procedure: gerar períodos para um mês específico
DELIMITER //
CREATE OR REPLACE PROCEDURE sp_gerar_periodos_mes(
    IN p_ano INT,
    IN p_mes INT
)
BEGIN
    DECLARE done INT DEFAULT FALSE;
    DECLARE v_rel_id INT;
    DECLARE v_inicio DATE;
    DECLARE v_fim DATE;
    DECLARE v_periodo_label VARCHAR(50);
    DECLARE v_tarefa_tipo VARCHAR(50);
    
    DECLARE cur_relacionamentos CURSOR FOR
        SELECT rt.id, t.tipo
        FROM relacionamento_tarefas rt
        JOIN tarefas t ON rt.tarefa_id = t.id
        WHERE rt.status = 'ativa';
    
    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;
    
    -- Definir período label
    SET v_periodo_label = CONCAT(p_ano, '-', LPAD(p_mes, 2, '0'));
    
    OPEN cur_relacionamentos;
    
    read_loop: LOOP
        FETCH cur_relacionamentos INTO v_rel_id, v_tarefa_tipo;
        IF done THEN
            LEAVE read_loop;
        END IF;
        
        -- Verificar se período já existe
        IF NOT EXISTS (
            SELECT 1 FROM periodos 
            WHERE relacionamento_tarefa_id = v_rel_id 
            AND periodo_label = v_periodo_label
        ) THEN
            -- Calcular datas baseado no tipo da tarefa
            CASE v_tarefa_tipo
                WHEN 'Mensal' THEN
                    SET v_inicio = DATE(CONCAT(p_ano, '-', LPAD(p_mes, 2, '0'), '-01'));
                    SET v_fim = LAST_DAY(v_inicio);
                WHEN 'Trimestral' THEN
                    SET v_inicio = DATE(CONCAT(p_ano, '-', LPAD(((p_mes-1) DIV 3) * 3 + 1, 2, '0'), '-01'));
                    SET v_fim = DATE_ADD(DATE_ADD(v_inicio, INTERVAL 3 MONTH), INTERVAL -1 DAY);
                WHEN 'Anual' THEN
                    SET v_inicio = DATE(CONCAT(p_ano, '-01-01'));
                    SET v_fim = DATE(CONCAT(p_ano, '-12-31'));
                ELSE
                    SET v_inicio = DATE(CONCAT(p_ano, '-', LPAD(p_mes, 2, '0'), '-01'));
                    SET v_fim = LAST_DAY(v_inicio);
            END CASE;
            
            -- Inserir período
            INSERT INTO periodos (
                relacionamento_tarefa_id, 
                inicio, 
                fim, 
                periodo_label, 
                status
            ) VALUES (
                v_rel_id, 
                v_inicio, 
                v_fim, 
                v_periodo_label, 
                'pendente'
            );
        END IF;
    END LOOP;
    
    CLOSE cur_relacionamentos;
END //
DELIMITER ;

-- ========================================
-- ÍNDICES ADICIONAIS PARA PERFORMANCE
-- ========================================

-- Índices compostos para consultas frequentes
CREATE INDEX idx_periodos_label_status ON periodos(periodo_label, status);
CREATE INDEX idx_rel_tarefa_empresa_status ON relacionamento_tarefas(tarefa_id, empresa_id, status);
CREATE INDEX idx_usuarios_tipo_setor ON usuarios(tipo, setor_id);

-- ========================================
-- COMENTÁRIOS FINAIS
-- ========================================

/*
ESTRUTURA DO SISTEMA:

1. SETORES: Departamentos da empresa (Fiscal, Pessoal, Contábil)
2. USUÁRIOS: Funcionários do sistema (admin, gerente, normal)
3. TRIBUTAÇÕES: Tipos de regime tributário
4. EMPRESAS: Clientes/empresas atendidas
5. TAREFAS: Tipos de serviços prestados
6. RELACIONAMENTO_TAREFAS: Vinculação tarefa-empresa-responsável
7. PERÍODOS: Execução das tarefas em períodos específicos
8. RETIFICAÇÕES: Histórico de correções/ajustes

FLUXO DE DADOS:
1. Criar setores, usuários, tributações
2. Cadastrar empresas e tarefas
3. Vincular tarefas às empresas (relacionamento_tarefas)
4. Gerar períodos para execução das tarefas
5. Acompanhar status e fazer retificações quando necessário

CONSULTAS ÚTEIS:
- Ver resumo por período: SELECT * FROM v_resumo_tarefas_periodo;
- Ver tarefas completas: SELECT * FROM v_tarefas_completas;
- Gerar períodos: CALL sp_gerar_periodos_mes(2025, 9);
*/
