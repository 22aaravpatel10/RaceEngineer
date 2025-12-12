import { TelemetryTrace } from '@/components/charts/TelemetryTrace';
import { RacePaceChart } from '@/components/charts/RacePaceChart';
import { TheWormChart } from '@/components/charts/TheWormChart';
import { FuelCorrectedScatter } from '@/components/charts/FuelCorrectedScatter';
import { GhostDeltaTrace } from '@/components/charts/GhostDeltaTrace';
import TheoreticalBestLapChart from '@/components/charts/TheoreticalBestLapChart';
import FastestLapTelemetryChart from '@/components/charts/FastestLapTelemetryChart';
import { PitRejoinGantt } from '@/components/charts/PitRejoinGantt';
import { ConsistencyBoxPlot } from '@/components/charts/ConsistencyBoxPlot';
import TopSpeedChart from '@/components/charts/TopSpeedChart';

export type ChartCategory = 'PRACTICE' | 'QUALI' | 'RACE' | 'GENERAL';

export interface ChartDefinition {
    id: string;
    label: string;
    category: ChartCategory;
    component: React.ComponentType<any>;
    gridCols?: string; // e.g., 'col-span-1' or 'col-span-2'
    height?: string; // tailwind height class
}

export const CHART_REGISTRY: ChartDefinition[] = [
    // Practice
    {
        id: 'telemetry_trace',
        label: 'Multi-Lap Telemetry',
        category: 'PRACTICE',
        component: TelemetryTrace,
        gridCols: 'col-span-1 lg:col-span-2',
        height: 'h-[400px]'
    },
    {
        id: 'race_pace_sim',
        label: 'Race Pace Simulation',
        category: 'PRACTICE',
        component: RacePaceChart,
        gridCols: 'col-span-1',
        height: 'h-[400px]'
    },

    // Quali
    {
        id: 'quali_telemetry',
        label: 'Fastest Lap Telemetry',
        category: 'QUALI',
        component: FastestLapTelemetryChart,
        gridCols: 'col-span-1 lg:col-span-2',
        height: 'h-[400px]'
    },
    {
        id: 'ghost_delta',
        label: 'Ghost Delta Trace',
        category: 'QUALI',
        component: GhostDeltaTrace,
        gridCols: 'col-span-1',
        height: 'h-[350px]'
    },
    {
        id: 'theoretical_best',
        label: 'Theoretical Best Lap',
        category: 'QUALI',
        component: TheoreticalBestLapChart,
        gridCols: 'col-span-1 lg:col-span-2',
        height: 'h-[500px]'
    },

    // Race
    {
        id: 'the_worm',
        label: 'Race Gaps (The Worm)',
        category: 'RACE',
        component: TheWormChart,
        gridCols: 'col-span-1 lg:col-span-2',
        height: 'h-[500px]'
    },
    {
        id: 'fuel_scatter',
        label: 'Fuel Corrected Pace',
        category: 'RACE',
        component: FuelCorrectedScatter,
        gridCols: 'col-span-1',
        height: 'h-[350px]'
    },
    {
        id: 'pit_rejoin_gantt',
        label: 'Tyre Strategy Gantt',
        component: PitRejoinGantt,
        category: 'RACE',
        gridCols: 'col-span-1 lg:col-span-2',
        height: 'h-[600px]'
    },
    {
        id: 'top_speed_chart',
        label: 'Top Speed History',
        component: TopSpeedChart,
        category: 'RACE',
        gridCols: 'col-span-1 lg:col-span-2',
        height: 'h-[400px]'
    },
    {
        id: 'consistency_box',
        label: 'Lap Time Consistency',
        category: 'RACE',
        component: ConsistencyBoxPlot,
        gridCols: 'col-span-1 lg:col-span-2',
        height: 'h-[400px]'
    }
];
