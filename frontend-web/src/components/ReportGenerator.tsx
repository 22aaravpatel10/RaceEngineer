"use client";

import { useEffect, useRef, useState } from 'react';
import { useF1Store } from '@/store/useF1Store';
import { CHART_REGISTRY } from '@/lib/chartRegistry';
import html2canvas from 'html2canvas';
import jsPDF from 'jspdf';
import { Download } from 'lucide-react';

export default function ReportGenerator() {
    const { isExporting, setExporting, session, selectedSessionType } = useF1Store();
    const [progress, setProgress] = useState(0);
    const containerRef = useRef<HTMLDivElement>(null);

    // Filter charts based on Export Config only
    const relevantCharts = CHART_REGISTRY.filter(chart => {
        const config = useF1Store.getState().exportConfig[chart.id];

        // If explicitly enabled, show it regardless of session suitability
        if (config && config.enabled) {
            return true;
        }

        // If explicitly disabled, hide it
        if (config && config.enabled === false) {
            return false;
        }

        // If not in config (should default to true in modal, but filter here for safety)
        // We act permissive if using the "Select All" philosophy, but let's default to false if not touched?
        // Actually, the Modal initializes them to TRUE. So if it's missing here, it might be new.
        // Let's default to FALSE to avoid surprises, forcing user to use Modal.
        return false;
    });

    // Flatten the charts to handle pagination (1:N mapping) so DOM matches Logic
    const chartsToRender = relevantCharts.flatMap(chart => {
        const config = useF1Store.getState().exportConfig[chart.id];

        // Handle Pagination for Potential Leaderboard (split into 2 pages)
        if (chart.id === 'potential_leaderboard') {
            return [1, 2].map(page => ({
                ...chart,
                renderId: `${chart.id}_p${page}`,
                page,
                limit: 10,
                config
            }));
        }

        // Handle Pagination for Top Speed (20 drivers -> 2 pages)
        if (chart.id === 'top_speed_chart') {
            return [1, 2].map(page => ({
                ...chart,
                renderId: `${chart.id}_p${page}`,
                page,
                limit: 10, // 10 drivers per page
                config
            }));
        }

        return [{
            ...chart,
            renderId: chart.id,
            config
        }];
    });

    useEffect(() => {
        if (isExporting && session && containerRef.current) {
            generatePDF();
        }
    }, [isExporting, session]);

    const generatePDF = async () => {
        if (!containerRef.current) return;

        try {
            const pdf = new jsPDF({
                orientation: 'landscape',
                unit: 'px',
                format: [1920, 1080] // HD Slide format
            });

            const domChildren = containerRef.current.children;
            const total = chartsToRender.length; // Use our flattened list length

            if (total === 0) {
                alert("No charts selected for export!");
                setExporting(false);
                return;
            }

            // Cover Page
            pdf.setFillColor(20, 20, 20);
            pdf.rect(0, 0, 1920, 1080, 'F');
            pdf.setTextColor(255, 255, 255);
            pdf.setFontSize(60);
            pdf.text("RACE ENGINEERING REPORT", 100, 400);
            pdf.setFontSize(40);
            pdf.setTextColor(200, 200, 200);
            pdf.text(`${session?.year} ${session?.eventName} - ${session?.sessionType}`, 100, 500);
            pdf.setFontSize(20);
            pdf.text(`Generated: ${new Date().toLocaleString()}`, 100, 900);

            setProgress(10); // Started

            // Capture each chart
            for (let i = 0; i < total; i++) {
                const chartMeta = chartsToRender[i];
                const chartEl = domChildren[i] as HTMLElement; // Should match 1:1 now

                // Update progress
                setProgress(10 + Math.round(((i + 1) / total) * 80));

                // Wait a moment for charts to render (especially Plotly)
                // Wait Logic: Ensure chart is actually ready
                // We poll the specific chart element for '.chart-loaded' class OR 'Loading...' text
                const maxWait = 25000; // 25s max safety
                const startWait = Date.now();

                // Loop until ready
                while (true) {
                    const text = chartEl.innerText || "";
                    const isStillLoadingText = text.includes("Loading") || text.includes("CRUNCHING") || text.includes("Generating") || text.includes("Calculating");
                    const hasSpinner = chartEl.querySelector('.animate-spin') !== null;
                    const hasLoadedClass = chartEl.querySelector('.chart-loaded') !== null;

                    // If we have the specific class, we are definitely ready.
                    if (hasLoadedClass) {
                        break;
                    }

                    // Fallback: If no loaded class yet (maybe component hasn't updated), check text/spinner
                    // If we don't see loading text AND don't see spinner, we might be ready? 
                    // But safest is to wait for the class if we know we added it.
                    // To avoid infinite wait on charts I didn't add the class to, we keep the old check too.
                    if (!isStillLoadingText && !hasSpinner && (Date.now() - startWait > 5000)) {
                        // If 5s passed and still silent, maybe it's done?
                        break;
                    }

                    if (Date.now() - startWait > maxWait) {
                        console.warn(`Chart ${i} export timed out (IsLoaded: ${hasLoadedClass}), capturing anyway...`);
                        break;
                    }

                    // Simple delay between checks
                    await new Promise(r => setTimeout(r, 500));
                }

                // Extra buffer for rendering (canvas paint) - increased for Plotly
                await new Promise(r => setTimeout(r, 1500));

                const canvas = await html2canvas(chartEl, {
                    scale: 2, // High res
                    backgroundColor: '#000000',
                    logging: false,
                    useCORS: true
                } as any);

                const imgData = canvas.toDataURL('image/jpeg', 0.9);

                pdf.addPage([1920, 1080], 'landscape');
                pdf.setFillColor(10, 10, 10);
                pdf.rect(0, 0, 1920, 1080, 'F'); // Dark Bg

                // Header on slide
                pdf.setTextColor(255, 255, 255);
                pdf.setFontSize(30);

                // Construct Title
                const config = chartMeta.config;
                let title = chartMeta.label;
                if (chartMeta.page) title += ` (Page ${chartMeta.page})`;

                pdf.text(title.toUpperCase(), 40, 50); // Reduced margin

                // Add configured driver info if present
                if (config?.driverOverride) {
                    pdf.setFontSize(20);
                    pdf.setTextColor(150, 150, 150);
                    pdf.text(`Focus: ${config.driverOverride}`, 40, 80);
                }

                // Center Image
                const imgProps = (pdf as any).getImageProperties(imgData);
                const pdfWidth = 1920;
                const pdfHeight = 1080;

                // Fit within reduced margins
                const margin = 40;
                const maxWidth = pdfWidth - (margin * 2);
                const maxHeight = pdfHeight - (margin * 2) - 60; // Extra space for header

                let w = imgProps.width;
                let h = imgProps.height;
                const ratio = w / h;

                if (w > maxWidth) { w = maxWidth; h = w / ratio; }
                if (h > maxHeight) { h = maxHeight; w = h * ratio; }

                const x = (pdfWidth - w) / 2;
                const y = ((pdfHeight - h) / 2) + 40; // Center vertically, offset for header

                pdf.addImage(imgData, 'JPEG', x, y, w, h);
            }

            pdf.save(`F1_Report_${session?.gp}_${session?.sessionType}.pdf`);
        } catch (err) {
            console.error("PDF Export Failed", err);
            alert("Export Failed: " + err);
        } finally {
            setExporting(false);
            setProgress(0);
        }
    };

    if (!isExporting) return null;

    return (
        <div className="fixed inset-0 z-[100] bg-black/90 flex flex-col items-center justify-center text-white">
            <div className="mb-8 flex flex-col items-center gap-4">
                <Download className="w-16 h-16 animate-bounce text-accent" />
                <h2 className="text-3xl font-bold">Generating Report...</h2>
                <div className="w-[400px] h-2 bg-white/10 rounded-full overflow-hidden">
                    <div
                        className="h-full bg-accent transition-all duration-300"
                        style={{ width: `${progress}%` }}
                    />
                </div>
                <p className="font-mono text-sm opacity-60">{progress}% Complete</p>
                <p className="text-xs text-red-400 mt-2">Do not close this window.</p>
            </div>

            {/* Hidden Rendering Container */}
            <div
                ref={containerRef}
                className="absolute top-[200vh] left-0 w-[1920px] h-auto bg-black grid grid-cols-1 gap-20 p-20"
                style={{ visibility: 'visible' }} // Must be visible to render, but off-screen
            >
                {chartsToRender.map(chart => {
                    const ChartComponent = chart.component;
                    const config = chart.config;
                    const driverOverride = config?.driverOverride;
                    const comparisonOverride = config?.comparisonOverride;

                    // Pagination Props (if applicable)
                    // We dynamically passed 'page' and 'limit' into the chart object earlier if needed
                    const pageProps = (chart as any).page ? { page: (chart as any).page, limit: (chart as any).limit } : {};

                    // Dynamic Height Logic: Give simpler charts less space, dense charts more
                    let heightClass = chart.height ? chart.height : 'h-[900px]'; // Default increased to 900px

                    // Specific overrides for export quality
                    if (chart.id === 'potential_leaderboard') heightClass = 'h-[1200px]'; // Ensure 10 items fit easily
                    if (chart.id === 'telemetry_trace') heightClass = 'h-[1000px]'; // Tall for traces
                    if (chart.id === 'tyre_health') heightClass = 'h-[950px]';
                    if (chart.id === 'pit_rejoin_gantt') heightClass = 'h-[800px]'; // More space for rows + legend
                    if (chart.id === 'top_speed_chart') heightClass = 'h-[1000px]'; // Fit 10 rows spaciously

                    return (
                        <div key={(chart as any).renderId} className="w-full h-auto min-h-0 bg-[#1C1C1E] p-8 rounded-xl border border-white/20 chart-export-container">
                            <h2 className="text-4xl text-white font-bold mb-6 uppercase tracking-wider">
                                {chart.label}
                                {(chart as any).page ? ` (Page ${(chart as any).page})` : ''}
                                {driverOverride ? ` [${driverOverride}]` : ''}
                                {comparisonOverride ? ` vs [${comparisonOverride}]` : ''}
                            </h2>
                            <div className={`w-full ${heightClass} relative`}>
                                <ChartComponent
                                    driverOverride={driverOverride}
                                    comparisonOverride={comparisonOverride}
                                    {...pageProps}
                                />
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
}
