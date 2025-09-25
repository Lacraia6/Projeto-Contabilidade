// Variáveis globais para armazenar dados
let todasEmpresasDropdown = [];
let todasTarefasDropdown = [];
let currentPeriodoId = null;
let currentTarefaData = {};

// ================================
// FUNÇÕES DE MODAL
// ================================

// Mostrar modal de confirmação de conclusão
function showConclusaoModal(periodoId, empresaNome, tarefaNome, periodo) {
  currentPeriodoId = periodoId;
  currentTarefaData = {
    empresa: empresaNome,
    tarefa: tarefaNome,
    periodo: periodo
  };
  
  // Preencher dados no modal
  document.getElementById('modalEmpresaNome').textContent = empresaNome;
  document.getElementById('modalTarefaNome').textContent = tarefaNome;
  document.getElementById('modalPeriodo').textContent = periodo;
  
  // Mostrar modal
  showModal('modalConfirmarConclusao');
}

// Mostrar modal de confirmação de retificação
function showRetificationModal(periodoId, empresaNome, tarefaNome, periodo) {
  currentPeriodoId = periodoId;
  currentTarefaData = {
    empresa: empresaNome,
    tarefa: tarefaNome,
    periodo: periodo
  };
  
  // Preencher dados no modal
  document.getElementById('modalRetEmpresaNome').textContent = empresaNome;
  document.getElementById('modalRetTarefaNome').textContent = tarefaNome;
  document.getElementById('modalRetPeriodo').textContent = periodo;
  
  // Limpar campo de motivo
  document.getElementById('motivoRetificacao').value = '';
  
  // Mostrar modal
  showModal('modalConfirmarRetificacao');
}

// Confirmar conclusão da tarefa
async function confirmarConclusao() {
  if (!currentPeriodoId) return;
  
  try {
    const response = await fetch('{{ url_for("dashboard.concluir_tarefa") }}', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: `periodo_id=${currentPeriodoId}`
    });
    
    const result = await response.json();
    
    if (result.success) {
      // Fechar modal de confirmação
      closeModal('modalConfirmarConclusao');
      
      // Mostrar modal de sucesso
      showSucessoModal('Tarefa Concluída com Sucesso!', 'A tarefa foi marcada como concluída com sucesso.');
      
      // Recarregar a página após um delay
      setTimeout(() => {
        location.reload();
      }, 2000);
    } else {
      alert('Erro ao concluir tarefa: ' + (result.message || 'Erro desconhecido'));
    }
  } catch (error) {
    console.error('Erro:', error);
    alert('Erro ao concluir tarefa. Tente novamente.');
  }
}

// Confirmar retificação da tarefa
async function confirmarRetificacao() {
  if (!currentPeriodoId) return;
  
  const motivo = document.getElementById('motivoRetificacao').value;
  
  try {
    const response = await fetch('{{ url_for("dashboard.concluir_tarefa") }}', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: `periodo_id=${currentPeriodoId}&retificar=true&motivo=${encodeURIComponent(motivo)}`
    });
    
    const result = await response.json();
    
    if (result.success) {
      // Fechar modal de confirmação
      closeModal('modalConfirmarRetificacao');
      
      // Mostrar modal de sucesso
      showSucessoModal('Tarefa Retificada com Sucesso!', 'A tarefa foi marcada como retificada com sucesso.');
      
      // Recarregar a página após um delay
      setTimeout(() => {
        location.reload();
      }, 2000);
    } else {
      alert('Erro ao retificar tarefa: ' + (result.message || 'Erro desconhecido'));
    }
  } catch (error) {
    console.error('Erro:', error);
    alert('Erro ao retificar tarefa. Tente novamente.');
  }
}

