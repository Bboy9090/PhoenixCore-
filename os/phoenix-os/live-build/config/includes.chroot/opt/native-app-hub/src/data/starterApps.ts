import {
  Terminal,
  ShoppingBag,
  Wrench,
  Activity,
  ShieldAlert,
  PenTool,
  BookHeart,
  Music
} from 'lucide-react';

export type AppGroup = {
  id: string;
  name: string;
  description: string;
};

export type StarterApp = {
  id: string;
  name: string;
  groupId: string;
  pitch: string;
  command: string;
  icon: any; // Lucide Icon component
};

export const GROUPS: AppGroup[] = [
  {
    id: 'system-core',
    name: 'System Core',
    description: 'Operational control and local software discovery'
  },
  {
    id: 'repair-and-recovery',
    name: 'Repair and Recovery',
    description: 'Repair-first identity for recovery, diagnostics, and compliance'
  },
  {
    id: 'creative-and-personal',
    name: 'Creative and Personal',
    description: 'Creation, reflection, and personal media workflows'
  }
];

export const STARTER_APPS: StarterApp[] = [
  {
    id: 'command',
    name: 'Command',
    groupId: 'system-core',
    pitch: 'Live system control center and suite readiness dashboard',
    command: 'python3 command.py',
    icon: Terminal
  },
  {
    id: 'market',
    name: 'Market',
    groupId: 'system-core',
    pitch: 'Curated local catalog for the validated starter suite',
    command: 'python3 market.py',
    icon: ShoppingBag
  },
  {
    id: 'bootforge',
    name: 'BootForge',
    groupId: 'repair-and-recovery',
    pitch: 'Safe boot media validation and dry-run planning',
    command: 'python3 bootforge.py',
    icon: ShieldAlert
  },
  {
    id: 'workshop',
    name: 'Workshop',
    groupId: 'repair-and-recovery',
    pitch: 'Live diagnostics and repair posture for the host machine',
    command: 'python3 workshop.py',
    icon: Wrench
  },
  {
    id: 'reforge',
    name: 'Reforge',
    groupId: 'repair-and-recovery',
    pitch: 'Responsible recovery routing with stored attestations',
    command: 'python3 reforge.py',
    icon: Activity
  },
  {
    id: 'ghost-writer',
    name: 'Ghost Writer',
    groupId: 'creative-and-personal',
    pitch: 'Template-driven writing studio with persistent local projects',
    command: 'python3 ghost_writer.py',
    icon: PenTool
  },
  {
    id: 'soul-codex',
    name: 'Soul Journey',
    groupId: 'creative-and-personal',
    pitch: 'Reflection, journaling, and insight tracking with real saved state',
    command: 'python3 soul_codex.py',
    icon: BookHeart
  },
  {
    id: 'sonic-codex',
    name: 'Sonic Jams',
    groupId: 'creative-and-personal',
    pitch: 'Import, preview, and export audio projects with waveform data',
    command: 'python3 sonic_codex.py',
    icon: Music
  }
];
