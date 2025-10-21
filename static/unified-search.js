/**
 * Sistema de Busca Unificado
 * Componente moderno para busca de empresas, tarefas, colaboradores e setores
 */

class UnifiedSearch {
    constructor(container, options = {}) {
        this.container = typeof container === 'string' ? document.querySelector(container) : container;
        this.options = {
            type: 'empresa', // empresa, tarefa, colaborador, setor
            multiple: true,
            placeholder: 'Digite para buscar...',
            minLength: 2,
            debounceMs: 300,
            cacheTime: 5 * 60 * 1000, // 5 minutos
            maxResults: 20,
            showFilters: true,
            allowClear: true,
            ...options
        };
        
        this.cache = new Map();
        this.selectedItems = new Set();
        this.currentPage = 1;
        this.totalPages = 1;
        this.isLoading = false;
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
            <div class="unified-search-wrapper">
                <div class="unified-search-input-container">
                    <div class="search-input-group">
                        <i class="fas fa-search search-icon"></i>
                        <input 
                            type="text" 
                            class="unified-search-input" 
                            placeholder="${this.options.placeholder}"
                            autocomplete="off"
                        >
                        <div class="search-indicators">
                            <span class="selected-count">0 selecionados</span>
                            ${this.options.allowClear ? '<button class="clear-all-btn" title="Limpar seleção">×</button>' : ''}
                        </div>
                    </div>
                    
                    <div class="unified-search-dropdown" style="display: none;">
                        ${this.options.showFilters ? this.createFiltersHTML() : ''}
                        
                        <div class="search-results-container">
                            <div class="search-results-list"></div>
                            <div class="search-loading" style="display: none;">
                                <i class="fas fa-spinner fa-spin"></i> Carregando...
                            </div>
                            <div class="search-no-results" style="display: none;">
                                <i class="fas fa-search"></i> Nenhum resultado encontrado
                            </div>
                        </div>
                        
                        <div class="search-pagination" style="display: none;">
                            <button class="prev-page" disabled>‹ Anterior</button>
                            <span class="page-info">Página 1 de 1</span>
                            <button class="next-page" disabled>Próxima ›</button>
                        </div>
                    </div>
                </div>
                
                <div class="selected-items-container">
                    <div class="selected-items-list"></div>
                </div>
                
                <input type="hidden" class="selected-values" value="">
            </div>
        `;
        
        // Cache dos elementos DOM
        this.elements = {
            input: this.container.querySelector('.unified-search-input'),
            dropdown: this.container.querySelector('.unified-search-dropdown'),
            resultsList: this.container.querySelector('.search-results-list'),
            loading: this.container.querySelector('.search-loading'),
            noResults: this.container.querySelector('.search-no-results'),
            selectedCount: this.container.querySelector('.selected-count'),
            selectedItemsList: this.container.querySelector('.selected-items-list'),
            selectedValues: this.container.querySelector('.selected-values'),
            clearBtn: this.container.querySelector('.clear-all-btn'),
            pagination: this.container.querySelector('.search-pagination'),
            prevBtn: this.container.querySelector('.prev-page'),
            nextBtn: this.container.querySelector('.next-page'),
            pageInfo: this.container.querySelector('.page-info')
        };
    }
    
    createFiltersHTML() {
        const filterOptions = {
            empresa: [
                { key: 'ativo', label: 'Apenas ativas' },
                { key: 'tributacao', label: 'Por tributação' }
            ],
            tarefa: [
                { key: 'tipo', label: 'Por tipo' },
                { key: 'setor', label: 'Por setor' }
            ],
            colaborador: [
                { key: 'ativo', label: 'Apenas ativos' },
                { key: 'setor', label: 'Por setor' }
            ],
            setor: [
                { key: 'ativo', label: 'Apenas ativos' }
            ]
        };
        
        const filters = filterOptions[this.options.type] || [];
        
        if (filters.length === 0) return '';
        
        return `
            <div class="search-filters">
                <div class="filter-input-group">
                    <input type="text" class="filter-input" placeholder="Filtrar resultados...">
                </div>
                <div class="filter-options">
                    ${filters.map(filter => `
                        <label class="filter-option">
                            <input type="checkbox" data-filter="${filter.key}">
                            <span>${filter.label}</span>
                        </label>
                    `).join('')}
                </div>
            </div>
        `;
    }
    
    bindEvents() {
        // Input events
        this.elements.input.addEventListener('input', (e) => this.handleInput(e));
        this.elements.input.addEventListener('focus', () => this.showDropdown());
        this.elements.input.addEventListener('blur', (e) => this.handleBlur(e));
        this.elements.input.addEventListener('keydown', (e) => this.handleKeydown(e));
        
        // Clear button
        if (this.elements.clearBtn) {
            this.elements.clearBtn.addEventListener('click', () => this.clearAll());
        }
        
        // Pagination
        if (this.elements.prevBtn) {
            this.elements.prevBtn.addEventListener('click', () => this.previousPage());
        }
        if (this.elements.nextBtn) {
            this.elements.nextBtn.addEventListener('click', () => this.nextPage());
        }
        
        // Filter events
        const filterInput = this.container.querySelector('.filter-input');
        if (filterInput) {
            filterInput.addEventListener('input', (e) => this.handleFilterInput(e));
        }
        
        const filterCheckboxes = this.container.querySelectorAll('[data-filter]');
        filterCheckboxes.forEach(checkbox => {
            checkbox.addEventListener('change', () => this.applyFilters());
        });
        
        // Click outside to close
        document.addEventListener('click', (e) => {
            if (!this.container.contains(e.target)) {
                this.hideDropdown();
            }
        });
    }
    
    handleInput(e) {
        const query = e.target.value.trim();
        
        // Clear debounce timer
        if (this.debounceTimer) {
            clearTimeout(this.debounceTimer);
        }
        
        // Show dropdown if there's a query
        if (query.length >= this.options.minLength) {
            this.debounceTimer = setTimeout(() => {
                this.search(query);
            }, this.options.debounceMs);
        } else {
            this.hideDropdown();
        }
    }
    
    handleBlur(e) {
        // Delay hiding to allow clicks on results
        setTimeout(() => {
            if (!this.container.contains(document.activeElement)) {
                this.hideDropdown();
            }
        }, 150);
    }
    
    handleKeydown(e) {
        const results = this.container.querySelectorAll('.search-result-item');
        const currentActive = this.container.querySelector('.search-result-item.active');
        
        switch (e.key) {
            case 'ArrowDown':
                e.preventDefault();
                this.navigateResults(results, currentActive, 'down');
                break;
            case 'ArrowUp':
                e.preventDefault();
                this.navigateResults(results, currentActive, 'up');
                break;
            case 'Enter':
                e.preventDefault();
                if (currentActive) {
                    this.selectItem(currentActive.dataset);
                }
                break;
            case 'Escape':
                this.hideDropdown();
                this.elements.input.blur();
                break;
        }
    }
    
    navigateResults(results, currentActive, direction) {
        if (results.length === 0) return;
        
        // Remove current active
        if (currentActive) {
            currentActive.classList.remove('active');
        }
        
        let newIndex = 0;
        if (currentActive) {
            const currentIndex = Array.from(results).indexOf(currentActive);
            newIndex = direction === 'down' 
                ? (currentIndex + 1) % results.length
                : (currentIndex - 1 + results.length) % results.length;
        }
        
        results[newIndex].classList.add('active');
        results[newIndex].scrollIntoView({ block: 'nearest' });
    }
    
    async search(query, page = 1) {
        if (this.isLoading) return;
        
        this.isLoading = true;
        this.currentPage = page;
        this.showLoading();
        
        try {
            const cacheKey = `${this.options.type}_${query}_${page}`;
            
            // Check cache first
            if (this.cache.has(cacheKey)) {
                const cached = this.cache.get(cacheKey);
                if (Date.now() - cached.timestamp < this.options.cacheTime) {
                    this.displayResults(cached.data);
                    this.isLoading = false;
                    return;
                }
            }
            
            // Build API URL
            const params = new URLSearchParams({
                q: query,
                page: page,
                limit: this.options.maxResults,
                ...this.getActiveFilters()
            });
            
            const response = await fetch(`/api/search/${this.options.type}?${params}`, {
                credentials: 'same-origin',
                headers: {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json'
                }
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.success) {
                // Cache the results
                this.cache.set(cacheKey, {
                    data: data,
                    timestamp: Date.now()
                });
                
                this.displayResults(data);
            } else {
                throw new Error(data.message || 'Erro na busca');
            }
            
        } catch (error) {
            console.error('Search error:', error);
            this.showError('Erro ao buscar. Tente novamente.');
        } finally {
            this.isLoading = false;
        }
    }
    
    getActiveFilters() {
        const filters = {};
        const checkboxes = this.container.querySelectorAll('[data-filter]:checked');
        
        checkboxes.forEach(checkbox => {
            filters[checkbox.dataset.filter] = 'true';
        });
        
        return filters;
    }
    
    displayResults(data) {
        this.hideLoading();
        
        if (!data.results || data.results.length === 0) {
            this.showNoResults();
            return;
        }
        
        this.totalPages = Math.ceil(data.total / this.options.maxResults);
        this.updatePagination();
        
        const resultsHTML = data.results.map(item => this.createResultItemHTML(item)).join('');
        this.elements.resultsList.innerHTML = resultsHTML;
        
        // Bind click events to results
        this.elements.resultsList.querySelectorAll('.search-result-item').forEach(item => {
            item.addEventListener('click', () => this.selectItem(item.dataset));
        });
        
        this.elements.resultsList.style.display = 'block';
    }
    
    createResultItemHTML(item) {
        const isSelected = this.selectedItems.has(item.id.toString());
        const selectedClass = isSelected ? 'selected' : '';
        
        return `
            <div class="search-result-item ${selectedClass}" data-id="${item.id}" data-name="${item.nome}">
                <div class="result-content">
                    <div class="result-main">
                        <span class="result-name">${item.nome}</span>
                        ${item.descricao ? `<span class="result-description">${item.descricao}</span>` : ''}
                    </div>
                    <div class="result-meta">
                        ${item.tipo ? `<span class="result-type">${item.tipo}</span>` : ''}
                        ${item.setor ? `<span class="result-sector">${item.setor}</span>` : ''}
                        ${item.status ? `<span class="result-status status-${item.status}">${item.status}</span>` : ''}
                    </div>
                </div>
                <div class="result-actions">
                    ${isSelected ? '<i class="fas fa-check selected-icon"></i>' : ''}
                </div>
            </div>
        `;
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
        this.updateSelectedCount();
        this.triggerChangeEvent();
    }
    
    updateSelectedItems() {
        const itemsHTML = Array.from(this.selectedItems).map(id => {
            // Find item data from current results or cache
            const item = this.findItemById(id);
            if (!item) return '';
            
            return `
                <div class="selected-item" data-id="${id}">
                    <span class="selected-item-name">${item.nome}</span>
                    <button class="remove-item-btn" data-id="${id}">×</button>
                </div>
            `;
        }).join('');
        
        this.elements.selectedItemsList.innerHTML = itemsHTML;
        
        // Bind remove events
        this.elements.selectedItemsList.querySelectorAll('.remove-item-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.removeItem(e.target.dataset.id);
            });
        });
    }
    
    findItemById(id) {
        // Try to find in current results
        const currentResult = this.elements.resultsList.querySelector(`[data-id="${id}"]`);
        if (currentResult) {
            return {
                id: currentResult.dataset.id,
                nome: currentResult.dataset.name
            };
        }
        
        // Try to find in cache
        for (const [key, cached] of this.cache.entries()) {
            if (cached.data.results) {
                const item = cached.data.results.find(r => r.id.toString() === id);
                if (item) return item;
            }
        }
        
        return null;
    }
    
    removeItem(id) {
        this.selectedItems.delete(id);
        this.updateSelectedItems();
        this.updateSelectedCount();
        this.triggerChangeEvent();
    }
    
    clearAll() {
        this.selectedItems.clear();
        this.elements.input.value = '';
        this.updateSelectedItems();
        this.updateSelectedCount();
        this.hideDropdown();
        this.triggerChangeEvent();
    }
    
    updateSelectedCount() {
        const count = this.selectedItems.size;
        this.elements.selectedCount.textContent = `${count} selecionado${count !== 1 ? 's' : ''}`;
        
        // Update hidden input
        this.elements.selectedValues.value = Array.from(this.selectedItems).join(',');
    }
    
    updatePagination() {
        if (this.totalPages <= 1) {
            this.elements.pagination.style.display = 'none';
            return;
        }
        
        this.elements.pagination.style.display = 'flex';
        this.elements.prevBtn.disabled = this.currentPage <= 1;
        this.elements.nextBtn.disabled = this.currentPage >= this.totalPages;
        this.elements.pageInfo.textContent = `Página ${this.currentPage} de ${this.totalPages}`;
    }
    
    previousPage() {
        if (this.currentPage > 1) {
            const query = this.elements.input.value.trim();
            this.search(query, this.currentPage - 1);
        }
    }
    
    nextPage() {
        if (this.currentPage < this.totalPages) {
            const query = this.elements.input.value.trim();
            this.search(query, this.currentPage + 1);
        }
    }
    
    showDropdown() {
        this.elements.dropdown.style.display = 'block';
    }
    
    hideDropdown() {
        this.elements.dropdown.style.display = 'none';
    }
    
    showLoading() {
        this.elements.loading.style.display = 'block';
        this.elements.resultsList.style.display = 'none';
        this.elements.noResults.style.display = 'none';
    }
    
    hideLoading() {
        this.elements.loading.style.display = 'none';
    }
    
    showNoResults() {
        this.elements.noResults.style.display = 'block';
        this.elements.resultsList.style.display = 'none';
        this.elements.pagination.style.display = 'none';
    }
    
    showError(message) {
        this.elements.noResults.innerHTML = `<i class="fas fa-exclamation-triangle"></i> ${message}`;
        this.showNoResults();
    }
    
    triggerChangeEvent() {
        const event = new CustomEvent('unifiedSearchChange', {
            detail: {
                selectedItems: Array.from(this.selectedItems),
                selectedValues: this.elements.selectedValues.value,
                type: this.options.type
            }
        });
        this.container.dispatchEvent(event);
    }
    
    // Public API methods
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
        this.updateSelectedCount();
    }
    
    clearCache() {
        this.cache.clear();
    }
    
    destroy() {
        // Clean up event listeners and cache
        this.cache.clear();
        if (this.debounceTimer) {
            clearTimeout(this.debounceTimer);
        }
    }
}

// Auto-initialize components with data-unified-search attribute
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('[data-unified-search]').forEach(container => {
        const options = JSON.parse(container.dataset.unifiedSearch || '{}');
        new UnifiedSearch(container, options);
    });
});

// Export for manual initialization
window.UnifiedSearch = UnifiedSearch;
