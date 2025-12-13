"use client";

import { useEffect, useState, useMemo } from 'react';
import { useF1Store } from '@/store/useF1Store';
import { api } from '@/lib/api';
import { cn } from '@/lib/utils';
import { ArrowUpDown } from 'lucide-react'; // Make sure you have lucide-react or use text arrows

interface DriverPotential {
    driver: string;
    team: string;
    color: string;
    actual: number;
    theoretical: number;
    delta: number;
    pct_unlocked: number;
}

type SortField = 'actual' | 'theoretical' | 'pct_unlocked';
type SortOrder = 'asc' | 'desc';

interface Props {
    page?: number;  // 1-indexed page number
    limit?: number; // Items per page (e.g. 10)
}

export default function PotentialLeaderboard({ page, limit }: Props) {
    const { session } = useF1Store();
    const [data, setData] = useState<DriverPotential[]>([]);
    const [loading, setLoading] = useState(false);

    // Sorting State
    const [sortField, setSortField] = useState<SortField>('pct_unlocked');
    const [sortOrder, setSortOrder] = useState<SortOrder>('desc');

    useEffect(() => {
        if (!session) return;
        setLoading(true);
        api.get('/analysis/grid-potential')
            .then(res => setData(res.data.data))
            .catch(console.error)
            .finally(() => setLoading(false));
    }, [session]);

    const handleSort = (field: SortField) => {
        if (sortField === field) {
            setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
        } else {
            setSortField(field);
            setSortOrder(field === 'pct_unlocked' ? 'desc' : 'asc'); // Default desc for %, asc for time
        }
    };

    const sortedData = useMemo(() => {
        const sorted = [...data].sort((a, b) => {
            const valA = a[sortField];
            const valB = b[sortField];
            return sortOrder === 'asc' ? valA - valB : valB - valA;
        });

        // Apply Pagination if provided
        if (page && limit) {
            const start = (page - 1) * limit;
            const end = start + limit;
            return sorted.slice(start, end);
        }

        return sorted;
    }, [data, sortField, sortOrder, page, limit]);

    const formatTime = (sec: number) => {
        const m = Math.floor(sec / 60);
        const s = (sec % 60).toFixed(3);
        return `${m}:${s.padStart(6, '0')}`;
    };

    if (loading) return (
        <div className="flex h-full flex-col items-center justify-center text-white/50 space-y-2">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white"></div>
            <p className="text-xs font-mono">CRUNCHING MINI-SECTORS (Takes ~10s)...</p>
        </div>
    );

    if (!data.length) return <div className="flex h-full items-center justify-center text-white/50">No Data</div>;

    return (
        <div className="w-full h-full flex flex-col bg-[#0b0b0b] rounded-xl border border-white/10 overflow-hidden">
            {/* Header / Sorters */}
            <div className="grid grid-cols-12 gap-2 p-3 bg-white/5 border-b border-white/10 text-[10px] font-bold uppercase tracking-wider text-text-secondary sticky top-0 z-20">
                <div className="col-span-1 text-center">#</div>
                <div className="col-span-2">Driver</div>

                {/* Clickable Headers */}
                <div
                    className="col-span-2 text-right cursor-pointer hover:text-white flex justify-end items-center gap-1"
                    onClick={() => handleSort('theoretical')}
                >
                    Theor. Best
                    {sortField === 'theoretical' && <span className="text-accent">{sortOrder === 'asc' ? '↑' : '↓'}</span>}
                </div>

                <div
                    className="col-span-2 text-right cursor-pointer hover:text-white flex justify-end items-center gap-1"
                    onClick={() => handleSort('actual')}
                >
                    Actual Best
                    {sortField === 'actual' && <span className="text-accent">{sortOrder === 'asc' ? '↑' : '↓'}</span>}
                </div>

                <div className="col-span-1" />

                <div
                    className="col-span-4 text-right cursor-pointer hover:text-white flex justify-end items-center gap-1"
                    onClick={() => handleSort('pct_unlocked')}
                >
                    Potential %
                    {sortField === 'pct_unlocked' && <span className="text-accent">{sortOrder === 'asc' ? '↑' : '↓'}</span>}
                </div>
            </div>

            {/* List */}
            <div className="flex-1 overflow-y-auto custom-scrollbar p-2 space-y-1">
                {sortedData.map((row, index) => (
                    <div
                        key={row.driver}
                        className="grid grid-cols-12 gap-2 items-center p-2 rounded hover:bg-white/5 border border-transparent hover:border-white/10 transition-colors group"
                    >
                        {/* Rank */}
                        <div className="col-span-1 text-center text-xs font-mono text-white/40">
                            {/* Adjusted Rank for Pagination */}
                            {(page && limit ? (index + 1 + (page - 1) * limit) : index + 1)}
                        </div>

                        {/* Driver */}
                        <div className="col-span-2 flex items-center gap-2">
                            <div className="h-6 w-1 rounded-full" style={{ backgroundColor: row.color }} />
                            <span className="font-bold text-sm">{row.driver}</span>
                        </div>

                        {/* Theoretical */}
                        <div className="col-span-2 text-right font-mono text-xs text-accent font-bold">
                            {formatTime(row.theoretical)}
                        </div>

                        {/* Actual */}
                        <div className="col-span-2 text-right font-mono text-xs text-white/70">
                            {formatTime(row.actual)}
                        </div>

                        {/* Spacer */}
                        <div className="col-span-1" />

                        {/* Potential Bar */}
                        <div className="col-span-4 flex flex-col justify-center items-end">
                            <div className="flex items-baseline gap-1">
                                <span className={cn(
                                    "text-sm font-bold tabular-nums",
                                    row.pct_unlocked > 99.8 ? "text-purple-400" :
                                        row.pct_unlocked > 99.0 ? "text-green-400" : "text-yellow-400"
                                )}>
                                    {row.pct_unlocked.toFixed(2)}%
                                </span>
                            </div>

                            {/* The Bar */}
                            <div className="w-full h-1.5 bg-white/10 rounded-full mt-1 overflow-hidden">
                                <div
                                    className="h-full rounded-full transition-all duration-1000"
                                    style={{
                                        // Improved Scaling: 90% is floor (0% width), 100% is ceiling (100% width)
                                        // This makes 95% appear as 50% filled, which is intuitive.
                                        width: `${Math.max(0, (row.pct_unlocked - 92) * 12.5)}%`,
                                        backgroundColor: row.color
                                    }}
                                />
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}
