import { useEffect, useState } from "react";
import { trpc } from "@/lib/trpc";
import { useAuth } from "@/_core/hooks/useAuth";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { AlertCircle, Activity, Zap, Server, Search, RefreshCw } from "lucide-react";

interface FleetStats {
  totalDevices: number;
  onlineCount: number;
  offlineCount: number;
  errorCount: number;
  deployingCount: number;
}

export default function GodViewDashboard() {
  const { user } = useAuth();
  const [searchTerm, setSearchTerm] = useState("");
  const [fleetStats, setFleetStats] = useState<FleetStats>({
    totalDevices: 0,
    onlineCount: 0,
    offlineCount: 0,
    errorCount: 0,
    deployingCount: 0,
  });

  // Fetch fleet data
  const { data: fleetData, isLoading, refetch } = trpc.fleet.listDevices.useQuery({});

  useEffect(() => {
    if (fleetData?.devices) {
      setFleetStats({
        totalDevices: fleetData.devices.length,
        onlineCount: fleetData.onlineCount || 0,
        offlineCount: fleetData.offlineCount || 0,
        errorCount: fleetData.errorCount || 0,
        deployingCount: fleetData.devices.filter((d: any) => d.status === "deploying").length,
      });
    }
  }, [fleetData]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case "online":
        return "bg-green-500 text-white";
      case "offline":
        return "bg-gray-500 text-white";
      case "error":
        return "bg-red-500 text-white";
      case "deploying":
        return "bg-blue-500 text-white";
      default:
        return "bg-gray-400 text-white";
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "online":
        return <Activity className="w-4 h-4" />;
      case "offline":
        return <Server className="w-4 h-4" />;
      case "error":
        return <AlertCircle className="w-4 h-4" />;
      case "deploying":
        return <Zap className="w-4 h-4" />;
      default:
        return null;
    }
  };

  const filteredDevices = (fleetData?.devices || []).filter((device: any) =>
    device.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    device.ipAddress?.includes(searchTerm) ||
    device.macAddress?.includes(searchTerm)
  );

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-bold text-foreground tracking-tight flex items-center gap-3">
            <Activity className="w-8 h-8 text-primary" />
            God View
          </h1>
          <p className="text-muted-foreground mt-2 text-lg">Real-time fleet monitoring and management</p>
        </div>
        <Button
          onClick={() => refetch()}
          variant="outline"
          size="lg"
          className="gap-3 shadow-premium border-primary/20 hover:bg-primary/5"
        >
          <RefreshCw className="w-4 h-4" />
          Synchronize Fleet
        </Button>
      </div>

        {/* Fleet Statistics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
          <Card className="shadow-premium hover-glow">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-muted-foreground">Total Devices</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">{fleetStats.totalDevices}</div>
              <p className="text-xs text-muted-foreground mt-1">Across all locations</p>
            </CardContent>
          </Card>

          <Card className="shadow-premium hover-glow bg-green-50 dark:bg-green-950">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-green-700 dark:text-green-300">Online</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-green-600 dark:text-green-400">{fleetStats.onlineCount}</div>
              <p className="text-xs text-green-600 dark:text-green-400 mt-1">Ready for deployment</p>
            </CardContent>
          </Card>

          <Card className="shadow-premium hover-glow bg-gray-50 dark:bg-gray-950">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-gray-700 dark:text-gray-300">Offline</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-gray-600 dark:text-gray-400">{fleetStats.offlineCount}</div>
              <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">Unreachable</p>
            </CardContent>
          </Card>

          <Card className="shadow-premium hover-glow bg-red-50 dark:bg-red-950">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-red-700 dark:text-red-300">Errors</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-red-600 dark:text-red-400">{fleetStats.errorCount}</div>
              <p className="text-xs text-red-600 dark:text-red-400 mt-1">Require attention</p>
            </CardContent>
          </Card>

          <Card className="shadow-premium hover-glow bg-blue-50 dark:bg-blue-950">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-blue-700 dark:text-blue-300">Deploying</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-blue-600 dark:text-blue-400">{fleetStats.deployingCount}</div>
              <p className="text-xs text-blue-600 dark:text-blue-400 mt-1">Active jobs</p>
            </CardContent>
          </Card>
        </div>

        {/* Search and Filter */}
        <div className="flex gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-3 w-4 h-4 text-muted-foreground" />
            <Input
              placeholder="Search by device name, IP, or MAC address..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
            />
          </div>
        </div>

        {/* Devices Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {isLoading ? (
            <div className="col-span-full text-center py-12">
              <p className="text-muted-foreground">Loading devices...</p>
            </div>
          ) : filteredDevices.length === 0 ? (
            <div className="col-span-full text-center py-12">
              <p className="text-muted-foreground">No devices found</p>
            </div>
          ) : (
            filteredDevices.map((device: any) => (
              <Card key={device.id} className="shadow-md hover:shadow-lg transition-shadow">
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <CardTitle className="text-lg">{device.name}</CardTitle>
                      <CardDescription className="text-xs mt-1">{device.deviceId}</CardDescription>
                    </div>
                    <Badge className={`${getStatusColor(device.status)} gap-1`}>
                      {getStatusIcon(device.status)}
                      {device.status}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    <div>
                      <p className="text-muted-foreground">OS Type</p>
                      <p className="font-medium capitalize">{device.osType}</p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">IP Address</p>
                      <p className="font-medium font-mono text-xs">{device.ipAddress || "N/A"}</p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">MAC Address</p>
                      <p className="font-medium font-mono text-xs">{device.macAddress || "N/A"}</p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">Last Seen</p>
                      <p className="font-medium text-xs">
                        {device.lastHeartbeat
                          ? new Date(device.lastHeartbeat).toLocaleTimeString()
                          : "Never"}
                      </p>
                    </div>
                  </div>

                  {/* Hardware Profile */}
                  {device.hardwareProfile && (
                    <div className="border-t pt-3 space-y-2">
                      <p className="text-xs font-semibold text-muted-foreground">Hardware</p>
                      <div className="grid grid-cols-2 gap-2 text-xs">
                        <div>
                          <p className="text-muted-foreground">CPU</p>
                          <p className="font-medium truncate">{device.hardwareProfile.cpu?.model || "Unknown"}</p>
                        </div>
                        <div>
                          <p className="text-muted-foreground">RAM</p>
                          <p className="font-medium">{device.hardwareProfile.ram?.total || 0} GB</p>
                        </div>
                      </div>
                    </div>
                  )}

                  <Button className="w-full mt-2" variant="outline" size="sm">
                    View Details
                  </Button>
                </CardContent>
              </Card>
            ))
          )}
        </div>
    </div>
  );
}