// Mostrar modal de sucesso
function showSucessoModal(titulo, texto) {
  document.getElementById('modalSucessoTitulo').textContent = titulo;
  document.getElementById('modalSucessoTexto').textContent = texto;
  document.getElementById('modalSucessoEmpresa').textContent = currentTarefaData.empresa;
  document.getElementById('modalSucessoTarefa').textContent = currentTarefaData.tarefa;
  document.getElementById('modalSucessoPeriodo').textContent = currentTarefaData.periodo;
  document.getElementById('modalSucessoData').textContent = new Date().toLocaleString('pt-BR');
  
  showModal('modalSucesso');
}

// Mostrar modal
function showModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.add('show');
    document.body.style.overflow = 'hidden';
  }
}

// Fechar modal
function closeModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.remove('show');
    document.body.style.overflow = '';
  }
}

// Fechar modal ao clicar no overlay
document.addEventListener('click', function(e) {
  if (e.target.classList.contains('modal-overlay')) {
    const modal = e.target;
    modal.classList.remove('show');
    document.body.style.overflow = '';
  }
});

// Fechar modal com ESC
document.addEventListener('keydown', function(e) {
  if (e.key === 'Escape') {
    const openModal = document.querySelector('.modal-overlay.show');
    if (openModal) {
      openModal.classList.remove('show');
      document.body.style.overflow = '';
    }
  }
});

// ================================
// FUNÇÕES DE DROPDOWN SEARCH
// ================================

// Carregar todas as empresas para dropdown
async function loadEmpresasForDropdown() {
  if (todasEmpresasDropdown.length === 0) {
    try {
      const response = await fetch('/tarefas/api/empresas?search=&limit=1000');
      const data = await response.json();
      todasEmpresasDropdown = data.empresas;
    } catch (error) {
      console.error('Erro ao carregar empresas para dropdown:', error);
    }
  }
  return todasEmpresasDropdown;
}

// Carregar todas as tarefas para dropdown
async function loadTarefasForDropdown() {
  if (todasTarefasDropdown.length === 0) {
    try {
      const response = await fetch('/tarefas/api/tarefas?search=&limit=1000');
      const data = await response.json();
      todasTarefasDropdown = data.tarefas;
    } catch (error) {
      console.error('Erro ao carregar tarefas para dropdown:', error);
    }
  }
  return todasTarefasDropdown;
}

// Renderizar opções do dropdown
function renderDropdownOptions(dropdown, filteredItems, type) {
  if (filteredItems.length === 0) {
    dropdown.innerHTML = '<div class="dropdown-search-item no-results">Nenhum resultado encontrado</div>';
    return;
  }

  dropdown.innerHTML = filteredItems.map(item => {
    if (type === 'empresa') {
      return `
        <div class="dropdown-search-item" onclick="selectDropdownOption(this, ${item.id}, '${item.nome}', 'empresa')">
          <div class="dropdown-search-item-name">${item.nome}</div>
          <div class="dropdown-search-item-details">Código: ${item.codigo} | Tributação: ${item.tributacao_nome}</div>
        </div>
      `;
    } else if (type === 'tarefa') {
      return `
        <div class="dropdown-search-item" onclick="selectDropdownOption(this, ${item.id}, '${item.nome}', 'tarefa')">
          <div class="dropdown-search-item-name">${item.nome}</div>
          <div class="dropdown-search-item-details">Tipo: ${item.tipo} | Setor: ${item.setor_nome} | Tributação: ${item.tributacao_nome}</div>
        </div>
      `;
    }
  }).join('');
}

// Inicializar dropdown search
function initDropdownSearch() {
  // Inicializar todos os dropdowns de empresa
  const empresaInputs = document.querySelectorAll('.empresa-dropdown-input');
  empresaInputs.forEach(input => {
    setupDropdownSearch(input, 'empresa');
  });

  // Inicializar todos os dropdowns de tarefa
  const tarefaInputs = document.querySelectorAll('.tarefa-dropdown-input');
  tarefaInputs.forEach(input => {
    setupDropdownSearch(input, 'tarefa');
  });
}

