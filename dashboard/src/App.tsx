import React, { useState, useEffect, useRef } from 'react';

interface SystemStatus {
    status: string;
    version: string;
    services?: {
        ai_engine?: string;
        bot_engine?: string;
        bitget?: string;
    };
    debug_error?: string;
}

const App: React.FC = () => {
    const [balance, setBalance] = useState<string>("$0,000.00");
    const [trades, setTrades] = useState<any[]>([]);
    const [logs, setLogs] = useState<any[]>([]);
    const [performance, setPerformance] = useState({ longs_open: 0, shorts_open: 0, daily_pnl: "+0.0%" });
    const [systemStatus, setSystemStatus] = useState<SystemStatus>({ status: "online", version: "0.0.1" });
    const [activeTab, setActiveTab] = useState<string>('Chats');
    const [chats, setChats] = useState<string[]>([]);
    const [selectedChat, setSelectedChat] = useState<string>('');
    const [settings, setSettings] = useState({
        risk_strategy: "CAP",
        max_leverage: "10",
        max_total_margin_usdt: "300",
        max_trade_margin_usdt: "100",
        risk_per_trade_pct: "1.0",
        monitored_chats: "RETO 1k a 10k"
    });
    const [telegramDialogs, setTelegramDialogs] = useState<any[]>([]);
    const [isScanning, setIsScanning] = useState(false);
    const scrollRef = useRef<HTMLDivElement>(null);

    const scrollToBottom = () => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    };

    useEffect(() => {
        scrollToBottom();
    }, [logs]);

    const scanTelegram = async () => {
        setIsScanning(true);
        try {
            const res = await fetch('http://localhost:8000/api/telegram/dialogs');
            if (res.ok) {
                const data = await res.json();
                setTelegramDialogs(data);
            }
        } catch (e) {
            console.error("Scan failed", e);
        } finally {
            setIsScanning(false);
        }
    };

    const toggleChat = async (id: number, name: string, isMonitored: boolean) => {
        try {
            const res = await fetch('http://localhost:8000/api/telegram/toggle', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    id,
                    name,
                    action: isMonitored ? 'remove' : 'add'
                })
            });
            if (res.ok) {
                setTelegramDialogs(prev => prev.map(d => 
                    d.id === id ? { ...d, is_monitored: !isMonitored } : d
                ));
                fetchData();
            }
        } catch (e) {
            console.error("Toggle failed", e);
        }
    };

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
                const chatData: string[] = await chatRes.json();
                // Filtrar Global y Mensajes Guardados para una vista más limpia
                const filtered = chatData.filter(c => c !== 'Global' && !c.includes('(ME)'));
                setChats(filtered);
                if (!selectedChat && (filtered.length > 0)) {
                    setSelectedChat(filtered[0]);
                }
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
        const interval = setInterval(fetchData, 2000);
        return () => clearInterval(interval);
    }, [selectedChat]);

    useEffect(() => {
        if (activeTab === 'Management') scanTelegram();
    }, [activeTab]);

    const updateSetting = async (name: string, value: string) => {
        setSettings(prev => ({ ...prev, [name]: value }));
        await fetch('http://localhost:8000/api/settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ [name]: value })
        });
    };

    return (
        <div className="min-h-screen bg-[#050505] font-body text-[#EAECEF] selection:bg-[#1FDDC4]/30">
            <nav className="sticky top-0 z-50 flex items-center justify-between w-full border-b border-white/5 bg-[#0B0E11]/80 backdrop-blur-md px-6 py-4">
                <div className="flex items-center gap-3">
                    <div className="h-6 w-6 bg-[#1FDDC4] rounded-sm rotate-45 flex items-center justify-center shadow-[0_0_15px_rgba(31,221,196,0.4)]">
                        <div className="h-3 w-3 bg-black rounded-full"></div>
                    </div>
                    <div className="font-outfit text-xl font-black tracking-tighter text-[#1FDDC4] uppercase">
                        Bitget <span className="text-white/90">Trading Agent</span>
                        <span className="text-[10px] opacity-40 ml-2 font-mono">v{systemStatus.version}</span>
                    </div>
                </div>
                <div className="hidden items-center gap-8 md:flex">
                    <StatusBadge label="AI CORE" active={systemStatus?.services?.ai_engine === 'online'} />
                    <StatusBadge label="BOT ENGINE" active={systemStatus?.services?.bot_engine === 'online'} />
                    <StatusBadge label="BITGET CONN" active={systemStatus?.services?.bitget === 'online'} />
                </div>
                <div className="flex items-center gap-4">
                    <div className="h-8 w-8 overflow-hidden rounded-full border border-outline-variant">
                        <img alt="Profile" src="https://lh3.googleusercontent.com/aida-public/AB6AXuCLZbEd7w7KZpAI6yBRbIeO6SFOnJ810aT-AxSQUa-e9oxLZT1RWHDi7v62VIYnWANWkzAMuDT9jDWtNIEpd126HdB04VSs4UzB-9i40Ngiw6idHVVlVa08BJutwoP9WsdfRTFLblIxhINITdlf5cUiNUcj9SHIwPuDQSANvdMQwj-AGWQdXaTxX1tKzoz_bsXp_sIkjscZIf4mQf80ceIlVp_qIBiKRvzZrvkjpttu671h_DjYRa00RLMeScudJWhZuKPcinhOQVY" />
                    </div>
                </div>
            </nav>

            <div className="flex min-h-screen">
                <aside className="fixed left-0 top-16 hidden h-[calc(100vh-64px)] w-64 flex-col border-r border-white/5 bg-[#0B0E11] py-8 lg:flex">
                    <div className="px-6 space-y-8">
                        <MiniStat label="LONGs ACTIVOS" value={performance.longs_open.toString()} />
                        <MiniStat label="SHORTs ACTIVOS" value={performance.shorts_open.toString()} />
                    </div>
                    <nav className="flex-1 mt-12 space-y-1">
                        <NavLink icon="grid_view" label="Dashboard" active={activeTab === 'Chats'} onClick={() => setActiveTab('Chats')} />
                        <NavLink icon="settings_input_component" label="Configuración" active={activeTab === 'Management'} onClick={() => setActiveTab('Management')} />
                    </nav>
                </aside>

                <main className="mx-auto w-full max-w-[1600px] flex-1 p-8 lg:ml-64">
                    <header className="mb-12 flex justify-between items-end">
                        <div className="space-y-1">
                            <span className="text-[#848E9C] text-[10px] font-bold uppercase tracking-[0.2em] font-mono">ACCOUNT_SUMMARY / EQUITY</span>
                            <h1 className="bitget-glow font-mono text-5xl font-extrabold tracking-tighter text-[#1FDDC4] md:text-7xl">{balance}</h1>
                        </div>
                        <a 
                            href="https://www.bitget.com/es/futures/usdt/BTCUSDT" 
                            target="_blank" 
                            rel="noopener noreferrer"
                            className="group flex items-center gap-4 bg-[#1FDDC4] hover:bg-[#1FDDC4]/90 text-black px-6 py-4 rounded-sm transition-all shadow-[0_0_20px_rgba(31,221,196,0.3)] hover:scale-[1.02] active:scale-95"
                        >
                            <div className="text-right">
                                <div className="text-[10px] font-mono font-black uppercase leading-none opacity-60">BITGET</div>
                                <div className="text-[14px] font-mono font-black uppercase">FUTUROS_DIRECTO</div>
                            </div>
                            <span className="material-symbols-outlined text-[24px] group-hover:translate-x-1 transition-transform">open_in_new</span>
                        </a>
                    </header>

                    <div className="space-y-8 transition-all duration-500">
                        {/* Secciones de Trading y Analytics eliminadas por solicitud de usuario */}

                        {activeTab === 'Chats' && (
                            <div className="grid grid-cols-12 gap-8 h-[800px]">
                                <div className="col-span-12 lg:col-span-5 flex flex-col space-y-6">
                                    <div className="space-y-4">
                                        <h2 className="font-mono text-sm font-bold tracking-[0.3em] text-[#848E9C] uppercase mb-4 flex items-center gap-2">
                                            <span className="material-symbols-outlined text-[18px]">forum</span>
                                            CHATS Y RAZONAMIENTO IA
                                        </h2>
                                        <div className="grid grid-cols-2 gap-2 max-h-[180px] overflow-y-auto pr-2 custom-scrollbar">
                                            {chats.map(c => (
                                                <button 
                                                    key={c} 
                                                    onClick={() => setSelectedChat(c)} 
                                                    className={`px-4 py-3 rounded-sm text-[9px] font-mono font-bold uppercase transition-all border text-left leading-tight break-words ${selectedChat === c ? 'bg-[#1FDDC4] text-black border-[#1FDDC4] shadow-[0_0_15px_rgba(31,221,196,0.2)]' : 'bg-white/5 border-white/10 text-[#848E9C] hover:border-white/30'}`}
                                                >
                                                    {c}
                                                </button>
                                            ))}
                                        </div>
                                    </div>
                                    <div ref={scrollRef} className="flex-1 glass-panel terminal-glow p-6 overflow-y-auto custom-scrollbar border-[#1FDDC4]/10 bg-[#1FDDC4]/2">
                                        {logs.filter((l:any) => selectedChat === 'Global' || l.source === selectedChat).map((log: any, i: number) => (
                                            <div key={i} className="mb-6 last:mb-0 space-y-2 border-l-2 border-white/5 pl-4 hover:border-[#1FDDC4]/40 transition-colors">
                                                <div className="flex justify-between items-center">
                                                    <span className="text-[9px] font-mono text-[#1FDDC4] font-bold opacity-80">[{new Date(log.timestamp).toLocaleTimeString()}]</span>
                                                    <span className="text-[8px] px-2 py-0.5 rounded-sm bg-[#1FDDC4]/10 text-[#1FDDC4] uppercase font-mono font-black">{log.source}</span>
                                                </div>
                                                <p className="text-[13px] leading-relaxed text-[#EAECEF] font-medium tracking-tight">{log.message}</p>
                                            </div>
                                        ))}
                                        {logs.length === 0 && <div className="h-full flex flex-col items-center justify-center opacity-20 font-mono text-xs gap-3">
                                            <span className="material-symbols-outlined animate-pulse text-3xl">terminal</span>
                                            LISTENING_FOR_SIGNALS...
                                        </div>}
                                    </div>
                                </div>
                                <div className="col-span-12 lg:col-span-7 overflow-y-auto pr-2 custom-scrollbar">
                                    <h2 className="font-mono text-sm font-bold tracking-[0.3em] text-[#848E9C] uppercase mb-6 flex items-center gap-2">
                                        <div className="h-1 w-4 bg-[#1FDDC4]"></div>
                                        MONITOREO_DE_ORDENES / {selectedChat}
                                    </h2>
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pb-12">
                                        {trades.filter((t: any) => selectedChat === 'Global' || t.source === selectedChat).map((t: any, i: number) => (
                                            <TradeCard key={i} {...t} showSource={selectedChat === 'Global'} onTradeClosed={fetchData} />
                                        ))}
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* Analytics Engine eliminado */}

                        {activeTab === 'Management' && (
                            <div className="space-y-12">
                                <ChatManagementPanel 
                                    settings={settings} 
                                    onUpdate={updateSetting} 
                                    telegramDialogs={telegramDialogs}
                                    isScanning={isScanning}
                                    scanTelegram={scanTelegram}
                                    toggleChat={toggleChat}
                                />
                                <div className="pt-8 border-t border-white/5">
                                    <TradingRulesPanel settings={settings} onUpdate={updateSetting} />
                                </div>
                            </div>
                        )}
                    </div>
                </main>
            </div>
        </div>
    );
};

