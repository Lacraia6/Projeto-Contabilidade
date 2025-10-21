/**
 * Sistema de Busca Simples
 * Versão simplificada sem dependências complexas
 */

class SimpleSearch {
    constructor(container, options = {}) {
        this.container = typeof container === 'string' ? document.querySelector(container) : container;
        this.options = {
            type: 'empresa',
            multiple: true,
            placeholder: 'Digite para buscar...',
            minLength: 2,
            debounceMs: 300,
            ...options
        };
        
        this.selectedItems = new Set();
        this.debounceTimer = null;
        
        this.init();
    }
    
    init() {
        this.createHTML();
        this.bindEvents();
        this.loadInitialData();
    }
    
    createHTML() {
        const typeLabels = {
            empresa: 'Empresas',
            tarefa: 'Tarefas', 
            colaborador: 'Colaboradores',
            setor: 'Setores'
        };
        
        this.container.innerHTML = `
            <div class="simple-search-wrapper">
                <div class="search-input-container">
                    <input 
                        type="text" 
                        class="search-input" 
                        placeholder="${this.options.placeholder}"
                        autocomplete="off"
                    >
                    <div class="search-dropdown" style="display: none;">
                        <div class="search-results"></div>
                        <div class="search-loading" style="display: none;">
                            <i class="fas fa-spinner fa-spin"></i> Buscando...
                        </div>
                        <div class="search-no-results" style="display: none;">
                            <i class="fas fa-search"></i> Nenhum resultado encontrado
                        </div>
                    </div>
                </div>
                
                <div class="selected-items">
                    <div class="selected-list"></div>
                </div>
                
                <input type="hidden" class="selected-values" value="">
            </div>
        `;
        
        // Cache dos elementos
        this.elements = {
            input: this.container.querySelector('.search-input'),
            dropdown: this.container.querySelector('.search-dropdown'),
            results: this.container.querySelector('.search-results'),
            loading: this.container.querySelector('.search-loading'),
            noResults: this.container.querySelector('.search-no-results'),
            selectedList: this.container.querySelector('.selected-list'),
            selectedValues: this.container.querySelector('.selected-values')
        };
    }
    
    bindEvents() {
        this.elements.input.addEventListener('input', (e) => this.handleInput(e));
        this.elements.input.addEventListener('focus', () => this.showDropdown());
        this.elements.input.addEventListener('blur', (e) => this.handleBlur(e));
        
        // Click outside to close
        document.addEventListener('click', (e) => {
            if (!this.container.contains(e.target)) {
                this.hideDropdown();
            }
        });
    }
    
    handleInput(e) {
        const query = e.target.value.trim();
        
        if (this.debounceTimer) {
            clearTimeout(this.debounceTimer);
        }
        
        // Buscar sempre que há input (mesmo vazio)
        this.debounceTimer = setTimeout(() => {
            this.search(query);
        }, this.options.debounceMs);
    }
    
    handleBlur(e) {
        setTimeout(() => {
            if (!this.container.contains(document.activeElement)) {
                this.hideDropdown();
            }
        }, 150);
    }
    