// Configurar dropdown search para um input específico
function setupDropdownSearch(input, type) {
  const container = input.closest('.dropdown-search-container');
  const dropdown = container.querySelector('.dropdown-search-list');
  const hiddenInput = container.querySelector('.dropdown-search-hidden');

  // Event listeners
  input.addEventListener('focus', () => {
    showDropdown(dropdown);
    filterDropdown(input, dropdown, type);
  });

  input.addEventListener('input', () => {
    filterDropdown(input, dropdown, type);
  });

  input.addEventListener('blur', (e) => {
    // Delay para permitir clique na opção
    setTimeout(() => {
      if (!container.contains(document.activeElement)) {
        hideDropdown(dropdown);
      }
    }, 200);
  });
}

// Filtrar dropdown conforme digita
function filterDropdown(input, dropdown, type) {
  const query = input.value.toLowerCase();
  let data = [];

  if (type === 'empresa') {
    data = todasEmpresasDropdown;
  } else if (type === 'tarefa') {
    data = todasTarefasDropdown;
  }

  const filtered = data.filter(item => {
    if (type === 'empresa') {
      return item.nome.toLowerCase().includes(query) || 
             item.codigo.toLowerCase().includes(query) ||
             item.tributacao_nome.toLowerCase().includes(query);
    } else if (type === 'tarefa') {
      return item.nome.toLowerCase().includes(query) || 
             item.tipo.toLowerCase().includes(query) ||
             item.setor_nome.toLowerCase().includes(query) ||
             item.tributacao_nome.toLowerCase().includes(query);
    }
    return false;
  });

  renderDropdownOptions(dropdown, filtered, type);
}

// Selecionar opção do dropdown
function selectDropdownOption(element, id, nome, type) {
  const container = element.closest('.dropdown-search-container');
  const input = container.querySelector('.dropdown-search-input');
  const hiddenInput = container.querySelector('.dropdown-search-hidden');
  const dropdown = container.querySelector('.dropdown-search-list');
  
  // Verificar se é seleção múltipla
  const isMultiple = container.classList.contains('multiple-selection');
  
  if (isMultiple) {
    // Seleção múltipla - adicionar à lista
    addSelectedItem(container, id, nome, type);
  } else {
    // Seleção única - substituir valor
    input.value = nome;
    hiddenInput.value = id;
  }

  // Limpar input de busca
  input.value = '';

  // Fechar dropdown
  hideDropdown(dropdown);

  // Trigger change event
  const event = new Event('change', { bubbles: true });
  hiddenInput.dispatchEvent(event);
}

// Adicionar item selecionado
function addSelectedItem(container, id, nome, type) {
  const selectedContainer = container.querySelector('.selected-items-container');
  if (!selectedContainer) return;

  // Verificar se já não está selecionado
  const existingItem = selectedContainer.querySelector(`[data-id="${id}"]`);
  if (existingItem) return;

  // Criar elemento do item selecionado
  const selectedItem = document.createElement('div');
  selectedItem.className = 'selected-item';
  selectedItem.setAttribute('data-id', id);
  selectedItem.innerHTML = `
    <span class="selected-item-text">${nome}</span>
    <button type="button" class="selected-item-remove" onclick="removeSelectedItem(this, '${id}')">&times;</button>
  `;

  selectedContainer.appendChild(selectedItem);

  // Atualizar input hidden com array de IDs
  updateHiddenInput(container);
}

// Remover item selecionado
function removeSelectedItem(button, id) {
  const selectedItem = button.closest('.selected-item');
  const container = selectedItem.closest('.dropdown-search-container');
  
  selectedItem.remove();
  
  // Atualizar input hidden
  updateHiddenInput(container);
}

// Atualizar input hidden com array de IDs
function updateHiddenInput(container) {
  const hiddenInput = container.querySelector('.dropdown-search-hidden');
  const selectedItems = container.querySelectorAll('.selected-item');
  
  const ids = Array.from(selectedItems).map(item => item.getAttribute('data-id'));
  hiddenInput.value = ids.join(',');
}