const ChatManagementPanel = ({ settings, onUpdate, telegramDialogs, isScanning, scanTelegram, toggleChat }: any) => {
    const [inputValue, setInputValue] = useState("");
    const chatsList = settings.monitored_chats ? settings.monitored_chats.split(',').map((s: string) => s.trim()).filter(Boolean) : [];

    const handleAddManual = () => {
        if (!inputValue) return;
        if (!chatsList.includes(inputValue)) {
            const newList = [...chatsList, inputValue].join(', ');
            onUpdate('monitored_chats', newList);
        }
        setInputValue("");
    };

    return (
        <div className="animate-in fade-in slide-in-from-bottom-4 duration-500 space-y-8">
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="font-mono text-2xl font-black uppercase tracking-tight text-white mb-1 bitget-glow">Bitget_Messenger</h2>
                    <p className="text-[10px] text-[#848E9C] font-mono uppercase tracking-widest">SIGNAL_SURVEILLANCE_MODULE / V2.4</p>
                </div>
                <button 
                    onClick={scanTelegram}
                    disabled={isScanning}
                    className={`flex items-center gap-2 px-8 py-3.5 rounded-sm font-mono font-black text-[11px] transition-all border uppercase ${isScanning ? 'bg-white/5 border-white/10 text-white/20 cursor-not-allowed' : 'bg-[#1FDDC4] text-black border-[#1FDDC4] hover:shadow-[0_0_20px_rgba(31,221,196,0.4)]'}`}
                >
                    <span className={`material-symbols-outlined text-[16px] ${isScanning ? 'animate-spin' : ''}`}>sync_alt</span>
                    {isScanning ? 'SCANNING_CHATS...' : 'REFRESH_DIALOGS'}
                </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {telegramDialogs.length > 0 ? telegramDialogs.map((chat: any) => {
                    const isMonitored = chatsList.includes(chat.id?.toString()) || chatsList.includes(chat.name);
                    return (
                        <div key={chat.id} className={`glass-panel p-5 flex items-center justify-between border-transition group rounded-sm ${isMonitored ? 'border-[#1FDDC4]/40 bg-[#1FDDC4]/5 shadow-[inset_0_0_20px_rgba(31,221,196,0.05)]' : 'border-white/5 hover:border-white/10'}`}>
                            <div className="flex items-center gap-4">
                                <div className={`w-11 h-11 rounded-sm flex items-center justify-center bg-white/5 border border-white/5 ${isMonitored ? 'text-[#1FDDC4] bg-[#1FDDC4]/10 border-[#1FDDC4]/20' : 'text-[#848E9C]'}`}>
                                    <span className="material-symbols-outlined text-[20px]">
                                        {chat.type === 'Community' ? 'hub' : chat.type === 'Channel' ? 'campaign' : 'groups'}
                                    </span>
                                </div>
                                <div className="flex-1 min-w-0 pr-4">
                                    <div className="text-[11px] font-mono font-bold text-white break-words leading-tight uppercase tracking-tight">{chat.name}</div>
                                    <div className="text-[8px] text-[#848E9C] font-mono font-bold uppercase mt-1 tracking-[0.1em]">{chat.type}</div>
                                </div>
                            </div>
                            <label className="relative inline-flex items-center cursor-pointer">
                                <input 
                                    type="checkbox" 
                                    className="sr-only peer" 
                                    checked={isMonitored}
                                    onChange={() => toggleChat(chat.id, chat.name, isMonitored)}
                                />
                                <div className="w-10 h-5.5 bg-white/10 peer-focus:outline-none rounded-sm peer peer-checked:after:translate-x-full peer-checked:after:border-black after:content-[''] after:absolute after:top-[3px] after:left-[3px] after:bg-white/20 after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-[#1FDDC4] peer-checked:after:bg-black"></div>
                            </label>
                        </div>
                    );
                }) : (
                    <div className="col-span-full py-12 flex flex-col items-center justify-center opacity-20 border-2 border-dashed border-white/5 rounded-2xl">
                        <span className="material-symbols-outlined text-4xl mb-4">search_off</span>
                        <p className="text-sm font-medium italic">Haz clic en "Refrescar" para buscar tus chats</p>
                    </div>
                )}
            </div>

            <div className="glass-panel p-8 border-white/5 mt-12 bg-white/2 rounded-sm">
                <h3 className="text-[9px] font-mono font-black uppercase text-[#848E9C] mb-6 flex items-center gap-2">
                    <span className="material-symbols-outlined text-[16px]">terminal</span> MANUAL_ENDPOINT_OVERRIDE
                </h3>
                <div className="flex gap-4">
                    <input 
                        type="text" 
                        value={inputValue}
                        onChange={(e) => setInputValue(e.target.value)}
                        placeholder="INPUT_ID_OR_NAME..."
                        className="flex-1 bg-black/40 border border-white/10 rounded-sm px-6 py-4 text-[12px] font-mono text-[#1FDDC4] focus:outline-none focus:border-[#1FDDC4]/40 transition-all placeholder:opacity-20"
                    />
                    <button 
                        onClick={handleAddManual}
                        className="bg-white/5 hover:bg-white/10 border border-white/10 text-white px-10 py-4 rounded-sm font-mono font-bold text-[10px] transition-all uppercase tracking-widest"
                    >
                        LINK_CHANNEL
                    </button>
                </div>
            </div>
        </div>
    );
};


