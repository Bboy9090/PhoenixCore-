import { useAuth } from "@/_core/hooks/useAuth";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Globe,
  Zap,
  Package,
  Activity,
  HardDrive,
  Cpu,
  Shield,
  Bell,
  Compass,
  BarChart3,
  ArrowRight,
  Loader2,
  Server,
} from "lucide-react";
import { Link } from "wouter";
import { getLoginUrl } from "@/const";

const FEATURES = [
  {
    id: "god-view",
    title: "God View Dashboard",
    description: "Real-time fleet monitoring with live device status, deployment tracking, and fleet analytics",
    icon: Globe,
    color: "from-blue-500 to-cyan-500",
    badge: "Fleet Management",
  },
  {
    id: "recipe-builder",
    title: "USB Recipe Builder",
    description: "Drag-and-drop interface to compose bootable USB configurations with automatic size estimation",
    icon: Package,
    color: "from-purple-500 to-pink-500",
    badge: "Deployment",
  },
  {
    id: "imaging",
    title: "Governed Imaging",
    description: "Policy-driven OS deployment simulation with preview analysis and multi-stage safety verification",
    icon: HardDrive,
    color: "from-cyan-500 to-blue-500",
    badge: "Policy-Driven",
  },
  {
    id: "deployments",
    title: "Deployment Tracker",
    description: "Monitor real-time installation progress with live log streaming and deployment history",
    icon: Zap,
    color: "from-orange-500 to-red-500",
    badge: "Real-Time",
  },
  {
    id: "bootcamp",
    title: "Boot Camp Driver Manager",
    description: "Browse, search, and deploy Windows drivers to Mac hardware with compatibility checks",
    icon: HardDrive,
    color: "from-green-500 to-emerald-500",
    badge: "Mac Support",
  },
  {
    id: "relay",
    title: "Phoenix Relay Controls",
    description: "Manage hybrid cloud-edge relay nodes, monitor cache health, and configure sync policies",
    icon: Server,
    color: "from-emerald-500 to-teal-500",
    badge: "Infrastructure",
  },
  {
    id: "notifications",
    title: "Notification Center",
    description: "Central hub for deployment alerts, fleet anomalies, and critical system notifications",
    icon: Bell,
    color: "from-blue-600 to-indigo-600",
    badge: "System Alerts",
  },
  {
    id: "monitoring",
    title: "API Monitoring Status",
    description: "Live health checks for FastAPI backend, WebSocket server, and Phoenix Relay nodes",
    icon: Activity,
    color: "from-indigo-500 to-blue-500",
    badge: "Health",
  },
  {
    id: "admin",
    title: "Admin Dashboard",
    description: "Manage users, view audit logs, and configure global deployment policies (Owner only)",
    icon: Shield,
    color: "from-red-500 to-pink-500",
    badge: "Admin",
  },
];

export default function Home() {
  const { user } = useAuth();

  return (
    <div className="space-y-10">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-4xl font-bold tracking-tight text-foreground">Phoenix Control Center</h1>
          <p className="text-muted-foreground mt-2 text-lg">
            Welcome back, <span className="text-foreground font-medium">{user?.name || user?.email || "User"}</span>
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Badge variant="outline" className="px-3 py-1 text-sm font-medium border-primary/20 bg-primary/5 text-primary capitalize">
            {user?.role || "user"}
          </Badge>
          <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-green-500/10 text-green-600 border border-green-500/20 text-xs font-semibold">
            <div className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse" />
            Agent Online
          </div>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard title="Active Deployments" value="0" subtitle="In progress" icon={Zap} />
        <StatCard title="Fleet Devices" value="0" subtitle="Online" icon={Server} />
        <StatCard title="System Health" value="100%" subtitle="Operational" icon={Activity} color="text-green-600" />
        <StatCard title="Audit Events" value="12" subtitle="Last 24h" icon={Shield} />
      </div>

      {/* Features Grid */}
      <div className="space-y-6">
        <h2 className="text-2xl font-bold tracking-tight">Platform Services</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {FEATURES.map((feature) => {
            const Icon = feature.icon;
            const isAdminOnly = feature.id === "admin";
            const canAccess = !isAdminOnly || user?.role === "owner" || user?.role === "admin";

            return (
              <Link key={feature.id} href={canAccess ? `/${feature.id}` : "#"}>
                <Card
                  className={`group shadow-premium border-muted/40 hover:border-primary/20 transition-all cursor-pointer h-full overflow-hidden ${
                    !canAccess ? "opacity-50 cursor-not-allowed" : "hover:-translate-y-1 hover:shadow-2xl"
                  }`}
                >
                  <CardHeader className="pb-3 relative">
                    <div className="flex items-start justify-between">
                      <div className={`p-3 rounded-xl bg-gradient-to-br ${feature.color} shadow-lg transition-transform group-hover:scale-110`}>
                        <Icon className="w-6 h-6 text-white" />
                      </div>
                      <Badge variant="secondary" className="text-[10px] uppercase tracking-wider font-bold">
                        {feature.badge}
                      </Badge>
                    </div>
                    <CardTitle className="text-xl mt-5 tracking-tight">{feature.title}</CardTitle>
                    <CardDescription className="text-sm line-clamp-2 leading-relaxed">
                      {feature.description}
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="pt-2">
                    <Button
                      variant="ghost"
                      className="w-full justify-between group-hover:bg-primary/5 transition-colors group-hover:text-primary"
                      disabled={!canAccess}
                    >
                      Open Service
                      <ArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-1" />
                    </Button>
                    {isAdminOnly && user?.role !== "owner" && user?.role !== "admin" && (
                      <p className="text-[10px] text-muted-foreground text-center mt-2 uppercase font-bold tracking-tighter opacity-70">
                        Restricted to owner/admin
                      </p>
                    )}
                  </CardContent>
                </Card>
              </Link>
            );
          })}
        </div>
      </div>
    </div>
  );
}

function StatCard({ title, value, subtitle, icon: Icon, color = "" }: any) {
  return (
    <Card className="shadow-premium border-muted/40 bg-card/50 backdrop-blur-sm">
      <CardHeader className="pb-2 flex flex-row items-center justify-between space-y-0">
        <CardTitle className="text-xs font-bold uppercase tracking-widest text-muted-foreground">
          {title}
        </CardTitle>
        <Icon className="w-4 h-4 text-muted-foreground/50" />
      </CardHeader>
      <CardContent>
        <div className={`text-3xl font-bold tracking-tighter ${color}`}>{value}</div>
        <p className="text-xs text-muted-foreground mt-1 font-medium">{subtitle}</p>
      </CardContent>
    </Card>
  );
}
