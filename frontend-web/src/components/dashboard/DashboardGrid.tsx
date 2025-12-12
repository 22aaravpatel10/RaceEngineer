'use client';

import React, { useRef, useState, useEffect } from 'react';
import { cn } from '@/lib/utils';
import { CHART_REGISTRY, ChartCategory } from '@/lib/chartRegistry';
import { Maximize2, Minimize2, GripHorizontal } from 'lucide-react';

interface DashboardGridProps {
    activeCharts: string[];
    onReorder: (newOrder: string[]) => void;
    telemetryData?: any;
    driverLaps?: any[];
    selectedDriver?: string | null;
    driverColor?: string;
    session?: any;
}

export function DashboardGrid({
    activeCharts,
    onReorder,
    telemetryData,
    driverLaps,
    selectedDriver,
    driverColor,
    session
}: DashboardGridProps) {
    const [draggedItem, setDraggedItem] = useState<string | null>(null);
    const [expandedCharts, setExpandedCharts] = useState<Record<string, boolean>>({});

    // Toggle expand/collapse
    const toggleExpand = (chartId: string) => {
        setExpandedCharts(prev => ({
            ...prev,
            [chartId]: !prev[chartId]
        }));
    };

    // Check if any chart is expanded (Guardrail: prevent dragging while resized layouts exist)
    const isAnyExpanded = Object.values(expandedCharts).some(v => v);

    // --- Drag & Drop Handlers ---
    const lastReorderTime = useRef(0);

    const handleDragStart = (e: React.DragEvent, id: string) => {
        if (isAnyExpanded) {
            e.preventDefault();
            return;
        }
        setDraggedItem(id);
        e.dataTransfer.effectAllowed = 'move';
        // Set transparent drag image if possible, or use default
    };

    const handleDragOver = (e: React.DragEvent, targetId: string) => {
        e.preventDefault(); // Necessary to allow dropping
        if (!draggedItem || draggedItem === targetId || isAnyExpanded) return;

        // Throttle reordering to every 100ms to prevent jitter
        const now = Date.now();
        if (now - lastReorderTime.current < 100) return;
        lastReorderTime.current = now;

        // Find indexes
        const curIndex = activeCharts.indexOf(draggedItem);
        const targetIndex = activeCharts.indexOf(targetId);

        if (curIndex !== -1 && targetIndex !== -1 && curIndex !== targetIndex) {
            const newOrder = [...activeCharts];
            // Remove dragged
            newOrder.splice(curIndex, 1);
            // Insert at target
            newOrder.splice(targetIndex, 0, draggedItem);

            onReorder(newOrder);
        }
    };

    const handleDragEnd = () => {
        setDraggedItem(null);
    };

    if (!session) return null;

    return (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 pb-20">
            {activeCharts.length === 0 && (
                <div className="col-span-full h-64 flex items-center justify-center text-text-secondary border border-dashed border-white/10 rounded-xl">
                    No charts selected. Open Sidebar to add specific analysis modules.
                </div>
            )}

            {activeCharts.map((chartId) => {
                const chartDef = CHART_REGISTRY.find(c => c.id === chartId);
                if (!chartDef) return null;

                const ChartComponent = chartDef.component;
                const isExpanded = expandedCharts[chartId];
                // Guardrail: Disable drag if any chart is expanded to preserve grid stability
                const isDraggable = !isAnyExpanded;

                // Determine layout class
                // If expanded, force full width. Otherwise use registry definition (defaulting to col-span-12 if missing)
                const colSpanClass = isExpanded ? 'col-span-full' : (chartDef.gridCols || 'col-span-12');

                // Prepare props (logic lifted from page.tsx)
                const props: any = {};
                if (chartId === 'telemetry_trace' || chartId === 'quali_telemetry') {
                    if (chartDef.component.name === 'TelemetryTrace' && !telemetryData) {
                        return (
                            <div key={chartId} className={cn("bg-card rounded-xl border border-white/5 p-8 text-center text-text-secondary shadow-lg", colSpanClass)}>
                                Select a driver to view telemetry
                            </div>
                        );
                    }
                    if (telemetryData) {
                        props.driver = telemetryData.driver;
                        props.color = telemetryData.color;
                        props.distance = telemetryData.distance;
                        props.speed = telemetryData.speed;
                        props.throttle = telemetryData.throttle;
                        props.brake = telemetryData.brake;
                        props.corners = telemetryData.corners;
                        props.brakingZones = telemetryData.brakingZones;
                    }
                }

                if (chartId === 'race_pace_sim') {
                    if (!driverLaps || driverLaps.length === 0) return null;
                    props.laps = driverLaps;
                    props.driver = selectedDriver;
                    props.color = driverColor;
                }

                return (
                    <div
                        key={chartId}
                        draggable={isDraggable}
                        onDragStart={(e) => handleDragStart(e, chartId)}
                        onDragOver={(e) => handleDragOver(e, chartId)}
                        onDragEnd={handleDragEnd}
                        className={cn(
                            "group bg-card rounded-xl border border-white/5 shadow-lg flex flex-col transition-all duration-200 ease-in-out hover:border-white/20 select-none w-full relative",
                            colSpanClass,
                            draggedItem === chartId ? "opacity-30 z-50 ring-2 ring-accent scale-[0.98]" : "opacity-100 z-0",
                            isAnyExpanded && !isExpanded ? "opacity-40 grayscale" : "", // Visual cue when locked
                            isExpanded ? "z-10" : "" // Expanded items slightly elevated
                        )}
                        style={{ minHeight: isExpanded ? '600px' : (chartDef.height || '400px') }}
                    >
                        {/* Header / Controls Overlay */}
                        <div className="absolute top-2 right-2 z-20 flex items-center gap-1 opacity-100 transition-opacity bg-black/40 backdrop-blur rounded p-1">
                            {/* Drag Handle */}
                            <div className={cn(
                                "p-1 text-text-secondary hover:text-white transition-colors",
                                isDraggable ? "cursor-grab active:cursor-grabbing" : "cursor-not-allowed opacity-50"
                            )}>
                                <GripHorizontal size={14} />
                            </div>

                            {/* Expand/Collapse */}
                            <button
                                onClick={() => toggleExpand(chartId)}
                                className="p-1 text-text-secondary hover:text-white hover:bg-white/10 rounded"
                                title={isExpanded ? "Collapse" : "Expand"}
                            >
                                {isExpanded ? <Minimize2 size={14} /> : <Maximize2 size={14} />}
                            </button>
                        </div>

                        {/* Title if not built-in (Most charts have titles inside Plotly, but for consistency maybe?) 
                            Actually, Plotly titles are inside the canvas. We'll leave them there. 
                        */}

                        {/* Chart Content */}
                        <div className="flex-1 w-full h-full p-2 relative">
                            {/* Adding a ResizeObserver wrapper implicitly via CSS flex-1 */}
                            <ChartComponent {...props} />
                        </div>
                    </div>
                );
            })}
        </div>
    );
}
