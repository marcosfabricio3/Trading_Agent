import React, { useState, useEffect } from 'react';

interface SystemStatus {
    status: string;
    version: string;
    services?: {
        ai_engine?: string;
        bot_engine?: string;
    };
    debug_error?: string;
}

const App: React.FC = () => {
    const [balance, setBalance] = useState<string>("$0,000.00");
    const [trades, setTrades] = useState<any[]>([]);
    const [logs, setLogs] = useState<any[]>([]);
    const [performance, setPerformance] = useState({ win_rate: "0%", total_trades: 0, daily_pnl: "+0.0%" });
    const [systemStatus, setSystemStatus] = useState<SystemStatus>({ status: "online", version: "0.0.1" });
    const [activeTab, setActiveTab] = useState<string>('Chats');
    const [chats, setChats] = useState<string[]>(['Global']);
    const [selectedChat, setSelectedChat] = useState<string>('Global');
    const [settings, setSettings] = useState({
        risk_strategy: "CAP",
        max_leverage: "10",
        max_total_margin_usdt: "300",
        max_trade_margin_usdt: "100",
        risk_per_trade_pct: "1.0",
        monitored_chats: "RETO 1k a 10k"
    });

    const fetchData = async () => {
        try {
            const res = await fetch('http://localhost:8000/api/trades');
            if (res.ok) {
                const data = await res.json();
                if (data.active) setTrades(data.active);
            }
            
            const balRes = await fetch('http://localhost:8000/api/balance');
            if (balRes.ok) {
                const balData = await balRes.json();
                if (balData.balance) setBalance(`$${balData.balance.toLocaleString()}`);
            }
            
            const logRes = await fetch(`http://localhost:8000/api/logs?chat=${selectedChat}`);
            if (logRes.ok) {
                const logData = await logRes.json();
                setLogs(logData);
            }

            const chatRes = await fetch('http://localhost:8000/api/chats');
            if (chatRes.ok) {
                const chatData = await chatRes.json();
                setChats(chatData);
            }

            const perfRes = await fetch('http://localhost:8000/api/performance');
            if (perfRes.ok) {
                const perfData = await perfRes.json();
                setPerformance(perfData);
            }

            const statusRes = await fetch('http://localhost:8000/api/status');
            if (statusRes.ok) {
                const statusData = await statusRes.json();
                setSystemStatus(statusData);
            }

            // Fetch Settings once
            const setRes = await fetch('http://localhost:8000/api/settings');
            if (setRes.ok) {
                const setData = await setRes.json();
                setSettings(setData);
            }

        } catch (e) {
            console.warn("API Connection flicker...");
        }
    };

    useEffect(() => {
        fetchData();
        const interval = setInterval(fetchData, 5000);
        return () => clearInterval(interval);
    }, [selectedChat]);

    const updateSetting = async (name: string, value: string) => {
        setSettings(prev => ({ ...prev, [name]: value }));
        await fetch('http://localhost:8000/api/settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ [name]: value })
        });
    };

    return (
        <div className="min-h-screen bg-[#050505] font-body text-[#E5E2E1]">
            <nav className="sticky top-0 z-50 flex items-center justify-between w-full border-b border-[#1C1B1B] bg-[#050505] px-6 py-4">
                <div className="font-outfit text-xl font-black tracking-tighter text-[#00FF88] uppercase">
                    Trading Agent PRO <span className="text-[10px] opacity-40 ml-2">v{systemStatus.version}</span>
                </div>
                <div className="hidden items-center gap-8 md:flex">
                    <StatusBadge label="AI ENGINE" active={systemStatus?.services?.ai_engine === 'online'} />
                    <StatusBadge label="BOT ENGINE" active={systemStatus?.services?.bot_engine === 'online'} />
                </div>
                <div className="flex items-center gap-4">
                    <div className="h-8 w-8 overflow-hidden rounded-full border border-outline-variant">
                        <img alt="Profile" src="https://lh3.googleusercontent.com/aida-public/AB6AXuCLZbEd7w7KZpAI6yBRbIeO6SFOnJ810aT-AxSQUa-e9oxLZT1RWHDi7v62VIYnWANWkzAMuDT9jDWtNIEpd126HdB04VSs4UzB-9i40Ngiw6idHVVlVa08BJutwoP9WsdfRTFLblIxhINITdlf5cUiNUcj9SHIwPuDQSANvdMQwj-AGWQdXaTxX1tKzoz_bsXp_sIkjscZIf4mQf80ceIlVp_qIBiKRvzZrvkjpttu671h_DjYRa00RLMeScudJWhZuKPcinhOQVY" />
                    </div>
                </div>
            </nav>

            <div className="flex min-h-screen">
                <aside className="fixed left-0 top-16 hidden h-[calc(100vh-64px)] w-64 flex-col border-r border-[#1C1B1B] bg-[#131313] py-8 lg:flex">
                    <div className="px-6 space-y-8">
                        <MiniStat label="WIN RATE" value={performance.win_rate} />
                        <MiniStat label="TOTAL TRADES" value={performance.total_trades.toString()} />
                    </div>
                    <nav className="flex-1 mt-12 space-y-1">
                        <NavLink icon="forum" label="Chats" active={activeTab === 'Chats'} onClick={() => setActiveTab('Chats')} />
                        <NavLink icon="gavel" label="Trading Rules" active={activeTab === 'Trading Rules'} onClick={() => setActiveTab('Trading Rules')} />
                        <NavLink icon="settings_suggest" label="Gestión Chat" active={activeTab === 'Gestión Chat'} onClick={() => setActiveTab('Gestión Chat')} />
                    </nav>
                </aside>

                <main className="mx-auto w-full max-w-[1600px] flex-1 p-8 lg:ml-64">
                    <header className="mb-12 flex justify-between items-end">
                        <div className="space-y-1">
                            <span className="text-on-surface-variant text-xs font-medium uppercase tracking-widest">Available Equity</span>
                            <h1 className="emerald-glow font-outfit text-5xl font-black tracking-tighter text-on-surface md:text-7xl">{balance}</h1>
                        </div>
                        <div className="border-primary-container/20 bg-primary-container/10 flex items-center gap-2 rounded-full border px-4 py-2">
                            <span className="font-outfit font-bold text-[#00FF88]">{performance.daily_pnl}</span>
                            <span className="text-on-surface-variant text-[10px] uppercase">24h PnL</span>
                        </div>
                    </header>

                    <div className="grid grid-cols-12 gap-8">
                        <section className="col-span-12 lg:col-span-4 transition-all duration-500">
                        <section className="col-span-12 lg:col-span-4 transition-all duration-500">
                            {activeTab === 'Chats' && (
                                <>
                                    <div className="flex items-center justify-between mb-6">
                                        <h2 className="font-outfit flex items-center gap-2 text-xl font-bold uppercase">Chat Center</h2>
                                        <span className="h-2 w-2 animate-pulse rounded-full bg-[#00FF88] shadow-[0_0_10px_#00FF88]"></span>
                                    </div>
                                    
                                    {/* Selector de Chats Dinámico */}
                                    <div className="flex gap-2 mb-6 overflow-x-auto pb-2 scrollbar-hide">
                                        {chats.map(c => (
                                            <button 
                                                key={c}
                                                onClick={() => setSelectedChat(c)}
                                                className={`px-4 py-2 rounded-full text-[10px] font-bold uppercase transition-all whitespace-nowrap ${selectedChat === c ? 'bg-[#00FF88] text-[#003919]' : 'bg-white/5 border border-white/10 opacity-40 hover:opacity-100'}`}
                                            >
                                                {c}
                                            </button>
                                        ))}
                                    </div>

                                    <div className="glass-panel ai-glow h-[600px] rounded-xl p-6 space-y-8 overflow-y-auto scrollbar-hide border-[#00FF88]/20 bg-[#00FF88]/5">
                                        {logs.length > 0 ? logs.map((log: any, i: number) => (
                                            <div key={i} className="space-y-4">
                                                <div className="flex justify-between items-start">
                                                    <span className={`text-[10px] font-mono tracking-widest opacity-60 ${i === 0 ? "text-[#00FF88]" : "text-[#713fda]"}`}>
                                                        {new Date(log.timestamp).toLocaleTimeString()}
                                                    </span>
                                                    {selectedChat === 'Global' && (
                                                        <span className="text-[8px] px-1.5 py-0.5 rounded bg-white/10 uppercase opacity-40">
                                                            {log.source || "System"}
                                                        </span>
                                                    )}
                                                </div>
                                                <p className={`text-sm leading-relaxed ${log.message.includes('ERROR') ? 'text-rose-400' : 'text-on-surface/80'}`}>
                                                    {log.message}
                                                </p>
                                                <div className="h-px w-8 bg-white/10"></div>
                                            </div>
                                        )) : (
                                            <div className="flex flex-col items-center justify-center h-full opacity-20 italic text-sm">
                                                <span className="material-symbols-outlined text-4xl mb-2">cloud_off</span>
                                                No hay registros para {selectedChat}
                                            </div>
                                        )}
                                    </div>
                                </>
                            )}
                            {activeTab === 'Trading Rules' && <TradingRulesPanel settings={settings} onUpdate={updateSetting} />}
                            {activeTab === 'Gestión Chat' && <ChatManagementPanel settings={settings} onUpdate={updateSetting} />}
                        </section>
                        </section>

                        <section className="col-span-12 lg:col-span-8">
                            <div className="flex items-center justify-between mb-6">
                                <h2 className="font-outfit text-xl font-bold uppercase tracking-tight">
                                    Active Operation Center <span className="text-[#00FF88]/60 ml-2">[{selectedChat}]</span>
                                </h2>
                                <div className="text-[10px] font-bold opacity-40 uppercase">
                                    {trades.filter((t: any) => selectedChat === 'Global' || t.source === selectedChat).length} POSICIONES ACTIVAS
                                </div>
                            </div>
                            <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
                                {trades
                                    .filter((t: any) => selectedChat === 'Global' || t.source === selectedChat)
                                    .map((t: any, i: number) => (
                                        <TradeCard 
                                            key={i} 
                                            {...t} 
                                            showSource={selectedChat === 'Global'} 
                                            onTradeClosed={fetchData}
                                        />
                                    ))
                                }
                                {trades.filter((t: any) => selectedChat === 'Global' || t.source === selectedChat).length === 0 && (
                                    <div className="col-span-2 glass-panel border-dashed border-white/10 rounded-xl p-12 flex flex-col items-center justify-center opacity-20">
                                        <span className="material-symbols-outlined text-4xl mb-2">account_balance_wallet</span>
                                        <p className="text-sm italic">No hay operaciones activas para {selectedChat}</p>
                                    </div>
                                )}
                            </div>
                        </section>
                    </div>
                </main>
            </div>
        </div>
    );
};

