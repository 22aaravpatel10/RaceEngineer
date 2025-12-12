import { TelemetryTrace } from '@/components/charts/TelemetryTrace';
import { RacePaceChart } from '@/components/charts/RacePaceChart';
import { TheWormChart } from '@/components/charts/TheWormChart';
import { FuelCorrectedScatter } from '@/components/charts/FuelCorrectedScatter';
import { GhostDeltaTrace } from '@/components/charts/GhostDeltaTrace';
import { PitRejoinGantt } from '@/components/charts/PitRejoinGantt';

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
        gridCols: 'col-span-1 lg:col-span-1',
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
        component: TelemetryTrace,
        gridCols: 'col-span-1',
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

    // Race
    {
        id: 'the_worm',
        label: 'Race Gaps (The Worm)',
        category: 'RACE',
        component: TheWormChart,
        gridCols: 'col-span-1 lg:col-span-2',
        height: 'h-[350px]'
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
        id: 'strategy_gantt',
        label: 'Tyre Strategy Gantt',
        category: 'RACE',
        component: PitRejoinGantt,
        gridCols: 'col-span-1 lg:col-span-2',
        height: 'h-[350px]'
    }
];
