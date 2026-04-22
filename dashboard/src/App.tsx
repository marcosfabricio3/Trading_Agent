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

interface Alert {
    id: number;
    type: 'success' | 'error' | 'info';
    message: string;
}

interface ConfirmConfig {
    title: string;
    message: string;
    resolve: (value: boolean) => void;
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
    const [isRestarting, setIsRestarting] = useState(false);
    const [alerts, setAlerts] = useState<Alert[]>([]);
    const [confirmConfig, setConfirmConfig] = useState<ConfirmConfig | null>(null);
    const scrollRef = useRef<HTMLDivElement>(null);
    const autoScrollRef = useRef(true);

    const showAlert = (message: string, type: 'success' | 'error' | 'info' = 'info') => {
        const id = Date.now();
        setAlerts(prev => [...prev, { id, message, type }]);
        setTimeout(() => {
            setAlerts(prev => prev.filter(a => a.id !== id));
        }, 5000);
    };

    const showConfirm = (title: string, message: string): Promise<boolean> => {
        return new Promise((resolve) => {
            setConfirmConfig({ title, message, resolve });
        });
    };

    const scrollToBottom = () => {
        if (scrollRef.current && autoScrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    };

    const handleScroll = () => {
        if (scrollRef.current) {
            const { scrollTop, scrollHeight, clientHeight } = scrollRef.current;
            // Si está a menos de 50px del fondo, mantenemos el auto-scroll activo
            autoScrollRef.current = scrollHeight - scrollTop - clientHeight < 50;
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
        if (activeTab === 'ChatManagement') scanTelegram();
    }, [activeTab]);

    const updateSetting = async (name: string, value: string) => {
        setSettings(prev => ({ ...prev, [name]: value }));
        await fetch('http://localhost:8000/api/settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ [name]: value })
        });
    };
    
    const handleRestartBackend = async () => {
        const confirmed = await showConfirm("REINICIAR MOTOR", "♻️ ¿Deseas reiniciar el MOTOR del agente? El frontend seguirá activo, pero la conexión se perderá unos segundos.");
        if (!confirmed) return;
        
        setIsRestarting(true);
        try {
            const res = await fetch('http://localhost:8000/api/system/restart', { method: 'POST' });
            if (res.ok) {
                // Dar tiempo al backend para morir y revivir
                setTimeout(() => {
                    setIsRestarting(false);
                }, 5000);
            }
        } catch (e) {
            console.error("Restart request failed", e);
            setIsRestarting(false);
        }
    };