const TradingRulesPanel = ({ settings, onUpdate }: { settings: any, onUpdate: (name: string, val: string) => void }) => {
    return (
        <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
            <h2 className="font-mono flex items-center gap-3 text-sm font-bold uppercase tracking-[0.3em] text-[#848E9C] mb-8">
                <span className="material-symbols-outlined text-[#1FDDC4] bitget-glow transform scale-110">shield_with_heart</span>
                EXECUTION_SAFETY_CONSTRAINTS
            </h2>
            <div className="glass-panel rounded-sm p-8 space-y-10 border-[#1FDDC4]/10 bg-[#1FDDC4]/2">
                <div className="space-y-5">
                    <label className="text-[9px] font-mono font-bold uppercase text-[#848E9C] tracking-widest flex items-center gap-2">
                        <div className="h-0.5 w-3 bg-[#1FDDC4]/40"></div>
                        RISK_MITIGATION_STRATEGY
                    </label>
                    <div className="flex gap-3">
                        {['CAP', 'DISCARD'].map(s => (
                            <button 
                                key={s}
                                onClick={() => onUpdate('risk_strategy', s)}
                                className={`flex-1 py-4 rounded-sm font-mono font-black text-[11px] transition-all border tracking-widest ${settings.risk_strategy === s ? 'bg-[#1FDDC4] text-black border-[#1FDDC4] shadow-[0_0_15px_rgba(31,221,196,0.2)]' : 'bg-white/5 border-white/10 text-[#848E9C] hover:border-white/20'}`}
                            >
                                {s === 'CAP' ? 'LIMIT_OVERFLOW' : 'IGNORE_SIGNAL'}
                            </button>
                        ))}
                    </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-x-12 gap-y-10">
                    <RuleInput label="MAX_LEVERAGE" value={settings.max_leverage} unit="x" min="1" max="100" onChange={(v: string) => onUpdate('max_leverage', v)} />
                    <RuleInput label="TOTAL_PORTFOLIO_MARGIN" value={settings.max_total_margin_usdt} unit="USDT" min="1" max="1000" onChange={(v: string) => onUpdate('max_total_margin_usdt', v)} />
                    <RuleInput label="SINGLE_ORDER_QUOTA" value={settings.max_trade_margin_usdt} unit="USDT" min="1" max="500" onChange={(v: string) => onUpdate('max_trade_margin_usdt', v)} />
                    <RuleInput label="DYNAMIC_RISK_COEFFICIENT" value={settings.risk_per_trade_pct} unit="%" min="0.1" max="10" onChange={(v: string) => onUpdate('risk_per_trade_pct', v)} />
                </div>
            </div>
        </div>
    );
};

