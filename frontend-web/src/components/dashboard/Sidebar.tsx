import { useEffect, useState } from 'react';
import { useF1Store, SessionMode } from '@/store/useF1Store';
import { cn } from '@/lib/utils';
import { api } from '@/lib/api';
import { CHART_REGISTRY } from '@/lib/chartRegistry';
import { ChevronLeft, ChevronRight, Settings, BarChart2, Users, Trophy, Timer, Zap, Flag } from 'lucide-react';

interface Race {
    round: number;
    name: string;
    sessions: string[];
}

const SESSION_LABELS: Record<string, string> = {
    "FP1": "Practice 1",
    "FP2": "Practice 2",
    "FP3": "Practice 3",
    "Q": "Qualifying",
    "S": "Sprint",
    "SS": "Sprint Shootout",
    "R": "Race"
};

export function Sidebar() {
    const {
        session, selectedDriver, selectedMode, selectDriver,
        selectedYear, selectedGP, selectedSessionType, activeCharts,
        setSelection, toggleChart, setMode, reorderCharts
    } = useF1Store();
    const [seasons, setSeasons] = useState<number[]>([2025, 2024, 2023]);
    const [races, setRaces] = useState<Race[]>([]);
    const [availableSessions, setAvailableSessions] = useState<string[]>(["FP1", "FP2", "FP3", "Q", "R"]);
    const [isCollapsed, setIsCollapsed] = useState(false);

    // Load Seasons (Fetch from API to update if needed)
    useEffect(() => {
        api.get('/seasons').then(res => {
            if (res.data && res.data.length > 0) {
                setSeasons(res.data);
            }
        }).catch(console.error);
    }, []);

    // Load Races when year changes
    useEffect(() => {
        if (!selectedYear) return;
        api.get('/races', { params: { year: selectedYear } })
            .then(res => {
                setRaces(res.data);
            })
            .catch(console.error);
    }, [selectedYear]);

    // Update available sessions
    useEffect(() => {
        const race = races.find(r => r.name === selectedGP);
        if (race && race.sessions && race.sessions.length > 0) {
            setAvailableSessions(race.sessions);
        }
    }, [selectedGP, races]);

    // Mode Click Handler
    const handleModeClick = (mode: SessionMode) => {
        setMode(mode);
        const modeCharts = CHART_REGISTRY
            .filter(c => c.category === mode)
            .map(c => c.id);
        reorderCharts(modeCharts);
    };

    const getModeIcon = (mode: string) => {
        switch (mode) {
            case 'PRACTICE': return <Timer size={20} />;
            case 'QUALI': return <Zap size={20} />;
            case 'RACE': return <Flag size={20} />;
            default: return <BarChart2 size={20} />;
        }
    };

    return (
        <aside
            className={cn(
                "bg-[#1C1C1E] rounded-xl flex flex-col h-full gap-4 transition-all duration-300 ease-in-out relative border border-white/5 z-50",
                isCollapsed ? "w-20 p-2" : "w-64 p-4"
            )}
        >
            {/* Collapse Toggle */}
            <button
                onClick={() => setIsCollapsed(!isCollapsed)}
                className="absolute -right-3 top-6 bg-accent text-white p-1 rounded-full z-10 shadow-lg hover:bg-accent/80 transition-colors"
            >
                {isCollapsed ? <ChevronRight size={14} /> : <ChevronLeft size={14} />}
            </button>

            {/* Header / Logo Area */}
            <div className={cn("flex items-center gap-2", isCollapsed ? "justify-center" : "px-2")}>
                <div className="w-8 h-8 bg-gradient-to-br from-accent to-purple-600 rounded-lg shrink-0 flex items-center justify-center">
                    <span className="font-bold text-white text-xs">F1</span>
                </div>
                {!isCollapsed && <span className="font-bold text-xl tracking-tighter">OVERCUT</span>}
            </div>

            {/* Helper: Section Title */}
            {!isCollapsed && (
                <div className="text-[10px] font-bold text-text-secondary uppercase tracking-wider px-2 mt-2">
                    Configuration
                </div>
            )}

            {/* Controls Section */}
            <div className={cn(
                "bg-black/20 rounded-lg flex flex-col gap-3 transition-all",
                isCollapsed ? "p-2 items-center" : "p-3"
            )}>
                {isCollapsed ? (
                    // Collapsed: Icons
                    <div className="flex flex-col gap-4 text-text-secondary">
                        <Trophy size={20} className={selectedGP ? "text-white" : ""} />
                        <Settings size={20} />
                    </div>
                ) : (
                    // Expanded: Full Controls
                    <>
                        <div className="flex flex-col gap-1">
                            <label className="text-[10px] font-bold text-text-secondary uppercase">Season</label>
                            <select
                                value={selectedYear}
                                onChange={(e) => setSelection(Number(e.target.value), "", selectedSessionType)}
                                className="bg-[#1C1C1E] text-white p-1.5 rounded text-sm border border-white/10 outline-none focus:border-accent"
                            >
                                {seasons.map(y => (
                                    <option key={y} value={y}>{y}</option>
                                ))}
                            </select>
                        </div>
                        <div className="flex flex-col gap-1">
                            <label className="text-[10px] font-bold text-text-secondary uppercase">Grand Prix</label>
                            <select
                                value={selectedGP}
                                onChange={(e) => setSelection(selectedYear, e.target.value, "R")}
                                className="bg-[#1C1C1E] text-white p-1.5 rounded text-sm border border-white/10 outline-none focus:border-accent"
                            >
                                <option value="" disabled>Select GP</option>
                                {races.map(r => (
                                    <option key={r.round} value={r.name}>{r.name}</option>
                                ))}
                            </select>
                        </div>
                        <div className="flex flex-col gap-1">
                            <label className="text-[10px] font-bold text-text-secondary uppercase">Session</label>
                            <select
                                value={selectedSessionType}
                                onChange={(e) => setSelection(selectedYear, selectedGP, e.target.value)}
                                className="bg-[#1C1C1E] text-white p-1.5 rounded text-sm border border-white/10 outline-none focus:border-accent"
                            >
                                {availableSessions.map(code => (
                                    <option key={code} value={code}>{SESSION_LABELS[code] || code}</option>
                                ))}
                            </select>
                        </div>
                    </>
                )}
            </div>

            <div className="h-px bg-white/5 mx-2" />

            {/* Mode Selection (Accordion) */}
            <div className="flex-1 overflow-y-auto space-y-2 pr-1 no-scrollbar">
                {['PRACTICE', 'QUALI', 'RACE'].map((category) => (
                    <div key={category} className={cn(
                        "rounded-lg transition-all",
                        isCollapsed ? "bg-transparent text-center" : "bg-black/20 border border-white/5"
                    )}>
                        <button
                            onClick={() => handleModeClick(category as SessionMode)}
                            className={cn(
                                "w-full flex items-center transition-colors",
                                isCollapsed ? "justify-center p-2 rounded-lg" : "justify-between p-3 text-xs font-bold",
                                selectedMode === category
                                    ? (isCollapsed ? "bg-accent text-white" : "bg-white/10 text-white")
                                    : "text-text-secondary hover:text-white"
                            )}
                            title={isCollapsed ? `${category} Dashboard` : undefined}
                        >
                            {isCollapsed ? (
                                getModeIcon(category)
                            ) : (
                                <>
                                    <span className="flex items-center gap-2">
                                        {/* Show icon even when expanded? Maybe nice touch */}
                                        {category === 'PRACTICE' && <Timer size={14} className="opacity-70" />}
                                        {category === 'QUALI' && <Zap size={14} className="opacity-70" />}
                                        {category === 'RACE' && <Flag size={14} className="opacity-70" />}
                                        <span>{category}</span>
                                    </span>
                                    <span className={cn("transition-transform", selectedMode === category ? "rotate-90" : "")}>›</span>
                                </>
                            )}
                        </button>

                        {/* Expanded Content (Only when Sidebar is Open) */}
                        {!isCollapsed && selectedMode === category && (
                            <div className="p-2 space-y-1 bg-black/20 border-t border-white/5">
                                {CHART_REGISTRY.filter(c => c.category === category).map(chart => (
                                    <label key={chart.id} className="flex items-center gap-2 px-2 py-1.5 rounded hover:bg-white/5 cursor-pointer group">
                                        <input
                                            type="checkbox"
                                            checked={activeCharts.includes(chart.id)}
                                            onChange={() => toggleChart(chart.id)}
                                            className="rounded border-white/20 bg-transparent text-accent focus:ring-accent"
                                        />
                                        <span className="text-xs text-text-secondary group-hover:text-white transition-colors">
                                            {chart.label}
                                        </span>
                                    </label>
                                ))}
                            </div>
                        )}
                    </div>
                ))}
            </div>

            <div className="h-px bg-white/5 mx-2" />

            {/* Driver List */}
            <h2 className={cn(
                "text-text-secondary text-xs font-bold uppercase tracking-wider mt-1 transition-opacity",
                isCollapsed ? "text-center text-[10px]" : "px-2"
            )}>
                {isCollapsed ? "Grid" : "Live Grid"}
            </h2>

            <div className="flex-1 overflow-y-auto space-y-1 no-scrollbar">
                {session?.drivers.map((driver) => (
                    <button
                        key={driver.code}
                        onClick={() => selectDriver(driver.code)}
                        className={cn(
                            'w-full flex items-center gap-3 rounded-lg transition-all relative group',
                            isCollapsed ? "justify-center p-2" : "p-2 px-3 text-left",
                            selectedDriver === driver.code
                                ? 'bg-white/10'
                                : 'hover:bg-white/5'
                        )}
                    >
                        {/* Driver Color Indicator */}
                        <div
                            className={cn(
                                "rounded-full shrink-0 transition-all",
                                isCollapsed ? "w-3 h-3" : "w-1 h-6"
                            )}
                            style={{ backgroundColor: driver.color }}
                        />

                        {/* Text (Hidden if collapsed) */}
                        {!isCollapsed ? (
                            <>
                                <span className={cn("font-bold text-sm", selectedDriver === driver.code ? "text-white" : "text-gray-400")}>
                                    {driver.code}
                                </span>
                                <span className="text-text-secondary text-xs ml-auto font-mono opacity-60 group-hover:opacity-100">
                                    {driver.bestLap}
                                </span>
                            </>
                        ) : (
                            // Collapsed: Tooltip-ish Code 
                            <span className="absolute left-10 bg-black px-2 py-1 rounded text-xs font-bold text-white opacity-0 group-hover:opacity-100 transition-opacity z-50 pointer-events-none whitespace-nowrap border border-white/10">
                                {driver.code} {driver.bestLap && `(${driver.bestLap})`}
                            </span>
                        )}
                    </button>
                ))}

                {!session && (
                    <div className="text-text-secondary text-sm text-center py-4 opacity-50">
                        ...
                    </div>
                )}
            </div>

            {/* Footer Session Info */}
            {!isCollapsed && session && (
                <div className="mt-auto pt-4 border-t border-white/5 px-2">
                    <p className="text-text-secondary text-xs truncate">
                        {session.eventName}
                    </p>
                    <p className="text-text-secondary text-[10px] opacity-60">
                        {session.sessionType}
                    </p>
                </div>
            )}
        </aside>
    );
}
