import { useEffect, useState } from "react";
import { trpc } from "@/lib/trpc";
import { useAuth } from "@/_core/hooks/useAuth";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { AlertCircle, CheckCircle, Clock, Zap, Download, AlertTriangle } from "lucide-react";

interface DeploymentStatus {
  id: number;
  deploymentId: string;
  status: "pending" | "building" | "deploying" | "completed" | "failed" | "cancelled";
  progressPercent: number;
  currentStep: string;
  logs: string[];
  startedAt?: Date;
  completedAt?: Date;
  errorMessage?: string;
}

export default function DeploymentTracker() {
  const { user } = useAuth();
  const [deployments, setDeployments] = useState<DeploymentStatus[]>([]);
  const [selectedDeploymentId, setSelectedDeploymentId] = useState<string | null>(null);

  const { data: deploymentList, isLoading } = trpc.deployment.list.useQuery({});

  useEffect(() => {
    if (deploymentList) {
      setDeployments(deploymentList as any);
    }
  }, [deploymentList]);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "completed":
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case "failed":
        return <AlertTriangle className="w-5 h-5 text-red-500" />;
      case "building":
      case "deploying":
        return <Zap className="w-5 h-5 text-blue-500 animate-pulse" />;
      case "pending":
        return <Clock className="w-5 h-5 text-yellow-500" />;
      default:
        return <AlertCircle className="w-5 h-5 text-gray-500" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "completed":
        return "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200";
      case "failed":
        return "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200";
      case "building":
      case "deploying":
        return "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200";
      case "pending":
        return "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200";
      default:
        return "bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200";
    }
  };

  const activeDeployments = deployments.filter((d) => d.status !== "completed" && d.status !== "failed");
  const completedDeployments = deployments.filter((d) => d.status === "completed" || d.status === "failed");

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-4xl font-bold text-foreground tracking-tight flex items-center gap-3">
          <Zap className="w-8 h-8 text-primary" />
          Deployment Tracker
        </h1>
        <p className="text-muted-foreground mt-2 text-lg">Monitor real-time installation and build progress</p>
      </div>

        {/* Tabs */}
        <Tabs defaultValue="active" className="w-full">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="active">
              Active Deployments ({activeDeployments.length})
            </TabsTrigger>
            <TabsTrigger value="history">
              History ({completedDeployments.length})
            </TabsTrigger>
          </TabsList>

          {/* Active Deployments */}
          <TabsContent value="active" className="space-y-4">
            {isLoading ? (
              <Card>
                <CardContent className="py-12 text-center">
                  <p className="text-muted-foreground">Loading deployments...</p>
                </CardContent>
              </Card>
            ) : activeDeployments.length === 0 ? (
              <Card>
                <CardContent className="py-12 text-center">
                  <p className="text-muted-foreground">No active deployments</p>
                </CardContent>
              </Card>
            ) : (
              activeDeployments.map((deployment) => (
                <Card
                  key={deployment.id}
                  className="shadow-premium cursor-pointer hover:shadow-lg transition-shadow"
                  onClick={() => setSelectedDeploymentId(deployment.deploymentId)}
                >
                  <CardHeader className="pb-3">
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-3 flex-1">
                        {getStatusIcon(deployment.status)}
                        <div>
                          <CardTitle className="text-lg">{deployment.deploymentId}</CardTitle>
                          <CardDescription className="text-xs mt-1">{deployment.currentStep}</CardDescription>
                        </div>
                      </div>
                      <Badge className={getStatusColor(deployment.status)}>
                        {deployment.status}
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    {/* Progress Bar */}
                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <p className="text-sm font-medium">Progress</p>
                        <p className="text-sm font-bold">{deployment.progressPercent}%</p>
                      </div>
                      <Progress value={deployment.progressPercent} className="h-2" />
                    </div>

                    {/* Timeline */}
                    {deployment.startedAt && (
                      <div className="grid grid-cols-2 gap-4 text-sm">
                        <div>
                          <p className="text-muted-foreground">Started</p>
                          <p className="font-medium">
                            {new Date(deployment.startedAt).toLocaleTimeString()}
                          </p>
                        </div>
                        {deployment.completedAt && (
                          <div>
                            <p className="text-muted-foreground">Completed</p>
                            <p className="font-medium">
                              {new Date(deployment.completedAt).toLocaleTimeString()}
                            </p>
                          </div>
                        )}
                      </div>
                    )}

                    {/* Error Message */}
                    {deployment.errorMessage && (
                      <div className="p-3 bg-red-50 dark:bg-red-950 border border-red-200 dark:border-red-800 rounded-lg">
                        <p className="text-sm text-red-800 dark:text-red-200">{deployment.errorMessage}</p>
                      </div>
                    )}

                    {/* Logs Preview */}
                    {deployment.logs.length > 0 && (
                      <div className="p-3 bg-muted rounded-lg max-h-32 overflow-y-auto">
                        <p className="text-xs font-mono text-muted-foreground space-y-1">
                          {deployment.logs.slice(-5).map((log, idx) => (
                            <div key={idx}>{log}</div>
                          ))}
                        </p>
                      </div>
                    )}

                    <Button variant="outline" className="w-full" size="sm">
                      View Full Details
                    </Button>
                  </CardContent>
                </Card>
              ))
            )}
          </TabsContent>

          {/* Deployment History */}
          <TabsContent value="history" className="space-y-4">
            {completedDeployments.length === 0 ? (
              <Card>
                <CardContent className="py-12 text-center">
                  <p className="text-muted-foreground">No completed deployments yet</p>
                </CardContent>
              </Card>
            ) : (
              completedDeployments.map((deployment) => (
                <Card key={deployment.id} className="shadow-sm">
                  <CardHeader className="pb-3">
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-3 flex-1">
                        {getStatusIcon(deployment.status)}
                        <div>
                          <CardTitle className="text-base">{deployment.deploymentId}</CardTitle>
                          <CardDescription className="text-xs mt-1">
                            {deployment.completedAt
                              ? new Date(deployment.completedAt).toLocaleString()
                              : "No completion time"}
                          </CardDescription>
                        </div>
                      </div>
                      <Badge className={getStatusColor(deployment.status)}>
                        {deployment.status}
                      </Badge>
                    </div>
                  </CardHeader>
                  {deployment.status === "failed" && deployment.errorMessage && (
                    <CardContent>
                      <p className="text-sm text-red-600 dark:text-red-400">{deployment.errorMessage}</p>
                    </CardContent>
                  )}
                </Card>
              ))
            )}
          </TabsContent>
        </Tabs>
    </div>
  );
}