// Limpar todas as seleções
function clearAllSelections(container) {
  const selectedContainer = container.querySelector('.selected-items-container');
  if (selectedContainer) {
    selectedContainer.innerHTML = '';
  }
  
  const hiddenInput = container.querySelector('.dropdown-search-hidden');
  hiddenInput.value = '';
}

// Mostrar dropdown
function showDropdown(dropdown) {
  dropdown.style.display = 'block';
  dropdown.classList.add('show');
}

// Esconder dropdown
function hideDropdown(dropdown) {
  dropdown.style.display = 'none';
  dropdown.classList.remove('show');
}

// ================================
// INICIALIZAÇÃO
// ================================

// Carregar itens pré-selecionados
function loadPreselectedItems() {
  const containers = document.querySelectorAll('.dropdown-search-container.multiple-selection');
  
  containers.forEach(container => {
    const hiddenInput = container.querySelector('.dropdown-search-hidden');
    const selectedContainer = container.querySelector('.selected-items-container');
    const input = container.querySelector('.dropdown-search-input');
    
    if (hiddenInput.value && selectedContainer) {
      const ids = hiddenInput.value.split(',').filter(id => id.trim());
      
      if (ids.length > 0) {
        // Determinar tipo baseado na classe do input
        const isEmpresa = input.classList.contains('empresa-dropdown-input');
        const isTarefa = input.classList.contains('tarefa-dropdown-input');
        
        if (isEmpresa) {
          // Carregar dados das empresas e criar tags
          loadEmpresasForDropdown().then(() => {
            ids.forEach(id => {
              const empresa = todasEmpresasDropdown.find(e => e.id == id);
              if (empresa) {
                addSelectedItem(container, empresa.id, empresa.nome, 'empresa');
              }
            });
          });
        } else if (isTarefa) {
          // Carregar dados das tarefas e criar tags
          loadTarefasForDropdown().then(() => {
            ids.forEach(id => {
              const tarefa = todasTarefasDropdown.find(t => t.id == id);
              if (tarefa) {
                addSelectedItem(container, tarefa.id, tarefa.nome, 'tarefa');
              }
            });
          });
        }
      }
    }
  });
}

// Inicializar quando a página carrega
document.addEventListener('DOMContentLoaded', function() {
  initDropdownSearch();
  
  // Carregar itens pré-selecionados após um pequeno delay
  setTimeout(() => {
    loadPreselectedItems();
  }, 500);
});

// ================================
// EXPOSIÇÃO DE FUNÇÕES
// ================================

// Limpar todos os filtros (para o painel do gerente)
function clearAllFilters() {
  // Limpar campo de período
  const periodoInput = document.getElementById('periodo');
  if (periodoInput) {
    periodoInput.value = '';
  }
  
  // Limpar todos os dropdowns de seleção múltipla
  const containers = document.querySelectorAll('.dropdown-search-container.multiple-selection');
  containers.forEach(container => {
    clearAllSelections(container);
  });
  
  // Limpar dropdowns de seleção única
  const singleContainers = document.querySelectorAll('.dropdown-search-container:not(.multiple-selection)');
  singleContainers.forEach(container => {
    const input = container.querySelector('.dropdown-search-input');
    const hiddenInput = container.querySelector('.dropdown-search-hidden');
    if (input) input.value = '';
    if (hiddenInput) hiddenInput.value = '';
  });
}

// Expor funções globalmente
window.initDropdownSearch = initDropdownSearch;
window.selectDropdownOption = selectDropdownOption;
window.addSelectedItem = addSelectedItem;
window.removeSelectedItem = removeSelectedItem;
window.clearAllSelections = clearAllSelections;
window.clearAllFilters = clearAllFilters;
window.showConclusaoModal = showConclusaoModal;
window.showRetificationModal = showRetificationModal;
window.confirmarConclusao = confirmarConclusao;
window.confirmarRetificacao = confirmarRetificacao;
window.closeModal = closeModal;