const RuleInput = ({ label, value, unit, min = "1", max = "500", onChange }: { label: string, value: string, unit: string, min?: string, max?: string, onChange: (v: string) => void }) => (
    <div className="space-y-4 border-b border-white/5 pb-4 last:border-0">
        <div className="flex justify-between items-center text-[9px] font-mono font-black uppercase">
            <span className="text-[#848E9C] tracking-[0.1em]">{label}</span>
            <span className="text-[#1FDDC4] bitget-glow">{value} <span className="opacity-40">{unit}</span></span>
        </div>
        <input 
            type="range" 
            min={min} 
            max={max}
            step={unit === '%' ? "0.1" : "1"}
            value={value} 
            onChange={(e) => onChange(e.target.value)}
            className="w-full h-1 bg-white/5 rounded-none appearance-none cursor-pointer accent-[#1FDDC4]" 
        />
    </div>
);

const NavLink = ({ icon, label, active = false, onClick }: { icon: string, label: string, active?: boolean, onClick?: () => void }) => (
    <button onClick={onClick} className={`flex w-full items-center gap-4 px-6 py-3.5 transition-all duration-300 relative group ${active ? 'text-[#1FDDC4] bg-[#1FDDC4]/5' : 'text-[#848E9C] hover:bg-white/5 hover:text-white/90'}`}>
        {active && <div className="absolute left-0 top-0 h-full w-1 bg-[#1FDDC4] shadow-[0_0_10px_#1FDDC4]"></div>}
        <span className={`material-symbols-outlined text-[20px] ${active ? 'bitget-glow' : 'opacity-60'}`}>{icon}</span>
        <span className="text-[13px] font-bold uppercase tracking-wider">{label}</span>
        {active && <span className="ml-auto text-[8px] font-mono opacity-40 uppercase tracking-tighter">SELECTED</span>}
    </button>
)