    return (
        <div className="h-screen flex flex-col overflow-hidden bg-[#050505] font-body text-[#EAECEF] selection:bg-[#1FDDC4]/30">
            <nav className="flex-shrink-0 z-50 flex items-center justify-between w-full border-b border-white/5 bg-[#0B0E11]/80 backdrop-blur-md px-6 py-4">
                <div className="flex items-center gap-3">
                    <div className="h-6 w-6 bg-[#1FDDC4] rounded-sm rotate-45 flex items-center justify-center shadow-[0_0_15px_rgba(31,221,196,0.4)]">
                        <div className="h-3 w-3 bg-black rounded-full"></div>
                    </div>
                    <div className="font-outfit text-xl font-black tracking-tighter text-[#1FDDC4] uppercase">
                        Bitget <span className="text-white/90">Trading Agent</span>
                        <span className="text-[10px] opacity-40 ml-2 font-mono">v{systemStatus.version}</span>
                    </div>
                </div>
                <div className="hidden items-center gap-6 md:flex">
                    <StatusBadge label="AI CORE" active={systemStatus?.services?.ai_engine === 'online'} />
                    <StatusBadge label="BOT ENGINE" active={systemStatus?.services?.bot_engine === 'online'} />
                    <StatusBadge label="BITGET CONN" active={systemStatus?.services?.bitget === 'online'} />
                </div>
            </nav>

            <div className="flex flex-1 min-h-0">
                <aside className="hidden h-full w-64 flex-shrink-0 flex-col border-r border-white/5 bg-[#0B0E11] py-8 lg:flex">
                    <div className="px-6 space-y-8">
                        <MiniStat label="LONGs ACTIVOS" value={performance.longs_open.toString()} />
                        <MiniStat label="SHORTs ACTIVOS" value={performance.shorts_open.toString()} />
                    </div>
                    <nav className="flex-1 mt-12 space-y-1">
                        <NavLink icon="grid_view" label="Dashboard" active={activeTab === 'Chats'} onClick={() => setActiveTab('Chats')} />
                        <NavLink icon="account_tree" label="Admin. Chats" active={activeTab === 'ChatManagement'} onClick={() => setActiveTab('ChatManagement')} />
                        <NavLink icon="settings_input_component" label="Configuración" active={activeTab === 'Management'} onClick={() => setActiveTab('Management')} />
                    </nav>

                    <div className="px-6 mt-auto">
                        <button 
                            onClick={handleRestartBackend}
                            disabled={isRestarting}
                            className={`w-full flex items-center justify-center gap-3 py-4 rounded-sm border font-mono text-[10px] font-black uppercase tracking-widest transition-all ${isRestarting ? 'bg-white/5 border-white/10 text-[#848E9C] cursor-not-allowed' : 'bg-[#F6465D]/10 border-[#F6465D]/20 text-[#F6465D] hover:bg-[#F6465D] hover:text-white shadow-[0_0_15px_rgba(246,70,93,0.1)] hover:shadow-[0_0_25px_rgba(246,70,93,0.3)] hover:scale-[1.02] active:scale-95'}`}
                        >
                            <span className={`material-symbols-outlined text-[18px] ${isRestarting ? 'animate-spin' : ''}`}>
                                {isRestarting ? 'sync' : 'restart_alt'}
                            </span>
                            {isRestarting ? 'REINICIANDO...' : 'ACTUALIZAR MOTOR'}
                        </button>
                    </div>
                </aside>

                <main className="mx-auto w-full max-w-[1600px] flex-1 flex flex-col p-6 min-h-0">
                    <header className="mb-6 flex-shrink-0 flex justify-between items-end">
                        <div className="space-y-1">
                            <span className="text-[#848E9C] text-[9px] font-bold uppercase tracking-[0.2em] font-mono">ACCOUNT_SUMMARY / EQUITY</span>
                            <h1 className="bitget-glow font-mono text-4xl font-extrabold tracking-tighter text-[#1FDDC4] md:text-6xl">{balance}</h1>
                        </div>
                        <a 
                            href="https://www.bitget.com/es/futures/usdt/BTCUSDT" 
                            target="_blank" 
                            rel="noopener noreferrer"
                            className="group flex items-center gap-3 bg-[#1FDDC4] hover:bg-[#1FDDC4]/90 text-black px-5 py-3 rounded-sm transition-all shadow-[0_0_15px_rgba(31,221,196,0.3)] hover:scale-[1.02] active:scale-95"
                        >
                            <div className="text-right">
                                <div className="text-[9px] font-mono font-black uppercase leading-none opacity-60">BITGET</div>
                                <div className="text-[12px] font-mono font-black uppercase">FUTUROS_DIRECTO</div>
                            </div>
                            <span className="material-symbols-outlined text-[20px] group-hover:translate-x-1 transition-transform">open_in_new</span>
                        </a>
                    </header>

                    <div className="flex-1 min-h-0 transition-all duration-500 flex flex-col">
                        {/* Secciones de Trading y Analytics eliminadas por solicitud de usuario */}

                        {activeTab === 'Chats' && (
                            <div className="grid grid-cols-12 gap-8 flex-1 min-h-0">
                                <div className="col-span-12 lg:col-span-5 flex flex-col space-y-6 min-h-0 h-full">
                                    <div className="space-y-4 flex-shrink-0">
                                        <h2 className="font-mono text-sm font-bold tracking-[0.3em] text-[#848E9C] uppercase mb-4 flex items-center gap-2">
                                            <span className="material-symbols-outlined text-[18px]">forum</span>
                                            CHATS Y RAZONAMIENTO IA
                                        </h2>
                                        <div className="grid grid-cols-2 gap-2 max-h-[140px] overflow-y-auto pr-2 custom-scrollbar">
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
                                    <div ref={scrollRef} onScroll={handleScroll} className="flex-1 min-h-0 glass-panel terminal-glow p-6 overflow-y-auto custom-scrollbar border-[#1FDDC4]/10 bg-[#1FDDC4]/2 relative">
                                        {logs.map((log: any, i: number) => (
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
                                <div className="col-span-12 lg:col-span-7 min-h-0 h-full overflow-y-auto pr-4 custom-scrollbar">
                                    <h2 className="font-mono text-sm font-bold tracking-[0.3em] text-[#848E9C] uppercase mb-6 flex items-center gap-2">
                                        <div className="h-1 w-4 bg-[#1FDDC4]"></div>
                                        MONITOREO_DE_ORDENES / {selectedChat}
                                    </h2>
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pb-12">
                                        {trades.filter((t: any) => selectedChat === 'Global' || t.source === selectedChat).map((t: any, i: number) => (
                                            <TradeCard 
                                                key={i} 
                                                {...t} 
                                                showSource={selectedChat === 'Global'} 
                                                onTradeClosed={fetchData} 
                                                showAlert={showAlert}
                                                showConfirm={showConfirm}
                                            />
                                        ))}
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* Analytics Engine eliminado */}

                        {activeTab === 'ChatManagement' && (
                            <div className="animate-in fade-in slide-in-from-bottom-4 duration-500 h-full overflow-y-auto pr-4 custom-scrollbar pb-8">
                                <ChatManagementPanel 
                                    settings={settings} 
                                    onUpdate={updateSetting} 
                                    telegramDialogs={telegramDialogs}
                                    isScanning={isScanning}
                                    scanTelegram={scanTelegram}
                                    toggleChat={toggleChat}
                                />
                            </div>
                        )}

                        {activeTab === 'Management' && (
                            <div className="animate-in fade-in slide-in-from-bottom-4 duration-500 h-full overflow-y-auto pr-4 custom-scrollbar pb-8">
                                <TradingRulesPanel settings={settings} onUpdate={updateSetting} />
                            </div>
                        )}
                    </div>
                </main>
            </div>

            {/* Custom UI Elements */}
            <ToastContainer alerts={alerts} />
            {confirmConfig && (
                <CustomConfirmModal 
                    title={confirmConfig.title}
                    message={confirmConfig.message}
                    onConfirm={() => {
                        confirmConfig.resolve(true);
                        setConfirmConfig(null);
                    }}
                    onCancel={() => {
                        confirmConfig.resolve(false);
                        setConfirmConfig(null);
                    }}
                />
            )}
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

                <div className="pt-6 border-t border-white/5 space-y-4">
                    <label className="text-[10px] font-mono font-bold uppercase text-[#848E9C] tracking-[0.2em] flex items-center gap-2">
                        <span className="material-symbols-outlined text-[16px] text-[#1FDDC4]">psychology</span>
                        AI_CUSTOM_PROMPT_CONSTRAINTS & RULES
                    </label>
                    <div className="relative group">
                        <textarea 
                            value={settings.ai_custom_rules || ""} 
                            onChange={(e) => onUpdate('ai_custom_rules', e.target.value)}
                            placeholder="Ej: 'Si el mensaje dice PARCIAL, asume siempre 50%.' o 'Ignora señales de monedas MEME como DOGE o PEPE'..."
                            className="w-full h-40 bg-black/40 border border-white/10 rounded-sm p-4 font-mono text-[11px] text-[#EAECEF] focus:outline-none focus:border-[#1FDDC4]/40 transition-all placeholder:opacity-20 custom-scrollbar resize-none"
                        />
                        <div className="absolute bottom-3 right-3 text-[8px] font-mono text-[#848E9C] opacity-40 uppercase">LIVE_SYNC_ENABLED</div>
                    </div>
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



const TradeCard = ({ id, symbol, side, entry_price, margin, tp, sl, source, leverage, status = 'open', pnl_pct = "+0.00%", showSource = false, onTradeClosed, showAlert, showConfirm }: any) => {
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
        const confirmed = await showConfirm("LIQUIDAR POSICIÓN", `⚠️ ADVERTENCIA: ¿Estás seguro de que deseas LIQUIDAR la posición de ${symbol} inmediatamente a mercado?`);
        if (confirmed) {
            try {
                const res = await fetch(`http://localhost:8000/api/trades/${id}/close`, { method: 'POST' });
                const data = await res.json();
                if (data.status === 'success') {
                    showAlert(`Posición de ${symbol} cerrada con éxito.`, 'success');
                    onTradeClosed?.();
                } else {
                    showAlert('Error al cerrar trade: ' + data.message, 'error');
                }
            } catch (err) {
                showAlert('Error de conexión con la API.', 'error');
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
                showAlert('✅ Parámetros sincronizados con el Exchange.', 'success');
            } else {
                showAlert('❌ Error: ' + data.message, 'error');
            }
        } catch (err) {
            showAlert('❌ Error de conexión.', 'error');
        } finally {
            setIsSaving(false);
        }
    };

    return (
        <div className={`glass-panel group rounded-sm p-4 transition-all relative overflow-hidden backdrop-blur-xl ${isPending ? 'border-[#F0B90B]/40 bg-[#F0B90B]/5 border-dashed border-2' : 'border-white/5 bg-[#0B0E11]/60 hover:border-[#1FDDC4]/40 terminal-glow'}`}>
            {showSource && (
                <div className="absolute top-0 right-0 px-3 py-1 bg-[#1FDDC4]/10 text-[#1FDDC4] text-[8px] font-mono font-black uppercase tracking-widest opacity-40">
                    {source || "MANUAL"}
                </div>
            )}
            
            <div className="mb-5 flex justify-between items-start">
                <div className="space-y-1">
                    <div className="font-mono text-xl font-black tracking-tighter flex items-center gap-2 text-white">
                        {symbol}
                        <span className="text-[9px] bg-white/5 px-2 py-0.5 rounded-none font-bold text-[#848E9C]">{displayLeverage}</span>
                    </div>
                    <div className="flex gap-2">
                        <span className={`px-2 py-0.5 text-[9px] font-black rounded-none uppercase tracking-widest ${isLong ? 'bg-[#00C087]/20 text-[#00C087]' : 'bg-[#F6465D]/20 text-[#F6465D]'}`}>
                            {side}
                        </span>
                        {isPending && (
                            <span className="px-2 py-0.5 text-[9px] font-black rounded-none uppercase tracking-widest bg-[#F0B90B]/20 text-[#F0B90B] animate-pulse">
                                WAITING
                            </span>
                        )}
                    </div>
                </div>
                <div className="text-right">
                    <div className={`font-mono text-2xl font-black tracking-tight ${isPending ? 'text-[#848E9C] opacity-20' : isLong ? 'text-[#00C087] filter drop-shadow-[0_0_10px_rgba(0,192,135,0.4)]' : 'text-[#F6465D] filter drop-shadow-[0_0_10px_rgba(246,70,93,0.4)]'}`}>
                        {isPending ? '0.00%' : pnl_pct}
                    </div>
                    <div className="text-[8px] text-[#848E9C] font-mono font-bold uppercase tracking-widest mt-0.5">
                        {isPending ? 'EST_ROI' : 'PNL_REALTIME'}
                    </div>
                </div>
            </div>
            
            <div className="grid grid-cols-2 gap-2 mb-5">
                <div className="space-y-0.5 group/item">
                    <label className="text-[8px] text-[#848E9C] font-mono font-bold uppercase tracking-[0.2em] flex items-center gap-1.5">
                        <span className="material-symbols-outlined text-[12px]">login</span>
                        ENTRY
                    </label>
                    <div className="font-mono text-[13px] font-bold text-white/90 pl-3 border-l border-white/10 truncate">{entry_price}</div>
                </div>
                <div className="space-y-0.5">
                    <label className="text-[8px] text-[#848E9C] font-mono font-bold uppercase tracking-[0.2em] flex items-center gap-1.5">
                        <span className="material-symbols-outlined text-[12px]">payments</span>
                        MARGIN
                    </label>
                    <div className="font-mono text-[13px] font-bold text-white/90 pl-3 border-l border-white/10 truncate">{margin} <span className="text-[8px] opacity-40">USDT</span></div>
                </div>
            </div>
 
            <div className="grid grid-cols-2 gap-3 border-t border-white/5 pt-4">
                <div className="space-y-2">
                    <label className="text-[8px] text-[#00C087] font-mono font-black uppercase tracking-[0.2em] flex items-center gap-2">
                        <span className="material-symbols-outlined text-[14px]">trending_up</span>
                        TP
                    </label>
                    <div className="relative group/edit">
                        <input 
                            type="number" 
                            step="any"
                            value={localTp || ''} 
                            placeholder="0.0000"
                            onChange={(e) => setLocalTp(e.target.value)}
                            className="w-full bg-white/10 border border-white/20 rounded-none px-3 py-2 font-mono text-xs font-bold text-[#00C087] focus:outline-none focus:border-[#00C087] focus:bg-[#00C087]/10 transition-all placeholder:opacity-20 shadow-inner"
                        />
                        <span className="absolute right-2 top-1/2 -translate-y-1/2 material-symbols-outlined text-[12px] text-[#00C087] opacity-40 group-hover/edit:opacity-100 transition-opacity">edit</span>
                    </div>
                </div>
                <div className="space-y-2">
                    <label className="text-[8px] text-[#F6465D] font-mono font-black uppercase tracking-[0.2em] flex items-center gap-2">
                        <span className="material-symbols-outlined text-[14px]">trending_down</span>
                        SL
                    </label>
                    <div className="relative group/edit">
                        <input 
                            type="number" 
                            step="any"
                            value={localSl || ''} 
                            placeholder="0.0000"
                            onChange={(e) => setLocalSl(e.target.value)}
                            className="w-full bg-white/10 border border-white/20 rounded-none px-3 py-2 font-mono text-xs font-bold text-[#F6465D] focus:outline-none focus:border-[#F6465D] focus:bg-[#F6465D]/10 transition-all placeholder:opacity-20 shadow-inner"
                        />
                        <span className="absolute right-2 top-1/2 -translate-y-1/2 material-symbols-outlined text-[12px] text-[#F6465D] opacity-40 group-hover/edit:opacity-100 transition-opacity">edit</span>
                    </div>
                </div>
            </div>
 
            <div className="flex gap-2 mt-6">
                <button
                    onClick={handleUpdateParams}
                    disabled={isSaving}
                    className="flex-[2] py-3 bg-[#1FDDC4] text-black font-mono font-black text-[10px] uppercase tracking-widest transition-all hover:bg-[#1FDDC4]/90 active:scale-95 disabled:opacity-20 flex items-center justify-center gap-2 overflow-hidden group/save"
                >
                    <span className={`material-symbols-outlined text-[16px] ${isSaving ? 'animate-spin' : 'group-hover/save:scale-110 transition-transform'}`}>{isSaving ? 'sync' : 'done_all'}</span>
                    {isSaving ? 'SYNC' : 'SAVE'}
                </button>
                <button
                    onClick={handleClose}
                    className="flex-1 py-3 bg-[#F6465D]/10 border border-[#F6465D]/30 text-[#F6465D] font-mono font-bold text-[9px] uppercase tracking-widest transition-all hover:bg-[#F6465D] hover:text-white active:scale-95 flex items-center justify-center gap-1 group/close"
                >
                    <span className="material-symbols-outlined text-[16px] group-hover/close:rotate-90 transition-transform">bolt</span>
                    EXIT
                </button>
            </div>
        </div>
    );
};

/* --- NUEVOS COMPONENTES ESTÉTICOS --- */

const ToastContainer = ({ alerts }: { alerts: Alert[] }) => (
    <div className="fixed bottom-8 right-8 z-[100] flex flex-col gap-3 pointer-events-none">
        {alerts.map(alert => (
            <div 
                key={alert.id}
                className={`animate-slide-in-right pointer-events-auto min-w-[300px] glass-panel p-4 border-l-4 shadow-2xl flex items-center gap-4 ${
                    alert.type === 'success' ? 'border-l-[#00C087] bg-[#00C087]/5' : 
                    alert.type === 'error' ? 'border-l-[#F6465D] bg-[#F6465D]/5' : 
                    'border-l-[#1FDDC4] bg-[#1FDDC4]/5'
                }`}
            >
                <span className={`material-symbols-outlined ${
                    alert.type === 'success' ? 'text-[#00C087]' : 
                    alert.type === 'error' ? 'text-[#F6465D]' : 
                    'text-[#1FDDC4]'
                }`}>
                    {alert.type === 'success' ? 'check_circle' : alert.type === 'error' ? 'error' : 'info'}
                </span>
                <div className="flex-1">
                    <div className="text-[10px] font-mono font-black uppercase opacity-40 mb-0.5">System_Notification</div>
                    <div className="text-[12px] font-mono font-bold text-white uppercase tracking-tight">{alert.message}</div>
                </div>
            </div>
        ))}
    </div>
);

const CustomConfirmModal = ({ title, message, onConfirm, onCancel }: { title: string, message: string, onConfirm: () => void, onCancel: () => void }) => (
    <div className="fixed inset-0 z-[200] flex items-center justify-center p-6 animate-fade-in">
        <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onCancel}></div>
        <div className="relative w-full max-w-md glass-panel p-8 border-[#1FDDC4]/20 animate-scale-up shadow-[0_0_50px_rgba(31,221,196,0.1)]">
            <div className="flex items-center gap-3 mb-6">
                <div className="h-1 w-8 bg-[#1FDDC4]"></div>
                <h2 className="font-mono text-lg font-black uppercase tracking-tight text-white bitget-glow">{title}</h2>
            </div>
            
            <p className="font-mono text-[13px] leading-relaxed text-[#848E9C] mb-10 uppercase tracking-tight">
                {message}
            </p>
            
            <div className="flex gap-4">
                <button 
                    onClick={onCancel}
                    className="flex-1 py-4 bg-white/5 border border-white/10 text-[#848E9C] font-mono font-bold text-[10px] uppercase tracking-widest transition-all hover:bg-white/10"
                >
                    ABORT_ACTION
                </button>
                <button 
                    onClick={onConfirm}
                    className="flex-1 py-4 bg-[#1FDDC4] text-black font-mono font-black text-[10px] uppercase tracking-widest transition-all hover:bg-[#1FDDC4]/90 shadow-[0_0_20px_rgba(31,221,196,0.2)]"
                >
                    CONFIRM_EXECUTION
                </button>
            </div>
        </div>
    </div>
);

export default App;
