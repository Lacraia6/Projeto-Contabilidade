// ================================
// SISTEMA DP & CONTABILIDADE - SCRIPT PRINCIPAL
// ================================

// ================================
// SISTEMA UNIVERSAL DE FILTROS
// ================================

// Variáveis globais para o sistema de filtros
window.FilterSystem = {
  searchTimeout: null,
  isLoading: false,
  dataCache: {
    empresas: [],
    colaboradores: [],
    tarefas: []
  },
  
  // Configurações padrão para diferentes tipos de filtro
  configs: {
    // Configurações para Dashboard (Funcionário)
    empresa_dashboard: {
      inputId: 'empresa-search',
      resultsId: 'empresa-results',
      hiddenId: 'empresa_ids',
      selectedId: 'empresa-selected',
      apiEndpoint: '/tarefas/api/empresas',
      multiple: true,
      placeholder: 'Digite para buscar empresa...',
      allText: 'Todas as empresas'
    },
    tarefa_dashboard: {
      inputId: 'tarefa-search',
      resultsId: 'tarefa-results',
      hiddenId: 'tarefa_ids',
      selectedId: 'tarefa-selected',
      apiEndpoint: '/tarefas/api/tarefas',
      multiple: true,
      placeholder: 'Digite para buscar tarefa...',
      allText: 'Todas as tarefas'
    },
    // Configurações para Gerenciamento (Gerente)
    empresa_gerenciamento: {
      inputId: 'empresa-search',
      resultsId: 'empresa-results',
      hiddenId: 'empresa_ids',
      selectedId: 'empresa-selected',
      apiEndpoint: '/gerenciamento/api/empresas',
      multiple: true,
      placeholder: 'Digite para buscar empresa...',
      allText: 'Todas as empresas'
    },
    tarefa_gerenciamento: {
      inputId: 'tarefa-search',
      resultsId: 'tarefa-results',
      hiddenId: 'tarefa_id',
      selectedId: 'tarefa-selected',
      apiEndpoint: '/gerenciamento/api/tarefas',
      multiple: false,
      placeholder: 'Digite para buscar tarefa...',
      allText: 'Todas as tarefas'
    },
    colaborador_gerenciamento: {
      inputId: 'colaborador-search',
      resultsId: 'colaborador-results',
      hiddenId: 'colaborador_id',
      selectedId: 'colaborador-selected',
      apiEndpoint: '/gerenciamento/api/colaboradores',
      multiple: false,
      placeholder: 'Digite para buscar colaborador...',
      allText: 'Todos os colaboradores'
    },
    
    // Configurações para Vinculação em Massa
    empresa_vinculacao: {
      inputId: 'empresa-search',
      resultsId: 'empresa-results',
      hiddenId: 'empresa_ids',
      selectedId: 'empresa-selected',
      apiEndpoint: '/tarefas/api/empresas',
      multiple: true,
      placeholder: 'Digite para buscar empresa...',
      allText: 'Todas as empresas'
    },
    tarefa_vinculacao: {
      inputId: 'tarefa-search',
      resultsId: 'tarefa-results',
      hiddenId: 'tarefa_ids',
      selectedId: 'tarefa-selected',
      apiEndpoint: '/tarefas/api/tarefas',
      multiple: true,
      placeholder: 'Digite para buscar tarefa...',
      allText: 'Todas as tarefas'
    },
    responsavel_vinculacao: {
      inputId: 'responsavel-search',
      resultsId: 'responsavel-results',
      hiddenId: 'responsavel_id',
      selectedId: 'responsavel-selected',
      apiEndpoint: '/tarefas/api/usuarios-setor',
      multiple: false,
      placeholder: 'Digite para buscar colaborador...',
      allText: 'Todos os colaboradores'
    },
    
    // Configurações para Vinculação Individual
    empresa_individual: {
      inputId: 'empresa-individual-search',
      resultsId: 'empresa-individual-results',
      hiddenId: 'empresa-individual_id',
      selectedId: 'empresa-individual-selected',
      apiEndpoint: '/tarefas/api/empresas',
      multiple: false,
      placeholder: 'Digite para buscar empresa...',
      allText: 'Selecione uma empresa'
    },
    tarefa_individual: {
      inputId: 'tarefa-individual-search',
      resultsId: 'tarefa-individual-results',
      hiddenId: 'tarefa-individual_id',
      selectedId: 'tarefa-individual-selected',
      apiEndpoint: '/tarefas/api/tarefas',
      multiple: false,
      placeholder: 'Digite para buscar tarefa...',
      allText: 'Selecione uma tarefa'
    },
    responsavel_individual: {
      inputId: 'responsavel-individual-search',
      resultsId: 'responsavel-individual-results',
      hiddenId: 'responsavel-individual_id',
      selectedId: 'responsavel-individual-selected',
      apiEndpoint: '/tarefas/api/usuarios-setor',
      multiple: false,
      placeholder: 'Digite para buscar colaborador...',
      allText: 'Nenhum responsável'
    },
    
    // Configurações para Relatórios
    empresa_relatorios: {
      inputId: 'empresa-search',
      resultsId: 'empresa-results',
      hiddenId: 'empresa_id',
      selectedId: 'empresa-selected',
      apiEndpoint: '/tarefas/api/empresas',
      multiple: false,
      placeholder: 'Digite para buscar empresa...',
      allText: 'Todas as empresas'
    },
    funcionario_relatorios: {
      inputId: 'funcionario-search',
      resultsId: 'funcionario-results',
      hiddenId: 'funcionario_id',
      selectedId: 'funcionario-selected',
      apiEndpoint: '/tarefas/api/usuarios-setor',
      multiple: false,
      placeholder: 'Digite para buscar funcionário...',
      allText: 'Todos os funcionários'
    },
    tarefa_relatorios: {
      inputId: 'tarefa-search',
      resultsId: 'tarefa-results',
      hiddenId: 'tarefa_id',
      selectedId: 'tarefa-selected',
      apiEndpoint: '/tarefas/api/tarefas',
      multiple: false,
      placeholder: 'Digite para buscar tarefa...',
      allText: 'Todas as tarefas'
    }
  }
};

// Função principal para inicializar filtros
window.FilterSystem.init = function(configType) {
  console.log(`🔧 Inicializando filtro: ${configType}`);
  
  const config = this.configs[configType];
  if (!config) {
    console.error('❌ Tipo de filtro não encontrado:', configType);
    return;
  }
  
  console.log('✅ Configuração encontrada:', config);

  const input = document.getElementById(config.inputId);
  if (!input) {
    console.error('❌ Input não encontrado:', config.inputId);
    return;
  }
  
  console.log('✅ Input encontrado:', config.inputId);

  // Carregar dados iniciais
  this.loadData(configType);

  // Event listeners
  input.addEventListener('input', (e) => {
    clearTimeout(this.searchTimeout);
    this.searchTimeout = setTimeout(() => {
      this.search(configType, e.target.value);
    }, 300);
  });

  input.addEventListener('focus', () => {
    this.showAll(configType);
  });

  // Fechar dropdown ao clicar fora
  document.addEventListener('click', (e) => {
    if (!e.target.closest(`#${config.inputId}`) && !e.target.closest(`#${config.resultsId}`)) {
      this.hideResults(configType);
    }
  });
};

