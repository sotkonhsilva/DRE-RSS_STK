let allProcedimentos = []; // Variável global para armazenar todos os procedimentos
let filteredProcedimentos = []; // Variável global para procedimentos filtrados
let currentTags = []; // Tags globais no modal
let currentTitleTags = []; // Tags de título no modal
let activeSeedCodes = []; // Códigos das seeds ativas (lista)
let allSeeds = []; // Todas as seeds salvas

// Variáveis para ordenação
let currentSortColumn = null;
let currentSortDirection = 'asc';

function loadProcedimentos() {
    const loading = document.getElementById('loading');
    const error = document.getElementById('error');
    const tableContainer = document.getElementById('tableContainer');

    loading.style.display = 'block';
    error.style.display = 'none';
    tableContainer.style.display = 'none';

    fetch('data/ativos.json')
        .then(response => {
            if (!response.ok) {
                throw new Error('Arquivo não encontrado');
            }
            return response.json();
        })
        .then(data => {
            loading.style.display = 'none';
            allProcedimentos = data; // Armazenar todos os procedimentos
            filteredProcedimentos = data; // Inicialmente, mostrar todos

            // Aplicar ordenação padrão por data de publicação (mais recente primeiro)
            currentSortColumn = 'publicacao';
            currentSortDirection = 'desc';
            const sortedProcedimentos = sortProcedimentos(data, 'publicacao', 'desc');

            displayProcedimentos(sortedProcedimentos);
        })
        .catch(err => {
            loading.style.display = 'none';
            error.style.display = 'block';
            console.error('Erro:', err);
        });
}

function filterProcedimentos() {
    const searchTerm = document.getElementById('searchInput').value.toLowerCase().trim();

    console.log('🔍 Filtrando procedimentos...');
    console.log('📝 Termo de pesquisa:', searchTerm);
    console.log('🌱 Seeds ativas:', activeSeedCodes);

    // Primeiro filtrar por termo de pesquisa
    let filtered = allProcedimentos;

    if (searchTerm !== '') {
        filtered = allProcedimentos.filter(proc => {
            // Criar uma string com todos os campos para pesquisa
            const searchableText = [
                proc.descricao || '',
                proc.designacao_contrato || '',
                proc.entidade || '',
                proc.entidade_adjudicante || '',
                proc.plataforma_eletronica || '',
                proc.preco_base || '',
                proc.prazo_apresentacao_propostas || '',
                proc.nipc || '',
                proc.distrito || '',
                proc.concelho || '',
                proc.freguesia || '',
                proc.site || '',
                proc.email || '',
                proc.numero_procedimento || '',
                proc.prazo_execucao || '',
                proc.fundos_eu || '',
                proc.autor_nome || '',
                proc.autor_cargo || '',
                extractPublicationDate(proc.detalhes_completos) || ''
            ].join(' ').toLowerCase();

            return searchableText.includes(searchTerm);
        });

        console.log('📊 Após pesquisa por termo:', filtered.length, 'procedimentos');
    }

    // Depois filtrar por seeds ativas (deve corresponder a QUALQUER uma das seeds ativas)
    if (activeSeedCodes.length > 0) {
        const beforeSeedFilter = filtered.length;
        filtered = filtered.filter(proc => procedureMatchesSeeds(proc));
        console.log('🌱 Após filtro de seeds:', filtered.length, 'procedimentos (removidos:', beforeSeedFilter - filtered.length, ')');
    }

    filteredProcedimentos = filtered;

    // Aplicar ordenação atual se existir
    if (currentSortColumn && currentSortDirection) {
        console.log('🔄 Aplicando ordenação:', currentSortColumn, currentSortDirection);
        const sortedProcedimentos = sortProcedimentos(filteredProcedimentos, currentSortColumn, currentSortDirection);
        displayProcedimentos(sortedProcedimentos);
    } else {
        console.log('📋 Exibindo sem ordenação');
        displayProcedimentos(filteredProcedimentos);
    }
}

