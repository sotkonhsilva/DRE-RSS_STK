'use client';

import React, { useState, useEffect, useMemo } from 'react';

// Icons as simple SVG components
const SearchIcon = () => (
    <svg xmlns="http://www.w3.org/2005/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
);

const RssIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M4 11a9 9 0 0 1 9 9"></path><path d="M4 4a16 16 0 0 1 16 16"></path><circle cx="5" cy="19" r="1"></circle></svg>
);

interface Procedimento {
    descricao?: string;
    designacao_contrato?: string;
    entidade?: string;
    entidade_adjudicante?: string;
    plataforma_eletronica?: string;
    preco_base?: string;
    prazo_apresentacao_propostas?: string;
    nipc?: string;
    distrito?: string;
    concelho?: string;
    freguesia?: string;
    site?: string;
    email?: string;
    numero_procedimento?: string;
    prazo_execucao?: string;
    fundos_eu?: string;
    autor_nome?: string;
    autor_cargo?: string;
    detalhes_completos?: string;
    link?: string;
    url_procedimento?: string;
}

interface Seed {
    code: string;
    tags: string[];
    titleTags: string[];
    district: string;
    name: string;
    created: string;
}

export default function PortalPage() {
    const [allProcedimentos, setAllProcedimentos] = useState<Procedimento[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(false);
    const [searchTerm, setSearchTerm] = useState('');
    const [seedSearchTerm, setSeedSearchTerm] = useState('');
    const [activeSeeds, setActiveSeeds] = useState<Seed[]>([]);
    const [allSeeds, setAllSeeds] = useState<Seed[]>([]);
    const [expandedRow, setExpandedRow] = useState<number | null>(null);
    const [copyStatus, setCopyStatus] = useState<string | null>(null);

    // Modal state
    const [isSeedModalOpen, setIsSeedModalOpen] = useState(false);
    const [isSeedListModalOpen, setIsSeedListModalOpen] = useState(false);

    // New Seed Form state
    const [newSeedDistrict, setNewSeedDistrict] = useState('');
    const [newSeedGlobalTags, setNewSeedGlobalTags] = useState<string[]>([]);
    const [newSeedTitleTags, setNewSeedTitleTags] = useState<string[]>([]);
    const [currentGlobalInput, setCurrentGlobalInput] = useState('');
    const [currentTitleInput, setCurrentTitleInput] = useState('');

    useEffect(() => {
        fetchData();
        loadSeeds();
    }, []);

    const fetchData = async () => {
        try {
            const response = await fetch('data/ativos.json');
            if (!response.ok) throw new Error('Falha ao carregar dados');
            const data = await response.json();
            setAllProcedimentos(data);
            setLoading(false);
        } catch (err) {
            console.error(err);
            setError(true);
            setLoading(false);
        }
    };

    const loadSeeds = async () => {
        const saved = localStorage.getItem('dre_seeds');
        let localSeeds: Seed[] = saved ? JSON.parse(saved) : [];

        try {
            const response = await fetch('data/seeds.json');
            if (response.ok) {
                const serverSeeds: Seed[] = await response.json();
                // Merge server seeds if they don't exist in local (by code)
                const merged = [...localSeeds];
                serverSeeds.forEach(ss => {
                    if (!merged.some(ls => ls.code === ss.code)) {
                        merged.push(ss);
                    }
                });
                setAllSeeds(merged);
                localStorage.setItem('dre_seeds', JSON.stringify(merged));
            } else {
                setAllSeeds(localSeeds);
            }
        } catch (err) {
            console.error("Erro ao carregar seeds do servidor:", err);
            setAllSeeds(localSeeds);
        }
    };

    const extractPublicationDate = (detalhesCompletos?: string) => {
        if (!detalhesCompletos) return '--';
        const dateMatch = detalhesCompletos.match(/Data de Envio do Anúncio:\s*(\d{1,2}-\d{1,2}-\d{4})/);
        if (dateMatch) {
            return dateMatch[1].replace(/-/g, '/');
        }
        return '--';
    };

    const procedureMatchesSeed = (proc: Procedimento, seed: Seed) => {
        if (seed.district && seed.district !== '') {
            if ((proc.distrito || '').toLowerCase() !== seed.district.toLowerCase()) {
                return false;
            }
        }
        const titleText = (proc.descricao || proc.designacao_contrato || '').toLowerCase();
        const otherText = [
            proc.entidade || '',
            proc.entidade_adjudicante || '',
            proc.plataforma_eletronica || '',
            proc.nipc || '',
            proc.concelho || '',
            proc.freguesia || ''
        ].join(' ').toLowerCase();

        if (seed.titleTags && seed.titleTags.length > 0) {
            if (!seed.titleTags.some(tag => titleText.includes(tag.toLowerCase()))) return false;
        }
        if (seed.tags && seed.tags.length > 0) {
            const fullText = titleText + ' ' + otherText;
            if (!seed.tags.some(tag => fullText.includes(tag.toLowerCase()))) return false;
        }
        return true;
    };

    const filteredProcedimentos = useMemo(() => {
        let filtered = allProcedimentos;
        if (searchTerm) {
            const term = searchTerm.toLowerCase();
            filtered = filtered.filter(proc => {
                const searchableText = [
                    proc.descricao || '',
                    proc.designacao_contrato || '',
                    proc.entidade || '',
                    proc.entidade_adjudicante || '',
                    proc.nipc || '',
                    proc.distrito || '',
                    proc.concelho || ''
                ].join(' ').toLowerCase();
                return searchableText.includes(term);
            });
        }
        if (activeSeeds.length > 0) {
            filtered = filtered.filter(proc =>
                activeSeeds.some(seed => procedureMatchesSeed(proc, seed))
            );
        }
        return [...filtered].sort((a, b) => {
            const dateA = extractPublicationDate(a.detalhes_completos);
            const dateB = extractPublicationDate(b.detalhes_completos);
            if (dateA === '--') return 1;
            if (dateB === '--') return -1;
            return new Date(dateB.split('/').reverse().join('-')).getTime() - new Date(dateA.split('/').reverse().join('-')).getTime();
        });
    }, [allProcedimentos, searchTerm, activeSeeds]);

    const handleApplySeed = (code?: string) => {
        const targetCode = (code || seedSearchTerm).toUpperCase();
        const seed = allSeeds.find(s => s.code === targetCode);
        if (seed && !activeSeeds.some(s => s.code === targetCode)) {
            setActiveSeeds([...activeSeeds, seed]);
            setSeedSearchTerm('');
        }
    };

    const saveNewSeed = () => {
        if (newSeedGlobalTags.length === 0 && newSeedTitleTags.length === 0 && !newSeedDistrict) {
            alert('Adicione pelo menos uma palavra-chave ou escolha um distrito.');
            return;
        }
        const code = `SEED${Math.random().toString(36).substring(2, 8).toUpperCase()}`;
        const newSeed: Seed = {
            code,
            tags: newSeedGlobalTags,
            titleTags: newSeedTitleTags,
            district: newSeedDistrict,
            name: newSeedTitleTags[0] || newSeedGlobalTags[0] || "Nova Semente",
            created: new Date().toISOString()
        };
        const updatedSeeds = [...allSeeds, newSeed];
        setAllSeeds(updatedSeeds);
        localStorage.setItem('dre_seeds', JSON.stringify(updatedSeeds));
        setIsSeedModalOpen(false);
        setNewSeedGlobalTags([]); setNewSeedTitleTags([]); setNewSeedDistrict('');
    };

    const handleCopyRss = (url: string) => {
        navigator.clipboard.writeText(url);
        setCopyStatus(url);
        setTimeout(() => setCopyStatus(null), 2000);
    };

    return (
        <div className="dashboard-container">
            <header className="mb-12 border-b border-[#1a1a1a] pb-8">
                <h1 className="text-4xl font-black tracking-tighter mb-2 italic">DRE<span className="text-amber-500">MONITOR</span></h1>
                <p className="text-slate-500 text-xs font-bold uppercase tracking-widest">Sistema Avançado de Monitorização de Procedimentos</p>
            </header>

            <section className="mb-12">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="main-card border-amber-500/20 bg-amber-500/[0.02]">
                        <div className="flex items-center gap-3 mb-4">
                            <div className="bg-amber-500 p-2 rounded">
                                <RssIcon />
                            </div>
                            <div>
                                <div className="text-xs font-black uppercase tracking-widest text-amber-500">Sincronização RSS</div>
                                <div className="text-lg font-bold">Subscrever Feeds</div>
                            </div>
                        </div>
                        <p className="text-slate-400 text-xs mb-6 leading-relaxed">
                            Receba notificações instantâneas no seu cliente de email ou leitor de RSS favorito sempre que novos procedimentos forem publicados.
                        </p>
                        <div className="space-y-3">
                            <div className="flex flex-col xl:flex-row gap-2">
                                <button
                                    className="pro-btn-primary flex-1 py-3 flex items-center justify-center gap-2"
                                    onClick={() => handleCopyRss('https://sotkonhsilva.github.io/DRE-RSS_STK/RSS/feed_rss_procedimentos.xml')}
                                >
                                    {copyStatus === 'https://sotkonhsilva.github.io/DRE-RSS_STK/RSS/feed_rss_procedimentos.xml' ? 'Copiado!' : 'Feed Principal'}
                                </button>
                                <button
                                    className="pro-btn-secondary flex-1 py-3 flex items-center justify-center gap-2 border-amber-500/30 text-amber-500"
                                    onClick={() => handleCopyRss('https://sotkonhsilva.github.io/DRE-RSS_STK/RSS/feed_filtros_seeds.xml')}
                                >
                                    {copyStatus === 'https://sotkonhsilva.github.io/DRE-RSS_STK/RSS/feed_filtros_seeds.xml' ? 'Copiado!' : 'Feed Filtrado (Seeds)'}
                                </button>
                            </div>
                            <div className="text-[9px] text-slate-600 font-mono text-center pt-2">
                                Clique para copiar o link e adicionar ao Outlook
                            </div>
                        </div>
                    </div>

                    <div className="main-card border-blue-500/20">
                        <div className="detail-title text-blue-400 mb-4">Como usar no Outlook?</div>
                        <div className="space-y-3 text-[11px] text-slate-400">
                            <div className="flex gap-3">
                                <span className="bg-slate-800 text-white w-5 h-5 flex items-center justify-center rounded-full flex-shrink-0">1</span>
                                <span>Copie o link do feed acima clicando no botão amarelo.</span>
                            </div>
                            <div className="flex gap-3">
                                <span className="bg-slate-800 text-white w-5 h-5 flex items-center justify-center rounded-full flex-shrink-0">2</span>
                                <span>No Outlook, clique com o botão direito na pasta <strong>"Feeds RSS"</strong>.</span>
                            </div>
                            <div className="flex gap-3">
                                <span className="bg-slate-800 text-white w-5 h-5 flex items-center justify-center rounded-full flex-shrink-0">3</span>
                                <span>Selecione <strong>"Adicionar um Novo Feed RSS"</strong>.</span>
                            </div>
                            <div className="flex gap-3">
                                <span className="bg-slate-800 text-white w-5 h-5 flex items-center justify-center rounded-full flex-shrink-0">4</span>
                                <span>Cole o URL (Ctrl+V) e clique em <strong>"Adicionar"</strong>.</span>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            <section className="mb-12">
                <div className="section-title">Parâmetros de Pesquisa</div>
                <div className="pro-search-section grid grid-cols-1 md:grid-cols-12 gap-4">
                    <div className="md:col-span-8 flex gap-3">
                        <input
                            className="pro-input"
                            placeholder="Pesquisar objeto, NIF ou entidade..."
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                        />
                    </div>
                    <div className="md:col-span-4 flex gap-2">
                        <button className="pro-btn-primary flex-1" onClick={() => { }}>Filtrar</button>
                        <button className="pro-btn-secondary" onClick={() => setSearchTerm('')}>Reset</button>
                    </div>

                    <div className="md:col-span-12 mt-4 pt-4 border-t border-[#1a1a1a] flex gap-4 items-center">
                        <input
                            className="pro-input max-w-xs"
                            placeholder="Código da Semente (Seed)"
                            value={seedSearchTerm}
                            onChange={(e) => setSeedSearchTerm(e.target.value)}
                        />
                        <button className="pro-btn-primary" onClick={() => handleApplySeed()}>Aplicar Seed</button>
                        <button className="pro-btn-secondary" onClick={() => setIsSeedListModalOpen(true)}>Catálogo</button>
                        <button className="pro-btn-secondary ml-auto border-amber-500/30 text-amber-500" onClick={() => setIsSeedModalOpen(true)}>+ Criar Seed</button>
                    </div>
                </div>
            </section>

            {activeSeeds.length > 0 && (
                <div className="flex gap-2 mb-6">
                    {activeSeeds.map(s => (
                        <div key={s.code} className="bg-amber-500 text-black px-3 py-1 rounded text-[10px] font-black tracking-widest flex items-center gap-2">
                            {s.code}
                            <button onClick={() => setActiveSeeds(activeSeeds.filter(x => x.code !== s.code))}>✕</button>
                        </div>
                    ))}
                </div>
            )}

            <section>
                <div className="section-title">Procedimentos Ativos (Real-time)</div>
                <div className="main-card">
                    {loading ? (
                        <div className="text-center py-20 text-slate-600 font-bold uppercase tracking-widest text-xs animate-pulse">Sincronizando base de dados...</div>
                    ) : (
                        <table className="data-table">
                            <thead>
                                <tr>
                                    <th style={{ width: '40px' }}>#</th>
                                    <th>Entidade Adjudicante ↓</th>
                                    <th style={{ width: '120px' }}>NIF ↓</th>
                                    <th style={{ width: '120px' }}>Publicação ↓</th>
                                    <th style={{ width: '200px' }}>Valor Contratual ↓</th>
                                    <th style={{ width: '140px' }}>Limite ↓</th>
                                    <th style={{ width: '60px' }}></th>
                                </tr>
                            </thead>
                            <tbody>
                                {filteredProcedimentos.length === 0 ? (
                                    <tr><td colSpan={7} className="text-center py-20 text-slate-700">Nenhum dado encontrado para os filtros atuais.</td></tr>
                                ) : (
                                    filteredProcedimentos.map((proc, idx) => (
                                        <React.Fragment key={idx}>
                                            <tr className="group">
                                                <td className="text-slate-600 font-bold text-[10px]">{idx + 1}</td>
                                                <td>
                                                    <div className="primary-text text-[11px] mb-1 leading-tight">{proc.entidade || 'N/A'}</div>
                                                    <div className="text-[10px] text-slate-500 line-clamp-1">{proc.descricao || proc.designacao_contrato}</div>
                                                </td>
                                                <td className="numeric-cell text-slate-400">{proc.nipc || '--'}</td>
                                                <td className="numeric-cell text-slate-500">{extractPublicationDate(proc.detalhes_completos)}</td>
                                                <td className="accent-text numeric-cell">{proc.preco_base || '--'}</td>
                                                <td className="numeric-cell text-rose-500/80 font-bold">{proc.prazo_apresentacao_propostas?.split(' ')[0] || '--'}</td>
                                                <td className="text-right">
                                                    <button
                                                        className="expand-row-btn"
                                                        onClick={() => setExpandedRow(expandedRow === idx ? null : idx)}
                                                    >
                                                        {expandedRow === idx ? '▲' : '▼'}
                                                    </button>
                                                </td>
                                            </tr>
                                            {expandedRow === idx && (
                                                <tr>
                                                    <td colSpan={7} className="details-panel">
                                                        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                                                            <div className="detail-subgroup">
                                                                <div className="detail-title">Informação Adicional</div>
                                                                <div className="space-y-3">
                                                                    <div><span className="detail-label">NIPC</span><div className="detail-value">{proc.nipc || '--'}</div></div>
                                                                    <div><span className="detail-label">Localização</span><div className="detail-value">{proc.concelho}, {proc.distrito}</div></div>
                                                                    <div><span className="detail-label">Freguesia</span><div className="detail-value">{proc.freguesia || '--'}</div></div>
                                                                    <div><span className="detail-label">N.º Procedimento</span><div className="detail-value">{proc.numero_procedimento}</div></div>
                                                                </div>
                                                            </div>
                                                            <div className="detail-subgroup">
                                                                <div className="detail-title">Execução e Fundos</div>
                                                                <div className="space-y-3">
                                                                    <div><span className="detail-label">Prazo de Execução</span><div className="detail-value">{proc.prazo_execucao}</div></div>
                                                                    <div><span className="detail-label">Fundos Comunitários</span><div className="detail-value">{proc.fundos_eu}</div></div>
                                                                    {(proc.site || proc.email) && (
                                                                        <div>
                                                                            <span className="detail-label">Contactos</span>
                                                                            <div className="detail-value text-[10px] break-all">
                                                                                {proc.site && <div className="text-blue-400">{proc.site}</div>}
                                                                                {proc.email && <div className="text-blue-400">{proc.email}</div>}
                                                                            </div>
                                                                        </div>
                                                                    )}
                                                                </div>
                                                            </div>
                                                            <div className="detail-subgroup items-center flex flex-col gap-4">
                                                                <a href={proc.link} target="_blank" className="pro-btn-primary w-full text-center py-4">Ver Anúncio Oficial (DRE)</a>
                                                                {proc.url_procedimento && (
                                                                    <a href={proc.url_procedimento} target="_blank" className="pro-btn-secondary w-full text-center py-4 border-amber-500/30 text-amber-500 hover:bg-amber-500 hover:text-black">Aceder ao Procedimento</a>
                                                                )}
                                                            </div>
                                                        </div>
                                                    </td>
                                                </tr>
                                            )}
                                        </React.Fragment>
                                    ))
                                )}
                            </tbody>
                        </table>
                    )}
                </div>
            </section>

            {/* Modal Components */}
            {isSeedModalOpen && (
                <div className="fixed inset-0 bg-black/90 flex items-center justify-center p-4 z-50">
                    <div className="main-card max-w-lg w-full">
                        <div className="detail-title mb-6 flex justify-between">
                            <span>Nova Configuração de Semente</span>
                            <button onClick={() => setIsSeedModalOpen(false)}>✕</button>
                        </div>
                        <div className="space-y-6">
                            <div>
                                <label className="detail-label">Distrito</label>
                                <select className="pro-input" value={newSeedDistrict} onChange={(e) => setNewSeedDistrict(e.target.value)}>
                                    <option value="">Nacional</option>
                                    {['Aveiro', 'Beja', 'Braga', 'Lisboa', 'Porto', 'Setúbal'].map(d => <option key={d} value={d}>{d}</option>)}
                                </select>
                            </div>
                            <div>
                                <label className="detail-label">Palavras-chave</label>
                                <input className="pro-input" onKeyDown={(e) => {
                                    if (e.key === 'Enter') {
                                        setNewSeedGlobalTags([...newSeedGlobalTags, (e.target as HTMLInputElement).value]);
                                        (e.target as HTMLInputElement).value = '';
                                    }
                                }} />
                                <div className="flex flex-wrap gap-2 mt-2">
                                    {newSeedGlobalTags.map(t => <span key={t} className="bg-slate-800 px-2 py-1 rounded text-[9px] uppercase">{t}</span>)}
                                </div>
                            </div>
                            <div className="flex gap-4 pt-4">
                                <button className="pro-btn-primary flex-1" onClick={saveNewSeed}>Gerar Código</button>
                                <button className="pro-btn-secondary flex-1" onClick={() => setIsSeedModalOpen(false)}>Cancelar</button>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {isSeedListModalOpen && (
                <div className="fixed inset-0 bg-black/95 flex items-center justify-center p-4 z-50">
                    <div className="main-card max-w-2xl w-full max-h-[80vh] overflow-y-auto">
                        <div className="detail-title mb-6 flex justify-between">
                            <span>Catálogo de Sementes Locais</span>
                            <button onClick={() => setIsSeedListModalOpen(false)}>✕</button>
                        </div>
                        <div className="space-y-4">
                            {allSeeds.map(s => (
                                <div key={s.code} className="border border-[#1a1a1a] p-4 flex justify-between items-center rounded">
                                    <div>
                                        <div className="accent-text text-sm">{s.code}</div>
                                        <div className="text-[10px] text-slate-500 uppercase">{s.tags.join(' • ') || 'Sem Tags'} | {s.district || 'Nacional'}</div>
                                    </div>
                                    <button className="pro-btn-primary text-[9px]" onClick={() => { handleApplySeed(s.code); setIsSeedListModalOpen(false); }}>Ativar</button>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
