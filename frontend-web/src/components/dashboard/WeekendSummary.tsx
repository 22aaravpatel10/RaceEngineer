"use client";

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { useF1Store } from '@/store/useF1Store';
// Icons
import { Trophy, Timer, Flag, AlertTriangle, CloudRain } from 'lucide-react';

interface SessionResult {
    position: number;
    driver: string;
    team: string;
    time: string;
    color: string;
    status: string;
}

interface FastestLap {
    driver: string;
    team: string;
    time: string;
    color: string;
}

interface SessionSummary {
    name: string;
    type: string;
    results?: SessionResult[];
    fastestLap?: FastestLap;
    error?: string;
}

interface WeekendData {
    eventName: string;
    date: string;
    location: string;
    sessions: SessionSummary[];
}

export function WeekendSummary() {
    const { selectedYear, selectedGP } = useF1Store();
    const [data, setData] = useState<WeekendData | null>(null);
    const [loading, setLoading] = useState(false);
    const [expanded, setExpanded] = useState<Record<number, boolean>>({});

    useEffect(() => {
        if (!selectedGP) return;

        setLoading(true);
        // Clean GP name for URL
        const gpParam = encodeURIComponent(selectedGP);
        api.get(`/weekend/${selectedYear}/${gpParam}`)
            .then(res => {
                setData(res.data.data);
            })
            .catch(err => {
                console.error("Failed to load summary", err);
            })
            .finally(() => setLoading(false));
    }, [selectedYear, selectedGP]);

    const toggleExpand = (idx: number) => {
        setExpanded(prev => ({
            ...prev,
            [idx]: !prev[idx]
        }));
    };

    if (loading) {
        return <div className="w-full h-full flex items-center justify-center text-white/50 text-xl animate-pulse">Loading Weekend Data...</div>;
    }

    if (!data) {
        return <div className="w-full h-full flex items-center justify-center text-white/50">Select a Grand Prix to view summary</div>;
    }

    return (
        <div className="w-full h-full overflow-y-auto p-6 space-y-8">
            {/* Header */}
            <div className="flex items-center justify-between border-b border-white/10 pb-4">
                <div>
                    <h1 className="text-3xl font-bold bg-gradient-to-r from-red-500 to-orange-500 bg-clip-text text-transparent">
                        {data.eventName}
                    </h1>
                    <div className="flex items-center gap-4 text-text-secondary mt-1">
                        <span className="flex items-center gap-1"><Flag size={14} /> {data.location}</span>
                        <span>{data.date}</span>
                    </div>
                </div>
                <div className="text-right">
                    <div className="text-sm text-text-secondary">SEASON</div>
                    <div className="text-2xl font-mono font-bold text-white">{selectedYear}</div>
                </div>
            </div>

            {/* Sessions Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {data.sessions.map((sess, idx) => {
                    const isExpanded = !!expanded[idx];
                    const resultsToShow = isExpanded ? sess.results : sess.results?.slice(0, 5);
                    const hasMore = (sess.results?.length || 0) > 5;

                    return (
                        <div key={idx} className={`bg-card rounded-xl p-4 border border-white/5 shadow-lg flex flex-col transition-all duration-300 ${isExpanded ? 'row-span-2' : ''}`}>
                            <div className="flex items-center justify-between mb-4 pb-2 border-b border-white/5">
                                <h3 className="font-bold text-lg text-white">{sess.name}</h3>
                                <span className="text-xs px-2 py-1 rounded bg-white/10 text-white/70 font-mono">
                                    {sess.type}
                                </span>
                            </div>

                            {sess.error ? (
                                <div className="flex-1 flex items-center justify-center text-red-400 text-sm">
                                    <AlertTriangle size={16} className="mr-2" /> {sess.error}
                                </div>
                            ) : (
                                <div className="space-y-3 flex-1 flex flex-col">
                                    {/* Winner / Top Result - Only show if not expanded to save space? Keep it for context */}
                                    {sess.results && sess.results.length > 0 && !isExpanded && (
                                        <div className="flex items-center gap-3 bg-white/5 p-2 rounded-lg">
                                            <Trophy className="text-yellow-500" size={20} />
                                            <div>
                                                <div className="font-bold text-xl" style={{ color: sess.results[0].color }}>
                                                    {sess.results[0].driver}
                                                </div>
                                                <div className="text-xs text-text-secondary">{sess.results[0].time}</div>
                                            </div>
                                        </div>
                                    )}

                                    {/* Table */}
                                    <div className="flex-1 overflow-x-auto">
                                        <table className="w-full text-sm">
                                            <thead>
                                                <tr className="text-left text-text-secondary text-xs border-b border-white/5">
                                                    <th className="pb-1">Pos</th>
                                                    <th className="pb-1">Driver</th>
                                                    <th className="pb-1 text-right">Time</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {resultsToShow?.map((r) => (
                                                    <tr key={r.position} className="group hover:bg-white/5 transition-colors border-b border-white/5 last:border-0">
                                                        <td className="py-1.5 font-mono text-white/50">{r.position}</td>
                                                        <td className="py-1.5 font-bold" style={{ color: r.color }}>{r.driver}</td>
                                                        <td className="py-1.5 text-right font-mono text-white/70">{r.time}</td>
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                    </div>

                                    {/* Expand Button */}
                                    {hasMore && (
                                        <button
                                            onClick={() => toggleExpand(idx)}
                                            className="w-full text-xs text-center py-2 text-white/50 hover:text-white hover:bg-white/5 rounded transition-colors mt-2"
                                        >
                                            {isExpanded ? 'Show Less' : `Show All (${sess.results?.length})`}
                                        </button>
                                    )}

                                    {/* Fastest Lap - Always visible at bottom */}
                                    {sess.fastestLap && (
                                        <div className="mt-2 pt-2 border-t border-white/5 flex items-center justify-between">
                                            <div className="flex items-center gap-2 text-purple-400">
                                                <Timer size={14} />
                                                <span className="text-xs font-bold">FASTEST LAP</span>
                                            </div>
                                            <div className="text-right">
                                                <span className="text-xs font-bold mr-2" style={{ color: sess.fastestLap.color }}>
                                                    {sess.fastestLap.driver}
                                                </span>
                                                <span className="text-xs font-mono text-white/70">{sess.fastestLap.time}</span>
                                            </div>
                                        </div>
                                    )}
                                </div>
                            )}
                        </div>
                    );
                })}
            </div>
        </div>
    );
}