// Carregar dados da API
window.FilterSystem.loadData = function(configType) {
  const config = this.configs[configType];
  if (!config || !config.apiEndpoint) {
    console.error(`Configuração não encontrada para: ${configType}`);
    return;
  }

  console.log(`Carregando dados para ${configType} de: ${config.apiEndpoint}`);
  
  fetch(config.apiEndpoint, {
    credentials: 'same-origin'  // Incluir cookies de sessão
  })
    .then(response => {
      console.log(`Response status para ${configType}:`, response.status);
      
      // Se redirecionado para login, mostrar erro
      if (response.status === 302 || response.redirected) {
        console.error(`Erro de autenticação para ${configType}: Redirecionado para login`);
        return Promise.reject('Erro de autenticação');
      }
      
      return response.json();
    })
    .then(data => {
      console.log(`Dados recebidos para ${configType}:`, data);
      
      // Verificar se é uma resposta válida
      if (!data) {
        console.error(`Erro ao carregar ${configType}: Resposta vazia`);
        return;
      }
      
      // Tentar diferentes estruturas de resposta
      let dataArray = [];
      
      if (data.empresas) {
        // Estrutura: {empresas: [...]}
        dataArray = data.empresas;
      } else if (data.tarefas) {
        // Estrutura: {tarefas: [...]}
        dataArray = data.tarefas;
      } else if (data.colaboradores) {
        // Estrutura: {colaboradores: [...]}
        dataArray = data.colaboradores;
      } else if (data.usuarios) {
        // Estrutura: {usuarios: [...]}
        dataArray = data.usuarios;
      } else if (data.success && data.data) {
        // Estrutura: {success: true, data: [...]}
        dataArray = data.data;
      } else if (data.success && (data.empresas || data.tarefas || data.colaboradores || data.usuarios)) {
        // Estrutura: {success: true, empresas: [...]}
        dataArray = data.empresas || data.tarefas || data.colaboradores || data.usuarios || [];
      } else if (Array.isArray(data)) {
        // Estrutura: [...]
        dataArray = data;
      } else {
        console.error(`Erro ao carregar ${configType}: Estrutura de resposta não reconhecida`, data);
        return;
      }
      
      this.dataCache[configType] = dataArray;
      console.log(`${configType} carregados:`, this.dataCache[configType].length);
    })
    .catch(error => {
      console.error(`Erro na requisição para ${configType}:`, error);
    });
};

// Função de busca
window.FilterSystem.search = function(configType, query) {
  const config = this.configs[configType];
  const resultsDiv = document.getElementById(config.resultsId);
  
  if (!resultsDiv) return;

  // Se não há query, mostrar todos
  if (!query || query.length === 0) {
    this.showAll(configType);
    return;
  }

  const data = this.dataCache[configType] || [];
  const filtered = data.filter(item => {
    const searchFields = this.getSearchFields(configType, item);
    return searchFields.some(field => 
      field.toLowerCase().includes(query.toLowerCase())
    );
  });

  this.renderResults(configType, filtered, query);
};

// Mostrar todos os itens
window.FilterSystem.showAll = function(configType) {
  const config = this.configs[configType];
  const resultsDiv = document.getElementById(config.resultsId);
  
  if (!resultsDiv) {
    console.error(`Elemento não encontrado: ${config.resultsId}`);
    return;
  }

  const data = this.dataCache[configType] || [];
  console.log(`Mostrando todos os resultados para ${configType}:`, data.length);
  this.renderResults(configType, data);
};

// Renderizar resultados
window.FilterSystem.renderResults = function(configType, items, query = '') {
  const config = this.configs[configType];
  const resultsDiv = document.getElementById(config.resultsId);
  
  if (!resultsDiv) return;

  if (items.length === 0) {
    const message = query ? 'Nenhum item encontrado' : 'Nenhum item disponível';
    resultsDiv.innerHTML = `<div class="search-result-item">${message}</div>`;
  } else {
    resultsDiv.innerHTML = items.map(item => this.createResultItem(configType, item)).join('');
  }

  resultsDiv.style.display = 'block';
};

// Criar item de resultado
window.FilterSystem.createResultItem = function(configType, item) {
  const config = this.configs[configType];
  const fields = this.getDisplayFields(configType, item);
  
  return `
    <div class="search-result-item" onclick="FilterSystem.selectItem('${configType}', ${item.id}, '${item.nome.replace(/'/g, "\\'")}')">
      <strong>${fields.primary}</strong>
      ${fields.secondary ? `<small>${fields.secondary}</small>` : ''}
    </div>
  `;
};

// Obter campos de busca
window.FilterSystem.getSearchFields = function(configType, item) {
  // Extrair tipo base removendo sufixos
  const baseType = configType.replace('_dashboard', '').replace('_gerenciamento', '').replace('_vinculacao', '').replace('_individual', '').replace('_relatorios', '');
  
  switch (baseType) {
    case 'empresa':
      return [item.nome, item.codigo || ''];
    case 'tarefa':
      return [item.nome, item.tipo || ''];
    case 'colaborador':
    case 'responsavel':
      return [item.nome, item.tipo || ''];
    default:
      return [item.nome];
  }
};

// Obter campos de exibição
window.FilterSystem.getDisplayFields = function(configType, item) {
  // Extrair tipo base removendo sufixos
  const baseType = configType.replace('_dashboard', '').replace('_gerenciamento', '').replace('_vinculacao', '').replace('_individual', '').replace('_relatorios', '');
  
  switch (baseType) {
    case 'empresa':
      return {
        primary: item.nome,
        secondary: item.codigo
      };
    case 'tarefa':
      return {
        primary: item.nome,
        secondary: item.tipo
      };
    case 'colaborador':
    case 'responsavel':
      return {
        primary: item.nome,
        secondary: item.tipo || 'Colaborador'
      };
    default:
      return {
        primary: item.nome,
        secondary: ''
      };
  }
};

// Selecionar item
window.FilterSystem.selectItem = function(configType, id, nome) {
  const config = this.configs[configType];
  
  if (config.multiple) {
    this.selectMultiple(configType, id, nome);
  } else {
    this.selectSingle(configType, id, nome);
  }

  // Limpar input e esconder resultados
  const input = document.getElementById(config.inputId);
  const resultsDiv = document.getElementById(config.resultsId);
  
  if (input) input.value = '';
  if (resultsDiv) resultsDiv.style.display = 'none';
};