function clearSearch() {
    document.getElementById('searchInput').value = '';
    filteredProcedimentos = allProcedimentos;

    // Aplicar ordenação atual se existir
    if (currentSortColumn && currentSortDirection) {
        const sortedProcedimentos = sortProcedimentos(allProcedimentos, currentSortColumn, currentSortDirection);
        displayProcedimentos(sortedProcedimentos);
    } else {
        displayProcedimentos(allProcedimentos);
    }
}

function formatDeadline(deadlineStr) {
    if (!deadlineStr || deadlineStr === 'N/A') return 'N/A';

    // Procurar por padrões de data e hora
    const dateTimeMatch = deadlineStr.match(/(\d{1,2})-(\d{1,2})-(\d{4})\s+(\d{1,2}):(\d{2})/);
    if (dateTimeMatch) {
        const [, day, month, year, hour, minute] = dateTimeMatch;
        return `
            <span class="deadline-date">${day}/${month}/${year}</span>
            <span class="deadline-time">${hour}:${minute}</span>
        `;
    }

    // Se não encontrar o padrão, retornar o original
    return deadlineStr;
}

function formatPrice(priceStr) {
    if (!priceStr || priceStr === 'N/A') return 'N/A';

    // Substituir EUR por €
    return priceStr.replace(/EUR/g, '€').replace(/eur/g, '€');
}

function extractPublicationDate(detalhesCompletos) {
    if (!detalhesCompletos) return 'N/A';

    // Procurar por "Data de Envio do Anúncio: DD-MM-YYYY"
    const dateMatch = detalhesCompletos.match(/Data de Envio do Anúncio:\s*(\d{1,2}-\d{1,2}-\d{4})/);
    if (dateMatch) {
        const [, dateStr] = dateMatch;
        // Converter DD-MM-YYYY para DD/MM/YYYY
        return dateStr.replace(/-/g, '/');
    }

    return 'N/A';
}

function sortProcedimentos(procedimentos, column, direction) {
    const sortedProcedimentos = [...procedimentos];

    sortedProcedimentos.sort((a, b) => {
        let valueA, valueB;

        switch (column) {
            case 'descricao':
                valueA = (a.descricao || a.designacao_contrato || '').toLowerCase();
                valueB = (b.descricao || b.designacao_contrato || '').toLowerCase();
                break;
            case 'entidade':
                valueA = (a.entidade || a.entidade_adjudicante || '').toLowerCase();
                valueB = (b.entidade || b.entidade_adjudicante || '').toLowerCase();
                break;
            case 'plataforma':
                valueA = (a.plataforma_eletronica || '').toLowerCase();
                valueB = (b.plataforma_eletronica || '').toLowerCase();
                break;
            case 'publicacao':
                valueA = extractPublicationDate(a.detalhes_completos);
                valueB = extractPublicationDate(b.detalhes_completos);
                // Converter datas para comparação
                if (valueA !== 'N/A' && valueB !== 'N/A') {
                    const dateA = new Date(valueA.split('/').reverse().join('-'));
                    const dateB = new Date(valueB.split('/').reverse().join('-'));
                    valueA = dateA.getTime();
                    valueB = dateB.getTime();
                }
                break;
            case 'prazo':
                valueA = a.prazo_apresentacao_propostas || '';
                valueB = b.prazo_apresentacao_propostas || '';
                // Converter datas para comparação
                if (valueA && valueB) {
                    const dateA = new Date(valueA.split(' ')[0].split('-').reverse().join('-'));
                    const dateB = new Date(valueB.split(' ')[0].split('-').reverse().join('-'));
                    valueA = dateA.getTime();
                    valueB = dateB.getTime();
                }
                break;
            case 'preco':
                valueA = parseFloat((a.preco_base || '0').replace(/[^\d,]/g, '').replace(',', '.'));
                valueB = parseFloat((b.preco_base || '0').replace(/[^\d,]/g, '').replace(',', '.'));
                break;
            default:
                return 0;
        }

        if (valueA < valueB) return direction === 'asc' ? -1 : 1;
        if (valueA > valueB) return direction === 'asc' ? 1 : -1;
        return 0;
    });

    return sortedProcedimentos;
}

