-- Script para criar as tabelas do sistema de checklists
-- Execute este script no seu banco de dados MySQL

-- Tabela de checklists
CREATE TABLE IF NOT EXISTS checklists (
    id INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id INT NOT NULL,
    nome VARCHAR(255) NOT NULL,
    descricao TEXT,
    criado_por INT NOT NULL,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ativo BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (empresa_id) REFERENCES empresas(id),
    FOREIGN KEY (criado_por) REFERENCES usuarios(id)
);

-- Tabela de itens do checklist
CREATE TABLE IF NOT EXISTS checklist_itens (
    id INT AUTO_INCREMENT PRIMARY KEY,
    checklist_id INT NOT NULL,
    titulo VARCHAR(255) NOT NULL,
    descricao TEXT,
    ordem INT DEFAULT 0,
    responsavel_id INT NOT NULL,
    obrigatorio BOOLEAN DEFAULT TRUE,
    ativo BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (checklist_id) REFERENCES checklists(id) ON DELETE CASCADE,
    FOREIGN KEY (responsavel_id) REFERENCES usuarios(id)
);

-- Tabela de conclusões dos itens
CREATE TABLE IF NOT EXISTS checklist_item_conclusoes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    item_id INT NOT NULL,
    usuario_id INT NOT NULL,
    concluido BOOLEAN DEFAULT FALSE,
    observacoes TEXT,
    concluido_em TIMESTAMP NULL,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (item_id) REFERENCES checklist_itens(id) ON DELETE CASCADE,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
);

-- Inserir usuário supervisor de exemplo (se não existir)
INSERT IGNORE INTO usuarios (nome, login, senha, tipo, ativo) 
VALUES ('Supervisor Sistema', 'supervisor', '123456', 'supervisor', TRUE);

-- Inserir tributações de exemplo (se não existirem)
INSERT IGNORE INTO tributacoes (id, nome) VALUES 
(1, 'Simples Nacional'),
(2, 'Lucro Presumido'),
(3, 'Lucro Real'),
(4, 'MEI');

-- Criar índices para melhor performance
CREATE INDEX idx_checklists_empresa ON checklists(empresa_id);
CREATE INDEX idx_checklists_criado_por ON checklists(criado_por);
CREATE INDEX idx_checklist_itens_checklist ON checklist_itens(checklist_id);
CREATE INDEX idx_checklist_itens_responsavel ON checklist_itens(responsavel_id);
CREATE INDEX idx_checklist_conclusoes_item ON checklist_item_conclusoes(item_id);
CREATE INDEX idx_checklist_conclusoes_usuario ON checklist_item_conclusoes(usuario_id);