const StatusBadge = ({ label, active }: { label: string, active?: boolean }) => (
    <div className="flex items-center gap-3 bg-white/5 px-3 py-1.5 rounded-sm border border-white/5">
        <div className={`h-2 w-2 rounded-full ${active ? 'bg-[#1FDDC4] shadow-[0_0_8px_#1FDDC4]' : 'bg-[#F6465D] opacity-40'} ${active ? 'animate-pulse' : ''}`}></div>
        <span className="text-[9px] font-mono font-bold text-[#848E9C] uppercase tracking-widest">{label}</span>
    </div>
)

const MiniStat = ({ label, value }: { label: string, value: string }) => (
    <div className="space-y-1.5 group">
        <div className="text-[8px] font-mono font-bold text-[#848E9C] uppercase tracking-[0.2em]">{label}</div>
        <div className="font-mono font-black text-2xl text-white group-hover:text-[#1FDDC4] transition-colors">{value}</div>
        <div className="h-[2px] w-8 bg-[#1FDDC4]/20 group-hover:w-full transition-all duration-500"></div>
    </div>
)



const TradeCard = ({ id, symbol, side, entry_price, margin, tp, sl, source, leverage, status = 'open', pnl_pct = "+0.00%", showSource = false, onTradeClosed }: any) => {
    // Si leverage viene como número (ej: 5), añadimos la 'x'. Si ya tiene string (ej: '10x'), lo dejamos.
    const displayLeverage = leverage ? (String(leverage).includes('x') ? leverage : `${leverage}x`) : "10x";
    const isLong = side?.toLowerCase() === 'long';
    const isPending = status === 'pending';
    const [localTp, setLocalTp] = useState(tp);
    const [localSl, setLocalSl] = useState(sl);
    const [isSaving, setIsSaving] = useState(false);

    useEffect(() => {
        setLocalTp(tp);
        setLocalSl(sl);
    }, [tp, sl]);

    const handleClose = async () => {
        if (window.confirm(`⚠️ ADVERTENCIA: ¿Estás seguro de que deseas LIQUIDAR la posición de ${symbol} inmediatamente a mercado?`)) {
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

    const handleUpdateParams = async () => {
        if (isSaving) return;
        setIsSaving(true);
        try {
            const res = await fetch(`http://localhost:8000/api/trades/${id}/params`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ tp: localTp, sl: localSl })
            });
            const data = await res.json();
            if (data.status === 'success') {
                alert('✅ Parámetros sincronizados con el Exchange.');
            } else {
                alert('❌ Error: ' + data.message);
            }
        } catch (err) {
            alert('❌ Error de conexión.');
        } finally {
            setIsSaving(false);
        }
    };

    return (
        <div className={`glass-panel group rounded-sm p-6 transition-all relative overflow-hidden backdrop-blur-xl ${isPending ? 'border-[#F0B90B]/40 bg-[#F0B90B]/5 border-dashed border-2' : 'border-white/5 bg-[#0B0E11]/60 hover:border-[#1FDDC4]/40 terminal-glow'}`}>
            {showSource && (
                <div className="absolute top-0 right-0 px-3 py-1 bg-[#1FDDC4]/10 text-[#1FDDC4] text-[8px] font-mono font-black uppercase tracking-widest opacity-40">
                    {source || "MANUAL"}
                </div>
            )}
            
            <div className="mb-8 flex justify-between items-start">
                <div className="space-y-2">
                    <div className="font-mono text-2xl font-black tracking-tighter flex items-center gap-2 text-white">
                        {symbol}
                        <span className="text-[10px] bg-white/5 px-2 py-0.5 rounded-none font-bold text-[#848E9C]">{displayLeverage}</span>
                    </div>
                    <div className="flex gap-2">
                        <span className={`px-2 py-0.5 text-[10px] font-black rounded-none uppercase tracking-widest ${isLong ? 'bg-[#00C087]/20 text-[#00C087]' : 'bg-[#F6465D]/20 text-[#F6465D]'}`}>
                            {side}
                        </span>
                        {isPending && (
                            <span className="px-2 py-0.5 text-[10px] font-black rounded-none uppercase tracking-widest bg-[#F0B90B]/20 text-[#F0B90B] animate-pulse">
                                WAITING_PRICE
                            </span>
                        )}
                    </div>
                </div>
                <div className="text-right">
                    <div className={`font-mono text-3xl font-black tracking-tight ${isPending ? 'text-[#848E9C] opacity-20' : isLong ? 'text-[#00C087] filter drop-shadow-[0_0_10px_rgba(0,192,135,0.4)]' : 'text-[#F6465D] filter drop-shadow-[0_0_10px_rgba(246,70,93,0.4)]'}`}>
                        {isPending ? '0.00%' : pnl_pct}
                    </div>
                    <div className="text-[9px] text-[#848E9C] font-mono font-bold uppercase tracking-widest mt-1">
                        {isPending ? 'ESTIMATED_ROI' : 'REALTIME_PNL'}
                    </div>
                </div>
            </div>
            
            <div className="grid grid-cols-2 gap-6 mb-8">
                <div className="space-y-1 group/item">
                    <label className="text-[9px] text-[#848E9C] font-mono font-bold uppercase tracking-[0.2em] flex items-center gap-2">
                        <span className="material-symbols-outlined text-[14px]">login</span>
                        ENTRY
                    </label>
                    <div className="font-mono text-lg font-bold text-white/90 pl-5 border-l border-white/5">{entry_price}</div>
                </div>
                <div className="space-y-1">
                    <label className="text-[9px] text-[#848E9C] font-mono font-bold uppercase tracking-[0.2em] flex items-center gap-2">
                        <span className="material-symbols-outlined text-[14px]">payments</span>
                        MARGIN
                    </label>
                    <div className="font-mono text-lg font-bold text-white/90 pl-5 border-l border-white/5">{margin} <span className="text-[10px] opacity-40">USDT</span></div>
                </div>
            </div>

            <div className="grid grid-cols-2 gap-4 border-t border-white/5 pt-6">
                <div className="space-y-3">
                    <label className="text-[9px] text-[#00C087] font-mono font-black uppercase tracking-[0.2em] flex items-center gap-2">
                        <span className="material-symbols-outlined text-[16px]">trending_up</span>
                        TAKE_PROFIT
                    </label>
                    <div className="relative group/edit">
                        <input 
                            type="number" 
                            step="any"
                            value={localTp || ''} 
                            placeholder="0.0000"
                            onChange={(e) => setLocalTp(e.target.value)}
                            className="w-full bg-white/10 border border-white/20 rounded-none px-4 py-3 font-mono text-sm font-bold text-[#00C087] focus:outline-none focus:border-[#00C087] focus:bg-[#00C087]/10 transition-all placeholder:opacity-20 shadow-inner"
                        />
                        <span className="absolute right-3 top-1/2 -translate-y-1/2 material-symbols-outlined text-[14px] text-[#00C087] opacity-40 group-hover/edit:opacity-100 transition-opacity">edit</span>
                    </div>
                </div>
                <div className="space-y-3">
                    <label className="text-[9px] text-[#F6465D] font-mono font-black uppercase tracking-[0.2em] flex items-center gap-2">
                        <span className="material-symbols-outlined text-[16px]">trending_down</span>
                        STOP_LOSS
                    </label>
                    <div className="relative group/edit">
                        <input 
                            type="number" 
                            step="any"
                            value={localSl || ''} 
                            placeholder="0.0000"
                            onChange={(e) => setLocalSl(e.target.value)}
                            className="w-full bg-white/10 border border-white/20 rounded-none px-4 py-3 font-mono text-sm font-bold text-[#F6465D] focus:outline-none focus:border-[#F6465D] focus:bg-[#F6465D]/10 transition-all placeholder:opacity-20 shadow-inner"
                        />
                        <span className="absolute right-3 top-1/2 -translate-y-1/2 material-symbols-outlined text-[14px] text-[#F6465D] opacity-40 group-hover/edit:opacity-100 transition-opacity">edit</span>
                    </div>
                </div>
            </div>

            <div className="flex gap-3 mt-8">
                <button 
                    onClick={handleUpdateParams}
                    disabled={isSaving}
                    className="flex-[2] py-4 bg-[#1FDDC4] text-black font-mono font-black text-[11px] uppercase tracking-widest transition-all hover:bg-[#1FDDC4]/90 active:scale-95 disabled:opacity-20 flex items-center justify-center gap-3 overflow-hidden group/save"
                >
                    <span className={`material-symbols-outlined text-[18px] ${isSaving ? 'animate-spin' : 'group-hover/save:scale-110 transition-transform'}`}>{isSaving ? 'sync' : 'done_all'}</span>
                    {isSaving ? 'SYNCING...' : 'SAVE_ADJUSTMENTS'}
                </button>
                <button 
                    onClick={handleClose}
                    className="flex-1 py-4 bg-[#F6465D]/10 border border-[#F6465D]/30 text-[#F6465D] font-mono font-bold text-[10px] uppercase tracking-widest transition-all hover:bg-[#F6465D] hover:text-white active:scale-95 flex items-center justify-center gap-2 group/close"
                >
                    <span className="material-symbols-outlined text-[18px] group-hover/close:rotate-90 transition-transform">bolt</span>
                    CIERRE
                </button>
            </div>
        </div>
    );
};



export default App;