function handleSort(column) {
    let newDirection = 'asc';

    if (currentSortColumn === column) {
        newDirection = currentSortDirection === 'asc' ? 'desc' : 'asc';
    }

    currentSortColumn = column;
    currentSortDirection = newDirection;

    // Atualizar indicadores visuais
    updateSortIndicators();

    // Ordenar os procedimentos filtrados atuais
    const sortedProcedimentos = sortProcedimentos(filteredProcedimentos, column, newDirection);
    displayProcedimentos(sortedProcedimentos);
}

function updateSortIndicators() {
    // Remover todas as classes de ordenação
    document.querySelectorAll('.procedures-table th.sortable').forEach(th => {
        th.classList.remove('sort-asc', 'sort-desc');
    });

    // Adicionar classe apropriada ao cabeçalho ativo
    if (currentSortColumn) {
        const activeHeader = document.querySelector(`[data-sort="${currentSortColumn}"]`);
        if (activeHeader) {
            activeHeader.classList.add(currentSortDirection === 'asc' ? 'sort-asc' : 'sort-desc');
        }
    }
}

function displayProcedimentos(procedimentos) {
    const tableBody = document.getElementById('proceduresTableBody');
    const tableContainer = document.getElementById('tableContainer');

    tableBody.innerHTML = '';

    if (procedimentos.length === 0) {
        const isMobile = window.innerWidth <= 768;
        const colspan = isMobile ? 6 : 7;
        tableBody.innerHTML = `<tr><td colspan="${colspan}" style="text-align: center; padding: 2rem; color: #666;">Nenhum procedimento encontrado</td></tr>`;
        tableContainer.style.display = 'block';
        return;
    }

    procedimentos.forEach((proc, index) => {
        // Linha principal do procedimento
        const mainRow = document.createElement('tr');
        mainRow.className = 'procedure-row';
        mainRow.onclick = () => toggleRow(index);

        mainRow.innerHTML = `
            <td style="text-align: center; width: 50px;">
                <div class="expand-icon">▼</div>
            </td>
            <td style="text-align: left;">
                <div class="procedure-title">${proc.descricao || proc.designacao_contrato || 'Sem descrição'}</div>
            </td>
            <td style="text-align: left;">
                <div class="entity-name">${proc.entidade || proc.entidade_adjudicante || 'N/A'}</div>
            </td>
            <td style="text-align: left;">
                <div class="procedure-platform">${proc.plataforma_eletronica || 'N/A'}</div>
            </td>
            <td style="text-align: center;">
                <div class="publication-date">${extractPublicationDate(proc.detalhes_completos)}</div>
            </td>
            <td style="text-align: center;">
                <div class="deadline">${formatDeadline(proc.prazo_apresentacao_propostas)}</div>
            </td>
            <td style="text-align: left;">
                <div class="price">${formatPrice(proc.preco_base)}</div>
            </td>
        `;

        // Linha de detalhes (inicialmente oculta)
        const detailsRow = document.createElement('tr');
        detailsRow.className = 'details-row';
        detailsRow.id = `details-${index}`;

        const detailsCell = document.createElement('td');
        detailsCell.className = 'details-cell';
        // Ajustar colSpan baseado no tamanho da tela
        const isMobile = window.innerWidth <= 768;
        detailsCell.colSpan = isMobile ? 6 : 7;

        detailsCell.innerHTML = `
            <div class="details-grid">
                <div class="detail-group">
                    <h4>Informações da Entidade</h4>
                    <div class="detail-item">
                        <span class="detail-label">NIPC:</span>
                        <span class="detail-value">${proc.nipc || 'N/A'}</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">Distrito:</span>
                        <span class="detail-value">${proc.distrito || 'N/A'}</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">Concelho:</span>
                        <span class="detail-value">${proc.concelho || 'N/A'}</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">Freguesia:</span>
                        <span class="detail-value">${proc.freguesia || 'N/A'}</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">Site:</span>
                        <span class="detail-value">
                            ${proc.site ? `<a href="${proc.site}" target="_blank">${proc.site}</a>` : 'N/A'}
                        </span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">Email:</span>
                        <span class="detail-value">
                            ${proc.email ? `<a href="mailto:${proc.email}">${proc.email}</a>` : 'N/A'}
                        </span>
                    </div>
                </div>
                
                <div class="detail-group">
                    <h4>Detalhes do Contrato</h4>
                    <div class="detail-item">
                        <span class="detail-label">Número:</span>
                        <span class="detail-value">${proc.numero_procedimento || 'N/A'}</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">Prazo de Execução:</span>
                        <span class="detail-value">${proc.prazo_execucao || 'N/A'}</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">Fundos EU:</span>
                        <span class="detail-value">${proc.fundos_eu || 'N/A'}</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">URL do Procedimento:</span>
                        <span class="detail-value">
                            ${proc.link ? `<a href="${proc.link}" target="_blank">Ver no DRE</a>` : 'N/A'}
                        </span>
                    </div>
                </div>
                
                <div class="detail-group">
                    <h4>Informações Adicionais</h4>
                    <div class="detail-item">
                        <span class="detail-label">Autor:</span>
                        <span class="detail-value">${proc.autor_nome || 'N/A'}</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">Cargo:</span>
                        <span class="detail-value">${proc.autor_cargo || 'N/A'}</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">URL Procedimento:</span>
                        <span class="detail-value">
                            ${proc.url_procedimento ? `<a href="${proc.url_procedimento}" target="_blank">Aceder</a>` : 'N/A'}
                        </span>
                    </div>
                </div>
            </div>
        `;

        detailsRow.appendChild(detailsCell);

        tableBody.appendChild(mainRow);
        tableBody.appendChild(detailsRow);
    });

    tableContainer.style.display = 'block';

    // Atualizar indicadores de ordenação
    updateSortIndicators();
}