// Seleção múltipla
window.FilterSystem.selectMultiple = function(configType, id, nome) {
  const config = this.configs[configType];
  const hiddenInput = document.getElementById(config.hiddenId);
  const selectedContainer = document.getElementById(config.selectedId);
  
  if (!hiddenInput || !selectedContainer) return;

  // Obter itens já selecionados
  let selectedIds = [];
  if (hiddenInput.value) {
    selectedIds = hiddenInput.value.split(',').map(id => parseInt(id.trim())).filter(id => !isNaN(id));
  }

  // Adicionar se não estiver já selecionado
  if (!selectedIds.includes(id)) {
    selectedIds.push(id);
    hiddenInput.value = selectedIds.join(',');

    // Adicionar visualmente
    const newItem = document.createElement('div');
    newItem.className = 'selected-item';
    newItem.innerHTML = `
      <span class="selected-item-text">${nome}</span>
      <button type="button" class="selected-item-remove" onclick="FilterSystem.removeItem('${configType}', ${id}, '${nome.replace(/'/g, "\\'")}')">&times;</button>
    `;

    // Remover texto padrão se existir
    const allItem = selectedContainer.querySelector('.selected-item-text');
    if (allItem && allItem.textContent === config.allText) {
      selectedContainer.innerHTML = '';
    }

    selectedContainer.appendChild(newItem);
  }
};

// Seleção única
window.FilterSystem.selectSingle = function(configType, id, nome) {
  const config = this.configs[configType];
  const hiddenInput = document.getElementById(config.hiddenId);
  const selectedContainer = document.getElementById(config.selectedId);
  
  if (!hiddenInput || !selectedContainer) return;

  hiddenInput.value = id;
  selectedContainer.innerHTML = `
    <span class="selected-item-text">${nome}</span>
    <button type="button" class="selected-item-remove" onclick="FilterSystem.clearSelection('${configType}')">&times;</button>
  `;
};

// Remover item (múltipla seleção)
window.FilterSystem.removeItem = function(configType, id, nome) {
  const config = this.configs[configType];
  const hiddenInput = document.getElementById(config.hiddenId);
  const selectedContainer = document.getElementById(config.selectedId);
  
  if (!hiddenInput || !selectedContainer) return;

  // Obter itens já selecionados
  let selectedIds = [];
  if (hiddenInput.value) {
    selectedIds = hiddenInput.value.split(',').map(id => parseInt(id.trim())).filter(id => !isNaN(id));
  }

  // Remover item
  selectedIds = selectedIds.filter(itemId => itemId !== id);

  if (selectedIds.length === 0) {
    hiddenInput.value = '';
    selectedContainer.innerHTML = `<div class="selected-item"><span class="selected-item-text">${config.allText}</span></div>`;
  } else {
    hiddenInput.value = selectedIds.join(',');

    // Remover visualmente
    const items = selectedContainer.querySelectorAll('.selected-item');
    items.forEach(item => {
      const removeBtn = item.querySelector(`button[onclick*="${id}"]`);
      if (removeBtn) {
        item.remove();
      }
    });
  }
};

// Limpar seleção
window.FilterSystem.clearSelection = function(configType) {
  const config = this.configs[configType];
  const hiddenInput = document.getElementById(config.hiddenId);
  const selectedContainer = document.getElementById(config.selectedId);
  
  if (!hiddenInput || !selectedContainer) return;

  hiddenInput.value = '';
  selectedContainer.innerHTML = `<div class="selected-item"><span class="selected-item-text">${config.allText}</span></div>`;
};

// Esconder resultados
window.FilterSystem.hideResults = function(configType) {
  const config = this.configs[configType];
  const resultsDiv = document.getElementById(config.resultsId);
  
  if (resultsDiv) {
    resultsDiv.style.display = 'none';
  }
};

// Limpar todos os filtros de uma página
window.FilterSystem.clearAllFilters = function() {
  // Limpar todos os tipos de filtro disponíveis na página
  Object.keys(this.configs).forEach(configType => {
    if (document.getElementById(this.configs[configType].inputId)) {
      this.clearSelection(configType);
      const input = document.getElementById(this.configs[configType].inputId);
      if (input) input.value = '';
    }
  });
};

// ================================
// FUNÇÕES DE DASHBOARD
// ================================

// Aplicar filtros do dashboard
window.applyDashboardFilters = function() {
  const periodo = document.getElementById('periodo').value;
  const empresaIds = document.getElementById('empresa_ids').value;
  const tarefaIds = document.getElementById('tarefa_ids').value;
  
  if (!validatePeriod(periodo)) {
    showFeedback('Período incorreto! Use o formato MM/AAAA (ex: 01/2025)', 'error');
    return;
  }
  
  if (window.FilterSystem.isLoading) return;
  window.FilterSystem.isLoading = true;
  
  showFeedback('Aplicando filtros...', 'info');
  
  let apiUrl = `/api/dashboard/resumo?periodo=${encodeURIComponent(periodo)}`;
  if (empresaIds) {
    apiUrl += `&empresa_ids=${encodeURIComponent(empresaIds)}`;
  }
  if (tarefaIds) {
    apiUrl += `&tarefa_ids=${encodeURIComponent(tarefaIds)}`;
  }
  
  fetch(apiUrl, {
    credentials: 'same-origin'
  })
    .then(response => {
      if (response.status === 302 || response.redirected) {
        return Promise.reject('Erro de autenticação');
      }
      return response.json();
    })
    .then(data => {
      if (data.success) {
        updateDashboardMetrics(data);
        updateDashboardTable(data);
        showFeedback('Filtros aplicados com sucesso!', 'success');
      } else {
        showFeedback(data.message || 'Erro ao aplicar filtros', 'error');
      }
    })
    .catch(error => {
      console.error('Erro:', error);
      showFeedback('Erro ao aplicar filtros', 'error');
    })
    .finally(() => {
      window.FilterSystem.isLoading = false;
    });
};

// Atualizar métricas do dashboard
window.updateDashboardMetrics = function(data) {
  document.getElementById('metric-pendentes').textContent = data.resumo.pendentes || 0;
  document.getElementById('metric-fazendo').textContent = data.resumo.fazendo || 0;
  document.getElementById('metric-concluidas').textContent = data.resumo.concluidas || 0;
  
  const taxaConclusao = data.taxa_conclusao || 0;
  document.getElementById('metric-taxa-conclusao').textContent = `${taxaConclusao.toFixed(0)}%`;
  
  // Atualizar data de última atualização
  const now = new Date();
  const timeString = now.toLocaleString('pt-BR');
  document.getElementById('last-update').textContent = timeString;
};

// Atualizar tabela do dashboard
window.updateDashboardTable = function(data) {
  const tbody = document.getElementById('tarefas-table-body');
  if (!tbody) return;

  if (data.tarefas.length === 0) {
    tbody.innerHTML = '<tr><td colspan="6" class="text-center">Nenhuma tarefa encontrada</td></tr>';
    return;
  }

  tbody.innerHTML = data.tarefas.map(tarefa => {
    const statusClass = getStatusClass(tarefa.status);
    const statusText = getStatusText(tarefa.status, tarefa.contador_retificacoes);
    const actions = getDashboardActions(tarefa);
    
    return `
      <tr>
        <td>${tarefa.empresa_nome}</td>
        <td>${tarefa.nome}</td>
        <td>${tarefa.tipo}</td>
        <td><span class="status-badge ${statusClass}">${statusText}</span></td>
        <td>${tarefa.vencimento}</td>
        <td>${actions}</td>
      </tr>
    `;
  }).join('');
};

