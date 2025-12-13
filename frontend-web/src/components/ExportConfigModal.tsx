"use client";

import { useF1Store } from '@/store/useF1Store';
import { CHART_REGISTRY } from '@/lib/chartRegistry';
import { X, Check, FileDown, Settings2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useState, useEffect } from 'react';

export default function ExportConfigModal() {
    const {
        isExportConfigOpen,
        setExportConfigOpen,
        exportConfig,
        updateExportConfig,
        setExporting,
        session
    } = useF1Store();

    // Local state for drivers
    const drivers = session?.drivers || [];

    // Initialize config if empty
    useEffect(() => {
        if (!isExportConfigOpen) return;

        // Populate defaults if missing
        CHART_REGISTRY.forEach(chart => {
            if (!exportConfig[chart.id]) {
                // Default to true for now, let user uncheck
                updateExportConfig(chart.id, true, undefined);
            }
        });
    }, [isExportConfigOpen]);

    if (!isExportConfigOpen) return null;

    const handleGenerate = () => {
        setExportConfigOpen(false);
        setExporting(true);
    };

    // Group charts by category for easier navigation
    const groupedCharts: Record<string, typeof CHART_REGISTRY> = {
        'PRACTICE': CHART_REGISTRY.filter(c => c.category === 'PRACTICE'),
        'QUALI': CHART_REGISTRY.filter(c => c.category === 'QUALI'),
        'RACE': CHART_REGISTRY.filter(c => c.category === 'RACE')
    };

    const categories = ['PRACTICE', 'QUALI', 'RACE'];

    return (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
            <div className="bg-[#1C1C1E] w-full max-w-2xl rounded-xl border border-white/10 shadow-2xl flex flex-col max-h-[90vh]">

                {/* Header */}
                <div className="p-4 border-b border-white/10 flex justify-between items-center bg-white/5 rounded-t-xl">
                    <div className="flex items-center gap-3">
                        <div className="p-2 bg-accent/20 rounded-lg text-accent">
                            <Settings2 size={20} />
                        </div>
                        <div>
                            <h2 className="text-white font-bold text-lg">Report Configuration</h2>
                            <p className="text-text-secondary text-xs">Select charts and configure drivers for your PDF Report</p>
                        </div>
                    </div>
                    <button
                        onClick={() => setExportConfigOpen(false)}
                        className="p-2 hover:bg-white/10 rounded-lg text-text-secondary hover:text-white transition-colors"
                    >
                        <X size={20} />
                    </button>
                </div>

                {/* Body (Scrollable) */}
                <div className="flex-1 overflow-y-auto p-4 space-y-6 custom-scrollbar">
                    {categories.map(cat => (
                        <div key={cat}>
                            <h3 className="text-xs font-bold text-text-secondary uppercase mb-2 sticky top-0 bg-[#1C1C1E] py-1 z-10 border-b border-white/5">
                                {cat} Charts
                            </h3>
                            <div className="space-y-2">
                                {groupedCharts[cat].map(chart => {
                                    const config = exportConfig[chart.id] || { enabled: true };

                                    return (
                                        <div
                                            key={chart.id}
                                            className={cn(
                                                "p-3 rounded-lg border flex items-center gap-4 transition-all",
                                                config.enabled
                                                    ? "bg-white/5 border-white/20"
                                                    : "bg-black/20 border-white/5 opacity-60"
                                            )}
                                        >
                                            {/* Checkbox */}
                                            <button
                                                onClick={() => updateExportConfig(chart.id, !config.enabled, config.driverOverride, config.comparisonOverride)}
                                                className={cn(
                                                    "w-6 h-6 rounded flex items-center justify-center border transition-colors shrink-0",
                                                    config.enabled
                                                        ? "bg-accent border-accent text-black"
                                                        : "border-white/20 hover:border-white/40"
                                                )}
                                            >
                                                {config.enabled && <Check size={14} strokeWidth={4} />}
                                            </button>

                                            {/* Info */}
                                            <div className="flex-1">
                                                <h4 className="text-sm font-bold text-white">{chart.label}</h4>
                                                <p className="text-xs text-text-secondary mt-0.5">{chart.description || "No description available"}</p>
                                            </div>

                                            {/* Driver Selector (if applicable) */}
                                            {config.enabled && chart.needsDriver && (
                                                <div className="flex flex-col gap-2 min-w-[200px]">
                                                    <div className="flex flex-col gap-1">
                                                        <label className="text-[10px] uppercase font-bold text-text-secondary">Focus Driver</label>
                                                        <select
                                                            className="bg-black/40 text-white text-xs p-1.5 rounded border border-white/10 outline-none focus:border-accent"
                                                            value={config.driverOverride || ""}
                                                            onChange={(e) => updateExportConfig(chart.id, true, e.target.value || undefined, config.comparisonOverride)}
                                                        >
                                                            <option value="">Session Default</option>
                                                            {drivers.map(d => (
                                                                <option key={d.code} value={d.code}>{d.code} - {d.team}</option>
                                                            ))}
                                                        </select>
                                                    </div>

                                                    {chart.needsComparison && (
                                                        <div className="flex flex-col gap-1">
                                                            <label className="text-[10px] uppercase font-bold text-text-secondary">Comparison</label>
                                                            <select
                                                                className="bg-black/40 text-white text-xs p-1.5 rounded border border-white/10 outline-none focus:border-accent"
                                                                value={config.comparisonOverride || ""}
                                                                onChange={(e) => updateExportConfig(chart.id, true, config.driverOverride, e.target.value || undefined)}
                                                            >
                                                                <option value="">None / Auto</option>
                                                                {drivers.map(d => (
                                                                    <option key={d.code} value={d.code}>{d.code} - {d.team}</option>
                                                                ))}
                                                            </select>
                                                        </div>
                                                    )}
                                                </div>
                                            )}
                                        </div>
                                    );
                                })}
                            </div>
                        </div>
                    ))}
                </div>

                {/* Footer */}
                <div className="p-4 border-t border-white/10 flex justify-end gap-3 bg-black/20 rounded-b-xl">
                    <button
                        onClick={() => setExportConfigOpen(false)}
                        className="px-4 py-2 text-sm font-bold text-text-secondary hover:text-white transition-colors"
                    >
                        Cancel
                    </button>
                    <button
                        onClick={handleGenerate}
                        className="px-6 py-2 bg-accent/90 hover:bg-accent text-black text-sm font-bold rounded-lg flex items-center gap-2 transition-all hover:scale-105 active:scale-95"
                    >
                        <FileDown size={18} />
                        Generate PDF Report
                    </button>
                </div>
            </div>
        </div>
    );
}