function toggleRow(index) {
    const detailsRow = document.getElementById(`details-${index}`);
    const mainRow = detailsRow.previousElementSibling;

    if (detailsRow.classList.contains('show')) {
        detailsRow.classList.remove('show');
        mainRow.classList.remove('expanded');
    } else {
        // Fechar todos os outros
        document.querySelectorAll('.details-row').forEach(row => {
            row.classList.remove('show');
        });
        document.querySelectorAll('.procedure-row').forEach(row => {
            row.classList.remove('expanded');
        });

        // Abrir o selecionado
        detailsRow.classList.add('show');
        mainRow.classList.add('expanded');
    }
}

// Funções para gerenciar seeds
function openSeedModal() {
    document.getElementById('seedModal').classList.add('show');
    document.getElementById('seedInput').focus();
    document.getElementById('districtSelect').value = '';
    currentTags = [];
    currentTitleTags = [];
    updateTagsDisplay();
}

function closeSeedModal() {
    document.getElementById('seedModal').classList.remove('show');
    document.getElementById('seedInput').value = '';
    document.getElementById('titleSeedInput').value = '';
    document.getElementById('districtSelect').value = '';
    currentTags = [];
    currentTitleTags = [];
    updateTagsDisplay();
}

function handleSeedInput(event, type) {
    if (event.key === 'Enter' || event.key === ',') {
        event.preventDefault();
        const inputId = type === 'global' ? 'seedInput' : 'titleSeedInput';
        const input = document.getElementById(inputId);
        const value = input.value.trim();

        if (value) {
            addTag(value, type);
            input.value = '';
        }
    }
}