const ChatManagementPanel = ({ settings, onUpdate }: { settings: any, onUpdate: (name: string, val: string) => void }) => {
    const [inputValue, setInputValue] = useState("");
    const [discoveredChats, setDiscoveredChats] = useState<any[]>([]);
    const [loadingDiscovery, setLoadingDiscovery] = useState(false);
    const chatsList = settings.monitored_chats ? settings.monitored_chats.split(',').map((s: string) => s.trim()).filter(Boolean) : [];

    const fetchDiscovery = async () => {
        setLoadingDiscovery(true);
        try {
            const res = await fetch('http://localhost:8000/api/discover');
            const data = await res.json();
            setDiscoveredChats(data);
        } catch (err) {
            console.error("Error fetching discovery:", err);
        } finally {
            setLoadingDiscovery(false);
        }
    };

    const addChat = () => {
        if (!inputValue) return;
        if (!chatsList.includes(inputValue)) {
            const newList = [...chatsList, inputValue].join(', ');
            onUpdate('monitored_chats', newList);
        }
        setInputValue("");
    };

    const removeChat = (name: string) => {
        const newList = chatsList.filter((c: string) => c !== name).join(', ');
        onUpdate('monitored_chats', newList);
    };

    return (
        <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
            <h2 className="font-outfit flex items-center gap-2 text-xl font-bold uppercase mb-6">
                <span className="material-symbols-outlined text-[#00FF88]">settings_suggest</span>
                Gestión Chat
            </h2>
            <div className="glass-panel rounded-xl p-6 space-y-6 border-[#00FF88]/20 bg-[#00FF88]/5">
                <div className="space-y-4">
                    <label className="text-[10px] font-bold uppercase opacity-60">Agregar Nuevo Chat</label>
                    <div className="flex gap-2">
                        <input 
                            type="text" 
                            value={inputValue}
                            onChange={(e) => setInputValue(e.target.value)}
                            placeholder="Nombre exacto del chat..."
                            className="flex-1 bg-white/5 border border-white/10 rounded-lg px-4 py-2 text-sm focus:outline-none focus:border-[#00FF88]/50"
                        />
                        <button onClick={addChat} className="bg-[#00FF88] text-[#003919] px-4 py-2 rounded-lg font-bold text-xs">AÑADIR</button>
                    </div>
                </div>

                <div className="space-y-4">
                    <label className="text-[10px] font-bold uppercase opacity-60">Chats Configurados</label>
                    <div className="space-y-2">
                        {chatsList.map((chat: string) => (
                            <div key={chat} className="flex items-center justify-between bg-white/5 border border-white/10 rounded-lg px-4 py-3">
                                <span className="text-sm font-medium">{chat}</span>
                                <button onClick={() => removeChat(chat)} className="text-rose-500 hover:text-rose-400 transition-colors">
                                    <span className="material-symbols-outlined text-sm">delete</span>
                                </button>
                            </div>
                        ))}
                    </div>
                </div>

                <div className="space-y-4 border-t border-white/5 pt-6">
                    <div className="flex justify-between items-center">
                        <label className="text-[10px] font-bold uppercase opacity-60">Descubrimiento de Chats (Real-Time)</label>
                        <button 
                            onClick={fetchDiscovery} 
                            disabled={loadingDiscovery}
                            className="text-[9px] font-bold text-[#00FF88] hover:underline disabled:opacity-30 flex items-center gap-1"
                        >
                            <span className="material-symbols-outlined text-[12px]">refresh</span>
                            {loadingDiscovery ? 'BUSCANDO...' : 'REFRESCAR CATÁLOGO'}
                        </button>
                    </div>

                    <div className="max-h-[300px] overflow-y-auto space-y-3 pr-2 scrollbar-hide">
                        {discoveredChats.length > 0 ? discoveredChats.map((chat: any) => (
                            <div key={chat.id} className="space-y-2">
                                <div className="flex items-center justify-between p-3 bg-white/5 rounded-lg border border-white/10 group">
                                    <div className="flex flex-col">
                                        <span className="text-[10px] opacity-40 font-mono">{chat.type}</span>
                                        <span className="text-sm font-bold">{chat.name}</span>
                                    </div>
                                    {!chatsList.includes(chat.name) && (
                                        <button 
                                            onClick={() => { setInputValue(chat.name); setTimeout(addChat, 100); }}
                                            className="hidden group-hover:block px-2 py-1 bg-[#00FF88]/10 text-[#00FF88] rounded text-[9px] font-bold border border-[#00FF88]/20"
                                        >
                                            + AÑADIR GRUPO
                                        </button>
                                    )}
                                </div>
                                {chat.is_forum && chat.topics?.length > 0 && (
                                    <div className="grid grid-cols-2 gap-2 pl-4">
                                        {chat.topics.map((topic: any) => (
                                            <div key={topic.id} className="flex items-center justify-between p-2 bg-white/5 rounded-md border border-white/5 group/topic">
                                                <span className="text-[11px] truncate pr-2">{topic.title}</span>
                                                {!chatsList.includes(topic.title) && (
                                                    <button 
                                                        onClick={() => { setInputValue(topic.title); setTimeout(addChat, 100); }}
                                                        className="hidden group-hover/topic:block text-[8px] font-bold text-[#00FF88] bg-[#00FF88]/10 px-1.5 py-0.5 rounded border border-[#00FF88]/20"
                                                    >
                                                        AÑADIR TEMA
                                                    </button>
                                                )}
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        )) : (
                            <div className="p-8 border border-dashed border-white/10 rounded-lg text-center opacity-30 italic text-[11px]">
                                Pulsa "REFRESCAR CATÁLOGO" para ver tus chats de Telegram
                            </div>
                        )}
                    </div>
                </div>
                
                <div className="pt-4 border-t border-white/10">
                    <p className="text-[10px] opacity-40 italic leading-relaxed">
                        * Consejo: Los temas (Topics) están dentro de comunidades. Si añades un Grupo tipo Foro, escucharás todos sus temas de forma predeterminada.
                    </p>
                </div>
            </div>
        </div>
    );
};

const TradingRulesPanel = ({ settings, onUpdate }: { settings: any, onUpdate: (name: string, val: string) => void }) => {
    return (
        <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
            <h2 className="font-outfit flex items-center gap-2 text-xl font-bold uppercase mb-6">
                <span className="material-symbols-outlined text-[#00FF88]">gavel</span>
                Trading Rules
            </h2>
            <div className="glass-panel rounded-xl p-6 space-y-8 border-[#00FF88]/20 bg-[#00FF88]/5">
                <div className="space-y-4">
                    <label className="text-[10px] font-bold uppercase opacity-60">Risk Strategy</label>
                    <div className="flex gap-2">
                        {['CAP', 'DISCARD'].map(s => (
                            <button 
                                key={s}
                                onClick={() => onUpdate('risk_strategy', s)}
                                className={`flex-1 py-3 rounded-lg font-bold text-xs transition-all ${settings.risk_strategy === s ? 'bg-[#00FF88] text-[#003919]' : 'bg-white/5 border border-white/10 opacity-40'}`}
                            >
                                {s === 'CAP' ? 'RECORTAR A LÍMITE' : 'DESCARTAR SEÑAL'}
                            </button>
                        ))}
                    </div>
                </div>

                <RuleInput label="MAX LEVERAGE" value={settings.max_leverage} unit="x" min="1" max="100" onChange={(v: string) => onUpdate('max_leverage', v)} />
                <RuleInput label="Max Total Margin" value={settings.max_total_margin_usdt} unit="USDT" min="1" max="1000" onChange={(v: string) => onUpdate('max_total_margin_usdt', v)} />
                <RuleInput label="Max Single Trade Margin" value={settings.max_trade_margin_usdt} unit="USDT" min="1" max="500" onChange={(v: string) => onUpdate('max_trade_margin_usdt', v)} />
                <RuleInput label="Default Risk/Trade" value={settings.risk_per_trade_pct} unit="%" min="0.1" max="10" onChange={(v: string) => onUpdate('risk_per_trade_pct', v)} />
            </div>
        </div>
    );
};

const RuleInput = ({ label, value, unit, min = "1", max = "500", onChange }: { label: string, value: string, unit: string, min?: string, max?: string, onChange: (v: string) => void }) => (
    <div className="space-y-2">
        <div className="flex justify-between items-center text-[10px] font-bold uppercase opacity-60">
            <span>{label}</span>
            <span className="text-[#00FF88]">{value} {unit}</span>
        </div>
        <input 
            type="range" 
            min={min} 
            max={max}
            value={value} 
            onChange={(e) => onChange(e.target.value)}
            className="w-full h-1 bg-white/10 rounded-lg appearance-none cursor-pointer accent-[#00FF88]" 
        />
    </div>
);

const NavLink = ({ icon, label, active = false, onClick }: { icon: string, label: string, active?: boolean, onClick?: () => void }) => (
    <button onClick={onClick} className={`flex w-full items-center gap-4 px-6 py-3 transition-all duration-300 ${active ? 'border-l-4 border-[#00FF88] bg-[#1C1B1B] text-[#00FF88]' : 'text-[#E5E2E1] opacity-60 hover:bg-[#1C1B1B] hover:opacity-100'}`}>
        <span className="material-symbols-outlined">{icon}</span>
        <span className="text-sm font-medium">{label}</span>
    </button>
)

const StatusBadge = ({ label, active }: { label: string, active?: boolean }) => (
    <div className="flex items-center gap-2">
        <div className={`h-1.5 w-1.5 rounded-full ${active ? 'bg-[#00FF88]' : 'bg-rose-500'}`}></div>
        <span className="text-[10px] font-bold opacity-60 uppercase">{label}</span>
    </div>
)

const MiniStat = ({ label, value }: { label: string, value: string }) => (
    <div className="space-y-1">
        <div className="text-[10px] font-bold opacity-40 uppercase">{label}</div>
        <div className="font-outfit font-black text-xl">{value}</div>
    </div>
)


const TradeCard = ({ id, symbol, side, entry_price, margin, tp, sl, source, leverage = "10x", pnl_pct = "+0.00%", showSource = false, onTradeClosed }: any) => {
    const isLong = side?.toLowerCase() === 'long';

    const handleClose = async () => {
        if (window.confirm(`¿Estás seguro de que deseas CERRAR la posición de ${symbol} inmediatamente?`)) {
            try {
                const res = await fetch(`http://localhost:8000/api/trades/${id}/close`, { method: 'POST' });
                const data = await res.json();
                if (data.status === 'success') {
                    onTradeClosed?.();
                } else {
                    alert('Error al cerrar trade: ' + data.message);
                }
            } catch (err) {
                alert('Error de conexión con la API.');
            }
        }
    };

    return (
        <div className="glass-panel group rounded-xl p-6 border-white/5 bg-white/5 transition-all hover:bg-white/10 relative overflow-hidden">
            {showSource && (
                <div className="absolute top-0 right-0 px-2 py-1 bg-white/5 text-[7px] font-bold uppercase tracking-tighter opacity-30 group-hover:opacity-100 transition-opacity">
                    ORIGEN: {source || "MANUAL"}
                </div>
            )}
            <div className="mb-6 flex justify-between items-start">
                <div>
                    <div className="font-outfit text-2xl font-black">{symbol}</div>
                    <span className={`px-2 py-0.5 text-[8px] font-bold rounded ${isLong ? 'bg-[#00FF88]/20 text-[#00FF88]' : 'bg-rose-500/20 text-rose-500'}`}>{side}</span>
                </div>
                <div className="text-right">
                    <div className={`font-mono text-lg font-bold ${isLong ? 'text-[#00FF88]' : 'text-rose-500'}`}>{pnl_pct}</div>
                </div>
            </div>
            <div className="grid grid-cols-2 gap-4 text-[10px] font-mono opacity-60">
                <div className="flex flex-col">
                    <span className="text-[8px] opacity-40">ENTRY</span>
                    {entry_price}
                </div>
                <div className="flex flex-col">
                    <span className="text-[8px] opacity-40">MARGIN</span>
                    {margin} USDT
                </div>
                <div className="flex flex-col">
                    <span className="text-[8px] opacity-40">TAKE PROFIT</span>
                    <span className="text-[#00FF88]">{tp}</span>
                </div>
                <div className="flex flex-col">
                    <span className="text-[8px] opacity-40">STOP LOSS</span>
                    <span className="text-rose-500">{sl}</span>
                </div>
                <div className="flex flex-col col-span-2 pt-2 border-t border-white/5 mt-2">
                    <span className="text-[8px] opacity-40">LEVERAGE: {leverage}</span>
                </div>
            </div>

            <button 
                onClick={handleClose}
                className="mt-6 w-full py-2 bg-rose-500/10 border border-rose-500/20 text-rose-500 text-[10px] font-bold uppercase rounded-lg hover:bg-rose-500 hover:text-white transition-all flex items-center justify-center gap-2"
            >
                <span className="material-symbols-outlined text-sm">cancel</span>
                Cerrar Emergencia
            </button>
        </div>
    );
};

export default App;