// ================================
// FUNÇÕES DE GERENCIAMENTO
// ================================

// Aplicar filtros do gerenciamento
window.applyManagementFilters = function() {
  const periodo = document.getElementById('periodo').value;
  const empresaIds = document.getElementById('empresa_ids').value;
  const colaboradorId = document.getElementById('colaborador_id').value;
  const tarefaId = document.getElementById('tarefa_id').value;
  
  if (!validatePeriod(periodo)) {
    showFeedback('Período incorreto! Use o formato MM/AAAA (ex: 01/2025)', 'error');
    return;
  }
  
  if (window.FilterSystem.isLoading) return;
  window.FilterSystem.isLoading = true;
  
  showFeedback('Aplicando filtros...', 'info');
  
  let apiUrl = `/gerenciamento/api/resumo?periodo=${encodeURIComponent(periodo)}`;
  if (empresaIds) {
    apiUrl += `&empresa_ids=${encodeURIComponent(empresaIds)}`;
  }
  if (colaboradorId) {
    apiUrl += `&colaborador_id=${colaboradorId}`;
  }
  if (tarefaId) {
    apiUrl += `&tarefa_id=${tarefaId}`;
  }
  
  fetch(apiUrl, {
    credentials: 'same-origin'
  })
    .then(response => {
      if (response.status === 302 || response.redirected) {
        return Promise.reject('Erro de autenticação');
      }
      return response.json();
    })
    .then(data => {
      if (data.success) {
        updateManagementMetrics(data);
        updateManagementTables(data);
        showFeedback('Filtros aplicados com sucesso!', 'success');
      } else {
        showFeedback(data.message || 'Erro ao aplicar filtros', 'error');
      }
    })
    .catch(error => {
      console.error('Erro:', error);
      showFeedback('Erro ao aplicar filtros', 'error');
    })
    .finally(() => {
      window.FilterSystem.isLoading = false;
    });
};

// Atualizar métricas do gerenciamento
window.updateManagementMetrics = function(data) {
  document.getElementById('metric-pendentes').textContent = data.resumo.pendentes || 0;
  document.getElementById('metric-fazendo').textContent = data.resumo.fazendo || 0;
  document.getElementById('metric-concluidas').textContent = data.resumo.concluidas || 0;
  
  const taxaConclusao = data.taxa_conclusao || 0;
  document.getElementById('metric-taxa-conclusao').textContent = `${taxaConclusao.toFixed(0)}%`;
};

// Atualizar tabelas do gerenciamento
window.updateManagementTables = function(data) {
  updateEmpresasTable(data.empresas_resumo || []);
  updateResponsaveisTable(data.responsaveis_tarefas || []);
};

// Atualizar tabela de empresas
window.updateEmpresasTable = function(empresas) {
  const tbody = document.getElementById('empresas-table-body');
  if (!tbody) return;

  if (empresas.length === 0) {
    tbody.innerHTML = '<tr><td colspan="5" class="text-center">Sem dados para os filtros selecionados</td></tr>';
    return;
  }

  tbody.innerHTML = empresas.map(empresa => {
    const total = empresa.pendentes + empresa.fazendo + empresa.concluidas;
    const taxaConclusao = total > 0 ? ((empresa.concluidas / total) * 100).toFixed(0) : 0;
    
    return `
      <tr>
        <td>${empresa.nome}</td>
        <td>${empresa.pendentes}</td>
        <td>${empresa.fazendo}</td>
        <td>${empresa.concluidas}</td>
        <td>${taxaConclusao}%</td>
      </tr>
    `;
  }).join('');
};

// Atualizar tabela de responsáveis
window.updateResponsaveisTable = function(responsaveis) {
  const tbody = document.getElementById('responsaveis-table-body');
  if (!tbody) return;

  if (responsaveis.length === 0) {
    tbody.innerHTML = '<tr><td colspan="5" class="text-center">Nenhuma tarefa atribuída encontrada</td></tr>';
    return;
  }

  tbody.innerHTML = responsaveis.map(responsavel => {
    const statusClass = getStatusClass(responsavel.status);
    const statusText = getStatusText(responsavel.status, responsavel.contador_retificacoes);
    
    // Converter período para formato brasileiro
    const periodoFormatado = formatPeriodoBrasileiro(responsavel.periodo_label);
    
    return `
      <tr>
        <td>${responsavel.usuario_nome || 'Não atribuído'}</td>
        <td>${responsavel.empresa_nome}</td>
        <td>${responsavel.tarefa_nome}</td>
        <td><span class="status-badge ${statusClass}">${statusText}</span></td>
        <td>${periodoFormatado}</td>
      </tr>
    `;
  }).join('');
};

// ================================
// FUNÇÕES AUXILIARES
// ================================

// Formatar período para formato brasileiro (MM/AAAA)
window.formatPeriodoBrasileiro = function(periodo) {
  if (!periodo) return '';
  
  // Se já está no formato MM/AAAA, retorna como está
  if (periodo.includes('/') && periodo.length === 7) {
    return periodo;
  }
  
  // Se está no formato AAAA-MM, converte para MM/AAAA
  if (periodo.includes('-') && periodo.length >= 7) {
    const ano = periodo.substring(0, 4);
    const mes = periodo.substring(5, 7);
    return `${mes}/${ano}`;
  }
  
  return periodo;
};

// Obter classe CSS do status
window.getStatusClass = function(status) {
  switch (status) {
    case 'concluida': return 'status-active';
    case 'retificada': return 'status-warning';
    case 'pendente': return 'status-pending';
    case 'fazendo': return 'status-inactive';
    default: return 'status-inactive';
  }
};

// Obter texto do status
window.getStatusText = function(status, contadorRetificacoes) {
  switch (status) {
    case 'concluida': return 'Concluída';
    case 'retificada': return `Retificada (${contadorRetificacoes}x)`;
    case 'pendente': return 'Pendente';
    case 'fazendo': return 'Em Andamento';
    default: return status;
  }
};