function addTag(tagText, type) {
    const cleanTag = tagText.trim().toLowerCase();
    if (cleanTag) {
        if (type === 'global') {
            if (!currentTags.includes(cleanTag)) {
                currentTags.push(cleanTag);
            }
        } else {
            if (!currentTitleTags.includes(cleanTag)) {
                currentTitleTags.push(cleanTag);
            }
        }
        updateTagsDisplay();
    }
}

function removeTag(tagIndex, type) {
    if (type === 'global') {
        currentTags.splice(tagIndex, 1);
    } else {
        currentTitleTags.splice(tagIndex, 1);
    }
    updateTagsDisplay();
}

function updateTagsDisplay() {
    // Atualizar tags globais
    const globalContainer = document.getElementById('tagsContainer');
    globalContainer.innerHTML = '';
    currentTags.forEach((tag, index) => {
        const tagElement = document.createElement('div');
        tagElement.className = 'tag';
        tagElement.innerHTML = `
            ${tag}
            <button class="tag-remove" onclick="removeTag(${index}, 'global')">&times;</button>
        `;
        globalContainer.appendChild(tagElement);
    });

    // Atualizar tags de título
    const titleContainer = document.getElementById('titleTagsContainer');
    titleContainer.innerHTML = '';
    currentTitleTags.forEach((tag, index) => {
        const tagElement = document.createElement('div');
        tagElement.className = 'tag';
        tagElement.style.background = '#e3f2fd';
        tagElement.style.color = '#2a5298';
        tagElement.style.borderColor = '#2a5298';
        tagElement.innerHTML = `
            ${tag}
            <button class="tag-remove" onclick="removeTag(${index}, 'title')">&times;</button>
        `;
        titleContainer.appendChild(tagElement);
    });
}

function saveSeed() {
    // Auto-commit do texto que estiver nos inputs para evitar o erro do alerta
    const globalInput = document.getElementById('seedInput');
    const titleInput = document.getElementById('titleSeedInput');

    if (globalInput.value.trim()) {
        addTag(globalInput.value.trim(), 'global');
        globalInput.value = '';
    }

    if (titleInput.value.trim()) {
        addTag(titleInput.value.trim(), 'title');
        titleInput.value = '';
    }

    const tags = currentTags;
    const titleTags = currentTitleTags;
    const district = document.getElementById('districtSelect').value;

    if (tags.length === 0 && titleTags.length === 0 && !district) {
        alert('Adicione pelo menos uma palavra-chave ou escolha um distrito.');
        return;
    }

    const seedCode = generateSeedCode();

    // Gerar um nome baseado nas tags disponíveis
    let seedName = "";
    if (titleTags.length > 0) {
        seedName = titleTags.slice(0, 2).join(', ');
        if (titleTags.length > 2) seedName += '...';
    } else if (tags.length > 0) {
        seedName = tags.slice(0, 2).join(', ');
        if (tags.length > 2) seedName += '...';
    } else if (district) {
        seedName = "Filtro: " + district;
    }

    const newSeed = {
        code: seedCode,
        tags: tags,
        titleTags: titleTags,
        district: district,
        name: seedName || "Nova Seed",
        created: new Date().toISOString()
    };

    allSeeds.push(newSeed);
    saveSeedsToFile();

    // Mostrar modal com detalhes da seed criada
    showSeedCreatedModal(newSeed);

    closeSeedModal();
}

