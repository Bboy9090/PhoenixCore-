import { render, screen } from "@testing-library/react";
import { vi, describe, it, expect, beforeEach } from "vitest";
import Home from "../pages/Home";
import { useAuth } from "../_core/hooks/useAuth";
import { ReactNode } from "react";

// Mock useAuth
vi.mock("../_core/hooks/useAuth", () => ({
  useAuth: vi.fn(),
}));

// Mock wouter
vi.mock("wouter", () => ({
  Link: ({ children, href }: { children: ReactNode; href: string }) => <a href={href}>{children}</a>,
}));

// Mock lucide-react (to speed up and avoid rendering issues)
vi.mock("lucide-react", async (importOriginal) => {
  const actual = await importOriginal<any>();
  return {
    ...actual,
    Zap: () => <div data-testid="icon-zap" />,
    Server: () => <div data-testid="icon-server" />,
    Activity: () => <div data-testid="icon-activity" />,
    Shield: () => <div data-testid="icon-shield" />,
    ArrowRight: () => <div data-testid="icon-arrow" />,
    Globe: () => <div data-testid="icon-globe" />,
    Package: () => <div data-testid="icon-package" />,
    HardDrive: () => <div data-testid="icon-harddrive" />,
    Bell: () => <div data-testid="icon-bell" />,
    Compass: () => <div data-testid="icon-compass" />,
    BarChart3: () => <div data-testid="icon-barchart" />,
    Loader2: () => <div data-testid="icon-loader" />,
  };
});

describe("Phoenix Control Center Smoke Tests", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders the Home page dashboard with all service cards", () => {
    (useAuth as any).mockReturnValue({
      user: { name: "Bobby", role: "owner" },
      loading: false,
      isAuthenticated: true,
    });

    render(<Home />);

    expect(screen.getByText(/Phoenix Control Center/i)).toBeInTheDocument();
    expect(screen.getByText(/Welcome back/i)).toBeInTheDocument();
    expect(screen.getByText(/Bobby/i)).toBeInTheDocument();

    // Check for major feature cards
    const featureTitles = [
      "God View Dashboard",
      "USB Recipe Builder",
      "Governed Imaging",
      "Deployment Tracker",
      "Boot Camp Driver Manager",
      "Phoenix Relay Controls",
      "Notification Center",
      "API Monitoring Status",
      "Admin Dashboard"
    ];

    featureTitles.forEach(title => {
      expect(screen.getByText(new RegExp(title, "i"))).toBeInTheDocument();
    });
  });

  it("verifies that dashboard cards point to correct canonical routes", () => {
    (useAuth as any).mockReturnValue({
      user: { name: "Bobby", role: "owner" },
      loading: false,
      isAuthenticated: true,
    });

    render(<Home />);

    const cardLinks = [
      { title: "God View Dashboard", href: "/god-view" },
      { title: "USB Recipe Builder", href: "/recipe-builder" },
      { title: "Governed Imaging", href: "/imaging" },
      { title: "Deployment Tracker", href: "/deployments" },
      { title: "Admin Dashboard", href: "/admin" },
    ];

    cardLinks.forEach(link => {
      const card = screen.getByText(new RegExp(link.title, "i")).closest('a');
      expect(card).toHaveAttribute('href', link.href);
    });
  });

  it("labels the Admin Console correctly when restricted", () => {
    (useAuth as any).mockReturnValue({
      user: { name: "Regular User", role: "user" },
      loading: false,
      isAuthenticated: true,
    });

    render(<Home />);

    expect(screen.getByText(/Restricted to owner\/admin/i)).toBeInTheDocument();
  });
});