// Função para escapar strings para JavaScript
function escapeJs(str) {
  if (!str) return '';
  return str.toString()
    .replace(/\\/g, '\\\\')
    .replace(/'/g, "\\'")
    .replace(/"/g, '\\"')
    .replace(/\n/g, '\\n')
    .replace(/\r/g, '\\r')
    .replace(/\t/g, '\\t');
}

// Obter ações do dashboard
window.getDashboardActions = function(tarefa) {
  if (tarefa.status === 'pendente') {
    return `<button class="btn btn-success btn-sm" onclick="showConclusaoModal(${tarefa.periodo_id}, '${escapeJs(tarefa.empresa_nome)}', '${escapeJs(tarefa.nome)}', '${escapeJs(tarefa.periodo_label)}')">Concluir</button>`;
  } else if (tarefa.status === 'concluida') {
    return `<button class="btn btn-warning btn-sm" onclick="showRetificationModal(${tarefa.periodo_id}, '${escapeJs(tarefa.empresa_nome)}', '${escapeJs(tarefa.nome)}', '${escapeJs(tarefa.periodo_label)}')">Retificar</button>`;
  } else if (tarefa.status === 'retificada') {
    return `<button class="btn btn-warning btn-sm" onclick="showRetificationModal(${tarefa.periodo_id}, '${escapeJs(tarefa.empresa_nome)}', '${escapeJs(tarefa.nome)}', '${escapeJs(tarefa.periodo_label)}')">Retificar Novamente</button>`;
  }
  return '';
};

// Validar período
window.validatePeriod = function(period) {
  const pattern = /^(0[1-9]|1[0-2])\/(20[0-9]{2})$/;
  return pattern.test(period);
};

// Formatar período
window.formatPeriod = function(value) {
  let formatted = value.replace(/\D/g, '');
  if (formatted.length >= 2) {
    formatted = formatted.substring(0, 2) + '/' + formatted.substring(2, 6);
  }
  return formatted;
};

// Mostrar feedback
window.showFeedback = function(message, type = 'success') {
  const container = document.getElementById('feedback-container');
  if (!container) return;

  container.innerHTML = `
    <div class="feedback-message feedback-${type}">
      <span>${message}</span>
      <button type="button" class="feedback-close" onclick="closeFeedback()">&times;</button>
    </div>
  `;
  
  container.style.display = 'block';
  
  // Auto-hide após 5 segundos
  setTimeout(() => {
    closeFeedback();
  }, 5000);
};

// Fechar feedback
window.closeFeedback = function() {
  const container = document.getElementById('feedback-container');
  if (container) {
    container.style.display = 'none';
  }
};

// ================================

// ================================
// FUNÇÕES DE MODAL
// ================================

// Variáveis para modais
let currentPeriodoId = null;

// Mostrar modal de conclusão
window.showConclusaoModal = function(periodoId, empresaNome, tarefaNome, periodo) {
  currentPeriodoId = periodoId;
  
  // Debug para verificar os valores recebidos
  console.log('showConclusaoModal chamado com:', {
    periodoId, empresaNome, tarefaNome, periodo
  });
  
  // Verificar se os elementos existem
  const modalEmpresa = document.getElementById('modalEmpresa');
  const modalTarefa = document.getElementById('modalTarefa');
  const modalPeriodo = document.getElementById('modalPeriodo');
  
  console.log('Elementos encontrados:', {
    modalEmpresa: !!modalEmpresa,
    modalTarefa: !!modalTarefa,
    modalPeriodo: !!modalPeriodo
  });
  
  if (modalEmpresa) modalEmpresa.textContent = empresaNome || 'N/A';
  if (modalTarefa) modalTarefa.textContent = tarefaNome || 'N/A';
  if (modalPeriodo) modalPeriodo.textContent = periodo || 'N/A';
  
  showModal('modalConfirmarConclusao');
};

// Mostrar modal de retificação
window.showRetificationModal = function(periodoId, empresaNome, tarefaNome, periodo) {
  currentPeriodoId = periodoId;
  
  // Debug para verificar os valores recebidos
  console.log('showRetificationModal chamado com:', {
    periodoId, empresaNome, tarefaNome, periodo
  });
  
  // Verificar se os elementos existem
  const modalRetEmpresa = document.getElementById('modalRetEmpresa');
  const modalRetTarefa = document.getElementById('modalRetTarefa');
  const modalRetPeriodo = document.getElementById('modalRetPeriodo');
  
  console.log('Elementos encontrados:', {
    modalRetEmpresa: !!modalRetEmpresa,
    modalRetTarefa: !!modalRetTarefa,
    modalRetPeriodo: !!modalRetPeriodo
  });
  
  if (modalRetEmpresa) modalRetEmpresa.textContent = empresaNome || 'N/A';
  if (modalRetTarefa) modalRetTarefa.textContent = tarefaNome || 'N/A';
  if (modalRetPeriodo) modalRetPeriodo.textContent = periodo || 'N/A';
  
  showModal('modalConfirmarRetificacao');
};

// Mostrar modal
window.showModal = function(modalId) {
  const modal = document.getElementById(modalId);
  if (!modal) return;
  
  modal.style.display = 'flex';
  modal.classList.add('show');
  document.body.style.overflow = 'hidden';
};

// Fechar modal
window.closeModal = function(modalId) {
  const modal = document.getElementById(modalId);
  if (!modal) return;
  
  modal.classList.remove('show');
  document.body.style.overflow = 'auto';
  
  setTimeout(() => {
    modal.style.display = 'none';
  }, 300);
};

// Confirmar conclusão
window.confirmarConclusao = function() {
  if (!currentPeriodoId) return;

  fetch('/api/dashboard/concluir-tarefa', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'same-origin',
    body: JSON.stringify({
      periodo_id: currentPeriodoId
    })
  })
  .then(response => {
    if (response.status === 302 || response.redirected) {
      return Promise.reject('Erro de autenticação');
    }
    return response.json();
  })
  .then(data => {
    if (data.success) {
      showFeedback('Tarefa concluída com sucesso!', 'success');
      closeModal('modalConfirmarConclusao');
      // Recarregar dados se a função existir
      if (typeof applyDashboardFilters === 'function') {
        applyDashboardFilters();
      }
      if (typeof applyManagementFilters === 'function') {
        applyManagementFilters();
      }
    } else {
      showFeedback(data.message || 'Erro ao concluir tarefa', 'error');
    }
  })
  .catch(error => {
    console.error('Erro:', error);
    showFeedback('Erro ao concluir tarefa', 'error');
  });
};

// Confirmar retificação
window.confirmarRetificacao = function() {
  if (!currentPeriodoId) return;

  const motivo = document.getElementById('motivoRetificacao').value;
  if (!motivo.trim()) {
    showFeedback('Por favor, informe o motivo da retificação', 'error');
    return;
  }

  fetch('/api/dashboard/retificar-tarefa', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'same-origin',
    body: JSON.stringify({
      periodo_id: currentPeriodoId,
      motivo: motivo
    })
  })
  .then(response => {
    if (response.status === 302 || response.redirected) {
      return Promise.reject('Erro de autenticação');
    }
    return response.json();
  })
  .then(data => {
    if (data.success) {
      showFeedback('Tarefa retificada com sucesso!', 'success');
      closeModal('modalConfirmarRetificacao');
      document.getElementById('motivoRetificacao').value = '';
      // Recarregar dados se a função existir
      if (typeof applyDashboardFilters === 'function') {
        applyDashboardFilters();
      }
      if (typeof applyManagementFilters === 'function') {
        applyManagementFilters();
      }
    } else {
      showFeedback(data.message || 'Erro ao retificar tarefa', 'error');
    }
  })
  .catch(error => {
    console.error('Erro:', error);
    showFeedback('Erro ao retificar tarefa', 'error');
  });
};

