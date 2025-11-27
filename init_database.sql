
SET NAMES utf8mb4;
SET CHARACTER SET utf8mb4;

SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS setores;
CREATE TABLE setores (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(255) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS tributacoes;
CREATE TABLE tributacoes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS usuarios;
CREATE TABLE usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(255) NOT NULL,
    login VARCHAR(150) UNIQUE NOT NULL,
    senha VARCHAR(255) NOT NULL,
    tipo VARCHAR(50) NOT NULL,
    setor_id INT,
    criado_em TIMESTAMP NULL DEFAULT NULL,
    atualizado_em TIMESTAMP NULL DEFAULT NULL,
    ativo BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (setor_id) REFERENCES setores(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS empresas;
CREATE TABLE empresas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    codigo VARCHAR(100) UNIQUE NOT NULL,
    nome VARCHAR(255) NOT NULL,
    tributacao_id INT,
    criado_em TIMESTAMP NULL DEFAULT NULL,
    atualizado_em TIMESTAMP NULL DEFAULT NULL,
    ativo BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (tributacao_id) REFERENCES tributacoes(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS tarefas;
CREATE TABLE tarefas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(255) NOT NULL,
    tipo VARCHAR(50) NOT NULL,
    descricao TEXT,
    tributacao_id INT,
    setor_id INT,
    tarefa_comum BOOLEAN DEFAULT FALSE,
    condicoes_especiais TEXT,
    criado_em TIMESTAMP NULL DEFAULT NULL,
    atualizado_em TIMESTAMP NULL DEFAULT NULL,
    FOREIGN KEY (tributacao_id) REFERENCES tributacoes(id) ON DELETE SET NULL,
    FOREIGN KEY (setor_id) REFERENCES setores(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS vinculacao_empresa_tributacao;
CREATE TABLE vinculacao_empresa_tributacao (
    id INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id INT NOT NULL,
    tributacao_id INT NOT NULL,
    data_inicio DATE NOT NULL,
    data_fim DATE,
    ativo BOOLEAN DEFAULT TRUE,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (empresa_id) REFERENCES empresas(id) ON DELETE CASCADE,
    FOREIGN KEY (tributacao_id) REFERENCES tributacoes(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS relacionamento_tarefas;
CREATE TABLE relacionamento_tarefas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tarefa_id INT NOT NULL,
    empresa_id INT NOT NULL,
    responsavel_id INT,
    vinculacao_id INT,
    status VARCHAR(50) DEFAULT 'ativa',
    dia_vencimento INT,
    prazo_especifico DATE,
    data_inicio DATE,
    data_fim DATE,
    versao_atual BOOLEAN DEFAULT TRUE,
    motivo_desativacao TEXT,
    criado_em TIMESTAMP NULL DEFAULT NULL,
    atualizado_em TIMESTAMP NULL DEFAULT NULL,
    FOREIGN KEY (tarefa_id) REFERENCES tarefas(id) ON DELETE CASCADE,
    FOREIGN KEY (empresa_id) REFERENCES empresas(id) ON DELETE CASCADE,
    FOREIGN KEY (responsavel_id) REFERENCES usuarios(id) ON DELETE SET NULL,
    FOREIGN KEY (vinculacao_id) REFERENCES vinculacao_empresa_tributacao(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS periodos;
CREATE TABLE periodos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    relacionamento_tarefa_id INT NOT NULL,
    inicio DATE NOT NULL,
    fim DATE NOT NULL,
    periodo_label VARCHAR(50) NOT NULL,
    status VARCHAR(50) DEFAULT 'pendente',
    data_conclusao DATE,
    data_retificacao DATE,
    contador_retificacoes INT DEFAULT 0,
    atualizado_em TIMESTAMP NULL DEFAULT NULL,
    FOREIGN KEY (relacionamento_tarefa_id) REFERENCES relacionamento_tarefas(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS retificacoes;
CREATE TABLE retificacoes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    periodo_id INT NOT NULL,
    usuario_id INT NOT NULL,
    motivo TEXT,
    criado_em TIMESTAMP NULL DEFAULT NULL,
    FOREIGN KEY (periodo_id) REFERENCES periodos(id) ON DELETE CASCADE,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS checklists;
CREATE TABLE checklists (
    id INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id INT NOT NULL,
    nome VARCHAR(255) NOT NULL,
    descricao TEXT,
    criado_por INT NOT NULL,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ativo BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (empresa_id) REFERENCES empresas(id) ON DELETE CASCADE,
    FOREIGN KEY (criado_por) REFERENCES usuarios(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS checklist_itens;
CREATE TABLE checklist_itens (
    id INT AUTO_INCREMENT PRIMARY KEY,
    checklist_id INT NOT NULL,
    titulo VARCHAR(255) NOT NULL,
    descricao TEXT,
    ordem INT DEFAULT 0,
    responsavel_id INT NOT NULL,
    obrigatorio BOOLEAN DEFAULT TRUE,
    ativo BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (checklist_id) REFERENCES checklists(id) ON DELETE CASCADE,
    FOREIGN KEY (responsavel_id) REFERENCES usuarios(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS checklist_item_conclusoes;
CREATE TABLE checklist_item_conclusoes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    item_id INT NOT NULL,
    usuario_id INT NOT NULL,
    concluido BOOLEAN DEFAULT FALSE,
    observacoes TEXT,
    concluido_em TIMESTAMP NULL DEFAULT NULL,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (item_id) REFERENCES checklist_itens(id) ON DELETE CASCADE,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS checklist_items_predefinidos;
CREATE TABLE checklist_items_predefinidos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    titulo VARCHAR(255) NOT NULL,
    descricao TEXT,
    categoria VARCHAR(100),
    ativo BOOLEAN DEFAULT TRUE,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS checklist_templates;
CREATE TABLE checklist_templates (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(255) NOT NULL,
    descricao TEXT,
    categoria VARCHAR(100),
    ativo BOOLEAN DEFAULT TRUE,
    criado_por INT NOT NULL,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (criado_por) REFERENCES usuarios(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS checklist_template_itens;
CREATE TABLE checklist_template_itens (
    id INT AUTO_INCREMENT PRIMARY KEY,
    template_id INT NOT NULL,
    titulo VARCHAR(255) NOT NULL,
    descricao TEXT,
    ordem INT DEFAULT 0,
    obrigatorio BOOLEAN DEFAULT TRUE,
    ativo BOOLEAN DEFAULT TRUE,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (template_id) REFERENCES checklist_templates(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS tarefa_tributacao;
CREATE TABLE tarefa_tributacao (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tarefa_id INT NOT NULL,
    tributacao_id INT NOT NULL,
    obrigatoria BOOLEAN DEFAULT TRUE,
    ordem INT DEFAULT 0,
    ativo BOOLEAN DEFAULT TRUE,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tarefa_id) REFERENCES tarefas(id) ON DELETE CASCADE,
    FOREIGN KEY (tributacao_id) REFERENCES tributacoes(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS configuracao_responsavel_padrao;
CREATE TABLE configuracao_responsavel_padrao (
    id INT AUTO_INCREMENT PRIMARY KEY,
    setor_id INT NOT NULL,
    tributacao_id INT NOT NULL,
    responsavel_id INT NOT NULL,
    ativo BOOLEAN DEFAULT TRUE,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (setor_id) REFERENCES setores(id) ON DELETE CASCADE,
    FOREIGN KEY (tributacao_id) REFERENCES tributacoes(id) ON DELETE CASCADE,
    FOREIGN KEY (responsavel_id) REFERENCES usuarios(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS periodos_execucao;
CREATE TABLE periodos_execucao (
    id INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id INT NOT NULL,
    ano INT NOT NULL,
    mes INT NOT NULL,
    data_inicio DATE NOT NULL,
    data_fim DATE NOT NULL,
    status VARCHAR(20) DEFAULT 'ativo',
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (empresa_id) REFERENCES empresas(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS atribuicoes_tarefas;
CREATE TABLE atribuicoes_tarefas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id INT NOT NULL,
    tributacao_id INT NOT NULL,
    tarefa_id INT NOT NULL,
    responsavel_id INT NOT NULL,
    periodo_execucao_id INT NOT NULL,
    data_atribuicao DATE NOT NULL,
    status VARCHAR(20) DEFAULT 'pendente',
    observacoes TEXT,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (empresa_id) REFERENCES empresas(id) ON DELETE CASCADE,
    FOREIGN KEY (tributacao_id) REFERENCES tributacoes(id) ON DELETE CASCADE,
    FOREIGN KEY (tarefa_id) REFERENCES tarefas(id) ON DELETE CASCADE,
    FOREIGN KEY (responsavel_id) REFERENCES usuarios(id) ON DELETE CASCADE,
    FOREIGN KEY (periodo_execucao_id) REFERENCES periodos_execucao(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS execucoes_tarefas;
CREATE TABLE execucoes_tarefas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    atribuicao_id INT NOT NULL,
    data_execucao DATE NOT NULL,
    status VARCHAR(20) NOT NULL,
    observacoes TEXT,
    anexos TEXT,
    confirmado_por INT,
    data_confirmacao TIMESTAMP NULL DEFAULT NULL,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (atribuicao_id) REFERENCES atribuicoes_tarefas(id) ON DELETE CASCADE,
    FOREIGN KEY (confirmado_por) REFERENCES usuarios(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS responsaveis_padrao_tarefas;
CREATE TABLE responsaveis_padrao_tarefas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    setor_id INT NOT NULL,
    tributacao_id INT NOT NULL,
    tarefa_id INT NOT NULL,
    responsavel_id INT NOT NULL,
    ativo BOOLEAN DEFAULT TRUE,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (setor_id) REFERENCES setores(id) ON DELETE CASCADE,
    FOREIGN KEY (tributacao_id) REFERENCES tributacoes(id) ON DELETE CASCADE,
    FOREIGN KEY (tarefa_id) REFERENCES tarefas(id) ON DELETE CASCADE,
    FOREIGN KEY (responsavel_id) REFERENCES usuarios(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS historico_mudancas_tributacao;
CREATE TABLE historico_mudancas_tributacao (
    id INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id INT NOT NULL,
    tributacao_anterior_id INT,
    tributacao_nova_id INT NOT NULL,
    data_mudanca DATE NOT NULL,
    motivo TEXT,
    criado_por INT NOT NULL,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (empresa_id) REFERENCES empresas(id) ON DELETE CASCADE,
    FOREIGN KEY (tributacao_anterior_id) REFERENCES tributacoes(id) ON DELETE SET NULL,
    FOREIGN KEY (tributacao_nova_id) REFERENCES tributacoes(id) ON DELETE CASCADE,
    FOREIGN KEY (criado_por) REFERENCES usuarios(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS mudancas_tributacao_pendentes;
CREATE TABLE mudancas_tributacao_pendentes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id INT NOT NULL,
    tributacao_anterior_id INT,
    tributacao_nova_id INT NOT NULL,
    data_mudanca DATE NOT NULL,
    motivo TEXT,
    status VARCHAR(20) DEFAULT 'pendente',
    criado_por INT NOT NULL,
    revisado_por INT,
    data_revisao TIMESTAMP NULL DEFAULT NULL,
    observacoes_revisao TEXT,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (empresa_id) REFERENCES empresas(id) ON DELETE CASCADE,
    FOREIGN KEY (tributacao_anterior_id) REFERENCES tributacoes(id) ON DELETE SET NULL,
    FOREIGN KEY (tributacao_nova_id) REFERENCES tributacoes(id) ON DELETE CASCADE,
    FOREIGN KEY (criado_por) REFERENCES usuarios(id) ON DELETE CASCADE,
    FOREIGN KEY (revisado_por) REFERENCES usuarios(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DROP TABLE IF EXISTS checklists_empresa;
CREATE TABLE checklists_empresa (
    id INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id INT NOT NULL,
    periodo_execucao_id INT NOT NULL,
    checklist_id INT NOT NULL,
    status VARCHAR(20) DEFAULT 'pendente',
    responsavel_id INT,
    data_inicio DATE,
    data_fim DATE,
    observacoes TEXT,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (empresa_id) REFERENCES empresas(id) ON DELETE CASCADE,
    FOREIGN KEY (periodo_execucao_id) REFERENCES periodos_execucao(id) ON DELETE CASCADE,
    FOREIGN KEY (checklist_id) REFERENCES checklists(id) ON DELETE CASCADE,
    FOREIGN KEY (responsavel_id) REFERENCES usuarios(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

SET FOREIGN_KEY_CHECKS = 1;

SET FOREIGN_KEY_CHECKS = 0;

INSERT INTO setores (id, nome) VALUES
(1, 'Fiscal'),
(2, 'Contábil'),
(3, 'DP'),
(4, 'Administrativo'),
(5, 'RH');

INSERT INTO tributacoes (id, nome) VALUES
(1, 'Simples Nacional'),
(2, 'Regime Normal'),
(3, 'MEI'),
(4, 'Lucro Presumido'),
(5, 'Lucro Real');

INSERT INTO usuarios (id, nome, login, senha, tipo, setor_id, ativo, criado_em) VALUES
(1, 'Administrador Sistema', 'admin', '123', 'admin', 4, 1, NOW()),
(2, 'João Silva', 'joao.silva', '123', 'normal', 1, 1, NOW()),
(3, 'Maria Santos', 'maria.santos', '123', 'normal', 2, 1, NOW()),
(4, 'Pedro Oliveira', 'pedro.oliveira', '123', 'gerente', 1, 1, NOW()),
(5, 'Ana Costa', 'ana.costa', '123', 'supervisor', 2, 1, NOW()),
(6, 'Carlos Ferreira', 'carlos.ferreira', '123', 'normal', 3, 1, NOW()),
(7, 'Juliana Lima', 'juliana.lima', '123', 'normal', 1, 1, NOW()),
(8, 'Roberto Alves', 'roberto.alves', '123', 'gerente', 2, 1, NOW());

INSERT INTO empresas (id, codigo, nome, tributacao_id, ativo, criado_em) VALUES
(1, 'EMP001', 'Empresa ABC Ltda', 1, 1, NOW()),
(2, 'EMP002', 'Comércio XYZ S.A.', 2, 1, NOW()),
(3, 'EMP003', 'Serviços 123 ME', 3, 1, NOW()),
(4, 'EMP004', 'Indústria Alpha Ltda', 2, 1, NOW()),
(5, 'EMP005', 'Tecnologia Beta S.A.', 1, 1, NOW()),
(6, 'EMP006', 'Construção Gamma ME', 3, 1, NOW()),
(7, 'EMP007', 'Consultoria Delta Ltda', 4, 1, NOW()),
(8, 'EMP008', 'Transportes Epsilon S.A.', 2, 1, NOW());

INSERT INTO tarefas (id, nome, tipo, descricao, tributacao_id, setor_id, tarefa_comum, condicoes_especiais, criado_em) VALUES
(1, 'Declaração de DASN', 'mensal', 'Declaração de DASN do Simples Nacional', 1, 1, 0, NULL, NOW()),
(2, 'Apuração de Impostos', 'mensal', 'Apuração de todos os impostos do mês', 2, 1, 0, NULL, NOW()),
(3, 'Escrituração Contábil', 'mensal', 'Escrituração contábil mensal', NULL, 2, 1, NULL, NOW()),
(4, 'Folha de Pagamento', 'mensal', 'Processamento da folha de pagamento', NULL, 3, 1, NULL, NOW()),
(5, 'Relatório de Vendas', 'mensal', 'Consolidação de relatório de vendas', NULL, 2, 0, NULL, NOW()),
(6, 'Declaração DCTF', 'trimestral', 'Declaração de Débitos e Créditos Tributários Federais', 2, 1, 0, NULL, NOW()),
(7, 'Declaração DASN Trimestral', 'trimestral', 'DASN trimestral para Simples Nacional', 1, 1, 0, NULL, NOW()),
(8, 'Balanço Trimestral', 'trimestral', 'Elaboração do balanço trimestral', NULL, 2, 0, NULL, NOW()),
(9, 'Declaração de Imposto de Renda Pessoa Jurídica', 'anual', 'DIRPJ - Declaração anual de IRPJ', 2, 1, 0, NULL, NOW()),
(10, 'Declaração Anual do Simples Nacional', 'anual', 'DASN-SIMEI anual', 1, 1, 0, NULL, NOW()),
(11, 'Balanço Patrimonial', 'anual', 'Elaboração do balanço patrimonial anual', NULL, 2, 0, NULL, NOW()),
(12, 'Demonstração de Resultado do Exercício', 'anual', 'DRE anual', NULL, 2, 0, NULL, NOW()),
(13, 'RAIS', 'anual', 'Relação Anual de Informações Sociais', NULL, 3, 1, NULL, NOW()),
(14, 'CAGED', 'anual', 'Cadastro Geral de Empregados e Desempregados', NULL, 3, 1, NULL, NOW());

INSERT INTO vinculacao_empresa_tributacao (id, empresa_id, tributacao_id, data_inicio, ativo, criado_em) VALUES
(1, 1, 1, '2024-01-01', 1, NOW()),
(2, 2, 2, '2024-01-01', 1, NOW()),
(3, 3, 3, '2024-01-01', 1, NOW()),
(4, 4, 2, '2024-01-01', 1, NOW()),
(5, 5, 1, '2024-01-01', 1, NOW()),
(6, 6, 3, '2024-01-01', 1, NOW()),
(7, 7, 4, '2024-01-01', 1, NOW()),
(8, 8, 2, '2024-01-01', 1, NOW());

INSERT INTO relacionamento_tarefas (id, tarefa_id, empresa_id, responsavel_id, vinculacao_id, status, dia_vencimento, versao_atual, criado_em) VALUES
(1, 1, 1, 2, 1, 'ativa', 20, 1, NOW()),
(2, 3, 1, 3, 1, 'ativa', 10, 1, NOW()),
(3, 4, 1, 6, 1, 'ativa', 5, 1, NOW()),
(4, 7, 1, 2, 1, 'ativa', 20, 1, NOW()),
(5, 10, 1, 2, 1, 'ativa', 31, 1, NOW()),
(6, 11, 1, 3, 1, 'ativa', 31, 1, NOW()),
(7, 13, 1, 6, 1, 'ativa', 31, 1, NOW()),
(8, 2, 2, 7, 2, 'ativa', 15, 1, NOW()),
(9, 3, 2, 3, 2, 'ativa', 10, 1, NOW()),
(10, 4, 2, 6, 2, 'ativa', 5, 1, NOW()),
(11, 6, 2, 7, 2, 'ativa', 15, 1, NOW()),
(12, 9, 2, 7, 2, 'ativa', 31, 1, NOW()),
(13, 11, 2, 3, 2, 'ativa', 31, 1, NOW()),
(14, 12, 2, 3, 2, 'ativa', 31, 1, NOW()),
(15, 13, 2, 6, 2, 'ativa', 31, 1, NOW()),
(16, 3, 3, 3, 3, 'ativa', 10, 1, NOW()),
(17, 4, 3, 6, 3, 'ativa', 5, 1, NOW()),
(18, 2, 4, 7, 4, 'ativa', 15, 1, NOW()),
(19, 3, 4, 3, 4, 'ativa', 10, 1, NOW()),
(20, 4, 4, 6, 4, 'ativa', 5, 1, NOW()),
(21, 1, 5, 2, 5, 'ativa', 20, 1, NOW()),
(22, 3, 5, 3, 5, 'ativa', 10, 1, NOW()),
(23, 4, 5, 6, 5, 'ativa', 5, 1, NOW());

INSERT INTO periodos_execucao (id, empresa_id, ano, mes, data_inicio, data_fim, status, criado_em) VALUES
(1, 1, 2024, 12, '2024-12-01', '2024-12-31', 'ativo', NOW()),
(2, 2, 2024, 12, '2024-12-01', '2024-12-31', 'ativo', NOW()),
(3, 3, 2024, 12, '2024-12-01', '2024-12-31', 'ativo', NOW()),
(4, 4, 2024, 12, '2024-12-01', '2024-12-31', 'ativo', NOW()),
(5, 5, 2024, 12, '2024-12-01', '2024-12-31', 'ativo', NOW());

INSERT INTO atribuicoes_tarefas (id, empresa_id, tributacao_id, tarefa_id, responsavel_id, periodo_execucao_id, data_atribuicao, status, criado_em) VALUES
(1, 1, 1, 1, 2, 1, '2024-12-01', 'pendente', NOW()),
(2, 1, 1, 3, 3, 1, '2024-12-01', 'pendente', NOW()),
(3, 1, 1, 4, 6, 1, '2024-12-01', 'pendente', NOW()),
(4, 2, 2, 2, 7, 2, '2024-12-01', 'pendente', NOW()),
(5, 2, 2, 3, 3, 2, '2024-12-01', 'pendente', NOW()),
(6, 2, 2, 4, 6, 2, '2024-12-01', 'pendente', NOW()),
(7, 3, 3, 3, 3, 3, '2024-12-01', 'pendente', NOW()),
(8, 3, 3, 4, 6, 3, '2024-12-01', 'pendente', NOW()),
(9, 4, 2, 2, 7, 4, '2024-12-01', 'pendente', NOW()),
(10, 4, 2, 3, 3, 4, '2024-12-01', 'pendente', NOW()),
(11, 5, 1, 1, 2, 5, '2024-12-01', 'pendente', NOW()),
(12, 5, 1, 3, 3, 5, '2024-12-01', 'pendente', NOW());

INSERT INTO periodos (id, relacionamento_tarefa_id, inicio, fim, periodo_label, status) VALUES
(1, 1, '2024-12-01', '2024-12-31', '2024-12', 'pendente'),
(2, 2, '2024-12-01', '2024-12-31', '2024-12', 'pendente'),
(3, 3, '2024-12-01', '2024-12-31', '2024-12', 'pendente'),
(4, 8, '2024-12-01', '2024-12-31', '2024-12', 'pendente'),
(5, 9, '2024-12-01', '2024-12-31', '2024-12', 'pendente'),
(6, 10, '2024-12-01', '2024-12-31', '2024-12', 'pendente'),
(7, 4, '2024-10-01', '2024-12-31', '2024-Q4', 'pendente'),
(8, 11, '2024-10-01', '2024-12-31', '2024-Q4', 'pendente'),
(9, 5, '2024-01-01', '2024-12-31', '2024', 'pendente'),
(10, 6, '2024-01-01', '2024-12-31', '2024', 'pendente'),
(11, 12, '2024-01-01', '2024-12-31', '2024', 'pendente'),
(12, 13, '2024-01-01', '2024-12-31', '2024', 'pendente');

INSERT INTO checklists (id, empresa_id, nome, descricao, criado_por, ativo, criado_em) VALUES
(1, 1, 'Checklist Mensal - Dezembro 2024', 'Checklist de rotinas mensais para dezembro', 5, 1, NOW()),
(2, 2, 'Checklist Fiscal - Q4 2024', 'Checklist de obrigações fiscais do 4º trimestre', 5, 1, NOW());

INSERT INTO checklist_itens (id, checklist_id, titulo, descricao, ordem, responsavel_id, obrigatorio, ativo) VALUES
(1, 1, 'Conferir DASN', 'Verificar se a DASN foi gerada corretamente', 1, 2, 1, 1),
(2, 1, 'Revisar Escrituração', 'Revisar todas as escriturações do mês', 2, 3, 1, 1),
(3, 1, 'Validar Folha de Pagamento', 'Validar cálculos da folha de pagamento', 3, 6, 1, 1),
(4, 2, 'Apurar Impostos', 'Apurar todos os impostos do trimestre', 1, 7, 1, 1),
(5, 2, 'Gerar DCTF', 'Gerar e validar a DCTF', 2, 7, 1, 1);

INSERT INTO configuracao_responsavel_padrao (id, setor_id, tributacao_id, responsavel_id, ativo, criado_em) VALUES
(1, 1, 1, 2, 1, NOW()),
(2, 1, 2, 7, 1, NOW()),
(3, 2, 2, 3, 1, NOW()),
(4, 3, 2, 6, 1, NOW());

INSERT INTO tarefa_tributacao (id, tarefa_id, tributacao_id, obrigatoria, ordem, ativo, criado_em) VALUES
(1, 1, 1, 1, 1, 1, NOW()),
(2, 2, 2, 1, 1, 1, NOW()),
(3, 6, 2, 1, 1, 1, NOW()),
(4, 7, 1, 1, 1, 1, NOW()),
(5, 9, 2, 1, 1, 1, NOW()),
(6, 10, 1, 1, 1, 1, NOW());

INSERT INTO responsaveis_padrao_tarefas (id, setor_id, tributacao_id, tarefa_id, responsavel_id, ativo, criado_em) VALUES
(1, 1, 1, 1, 2, 1, NOW()),
(2, 1, 2, 2, 7, 1, NOW()),
(3, 1, 2, 6, 7, 1, NOW()),
(4, 2, 2, 3, 3, 1, NOW()),
(5, 3, 2, 4, 6, 1, NOW());

INSERT INTO checklists_empresa (id, empresa_id, periodo_execucao_id, checklist_id, status, responsavel_id, data_inicio, criado_em) VALUES
(1, 1, 1, 1, 'pendente', 2, '2024-12-01', NOW()),
(2, 2, 2, 2, 'pendente', 7, '2024-12-01', NOW());

SET FOREIGN_KEY_CHECKS = 1;
