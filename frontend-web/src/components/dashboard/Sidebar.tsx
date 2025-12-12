import { useEffect, useState } from 'react';
import { useF1Store, SessionMode } from '@/store/useF1Store';
import { cn } from '@/lib/utils';
import { api } from '@/lib/api';
import { CHART_REGISTRY } from '@/lib/chartRegistry';

interface Race {
    round: number;
    name: string;
}

export function Sidebar() {
    const { session, selectedDriver, selectedMode, selectDriver, setMode, selectedYear, selectedGP, selectedSessionType, setSelection, activeCharts, toggleChart } = useF1Store();
    const [seasons, setSeasons] = useState<number[]>([]);
    const [races, setRaces] = useState<Race[]>([]);

    // Load Seasons
    useEffect(() => {
        api.get('/seasons').then(res => setSeasons(res.data)).catch(console.error);
    }, []);

    // Load Races when year changes
    useEffect(() => {
        api.get('/races', { params: { year: selectedYear } })
            .then(res => {
                setRaces(res.data);
            })
            .catch(console.error);
    }, [selectedYear]);

    return (
        <aside className="w-64 bg-card rounded-xl p-4 flex flex-col h-full gap-4">

            {/* Season & GP Selection */}
            <div className="flex flex-col gap-3 p-3 bg-background rounded-lg">
                <div className="flex flex-col gap-1">
                    <label className="text-[10px] font-bold text-text-secondary uppercase">Season</label>
                    <select
                        value={selectedYear}
                        onChange={(e) => setSelection(Number(e.target.value), "", selectedSessionType)}
                        className="bg-card text-white p-1.5 rounded text-sm border border-white/10 outline-none focus:border-accent"
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
                        onChange={(e) => setSelection(selectedYear, e.target.value, selectedSessionType)}
                        className="bg-card text-white p-1.5 rounded text-sm border border-white/10 outline-none focus:border-accent"
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
                        className="bg-card text-white p-1.5 rounded text-sm border border-white/10 outline-none focus:border-accent"
                    >
                        <option value="FP1">Practice 1</option>
                        <option value="FP2">Practice 2</option>
                        <option value="FP3">Practice 3</option>
                        <option value="S">Sprint</option>
                        <option value="SS">Sprint Shootout</option>
                        <option value="Q">Qualifying</option>
                        <option value="R">Race</option>
                    </select>
                </div>
            </div>

            {/* Chart Selection (Accordion) */}
            <div className="flex-1 overflow-y-auto space-y-2 pr-1">
                {['PRACTICE', 'QUALI', 'RACE'].map((category) => (
                    <div key={category} className="bg-background rounded-lg overflow-hidden border border-white/5">
                        <button
                            onClick={() => setMode(category as SessionMode)}
                            className={cn(
                                "w-full flex items-center justify-between p-3 text-xs font-bold transition-colors",
                                selectedMode === category
                                    ? "bg-white/10 text-white"
                                    : "text-text-secondary hover:text-white hover:bg-white/5"
                            )}
                        >
                            <span>{category} DASHBOARD</span>
                            <span className={cn("transition-transform", selectedMode === category ? "rotate-90" : "")}>
                                ›
                            </span>
                        </button>

                        {/* Expanded Content */}
                        {selectedMode === category && (
                            <div className="p-2 space-y-1 bg-black/20">
                                {CHART_REGISTRY.filter(c => c.category === category).map(chart => (
                                    <label key={chart.id} className="flex items-center gap-2 px-2 py-1.5 rounded hover:bg-white/5 cursor-pointer">
                                        <input
                                            type="checkbox"
                                            checked={activeCharts.includes(chart.id)}
                                            onChange={() => toggleChart(chart.id)}
                                            className="rounded border-white/20 bg-transparent text-accent focus:ring-accent"
                                        />
                                        <span className="text-xs text-text-secondary select-none">
                                            {chart.label}
                                        </span>
                                    </label>
                                ))}
                            </div>
                        )}
                    </div>
                ))}
            </div>

            {/* Driver List */}
            <h2 className="text-text-secondary text-xs font-bold uppercase tracking-wider mt-2">
                Live Grid
            </h2>

            <div className="flex-1 overflow-y-auto space-y-1">
                {session?.drivers.map((driver) => (
                    <button
                        key={driver.code}
                        onClick={() => selectDriver(driver.code)}
                        className={cn(
                            'w-full flex items-center gap-3 p-3 rounded-lg transition-all text-left',
                            selectedDriver === driver.code
                                ? 'bg-card-hover border-l-[3px]'
                                : 'hover:bg-card-hover/50'
                        )}
                        style={{
                            borderLeftColor: selectedDriver === driver.code ? driver.color : 'transparent',
                        }}
                    >
                        <div
                            className="w-1 h-6 rounded-full"
                            style={{ backgroundColor: driver.color }}
                        />
                        <span className="font-bold text-sm">{driver.code}</span>
                        <span className="text-text-secondary text-xs ml-auto font-mono">
                            {driver.bestLap}
                        </span>
                    </button>
                ))}

                {!session && (
                    <div className="text-text-secondary text-sm text-center py-8">
                        Loading session...
                    </div>
                )}
            </div>

            {/* Session Info */}
            {session && (
                <div className="mt-auto pt-4 border-t border-card-hover">
                    <p className="text-text-secondary text-xs">
                        {session.eventName} • {session.sessionType}
                    </p>
                </div>
            )}
        </aside>
    );
}
