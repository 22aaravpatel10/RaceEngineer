import MultiLapTelemetryChart from '@/components/charts/MultiLapTelemetryChart';
import { RacePaceChart } from '@/components/charts/RacePaceChart';
import { TheWormChart } from '@/components/charts/TheWormChart';
import { FuelCorrectedScatter } from '@/components/charts/FuelCorrectedScatter';
import { GhostDeltaTrace } from '@/components/charts/GhostDeltaTrace';
import TheoreticalBestLapChart from '@/components/charts/TheoreticalBestLapChart';
import FastestLapTelemetryChart from '@/components/charts/FastestLapTelemetryChart';
import { PitRejoinGantt } from '@/components/charts/PitRejoinGantt';
import { ConsistencyBoxPlot } from '@/components/charts/ConsistencyBoxPlot';
import TopSpeedChart from '@/components/charts/TopSpeedChart';
import PotentialLeaderboard from '@/components/charts/PotentialLeaderboard';
import TyreHealthChart from '@/components/charts/TyreHealthChart';

export type ChartCategory = 'PRACTICE' | 'QUALI' | 'RACE' | 'GENERAL';

export interface ChartDefinition {
    id: string;
    label: string;
    category: ChartCategory;
    component: React.ComponentType<any>;
    gridCols?: string; // e.g., 'col-span-6' (half) or 'col-span-12' (full)
    height?: string; // tailwind height class
    description?: string; // Short 3-4 word description for export menu
    needsDriver?: boolean; // If true, export menu allows driver selection
    needsComparison?: boolean; // If true, export menu allows secondary driver selection
}

export const CHART_REGISTRY: ChartDefinition[] = [
    // Practice
    {
        id: 'telemetry_trace',
        label: 'Multi-Lap Telemetry',
        category: 'PRACTICE',
        component: MultiLapTelemetryChart,
        gridCols: 'col-span-full lg:col-span-12',
        height: 'h-[400px]',
        description: 'Speed/Throttle trace over multiple laps',
        needsDriver: true
    },
    {
        id: 'race_pace_sim',
        label: 'Race Pace Simulation',
        category: 'PRACTICE',
        component: RacePaceChart,
        gridCols: 'col-span-full lg:col-span-12',
        height: 'h-[400px]',
        description: 'Scatter plot of lap times vs fuel'
    },

    // Quali
    {
        id: 'quali_telemetry',
        label: 'Fastest Lap Telemetry',
        category: 'QUALI',
        component: FastestLapTelemetryChart,
        gridCols: 'col-span-full lg:col-span-12',
        height: 'h-[400px]',
        description: 'Detailed telemetry for fastest lap',
        needsDriver: true,
        needsComparison: true
    },
    {
        id: 'ghost_delta',
        label: 'Ghost Delta Trace',
        category: 'QUALI',
        component: GhostDeltaTrace,
        gridCols: 'col-span-full lg:col-span-12',
        height: 'h-[350px]',
        description: 'GPS time delta against rival',
        needsDriver: true,
        needsComparison: true
    },
    {
        id: 'theoretical_best',
        label: 'Theoretical Best Lap',
        category: 'QUALI',
        component: TheoreticalBestLapChart,
        gridCols: 'col-span-full lg:col-span-12',
        height: 'h-[500px]',
        description: 'Mini-sector analysis for best lap',
        needsDriver: true,
        needsComparison: true
    },

    // Race
    {
        id: 'the_worm',
        label: 'Race Gaps (The Worm)',
        category: 'RACE',
        component: TheWormChart,
        gridCols: 'col-span-full lg:col-span-12',
        height: 'h-[500px]',
        description: 'Race gap evolution to leader'
    },
    {
        id: 'fuel_scatter',
        label: 'Fuel Corrected Pace',
        category: 'RACE',
        component: FuelCorrectedScatter,
        gridCols: 'col-span-full lg:col-span-12',
        height: 'h-[350px]',
        description: 'Pace adjusted for fuel load'
    },
    {
        id: 'pit_rejoin_gantt',
        label: 'Tyre Strategy Gantt',
        component: PitRejoinGantt,
        category: 'RACE',
        gridCols: 'col-span-full lg:col-span-12',
        height: 'h-[600px]',
        description: 'Tyre stints and pit window'
    },
    {
        id: 'top_speed_chart',
        label: 'Top Speed History',
        component: TopSpeedChart,
        category: 'RACE',
        gridCols: 'col-span-full lg:col-span-12',
        height: 'h-[400px]',
        description: 'Maximum speeds by driver'
    },
    {
        id: 'consistency_box',
        label: 'Lap Time Consistency',
        category: 'RACE',
        component: ConsistencyBoxPlot,
        gridCols: 'col-span-full lg:col-span-12',
        height: 'h-[400px]',
        description: 'Lap time spread distribution'
    },
    {
        id: 'potential_leaderboard',
        label: 'Potential Unlocked (Mini-Sectors)',
        component: PotentialLeaderboard,
        gridCols: 'col-span-full lg:col-span-12',
        height: 'h-[500px]',
        category: 'QUALI',
        description: 'Total potential unlocked %'
    },
    {
        id: 'tyre_health',
        label: 'Tyre Degradation (Fuel Corrected)',
        category: 'RACE',
        component: TyreHealthChart,
        gridCols: 'col-span-full lg:col-span-12',
        height: 'h-[400px]',
        description: 'Tyre degradation (s/lap loss)'
    }
];
