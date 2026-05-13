import { useEffect, useState } from "react";
import { trpc } from "@/lib/trpc";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Activity, AlertTriangle, CheckCircle, Clock } from "lucide-react";

interface ServiceHealth {
  serviceName: string;
  status: "healthy" | "degraded" | "offline";
  latency: number | null;
  uptime: string | null;
  lastCheck: Date;
}

export default function MonitoringStatus() {
  const [services, setServices] = useState<ServiceHealth[]>([]);

  const { data: systemHealth, isLoading } = trpc.monitoring.getSystemHealth.useQuery();

  useEffect(() => {
    if (systemHealth?.metrics) {
      setServices(systemHealth.metrics);
    }
  }, [systemHealth]);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "healthy":
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case "degraded":
        return <AlertTriangle className="w-5 h-5 text-yellow-500" />;
      case "offline":
        return <AlertTriangle className="w-5 h-5 text-red-500" />;
      default:
        return <Activity className="w-5 h-5 text-gray-500" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "healthy":
        return "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200";
      case "degraded":
        return "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200";
      case "offline":
        return "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200";
      default:
        return "bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200";
    }
  };

  const overallStatus = systemHealth?.overallStatus || "unknown";

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-4xl font-bold text-foreground tracking-tight flex items-center gap-3">
          <Activity className="w-8 h-8 text-primary" />
          System Monitoring
        </h1>
        <p className="text-muted-foreground mt-2 text-lg">Real-time health checks for all backend services</p>
      </div>

        {/* Overall Status */}
        <Card className="shadow-premium border-2 border-primary/20">
          <CardHeader>
            <CardTitle className="flex items-center gap-3">
              <Activity className="w-6 h-6" />
              Overall System Status
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Current Status</p>
                <p className="text-2xl font-bold capitalize mt-1">{overallStatus}</p>
              </div>
              <Badge className={`${getStatusColor(overallStatus)} text-lg px-4 py-2`}>
                {overallStatus}
              </Badge>
            </div>
            <p className="text-xs text-muted-foreground mt-4">
              Last updated: {systemHealth?.timestamp ? new Date(systemHealth.timestamp).toLocaleTimeString() : "N/A"}
            </p>
          </CardContent>
        </Card>

        {/* Services Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {isLoading ? (
            <Card className="col-span-full">
              <CardContent className="py-12 text-center">
                <p className="text-muted-foreground">Loading service status...</p>
              </CardContent>
            </Card>
          ) : services.length === 0 ? (
            <Card className="col-span-full">
              <CardContent className="py-12 text-center">
                <p className="text-muted-foreground">No services available</p>
              </CardContent>
            </Card>
          ) : (
            services.map((service) => (
              <Card key={service.serviceName} className="shadow-md">
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3 flex-1">
                      {getStatusIcon(service.status)}
                      <div>
                        <CardTitle className="text-base">{service.serviceName}</CardTitle>
                        <CardDescription className="text-xs mt-1">
                          {service.status === "healthy" ? "Operational" : "Requires attention"}
                        </CardDescription>
                      </div>
                    </div>
                    <Badge className={getStatusColor(service.status)}>
                      {service.status}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  {/* Uptime */}
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <p className="text-sm font-medium">Uptime</p>
                      <p className="text-sm font-bold">{service.uptime || "N/A"}%</p>
                    </div>
                    <Progress value={service.uptime ? parseFloat(service.uptime) : 0} className="h-2" />
                  </div>

                  {/* Latency */}
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <p className="text-muted-foreground">Latency</p>
                      <p className="font-medium">{service.latency || "N/A"}ms</p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">Last Check</p>
                      <p className="font-medium text-xs">
                        {new Date(service.lastCheck).toLocaleTimeString()}
                      </p>
                    </div>
                  </div>

                  {/* Status Indicator */}
                  <div className="pt-2 border-t">
                    <div className="flex items-center gap-2">
                      <div
                        className={`w-3 h-3 rounded-full ${
                          service.status === "healthy"
                            ? "bg-green-500"
                            : service.status === "degraded"
                              ? "bg-yellow-500"
                              : "bg-red-500"
                        }`}
                      />
                      <p className="text-xs text-muted-foreground">
                        {service.status === "healthy"
                          ? "All systems operational"
                          : service.status === "degraded"
                            ? "Performance degraded"
                            : "Service unavailable"}
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))
          )}
        </div>

        {/* Service Details */}
        <Card className="shadow-premium">
          <CardHeader>
            <CardTitle>Service Details</CardTitle>
            <CardDescription>Detailed information about each service</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {services.map((service) => (
                <div
                  key={service.serviceName}
                  className="p-4 border rounded-lg hover:bg-muted/50 transition-colors"
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      {getStatusIcon(service.status)}
                      <p className="font-semibold">{service.serviceName}</p>
                    </div>
                    <Badge className={getStatusColor(service.status)}>
                      {service.status}
                    </Badge>
                  </div>
                  <div className="grid grid-cols-3 gap-4 text-sm mt-2">
                    <div>
                      <p className="text-muted-foreground">Uptime</p>
                      <p className="font-medium">{service.uptime || "N/A"}%</p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">Latency</p>
                      <p className="font-medium">{service.latency || "N/A"}ms</p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">Last Check</p>
                      <p className="font-medium text-xs">
                        {new Date(service.lastCheck).toLocaleTimeString()}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
    </div>
  );
}
