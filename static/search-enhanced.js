// ================================
// SISTEMA DP & CONTABILIDADE - BUSCA MELHORADA
// ================================

// Variáveis globais para armazenar dados
let todasEmpresasVinculacao = [];
let todasTarefasVinculacao = [];

// ================================
// FUNCIONALIDADE DE EMPRESAS
// ================================

// Carregar todas as empresas ao inicializar
async function carregarTodasEmpresasVinculacao() {
  try {
    const response = await fetch('/tarefas/api/empresas?search=&limit=1000');
    const data = await response.json();
    todasEmpresasVinculacao = data.empresas;
    filtrarEmpresasVinculacao();
  } catch (error) {
    console.error('Erro ao carregar empresas:', error);
    const resultsContainer = document.getElementById('empresaResults');
    if (resultsContainer) {
      resultsContainer.innerHTML = '<div class="error-text">Erro ao carregar empresas</div>';
    }
  }
}

// Filtrar empresas conforme digita
function filtrarEmpresasVinculacao() {
  const searchTerm = document.getElementById('empresaSearch').value.toLowerCase();
  const resultsContainer = document.getElementById('empresaResults');
  
  if (!resultsContainer) return;
  
  const empresasFiltradas = todasEmpresasVinculacao.filter(empresa => 
    empresa.nome.toLowerCase().includes(searchTerm) || 
    empresa.codigo.toLowerCase().includes(searchTerm) ||
    empresa.tributacao_nome.toLowerCase().includes(searchTerm)
  );
  
  if (empresasFiltradas.length === 0) {
    resultsContainer.innerHTML = '<div class="no-results">Nenhuma empresa encontrada</div>';
    return;
  }
  
  resultsContainer.innerHTML = empresasFiltradas.map(empresa => `
    <div class="search-item" onclick="toggleEmpresaSelection(${empresa.id}, '${empresa.nome}', '${empresa.codigo}', '${empresa.tributacao_nome}')">
      <input type="checkbox" ${selectedEmpresas && selectedEmpresas.has(empresa.id) ? 'checked' : ''} onchange="event.stopPropagation()">
      <div class="search-item-info">
        <div class="search-item-name">${empresa.nome}</div>
        <div class="search-item-details">Código: ${empresa.codigo} | Tributação: ${empresa.tributacao_nome}</div>
      </div>
    </div>
  `).join('');
}

// Função de busca (mantida para compatibilidade)
async function searchEmpresas() {
  filtrarEmpresasVinculacao();
}

// ================================
// FUNCIONALIDADE DE TAREFAS
// ================================

// Carregar todas as tarefas ao inicializar
async function carregarTodasTarefasVinculacao() {
  try {
    const response = await fetch('/tarefas/api/tarefas?search=&limit=1000');
    const data = await response.json();
    todasTarefasVinculacao = data.tarefas;
    filtrarTarefasVinculacao();
  } catch (error) {
    console.error('Erro ao carregar tarefas:', error);
    const resultsContainer = document.getElementById('tarefaResults');
    if (resultsContainer) {
      resultsContainer.innerHTML = '<div class="error-text">Erro ao carregar tarefas</div>';
    }
  }
}

// Filtrar tarefas conforme digita
function filtrarTarefasVinculacao() {
  const searchTerm = document.getElementById('tarefaSearch').value.toLowerCase();
  const resultsContainer = document.getElementById('tarefaResults');
  
  if (!resultsContainer) return;
  
  const tarefasFiltradas = todasTarefasVinculacao.filter(tarefa => 
    tarefa.nome.toLowerCase().includes(searchTerm) || 
    tarefa.tipo.toLowerCase().includes(searchTerm) ||
    tarefa.setor_nome.toLowerCase().includes(searchTerm) ||
    tarefa.tributacao_nome.toLowerCase().includes(searchTerm)
  );
  
  if (tarefasFiltradas.length === 0) {
    resultsContainer.innerHTML = '<div class="no-results">Nenhuma tarefa encontrada</div>';
    return;
  }
  
  resultsContainer.innerHTML = tarefasFiltradas.map(tarefa => `
    <div class="search-item" onclick="toggleTarefaSelection(${tarefa.id}, '${tarefa.nome}', '${tarefa.tipo}', '${tarefa.setor_nome}', '${tarefa.tributacao_nome}')">
      <input type="checkbox" ${selectedTarefas && selectedTarefas.has(tarefa.id) ? 'checked' : ''} onchange="event.stopPropagation()">
      <div class="search-item-info">
        <div class="search-item-name">${tarefa.nome}</div>
        <div class="search-item-details">Tipo: ${tarefa.tipo} | Setor: ${tarefa.setor_nome} | Tributação: ${tarefa.tributacao_nome}</div>
      </div>
    </div>
  `).join('');
}