// Função para toggle de detalhes das contas
function toggledesc(codigo) {
  const row = document.getElementById("detalhe-" + codigo);
  const button = document.querySelector(`.btn-descricao-toggle[data-codigo="${codigo}"]`);
  
  if (!row || !button) return;

  const icon = button.querySelector("i");

  if (row.classList.contains("hidden")) {
    row.classList.remove("hidden");
    row.style.display = "table-row";
    if (icon) icon.className = "fas fa-chevron-up";
    button.innerHTML = '<i class="fas fa-chevron-up"></i> Ocultar';
  } else {
    row.classList.add("hidden");
    row.style.display = "none";
    if (icon) icon.className = "fas fa-chevron-down";
    button.innerHTML = '<i class="fas fa-chevron-down"></i> Detalhes';
  }
}

// Função para mudar cor do select de status
function mudarCor(select) {
  const valor = select.value;
  const cores = {
    'Pendente': '#a74128ff',
    'Feito': '#28a78cff', 
    'Fazendo': '#ffa620ff'
  };
  
  select.style.backgroundColor = cores[valor] || 'white';
  select.style.color = valor ? 'white' : 'black';
}

// Função para toggle de formulários CORRIGIDA
function toggleForm(id) {
  const div = document.getElementById(id);
  
  if (!div) {
    console.error('Elemento não encontrado:', id);
    return;
  }

  // Verifica se é um formulário de edição (tr element)
  const isTableRow = div.tagName.toLowerCase() === 'tr';
  
  // Encontra o ícone correspondente
  const icon = document.getElementById('toggle-icon-' + id);
  
  const isHidden = div.classList.contains('hidden') ||
                   div.style.display === 'none' ||
                   div.style.display === '';

  if (isHidden) {
    div.classList.remove('hidden');
    
    if (isTableRow) {
      div.style.display = 'table-row';
    } else {
      div.style.display = 'block';
    }
    
    if (icon) icon.textContent = '−';
    console.log(`Formulário ${id} expandido`);
  } else {
    div.classList.add('hidden');
    div.style.display = 'none';
    if (icon) icon.textContent = '+';
    console.log(`Formulário ${id} recolhido`);
  }
}

// Função específica para toggle de edição de contas
function toggleEditForm(formId) {
  console.log('Tentando alternar formulário:', formId);
  
  const formRow = document.getElementById(formId);
  if (!formRow) {
    console.error('Formulário de edição não encontrado:', formId);
    return;
  }

  const isHidden = formRow.classList.contains('hidden') || 
                   formRow.style.display === 'none' ||
                   formRow.style.display === '';

  if (isHidden) {
    // Primeiro fecha outros formulários de edição abertos
    document.querySelectorAll('tr[id^="editForm-"]').forEach(row => {
      if (row.id !== formId) {
        row.classList.add('hidden');
        row.style.display = 'none';
      }
    });

    // Abre o formulário atual
    formRow.classList.remove('hidden');
    formRow.style.display = 'table-row';
    console.log(`Formulário ${formId} aberto`);
  } else {
    // Fecha o formulário atual
    formRow.classList.add('hidden');
    formRow.style.display = 'none';
    console.log(`Formulário ${formId} fechado`);
  }
}

// Função para controlar campo ID Empresa
function toggleIdEmpresaField() {
  const tipoContaSelect = document.getElementById('tipo_conta');
  const idEmpresaInput = document.getElementById('idEmpresa');
  
  if (!tipoContaSelect || !idEmpresaInput) return;
  
  const tipoContaValue = tipoContaSelect.value;
  
  if (tipoContaValue === 'privada') {
    idEmpresaInput.disabled = false;
    idEmpresaInput.required = true;
    idEmpresaInput.placeholder = 'Digite o ID da empresa...';
  } else {
    idEmpresaInput.disabled = true;
    idEmpresaInput.required = false;
    idEmpresaInput.value = '';
    idEmpresaInput.placeholder = 'Disponível apenas para contas privadas';
  }
}

// Validação do formulário de contas
function validateContaForm(event) {
  const tipoContaSelect = document.getElementById('tipo_conta');
  const idEmpresaInput = document.getElementById('idEmpresa');
  
  if (!tipoContaSelect || !idEmpresaInput) return true;
  
  const tipoContaValue = tipoContaSelect.value;
  const idEmpresaValue = idEmpresaInput.value.trim();
  
  if (tipoContaValue === 'privada' && !idEmpresaValue) {
    event.preventDefault();
    alert('Para contas privadas, o ID da Empresa é obrigatório.');
    idEmpresaInput.focus();
    return false;
  }
  
  if (tipoContaValue === 'publica') {
    idEmpresaInput.value = '';
  }
  
  return true;
}

// ================================
// DASHBOARD - ANIMAÇÕES E CONTADORES
// ================================

// Função principal para animar contadores
function animateCounters() {
  console.log('🎬 Iniciando animação dos contadores...');
  
  const counters = document.querySelectorAll('.metric-value');
  
  if (counters.length === 0) {
    console.warn('⚠️ Nenhum contador encontrado para animar');
    return;
  }
  
  console.log(`📊 Encontrados ${counters.length} contadores para animar`);
  
  counters.forEach((counter, index) => {
    const originalText = counter.textContent.trim();
    console.log(`Contador ${index + 1}: "${originalText}"`);
    
    // Extrai o número do texto - suporte para percentuais
    let target = 0;
    let isPercentage = originalText.includes('%');
    
    if (isPercentage) {
      target = parseFloat(originalText.replace(/[^\d.]/g, '')) || 0;
    } else {
      target = parseInt(originalText.replace(/[^\d]/g, '')) || 0;
    }
    
    console.log(`Valor alvo: ${target}${isPercentage ? '%' : ''}`);
    
    // Define valor inicial
    counter.textContent = isPercentage ? '0%' : '0';
    
    if (target === 0) {
      // Se o alvo é 0, apenas define o valor final
      counter.textContent = isPercentage ? '0%' : '0';
      return;
    }
    
    // Configuração da animação
    const duration = 1500 + (index * 200); // Animações escalonadas
    const startTime = performance.now();

    function updateCounter(currentTime) {
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);
      
      // Efeito de easing suave
      const eased = progress < 0.5 
        ? 2 * progress * progress 
        : 1 - Math.pow(-2 * progress + 2, 2) / 2;
      
      const currentValue = Math.round(target * eased);
      
      // Atualiza o display
      if (isPercentage) {
        counter.textContent = `${currentValue}%`;
      } else {
        counter.textContent = currentValue.toLocaleString('pt-BR');
      }

      if (progress < 1) {
        requestAnimationFrame(updateCounter);
      } else {
        // Valor final exato
        counter.textContent = isPercentage 
          ? `${target}%` 
          : target.toLocaleString('pt-BR');
        
        console.log(`✅ Animação ${index + 1} concluída: ${counter.textContent}`);
      }
    }
    
    // Inicia a animação com delay
    setTimeout(() => {
      requestAnimationFrame(updateCounter);
    }, index * 100);
  });
}

