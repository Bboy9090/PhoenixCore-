import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { vi, describe, it, expect, beforeEach } from "vitest";
import ImagingPage from "../pages/Imaging";
import { trpc } from "../lib/trpc";
import { ReactNode } from "react";

// Mock TRPC
vi.mock("../lib/trpc", () => ({
  trpc: {
    recipe: {
      list: { useQuery: vi.fn(() => ({ data: [{ id: 1, name: "Test Recipe", osImage: { name: "Test OS" }, estimatedSize: "1.5" }] })) }
    },
    hardware: {
      detectConnected: { useQuery: vi.fn(() => ({ data: { devices: [{ id: 1, name: "Test Drive", osType: "windows", status: "online" }] } })) }
    },
    operation: {
      preview: { useMutation: vi.fn(() => ({ mutateAsync: vi.fn(() => Promise.resolve({ proposedChanges: [], risks: [] })), isPending: false })) },
      evaluate: { useQuery: vi.fn(() => ({ data: { allowed: true, requirements: ["Consent"] }, isLoading: false })) },
      confirm: { useMutation: vi.fn(() => ({ mutateAsync: vi.fn(() => Promise.resolve({ confirmationToken: "mock-token" })), isPending: false })) },
      execute: { useMutation: vi.fn(() => ({ mutateAsync: vi.fn(() => Promise.resolve({ jobId: "mock-job" })), isPending: false })) },
      status: { useQuery: vi.fn(() => ({ data: { state: "executing", progressPercent: 45, logs: [] }, isLoading: false })) },
      audit: { useQuery: vi.fn(() => ({ data: { record: {}, signedBy: "Test" }, isLoading: false })) },
    }
  },
}));

// Mock lucide-react
vi.mock("lucide-react", () => ({
  HardDrive: () => <div data-testid="icon-harddrive" />,
  ShieldCheck: () => <div data-testid="icon-shield" />,
  ShieldAlert: () => <div data-testid="icon-shield-alert" />,
  AlertTriangle: () => <div data-testid="icon-alert" />,
  Loader2: () => <div data-testid="icon-loader" />,
  ArrowRight: () => <div data-testid="icon-arrow" />,
  CheckCircle2: () => <div data-testid="icon-check" />,
  XCircle: () => <div data-testid="icon-x" />,
  Terminal: () => <div data-testid="icon-terminal" />,
  Info: () => <div data-testid="icon-info" />,
  Zap: () => <div data-testid="icon-zap" />,
  Search: () => <div data-testid="icon-search" />,
  Play: () => <div data-testid="icon-play" />,
  Activity: () => <div data-testid="icon-activity" />,
  FileText: () => <div data-testid="icon-filetext" />,
  LayoutDashboard: () => <div data-testid="icon-dashboard" />,
}));

// Mock ScrollArea (Radix UI)
vi.mock("@/components/ui/scroll-area", () => ({
  ScrollArea: ({ children }: { children: ReactNode }) => <div data-testid="scroll-area">{children}</div>,
  ScrollBar: () => <div />,
}));

// Mock toast
vi.mock("sonner", () => ({
  toast: {
    error: vi.fn(),
    success: vi.fn(),
  }
}));

describe("Imaging Dashboard UI", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders the imaging dashboard with mock simulation warnings", () => {
    render(<ImagingPage />);
    expect(screen.getByText(/Governed Imaging/i)).toBeInTheDocument();
    expect(screen.getByText(/Non-Destructive Simulation Mode/i)).toBeInTheDocument();
  });

  it("identifies policy-driven target selection", () => {
    render(<ImagingPage />);
    expect(screen.getByText(/2. Select Target Device/i)).toBeInTheDocument();
    expect(screen.getByText(/Select a connected removable drive/i)).toBeInTheDocument();
  });
});