// Função de busca (mantida para compatibilidade)
async function searchTarefas() {
  filtrarTarefasVinculacao();
}

// ================================
// FUNCIONALIDADE DE DASHBOARD
// ================================

// Carregar todas as empresas para o dashboard
async function carregarTodasEmpresasDashboard() {
  try {
    const response = await fetch('/api/empresas/search?q=');
    const data = await response.json();
    window.todasEmpresas = data;
    filtrarEmpresasDashboard();
  } catch (error) {
    console.error('Erro ao carregar empresas:', error);
  }
}

// Carregar todas as tarefas para o dashboard
async function carregarTodasTarefasDashboard() {
  try {
    const response = await fetch('/api/tarefas/search?q=');
    const data = await response.json();
    window.todasTarefas = data;
    filtrarTarefasDashboard();
  } catch (error) {
    console.error('Erro ao carregar tarefas:', error);
  }
}

// Filtrar empresas no dashboard
function filtrarEmpresasDashboard() {
  const query = document.getElementById('empresa-search').value.toLowerCase();
  const results = document.getElementById('empresa-results');
  
  if (!results || !window.todasEmpresas) return;
  
  const empresasFiltradas = window.todasEmpresas.filter(empresa => 
    empresa.nome.toLowerCase().includes(query) || 
    empresa.codigo.toLowerCase().includes(query)
  );
  
  results.innerHTML = '';
  if (empresasFiltradas.length > 0) {
    empresasFiltradas.forEach(empresa => {
      const item = document.createElement('div');
      item.className = 'search-result-item';
      item.innerHTML = `
        <div class="result-info">
          <strong>${empresa.nome}</strong>
          <small>${empresa.codigo}</small>
        </div>
      `;
      item.onclick = () => selectEmpresa(empresa);
      results.appendChild(item);
    });
  } else {
    results.innerHTML = '<div class="search-result-item">Nenhuma empresa encontrada</div>';
  }
  results.style.display = 'block';
}

// Filtrar tarefas no dashboard
function filtrarTarefasDashboard() {
  const query = document.getElementById('tarefa-search').value.toLowerCase();
  const results = document.getElementById('tarefa-results');
  
  if (!results || !window.todasTarefas) return;
  
  const tarefasFiltradas = window.todasTarefas.filter(tarefa => 
    tarefa.nome.toLowerCase().includes(query) || 
    tarefa.tipo.toLowerCase().includes(query)
  );
  
  results.innerHTML = '';
  if (tarefasFiltradas.length > 0) {
    tarefasFiltradas.forEach(tarefa => {
      const item = document.createElement('div');
      item.className = 'search-result-item';
      item.innerHTML = `
        <div class="result-info">
          <strong>${tarefa.nome}</strong>
          <small>${tarefa.tipo}</small>
        </div>
      `;
      item.onclick = () => selectTarefa(tarefa);
      results.appendChild(item);
    });
  } else {
    results.innerHTML = '<div class="search-result-item">Nenhuma tarefa encontrada</div>';
  }
  results.style.display = 'block';
}

// ================================
// INICIALIZAÇÃO
// ================================

// Inicializar funcionalidades quando a página carrega
document.addEventListener('DOMContentLoaded', function() {
  // Verificar se estamos na página de vinculação
  if (document.getElementById('empresaSearch') && document.getElementById('empresaResults')) {
    carregarTodasEmpresasVinculacao();
  }
  
  if (document.getElementById('tarefaSearch') && document.getElementById('tarefaResults')) {
    carregarTodasTarefasVinculacao();
  }
  
  // Verificar se estamos no dashboard
  if (document.getElementById('empresa-search') && document.getElementById('empresa-results')) {
    carregarTodasEmpresasDashboard();
  }
  
  if (document.getElementById('tarefa-search') && document.getElementById('tarefa-results')) {
    carregarTodasTarefasDashboard();
  }
});

// ================================
// EXPOSIÇÃO DE FUNÇÕES
// ================================

// Expor funções globalmente
window.carregarTodasEmpresasVinculacao = carregarTodasEmpresasVinculacao;
window.carregarTodasTarefasVinculacao = carregarTodasTarefasVinculacao;
window.filtrarEmpresasVinculacao = filtrarEmpresasVinculacao;
window.filtrarTarefasVinculacao = filtrarTarefasVinculacao;
window.carregarTodasEmpresasDashboard = carregarTodasEmpresasDashboard;
window.carregarTodasTarefasDashboard = carregarTodasTarefasDashboard;
window.filtrarEmpresasDashboard = filtrarEmpresasDashboard;
window.filtrarTarefasDashboard = filtrarTarefasDashboard;