// Função para atualizar data atual
function updateCurrentDate() {
  const dateEl = document.getElementById('current-date');
  if (dateEl) {
    const now = new Date();
    dateEl.textContent = now.toLocaleDateString('pt-BR', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
    console.log('📅 Data atualizada:', dateEl.textContent);
  }
}

// Função para inicializar dashboard
function initializeDashboard() {
  console.log('🚀 Inicializando dashboard...');
  
  const dashboardSection = document.getElementById('dashboard');
  if (!dashboardSection) {
    console.log('ℹ️ Dashboard não encontrado nesta página');
    return;
  }
  
  // Atualiza data
  updateCurrentDate();
  
  // Verifica se o dashboard está visível
  const isVisible = dashboardSection.offsetParent !== null && 
                   dashboardSection.style.display !== 'none';
  
  if (!isVisible) {
    console.log('ℹ️ Dashboard não está visível');
    return;
  }
  
  console.log('📊 Dashboard visível, iniciando animações...');
  
  // Múltiplas tentativas de animação para garantir sucesso
  const tryAnimate = (attempt = 1) => {
    const counters = document.querySelectorAll('.metric-value');
    
    if (counters.length > 0) {
      console.log(`✅ Tentativa ${attempt}: Encontrados ${counters.length} contadores`);
      animateCounters();
      return;
    }
    
    if (attempt < 5) {
      console.log(`⏳ Tentativa ${attempt}: Aguardando contadores... (${attempt * 300}ms)`);
      setTimeout(() => tryAnimate(attempt + 1), 300);
    } else {
      console.warn('⚠️ Contadores não encontrados após 5 tentativas');
    }
  };
  
  // Inicia as tentativas
  tryAnimate();
  
  // Adiciona interatividade aos cards
  document.querySelectorAll('.metric-card').forEach(card => {
    card.addEventListener('click', function() {
      const metric = this.dataset.metric;
      console.log(`📊 Card clicado: ${metric}`);
      
      // Adiciona efeito visual
      this.style.transform = 'scale(0.98)';
      setTimeout(() => {
        this.style.transform = 'scale(1)';
      }, 150);
    });
  });
}

// ================================
// INICIALIZAÇÃO ESPECÍFICA PARA CONTAS
// ================================

function initializeContasPage() {
  console.log('📊 Inicializando página de contas...');

  // 1. Inicializa contadores da página de contas
  const contadores = document.querySelectorAll('#contas .metric-value');
  if (contadores.length > 0) {
    console.log(`📊 Animando ${contadores.length} contadores da página de contas`);
    
    contadores.forEach((contador, index) => {
      const valor = parseInt(contador.textContent) || 0;
      let atual = 0;
      const incremento = valor / 30;
      contador.textContent = '0';
      
      const intervalo = setInterval(() => {
        atual += incremento;
        if (atual >= valor) {
          contador.textContent = valor;
          clearInterval(intervalo);
        } else {
          contador.textContent = Math.floor(atual);
        }
      }, 50);
    });
  }

  // 2. Garante que todos os formulários de edição começem ocultos
  document.querySelectorAll('tr[id^="editForm-"]').forEach(row => {
    row.classList.add('hidden');
    row.style.display = 'none';
  });

  console.log('✅ Página de contas inicializada!');
}

// ================================
// INICIALIZAÇÃO ESPECÍFICA PARA RELATÓRIOS
// ================================

function initializeRelatoriosPage() {
  console.log('📊 Inicializando página de relatórios...');

  const periodoSelect = document.getElementById('periodo');
  const mesGroup = document.getElementById('mesGroup');

  if (periodoSelect && mesGroup) {
    // Mostrar/ocultar campo de mês baseado na seleção do período
    periodoSelect.addEventListener('change', function() {
      if (this.value === 'personalizado') {
        mesGroup.style.display = 'flex';
      } else {
        mesGroup.style.display = 'none';
        document.getElementById('mes').value = '';
      }
    });

    // Reset form functionality
    const resetBtn = document.querySelector('button[type="reset"]');
    if (resetBtn) {
      resetBtn.addEventListener('click', function() {
        mesGroup.style.display = 'none';
      });
    }
  }

  console.log('✅ Página de relatórios inicializada!');
}

// ================================
// INICIALIZAÇÃO PRINCIPAL
// ================================

document.addEventListener('DOMContentLoaded', function() {
  console.log('🌟 Sistema DP & Contabilidade carregado!');
  
  // 1. Inicialização dos selects de status
  document.querySelectorAll('.statusSelect').forEach(select => {
    mudarCor(select);
    
    select.addEventListener('change', function() {
      mudarCor(this);
      console.log(`Status alterado: Conta ${this.dataset.conta} → ${this.value}`);
    });
  });
  
  // 2. Configuração de linhas ocultas
  document.querySelectorAll('tr.hidden').forEach(row => {
    row.style.display = 'none';
  });
  
  // 3. Botões de toggle de detalhes (para página de gerenciamento)
  document.querySelectorAll('.btn-descricao-toggle[data-codigo]').forEach(btn => {
    btn.addEventListener('click', function() {
      const codigo = this.getAttribute("data-codigo");
      toggledesc(codigo);
    });
  });
  
  // 4. Formulário de contas
  const tipoContaSelect = document.getElementById('tipo_conta');
  const contaForm = document.getElementById('contaForm');
  
  if (tipoContaSelect) {
    tipoContaSelect.addEventListener('change', toggleIdEmpresaField);
    toggleIdEmpresaField(); // Inicialização
  }
  
  if (contaForm) {
    contaForm.addEventListener('submit', validateContaForm);
  }
  
  // 5. Inicialização do Dashboard (se existir)
  initializeDashboard();
  
  // 6. Configura todos os botões de edição
  document.querySelectorAll('[data-toggle-edit]').forEach(btn => {
    const formId = btn.getAttribute('data-toggle-edit');
    btn.addEventListener('click', function(e) {
      e.preventDefault();
      toggleEditForm(formId);
    });
  });

  // 7. Configura botões de cancelar edição
  document.querySelectorAll('[data-cancel-edit]').forEach(btn => {
    const formId = btn.getAttribute('data-cancel-edit');
    btn.addEventListener('click', function(e) {
      e.preventDefault();
      toggleEditForm(formId); // vai fechar o form
    });
  });

  // 8. Inicialização específica da página de contas (se existir)
  const contasSection = document.getElementById('contas');
  if (contasSection) {
    initializeContasPage();
  }

  // 8.1. Inicialização específica da página de relatórios (se existir)
  const relatoriosSection = document.getElementById('relatorios');
  if (relatoriosSection) {
    initializeRelatoriosPage();
  }
  
  // 9. Botão de refresh (se existir)
  const refreshBtn = document.querySelector('button[onclick="location.reload()"]');
  if (refreshBtn) {
    refreshBtn.addEventListener('click', function(e) {
      e.preventDefault();
      console.log('🔄 Refresh solicitado');
      location.reload();
    });
  }
  
  console.log('✅ Inicialização completa!');
});

// ================================
// INICIALIZAÇÃO UNIVERSAL DE FILTROS
// ================================

// Função para inicializar filtros automaticamente
window.initPageFilters = function() {
  console.log('🚀 Inicializando filtros da página...');
  
  // Detectar página e inicializar filtros apropriados
  const path = window.location.pathname;
  console.log('📍 Caminho da página:', path);
  
  if (path.includes('/dashboard')) {
    console.log('📊 Inicializando filtros do dashboard...');
    
    // Verificar se os elementos existem
    const empresaSearch = document.getElementById('empresa-search');
    const tarefaSearch = document.getElementById('tarefa-search');
    
    console.log('Elementos encontrados:', {
      empresaSearch: !!empresaSearch,
      tarefaSearch: !!tarefaSearch
    });
    
    // Inicializar filtros do dashboard
    if (empresaSearch) {
      console.log('✅ Inicializando filtro empresa_dashboard');
      window.FilterSystem.init('empresa_dashboard');
    } else {
      console.error('❌ Elemento empresa-search não encontrado');
    }
    
    if (tarefaSearch) {
      console.log('✅ Inicializando filtro tarefa_dashboard');
      window.FilterSystem.init('tarefa_dashboard');
    } else {
      console.error('❌ Elemento tarefa-search não encontrado');
    }
    
    // Configurar botão aplicar
    const applyBtn = document.querySelector('button[onclick="applyFilters()"]');
    if (applyBtn) {
      applyBtn.setAttribute('onclick', 'applyDashboardFilters()');
    }
    
    // Configurar botão limpar
    const clearBtn = document.querySelector('button[onclick="clearAllFilters()"]');
    if (clearBtn) {
      clearBtn.setAttribute('onclick', 'window.FilterSystem.clearAllFilters()');
    }
    
    console.log('✅ Filtros do dashboard inicializados');
    
  } else if (path.includes('/gerenciamento')) {
    // Inicializar filtros do gerenciamento
    if (document.getElementById('empresa-search')) {
      window.FilterSystem.init('empresa_gerenciamento');
    }
    if (document.getElementById('colaborador-search')) {
      window.FilterSystem.init('colaborador_gerenciamento');
    }
    if (document.getElementById('tarefa-search')) {
      window.FilterSystem.init('tarefa_gerenciamento');
    }
    
    // Configurar botão aplicar
    const applyBtn = document.querySelector('button[onclick="applyFilters()"]');
    if (applyBtn) {
      applyBtn.setAttribute('onclick', 'applyManagementFilters()');
    }
    
    // Configurar botão limpar
    const clearBtn = document.querySelector('button[onclick="clearAllFilters()"]');
    if (clearBtn) {
      clearBtn.setAttribute('onclick', 'window.FilterSystem.clearAllFilters()');
    }
    
    console.log('✅ Filtros do gerenciamento inicializados');
    
  } else if (path.includes('/tarefas')) {
    // Inicializar filtros da vinculação em massa
    if (document.getElementById('empresa-search')) {
      window.FilterSystem.init('empresa_vinculacao');
    }
    if (document.getElementById('tarefa-search')) {
      window.FilterSystem.init('tarefa_vinculacao');
    }
    if (document.getElementById('responsavel-search')) {
      window.FilterSystem.init('responsavel_vinculacao');
    }
    
    console.log('✅ Filtros da vinculação em massa inicializados');
    
    // Inicializar filtros da vinculação individual
    if (document.getElementById('empresa-individual-search')) {
      window.FilterSystem.init('empresa_individual');
    }
    if (document.getElementById('tarefa-individual-search')) {
      window.FilterSystem.init('tarefa_individual');
    }
    if (document.getElementById('responsavel-individual-search')) {
      window.FilterSystem.init('responsavel_individual');
    }
    
    console.log('✅ Filtros da vinculação individual inicializados');
  } else if (path.includes('/relatorios')) {
    // Inicializar filtros dos relatórios
    if (document.getElementById('empresa-search')) {
      window.FilterSystem.init('empresa_relatorios');
    }
    if (document.getElementById('funcionario-search')) {
      window.FilterSystem.init('funcionario_relatorios');
    }
    if (document.getElementById('tarefa-search')) {
      window.FilterSystem.init('tarefa_relatorios');
    }
    
    console.log('✅ Filtros dos relatórios inicializados');
  }
  
  // Configurar fechamento de modais ao clicar fora
  document.addEventListener('click', function(event) {
    const modals = ['modalConfirmarConclusao', 'modalConfirmarRetificacao'];
    modals.forEach(modalId => {
      const modal = document.getElementById(modalId);
      if (event.target === modal && modal.classList.contains('show')) {
        closeModal(modalId);
      }
    });
  });
};

// Inicializar automaticamente quando o DOM estiver pronto
document.addEventListener('DOMContentLoaded', function() {
  console.log('📄 DOM carregado, aguardando inicialização...');
  
  // Aguardar mais tempo para garantir que todos os elementos estejam carregados
  setTimeout(() => {
    console.log('⏰ Timeout atingido, inicializando filtros...');
    window.initPageFilters();
  }, 500);
});

// Fallback: tentar inicializar quando a página estiver completamente carregada
window.addEventListener('load', function() {
  console.log('🌐 Página completamente carregada, verificando filtros...');
  
  setTimeout(() => {
    const path = window.location.pathname;
    if (path.includes('/dashboard')) {
      const empresaSearch = document.getElementById('empresa-search');
      const tarefaSearch = document.getElementById('tarefa-search');
      
      if (empresaSearch || tarefaSearch) {
        console.log('🔄 Reinicializando filtros do dashboard...');
        window.initPageFilters();
      }
    }
  }, 200);
});

// ================================
// FUNÇÕES GLOBAIS PARA DEBUG
// ================================

// Função para testar manualmente os filtros
window.testFilters = function() {
  console.log('🧪 Testando filtros manualmente...');
  
  const path = window.location.pathname;
  console.log('📍 Caminho:', path);
  
  if (path.includes('/dashboard')) {
    const empresaSearch = document.getElementById('empresa-search');
    const tarefaSearch = document.getElementById('tarefa-search');
    
    console.log('Elementos encontrados:', {
      empresaSearch: !!empresaSearch,
      tarefaSearch: !!tarefaSearch
    });
    
    if (empresaSearch) {
      console.log('🔧 Testando inicialização empresa_dashboard...');
      window.FilterSystem.init('empresa_dashboard');
    }
    
    if (tarefaSearch) {
      console.log('🔧 Testando inicialização tarefa_dashboard...');
      window.FilterSystem.init('tarefa_dashboard');
    }
  }
};

// Expõe funções para debug no console
window.animateCounters = animateCounters;
window.updateCurrentDate = updateCurrentDate;
window.toggleEditForm = toggleEditForm;
window.toggleForm = toggleForm;
