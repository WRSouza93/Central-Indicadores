// Sistema de construção de dashboards
let dashboardConfig = {
    layout: 'grid',
    widgets: []
};

let widgetAtual = null;

function initDashboardBuilder() {
    const areaConstrucao = document.getElementById('areaConstrucao');
    
    // Configurar drag and drop
    configurarDragDrop();
    
    // Configurar área de construção
    areaConstrucao.addEventListener('dragover', function(e) {
        e.preventDefault();
        areaConstrucao.classList.add('drag-over');
    });
    
    areaConstrucao.addEventListener('dragleave', function(e) {
        if (!areaConstrucao.contains(e.relatedTarget)) {
            areaConstrucao.classList.remove('drag-over');
        }
    });
    
    areaConstrucao.addEventListener('drop', function(e) {
        e.preventDefault();
        areaConstrucao.classList.remove('drag-over');
        
        const widgetData = JSON.parse(e.dataTransfer.getData('text/plain'));
        adicionarWidget(widgetData, e.clientX, e.clientY);
    });
}

function configurarDragDrop() {
    const widgets = document.querySelectorAll('.widget-item');
    
    widgets.forEach(widget => {
        widget.addEventListener('dragstart', function(e) {
            const widgetData = {
                tipo: this.dataset.tipo,
                indicadorId: this.dataset.indicadorId,
                nome: this.dataset.nome,
                cor: this.dataset.cor,
                icone: this.dataset.icone
            };
            
            e.dataTransfer.setData('text/plain', JSON.stringify(widgetData));
        });
    });
}

function adicionarWidget(widgetData, x, y) {
    const areaConstrucao = document.getElementById('areaConstrucao');
    
    // Limpar mensagem inicial se existir
    if (areaConstrucao.querySelector('.text-muted')) {
        areaConstrucao.innerHTML = '';
    }
    
    // Criar elemento do widget
    const widgetElement = criarElementoWidget(widgetData);
    
    // Adicionar ao dashboard
    areaConstrucao.appendChild(widgetElement);
    
    // Adicionar à configuração
    dashboardConfig.widgets.push({
        id: Date.now(),
        tipo: widgetData.tipo,
        indicador_id: widgetData.indicadorId,
        posicao: dashboardConfig.widgets.length,
        configuracao: {}
    });
    
    // Configurar widget se necessário
    if (widgetData.tipo !== 'kpi') {
        configurarWidget(widgetElement, widgetData);
    }
}

function criarElementoWidget(widgetData) {
    const div = document.createElement('div');
    div.className = 'col-md-6 col-lg-4 mb-3 dashboard-widget-container';
    div.draggable = true;
    
    let conteudo = '';
    
    switch(widgetData.tipo) {
        case 'kpi':
            conteudo = `
                <div class="card dashboard-widget">
                    <div class="card-body text-center">
                        <div class="d-flex justify-content-between align-items-start mb-2">
                            <h6 class="card-title">
                                <i class="${widgetData.icone}" style="color: ${widgetData.cor}"></i>
                                ${widgetData.nome}
                            </h6>
                            <div class="dropdown">
                                <button class="btn btn-sm btn-outline-secondary" type="button" data-bs-toggle="dropdown">
                                    <i class="fas fa-ellipsis-v"></i>
                                </button>
                                <ul class="dropdown-menu">
                                    <li><a class="dropdown-item" href="#" onclick="configurarWidget(this)">
                                        <i class="fas fa-cog"></i> Configurar
                                    </a></li>
                                    <li><a class="dropdown-item text-danger" href="#" onclick="removerWidget(this)">
                                        <i class="fas fa-trash"></i> Remover
                                    </a></li>
                                </ul>
                            </div>
                        </div>
                        <div class="kpi-value" style="color: ${widgetData.cor}">--</div>
                        <span class="kpi-status status-neutro">
                            <i class="fas fa-minus-circle"></i> Aguardando dados
                        </span>
                    </div>
                </div>
            `;
            break;
            
        case 'grafico-linha':
            conteudo = `
                <div class="card dashboard-widget">
                    <div class="card-header d-flex justify-content-between align-items-center">
                        <h6 class="mb-0">Gráfico de Linha</h6>
                        <div class="dropdown">
                            <button class="btn btn-sm btn-outline-secondary" type="button" data-bs-toggle="dropdown">
                                <i class="fas fa-ellipsis-v"></i>
                            </button>
                            <ul class="dropdown-menu">
                                <li><a class="dropdown-item" href="#" onclick="configurarWidget(this)">
                                    <i class="fas fa-cog"></i> Configurar
                                </a></li>
                                <li><a class="dropdown-item text-danger" href="#" onclick="removerWidget(this)">
                                    <i class="fas fa-trash"></i> Remover
                                </a></li>
                            </ul>
                        </div>
                    </div>
                    <div class="card-body">
                        <canvas height="200"></canvas>
                    </div>
                </div>
            `;
            break;
            
        default:
            conteudo = `
                <div class="card dashboard-widget">
                    <div class="card-body">
                        <h6>Widget ${widgetData.tipo}</h6>
                        <p>Configurar widget...</p>
                    </div>
                </div>
            `;
    }
    
    div.innerHTML = conteudo;
    return div;
}

function configurarWidget(elemento, widgetData) {
    widgetAtual = elemento;
    
    // Abrir modal de configuração
    const modal = new bootstrap.Modal(document.getElementById('modalConfigWidget'));
    modal.show();
}

function removerWidget(elemento) {
    if (confirm('Remover este widget?')) {
        const container = elemento.closest('.dashboard-widget-container');
        container.remove();
        
        // Remover da configuração
        // Implementar lógica de remoção da configuração
    }
}

function obterConfiguracaoDashboard() {
    const widgets = document.querySelectorAll('.dashboard-widget-container');
    const config = {
        layout: 'grid',
        widgets: []
    };
    
    widgets.forEach((widget, index) => {
        // Extrair dados do widget
        const widgetConfig = {
            tipo: 'kpi', // Determinar tipo baseado no conteúdo
            posicao: index,
            configuracao: {}
        };
        
        config.widgets.push(widgetConfig);
    });
    
    return config;
}

function carregarDashboard(config) {
    if (!config || !config.widgets) return;
    
    const areaConstrucao = document.getElementById('areaConstrucao');
    areaConstrucao.innerHTML = '';
    
    config.widgets.forEach(widget => {
        // Recriar widgets baseado na configuração salva
        // Implementar lógica de recriação
    });
}

function salvarConfigWidget() {
    // Implementar salvamento da configuração do widget
    const modal = bootstrap.Modal.getInstance(document.getElementById('modalConfigWidget'));
    modal.hide();
}
