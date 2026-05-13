import { render, screen } from "@testing-library/react";
import { vi, describe, it, expect, beforeEach } from "vitest";
import DashboardLayout from "../components/DashboardLayout";
import { useAuth } from "../_core/hooks/useAuth";
import { trpc } from "../lib/trpc";
import { ReactNode } from "react";

// Mock useAuth
vi.mock("../_core/hooks/useAuth", () => ({
  useAuth: vi.fn(),
}));

// Mock trpc
vi.mock("../lib/trpc", () => ({
  trpc: {
    useUtils: vi.fn(() => ({
      auth: { me: { invalidate: vi.fn() } }
    })),
    auth: {
      logout: { useMutation: vi.fn(() => ({ mutateAsync: vi.fn() })) },
      me: { useQuery: vi.fn() }
    },
    notification: {
      list: { useQuery: vi.fn(() => ({ data: [] })) }
    }
  },
}));

// Mock lucide-react
vi.mock("lucide-react", () => ({
  LayoutDashboard: () => <div data-testid="icon-dashboard" />,
  Map: () => <div data-testid="icon-map" />,
  Package: () => <div data-testid="icon-package" />,
  Zap: () => <div data-testid="icon-zap" />,
  Terminal: () => <div data-testid="icon-terminal" />,
  Server: () => <div data-testid="icon-server" />,
  Bell: () => <div data-testid="icon-bell" />,
  Activity: () => <div data-testid="icon-activity" />,
  ShieldCheck: () => <div data-testid="icon-shield" />,
  LogOut: () => <div data-testid="icon-logout" />,
  PanelLeft: () => <div data-testid="icon-panel" />,
  ChevronDown: () => <div data-testid="icon-chevron" />,
  Loader2: () => <div data-testid="icon-loader" />,
  ArrowRight: () => <div data-testid="icon-arrow" />,
  HardDrive: () => <div data-testid="icon-harddrive" />,
}));

// Mock wouter
vi.mock("wouter", () => ({
  Link: ({ children, href }: { children: ReactNode; href: string }) => <a href={href}>{children}</a>,
  useLocation: vi.fn(() => ["/", vi.fn()]),
  useRoute: vi.fn(() => [true, {}]),
}));

// Mock Sidebar components (since they rely on complex context)
vi.mock("@/components/ui/sidebar", () => ({
  Sidebar: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  SidebarContent: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  SidebarFooter: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  SidebarHeader: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  SidebarInset: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  SidebarMenu: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  SidebarMenuButton: ({ children, asChild }: { children: ReactNode, asChild?: boolean }) => asChild ? <>{children}</> : <button>{children}</button>,
  SidebarMenuItem: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  SidebarProvider: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  SidebarTrigger: () => <button>Toggle</button>,
  useSidebar: () => ({ isMobile: false, state: "expanded", open: true, setOpen: vi.fn() }),
}));

describe("Phoenix Control Center Routing & Shell", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders the DashboardLayout shell when authenticated", () => {
    (useAuth as any).mockReturnValue({
      user: { email: "test@phoenix.io", role: "user" },
      loading: false,
      isAuthenticated: true,
    });

    render(
      <DashboardLayout>
        <div data-testid="content">Dashboard Content</div>
      </DashboardLayout>
    );

    expect(screen.getByTestId("icon-activity")).toBeInTheDocument();
    expect(screen.getByTestId("content")).toBeInTheDocument();
  });

  it("contains all canonical platform navigation links", () => {
    (useAuth as any).mockReturnValue({
      user: { email: "test@phoenix.io", role: "user" },
      loading: false,
      isAuthenticated: true,
    });

    render(
      <DashboardLayout>
        <div>Content</div>
      </DashboardLayout>
    );

    const expectedLinks = [
      { text: "Overview", href: "/" },
      { text: "God View", href: "/god-view" },
      { text: "Recipe Builder", href: "/recipe-builder" },
      { text: "Imaging", href: "/imaging" },
      { text: "Deployments", href: "/deployments" },
      { text: "Boot Camp", href: "/bootcamp" },
      { text: "Relay Controls", href: "/relay" },
      { text: "Notifications", href: "/notifications" },
      { text: "System Health", href: "/monitoring" },
    ];

    expectedLinks.forEach(link => {
      expect(screen.getByText(new RegExp(link.text, "i"))).toBeInTheDocument();
      const anchor = screen.getByText(new RegExp(link.text, "i")).closest('a');
      expect(anchor).toHaveAttribute('href', link.href);
    });
  });

  it("hides Admin link for non-admin users", () => {
    (useAuth as any).mockReturnValue({
      user: { email: "test@phoenix.io", role: "user" },
      loading: false,
      isAuthenticated: true,
    });

    render(
      <DashboardLayout>
        <div>Content</div>
      </DashboardLayout>
    );

    expect(screen.queryByText("Admin")).not.toBeInTheDocument();
  });

  it("shows Admin link for owner role", () => {
    (useAuth as any).mockReturnValue({
      user: { email: "owner@phoenix.io", role: "owner" },
      loading: false,
      isAuthenticated: true,
    });

    render(
      <DashboardLayout>
        <div>Content</div>
      </DashboardLayout>
    );

    expect(screen.getByText(/Admin/i)).toBeInTheDocument();
    const anchor = screen.getByText(/Admin/i).closest('a');
    expect(anchor).toHaveAttribute('href', "/admin");
  });

  it("requires authentication in DashboardLayout", () => {
    (useAuth as any).mockReturnValue({
      user: null,
      loading: false,
      isAuthenticated: false,
    });

    render(
      <DashboardLayout>
        <div>Content</div>
      </DashboardLayout>
    );

    expect(screen.getByText(/Sign in to continue/i)).toBeInTheDocument();
    expect(screen.queryByText(/Phoenix OS/i)).not.toBeInTheDocument();
  });
});