    async search(query) {
        this.showLoading();
        
        try {
            const response = await fetch(`/api/search/${this.options.type}?q=${encodeURIComponent(query)}&limit=20`, {
                credentials: 'same-origin'
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.success) {
                this.displayResults(data.results);
            } else {
                throw new Error(data.message || 'Erro na busca');
            }
            
        } catch (error) {
            console.error('Search error:', error);
            this.showError('Erro ao buscar. Tente novamente.');
        }
    }
    
    displayResults(results) {
        this.hideLoading();
        
        if (!results || results.length === 0) {
            this.showNoResults();
            return;
        }
        
        const resultsHTML = results.map(item => {
            const isSelected = this.selectedItems.has(item.id.toString());
            return `
                <div class="search-result ${isSelected ? 'selected' : ''}" 
                     data-id="${item.id}" 
                     data-name="${item.nome}">
                    <div class="result-content">
                        <div class="result-name">${item.nome}</div>
                        ${item.descricao ? `<div class="result-desc">${item.descricao}</div>` : ''}
                        ${item.tipo ? `<div class="result-type">${item.tipo}</div>` : ''}
                    </div>
                    <div class="result-actions">
                        ${isSelected ? '<i class="fas fa-check"></i>' : '<i class="fas fa-plus"></i>'}
                    </div>
                </div>
            `;
        }).join('');
        
        this.elements.results.innerHTML = resultsHTML;
        
        // Bind click events
        this.elements.results.querySelectorAll('.search-result').forEach(item => {
            item.addEventListener('click', () => this.selectItem(item.dataset));
        });
        
        this.elements.results.style.display = 'block';
        this.elements.noResults.style.display = 'none';
    }
    
    selectItem(itemData) {
        const itemId = itemData.id;
        const itemName = itemData.name;
        
        if (this.options.multiple) {
            if (this.selectedItems.has(itemId)) {
                this.selectedItems.delete(itemId);
            } else {
                this.selectedItems.add(itemId);
            }
        } else {
            this.selectedItems.clear();
            this.selectedItems.add(itemId);
            this.hideDropdown();
        }
        
        this.updateSelectedItems();
        this.updateSelectedValues();
        this.triggerChangeEvent();
    }
    
    updateSelectedItems() {
        const itemsHTML = Array.from(this.selectedItems).map(id => {
            // Find item name from current results or use ID
            const resultItem = this.elements.results.querySelector(`[data-id="${id}"]`);
            const name = resultItem ? resultItem.dataset.name : `Item ${id}`;
            
            return `
                <div class="selected-item" data-id="${id}">
                    <span class="item-name">${name}</span>
                    <button class="remove-btn" data-id="${id}">×</button>
                </div>
            `;
        }).join('');
        
        this.elements.selectedList.innerHTML = itemsHTML;
        
        // Bind remove events
        this.elements.selectedList.querySelectorAll('.remove-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.removeItem(e.target.dataset.id);
            });
        });
    }
    
    removeItem(id) {
        this.selectedItems.delete(id);
        this.updateSelectedItems();
        this.updateSelectedValues();
        this.triggerChangeEvent();
    }
    
    updateSelectedValues() {
        this.elements.selectedValues.value = Array.from(this.selectedItems).join(',');
    }
    
    triggerChangeEvent() {
        const event = new CustomEvent('simpleSearchChange', {
            detail: {
                selectedItems: Array.from(this.selectedItems),
                selectedValues: this.elements.selectedValues.value,
                type: this.options.type
            }
        });
        this.container.dispatchEvent(event);
    }
    
    showDropdown() {
        this.elements.dropdown.style.display = 'block';
    }
    
    hideDropdown() {
        this.elements.dropdown.style.display = 'none';
    }
    
    showLoading() {
        this.elements.loading.style.display = 'block';
        this.elements.results.style.display = 'none';
        this.elements.noResults.style.display = 'none';
    }
    
    hideLoading() {
        this.elements.loading.style.display = 'none';
    }
    
    showNoResults() {
        this.elements.noResults.style.display = 'block';
        this.elements.results.style.display = 'none';
    }
    
    showError(message) {
        this.elements.noResults.innerHTML = `<i class="fas fa-exclamation-triangle"></i> ${message}`;
        this.showNoResults();
    }
    
    loadInitialData() {
        // Carregar dados iniciais quando o componente é criado
        this.search('');
    }
    
    // Public API
    getSelectedItems() {
        return Array.from(this.selectedItems);
    }
    
    getSelectedValues() {
        return this.elements.selectedValues.value;
    }
    
    setSelectedItems(items) {
        this.selectedItems.clear();
        items.forEach(id => this.selectedItems.add(id.toString()));
        this.updateSelectedItems();
        this.updateSelectedValues();
    }
    
    clear() {
        this.selectedItems.clear();
        this.elements.input.value = '';
        this.updateSelectedItems();
        this.updateSelectedValues();
        this.hideDropdown();
    }
}

// Auto-initialize
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('[data-simple-search]').forEach(container => {
        const options = JSON.parse(container.dataset.simpleSearch || '{}');
        new SimpleSearch(container, options);
    });
});

window.SimpleSearch = SimpleSearch;