function generateSeedCode() {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
    let result = 'SEED';
    for (let i = 0; i < 6; i++) {
        result += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return result;
}

function saveSeedsToFile() {
    // Salvar seeds no localStorage (método principal)
    localStorage.setItem('dre_seeds', JSON.stringify(allSeeds));
    console.log('Seeds salvas no localStorage:', allSeeds.length);
}

function loadSeedsFromFile() {
    // Carregar seeds do localStorage (prioridade)
    const saved = localStorage.getItem('dre_seeds');
    if (saved) {
        try {
            allSeeds = JSON.parse(saved);
            console.log('Seeds carregadas do localStorage:', allSeeds.length);
            return;
        } catch (err) {
            console.log('Erro ao carregar seeds do localStorage:', err);
        }
    }

    // Fallback para o ficheiro JSON (se existir)
    fetch('data/seeds.json')
        .then(response => {
            if (!response.ok) {
                console.log('Ficheiro seeds.json não encontrado');
                return;
            }
            return response.json();
        })
        .then(data => {
            if (data) {
                allSeeds = data;
                console.log('Seeds carregadas do ficheiro:', allSeeds.length);
                // Salvar no localStorage para futuras sessões
                localStorage.setItem('dre_seeds', JSON.stringify(allSeeds));
            }
        })
        .catch(err => {
            console.log('Erro ao carregar seeds do ficheiro:', err);
        });
}

function searchBySeed() {
    const seedCode = document.getElementById('seedSearchInput').value.trim().toUpperCase();

    if (!seedCode) {
        alert('Digite um código de seed válido.');
        return;
    }

    const seed = allSeeds.find(s => s.code === seedCode);
    if (!seed) {
        alert('Seed não encontrada. Verifique o código e tente novamente.');
        return;
    }

    if (activeSeedCodes.includes(seedCode)) {
        alert('Esta seed já está ativa.');
        return;
    }

    activeSeedCodes.push(seedCode);
    updateActiveSeedDisplay();

    // Limpar input
    document.getElementById('seedSearchInput').value = '';

    // Aplicar filtragem das seeds primeiro, depois ordenação
    filterProcedimentos();
}

function removeActiveSeed(seedCode) {
    activeSeedCodes = activeSeedCodes.filter(c => c !== seedCode);
    updateActiveSeedDisplay();
    filterProcedimentos();
}

function clearSeedSearch() {
    activeSeedCodes = [];
    document.getElementById('seedSearchInput').value = '';
    updateActiveSeedDisplay();

    // Aplicar filtragem sem seeds, depois ordenação
    filterProcedimentos();
}

function clearActiveSeeds() {
    activeSeedCodes = [];
    document.getElementById('seedSearchInput').value = '';
    updateActiveSeedDisplay();

    // Aplicar filtragem sem seeds, depois ordenação
    filterProcedimentos();
}

function searchBySeedCode(seedCode) {
    if (!activeSeedCodes.includes(seedCode)) {
        activeSeedCodes.push(seedCode);
        updateActiveSeedDisplay();
        filterProcedimentos();
    }
    closeSeedsListModal();
}

function showAvailableSeeds() {
    showSeedsListModal();
}

function updateActiveSeedDisplay() {
    const filterContainer = document.getElementById('seedFilter');
    const activeSeedsContainer = document.getElementById('activeSeeds');

    if (activeSeedCodes.length === 0) {
        filterContainer.style.display = 'none';
        return;
    }

    filterContainer.style.display = 'block';
    activeSeedsContainer.innerHTML = '';

    activeSeedCodes.forEach(code => {
        const seed = allSeeds.find(s => s.code === code);
        if (seed) {
            const seedElement = document.createElement('div');
            seedElement.className = 'active-seed';
            const districtInfo = seed.district ? ` (${seed.district})` : '';
            seedElement.innerHTML = `
                <span>${seed.code} - ${seed.name}${districtInfo}</span>
                <button onclick="removeActiveSeed('${seed.code}')" style="background: #dc3545; color: white; border: none; padding: 0.25rem 0.5rem; border-radius: 3px; font-size: 0.75rem; cursor: pointer; margin-left: 0.5rem;">✕</button>
            `;
            activeSeedsContainer.appendChild(seedElement);
        }
    });
}

// Função para verificar se um procedimento corresponde a QUALQUER uma das seeds ativas
function procedureMatchesSeeds(procedure) {
    if (activeSeedCodes.length === 0) return true;

    // Se múltiplas seeds estão ativas, o procedimento deve corresponder a PELO MENOS UMA (OR logic)
    return activeSeedCodes.some(code => {
        const seed = allSeeds.find(s => s.code === code);
        if (!seed) return false;
        return procedureMatchesSeedDefinition(procedure, seed);
    });
}

// Função para verificar se um procedimento corresponde a uma definição de seed específica
function procedureMatchesSeedDefinition(procedure, seed) {
    // 1. Verificar Distrito (se definido na seed)
    if (seed.district && seed.district !== '') {
        const procedureDistrict = (procedure.distrito || '').toLowerCase();
        const seedDistrict = seed.district.toLowerCase();

        if (procedureDistrict !== seedDistrict) {
            return false;
        }
    }

    // 2. Extrair informações para busca
    const titleText = (procedure.descricao || procedure.designacao_contrato || '').toLowerCase();

    const otherText = [
        procedure.entidade || '',
        procedure.entidade_adjudicante || '',
        procedure.plataforma_eletronica || '',
        procedure.nipc || '',
        procedure.concelho || '',
        procedure.freguesia || '',
        procedure.autor_nome || '',
        procedure.autor_cargo || ''
    ].join(' ').toLowerCase();

    // 3. Verificar Tags
    // Se a seed tiver 'titleTags', elas DEVEM aparecer no título
    if (seed.titleTags && seed.titleTags.length > 0) {
        const titleMatch = seed.titleTags.some(tag => titleText.includes(tag.toLowerCase()));
        if (!titleMatch) return false;
    }

    // Se a seed tiver 'tags' genéricas, elas podem aparecer em qualquer lugar (inclusive título)
    if (seed.tags && seed.tags.length > 0) {
        const fullText = titleText + ' ' + otherText;
        const tagMatch = seed.tags.some(tag => fullText.includes(tag.toLowerCase()));
        return tagMatch;
    }

    // Se não tiver tags mas passou no distrito, é válido
    return true;
}

// Funções para os novos modais
function showSeedCreatedModal(seed) {
    const modal = document.createElement('div');
    modal.className = 'modal-overlay';
    modal.style.display = 'flex';
    modal.innerHTML = `
        <div class="modal" style="max-width: 500px;">
            <div class="modal-header">
                <h3 class="modal-title">✅ Seed Criada com Sucesso!</h3>
                <button class="close-btn" onclick="this.closest('.modal-overlay').remove()">&times;</button>
            </div>
            
            <div style="margin-bottom: 1.5rem;">
                <div style="margin-bottom: 1rem;">
                    <strong>Nome:</strong> ${seed.name}
                </div>
                <div style="margin-bottom: 1rem;">
                    <strong>Distrito:</strong> ${seed.district || 'Todos os distritos'}
                </div>
                <div style="margin-bottom: 1rem;">
                    <strong>Tags:</strong> ${seed.tags.join(', ')}
                </div>
                <div style="margin-bottom: 1rem;">
                    <strong>Código da Seed:</strong>
                    <div style="display: flex; align-items: center; gap: 0.5rem; margin-top: 0.5rem;">
                        <span class="seed-code" onclick="copyToClipboard('${seed.code}')" style="cursor: pointer;">${seed.code}</span>
                        <button onclick="copyToClipboard('${seed.code}')" style="background: #28a745; color: white; border: none; padding: 0.25rem 0.5rem; border-radius: 4px; font-size: 0.8rem; cursor: pointer;">Copiar</button>
                    </div>
                </div>
                <div style="background: #e3f2fd; padding: 1rem; border-radius: 6px; border-left: 4px solid #2196f3; font-size: 0.9rem; color: #1976d2;">
                    💡 Guarde este código para usar na pesquisa de seeds!
                </div>
            </div>
            
            <div class="modal-actions">
                <button class="cancel-btn" onclick="this.closest('.modal-overlay').remove()">Fechar</button>
            </div>
        </div>
    `;
    document.body.appendChild(modal);
}

function showSeedsListModal() {
    const modal = document.getElementById('seedsListModal');
    const container = document.getElementById('seedsListContainer');

    container.innerHTML = '';

    if (allSeeds.length === 0) {
        container.innerHTML = `
            <div style="text-align: center; padding: 2rem; color: #6c757d;">
                <div style="font-size: 3rem; margin-bottom: 1rem;">🌱</div>
                <h4 style="margin-bottom: 0.5rem;">Nenhuma seed criada ainda</h4>
                <p style="font-size: 0.9rem;">Crie uma nova seed usando o botão "Criar Seed" para começar a filtrar procedimentos automaticamente.</p>
            </div>
        `;
    } else {
        allSeeds.forEach((seed, index) => {
            const seedElement = document.createElement('div');
            seedElement.className = 'seed-item';

            const districtInfo = seed.district ? seed.district : 'Todos os distritos';
            const createdDate = new Date(seed.created).toLocaleDateString('pt-PT');

            seedElement.innerHTML = `
                <div class="seed-header">
                    <div class="seed-name">${seed.name}</div>
                    <div style="display: flex; gap: 0.5rem;">
                        <button class="search-btn" onclick="searchBySeedCode('${seed.code}')" style="padding: 0.25rem 0.5rem; font-size: 0.8rem;">Ativar</button>
                        <div class="seed-code" onclick="copyToClipboard('${seed.code}')" title="Clique para copiar">${seed.code}</div>
                    </div>
                </div>
                <div class="seed-details">
                    <div class="seed-detail">
                        <strong>Distrito:</strong> ${districtInfo}
                    </div>
                    <div class="seed-detail">
                        <strong>Criada:</strong> ${createdDate}
                    </div>
                    <div class="seed-detail" style="grid-column: 1 / -1;">
                        <strong>Tags (Global):</strong> ${seed.tags && seed.tags.length > 0 ? seed.tags.join(', ') : 'Nenhuma'}
                    </div>
                    ${seed.titleTags && seed.titleTags.length > 0 ? `
                    <div class="seed-detail" style="grid-column: 1 / -1; color: #2a5298;">
                        <strong>Tags (Título):</strong> ${seed.titleTags.join(', ')}
                    </div>
                    ` : ''}
                </div>
            `;

            container.appendChild(seedElement);
        });
    }

    modal.classList.add('show');
}

function closeSeedsListModal() {
    document.getElementById('seedsListModal').classList.remove('show');
}

function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showCopyFeedback('Código copiado!');
    }).catch(() => {
        // Fallback para navegadores mais antigos
        const textArea = document.createElement('textarea');
        textArea.value = text;
        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand('copy');
        document.body.removeChild(textArea);
        showCopyFeedback('Código copiado!');
    });
}

function showCopyFeedback(message) {
    const feedback = document.createElement('div');
    feedback.className = 'copy-feedback';
    feedback.textContent = message;
    document.body.appendChild(feedback);

    setTimeout(() => {
        feedback.remove();
    }, 2000);
}

// Carregar procedimentos quando a página carregar
document.addEventListener('DOMContentLoaded', function () {
    loadSeedsFromFile();
    loadProcedimentos();

    // Adicionar event listeners para ordenação
    document.querySelectorAll('.procedures-table th.sortable').forEach(th => {
        th.addEventListener('click', function () {
            const column = this.getAttribute('data-sort');
            handleSort(column);
        });
    });

    // Listener para redimensionamento da janela
    window.addEventListener('resize', function () {
        // Reajustar colSpan das linhas de detalhes existentes
        const detailsRows = document.querySelectorAll('.details-row');
        const isMobile = window.innerWidth <= 768;
        const newColSpan = isMobile ? 6 : 7;

        detailsRows.forEach(row => {
            const cell = row.querySelector('.details-cell');
            if (cell) {
                cell.colSpan = newColSpan;
            }
        });
    });
});
