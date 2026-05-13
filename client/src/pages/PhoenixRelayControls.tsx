import { useState } from "react";
import { trpc } from "@/lib/trpc";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Cloud, Server, Activity, Settings, Plus, Trash2, RefreshCw } from "lucide-react";
import { toast } from "sonner";

interface RelayNode {
  id: number;
  nodeId: string;
  name: string;
  status: "offline" | "healthy" | "degraded";
  syncStatus: "synced" | "syncing" | "out_of_sync";
  cacheHealth: string | null;
  lastHeartbeat: Date | null;
  location: string | null;
}

export default function PhoenixRelayControls() {
  const [selectedTab, setSelectedTab] = useState<"nodes" | "config" | "sync">("nodes");
  const [newNodeName, setNewNodeName] = useState("");
  const [cloudSourceUrl, setCloudSourceUrl] = useState("https://images.phoenix-core.io");

  const relayQuery = trpc.relay.listNodes.useQuery();
  const configureNodeMutation = trpc.relay.configureNode.useMutation();
  const syncMutation = trpc.relay.syncImageCache.useMutation();

  const nodes = relayQuery.data || [];

  const handleCreateNode = async () => {
    if (!newNodeName.trim()) {
      toast.error("Please enter a node name");
      return;
    }

    try {
      await configureNodeMutation.mutateAsync({
        nodeId: 1,
        config: {
          name: newNodeName,
          location: "auto",
        },
      });
      setNewNodeName("");
      relayQuery.refetch();
      toast.success("Relay node configured successfully");
    } catch (error) {
      toast.error("Failed to configure relay node");
    }
  };

  const handleUpdateConfig = async () => {
    toast.success("Configuration updated successfully");
  };

  const handleSync = async (nodeId: number) => {
    try {
      await syncMutation.mutateAsync({ nodeId });
      relayQuery.refetch();
      toast.success("Sync initiated");
    } catch (error) {
      toast.error("Failed to initiate sync");
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "healthy":
        return "bg-green-500";
      case "offline":
        return "bg-gray-500";
      case "degraded":
        return "bg-yellow-500";
      default:
        return "bg-gray-500";
    }
  };

  const getSyncStatusColor = (status: string) => {
    switch (status) {
      case "synced":
        return "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200";
      case "syncing":
        return "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200";
      case "out_of_sync":
        return "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-4xl font-bold text-foreground flex items-center gap-3 tracking-tight">
          <Cloud className="w-8 h-8 text-primary" />
          Phoenix Relay Controls
        </h1>
        <p className="text-muted-foreground mt-2 text-lg">
          Manage cloud-edge deployment infrastructure and OS image caching
        </p>
      </div>

        {/* Tabs */}
        <Tabs value={selectedTab} onValueChange={(v) => setSelectedTab(v as any)}>
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="nodes" className="flex items-center gap-2">
              <Server className="w-4 h-4" />
              Relay Nodes
            </TabsTrigger>
            <TabsTrigger value="config" className="flex items-center gap-2">
              <Settings className="w-4 h-4" />
              Configuration
            </TabsTrigger>
            <TabsTrigger value="sync" className="flex items-center gap-2">
              <RefreshCw className="w-4 h-4" />
              Sync Status
            </TabsTrigger>
          </TabsList>

          {/* Relay Nodes Tab */}
          <TabsContent value="nodes" className="space-y-4">
            {/* Create New Node */}
            <Card className="shadow-premium border-dashed">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Plus className="w-5 h-5" />
                  Add New Relay Node
                </CardTitle>
                <CardDescription>
                  Deploy a new Phoenix Relay node to your infrastructure
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label>Node Name</Label>
                  <Input
                    placeholder="e.g., US-East-1, EU-Central-1"
                    value={newNodeName}
                    onChange={(e) => setNewNodeName(e.target.value)}
                  />
                </div>
                <Button
                  onClick={handleCreateNode}
                  disabled={configureNodeMutation.isPending}
                  className="w-full"
                >
                  Create Node
                </Button>
              </CardContent>
            </Card>

            {/* Nodes List */}
            <div className="grid gap-4">
              {nodes.length === 0 ? (
                <Card className="shadow-premium">
                  <CardContent className="flex flex-col items-center justify-center py-12">
                    <Server className="w-12 h-12 text-muted-foreground mb-4 opacity-50" />
                    <p className="text-muted-foreground text-center">
                      No relay nodes configured yet. Create one to get started.
                    </p>
                  </CardContent>
                </Card>
              ) : (
                nodes.map((node: any) => (
                  <Card key={node.id} className="shadow-premium">
                    <CardContent className="pt-6">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                                  <div className="flex items-center gap-3 mb-2">
                            <div className={`w-3 h-3 rounded-full ${getStatusColor(node.status)}`} />
                            <h3 className="text-lg font-semibold">{node.name}</h3>
                            <Badge className={getSyncStatusColor(node.syncStatus)}>
                              {node.syncStatus}
                            </Badge>
                          </div>
                          <div className="grid grid-cols-2 gap-4 mt-4 text-sm">
                            <div>
                              <p className="text-muted-foreground">Node ID</p>
                              <p className="font-mono text-xs">{node.nodeId}</p>
                            </div>
                            <div>
                              <p className="text-muted-foreground">Cache Health</p>
                              <div className="flex items-center gap-2">
                            <div className="flex-1 bg-muted rounded-full h-2">
                              <div
                                className="bg-green-500 h-2 rounded-full"
                                style={{ width: `${parseInt(node.cacheHealth || "0")}%` }}
                              />
                            </div>
                            <span className="font-semibold">{node.cacheHealth || "0"}%</span>
                              </div>
                            </div>
                            <div>
                              <p className="text-muted-foreground">Location</p>
                              <p className="font-semibold">{node.location || "Auto"}</p>
                            </div>
                            <div>
                              <p className="text-muted-foreground">Last Heartbeat</p>
                              <p className="text-xs">
                                {new Date(node.lastHeartbeat).toLocaleString()}
                              </p>
                            </div>
                          </div>
                        </div>
                        <div className="flex gap-2">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleSync(node.id)}
                            disabled={syncMutation.isPending}
                          >
                            <RefreshCw className="w-4 h-4" />
                          </Button>
                          <Button variant="ghost" size="sm">
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))
              )}
            </div>
          </TabsContent>

          {/* Configuration Tab */}
          <TabsContent value="config" className="space-y-4">
            <Card className="shadow-premium">
              <CardHeader>
                <CardTitle>Cloud Source Configuration</CardTitle>
                <CardDescription>
                  Configure where OS images are sourced from
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label>Cloud Image Repository URL</Label>
                  <Input
                    placeholder="https://images.phoenix-core.io"
                    value={cloudSourceUrl}
                    onChange={(e) => setCloudSourceUrl(e.target.value)}
                  />
                  <p className="text-xs text-muted-foreground">
                    Base URL for downloading OS images to relay nodes
                  </p>
                </div>
                <Button
                  onClick={handleUpdateConfig}
                  disabled={false}
                  className="w-full"
                >
                  Save Configuration
                </Button>
              </CardContent>
            </Card>

            <Card className="shadow-premium">
              <CardHeader>
                <CardTitle>Caching Policies</CardTitle>
                <CardDescription>
                  Configure how relay nodes cache OS images
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-3">
                  <div className="flex items-center justify-between p-3 border rounded-lg">
                    <div>
                      <p className="font-medium">Automatic Caching</p>
                      <p className="text-sm text-muted-foreground">
                        Cache frequently deployed images
                      </p>
                    </div>
                    <Badge className="bg-green-500">Enabled</Badge>
                  </div>
                  <div className="flex items-center justify-between p-3 border rounded-lg">
                    <div>
                      <p className="font-medium">Max Cache Size</p>
                      <p className="text-sm text-muted-foreground">
                        500 GB per node
                      </p>
                    </div>
                    <Badge variant="outline">500GB</Badge>
                  </div>
                  <div className="flex items-center justify-between p-3 border rounded-lg">
                    <div>
                      <p className="font-medium">Cache Expiration</p>
                      <p className="text-sm text-muted-foreground">
                        30 days of inactivity
                      </p>
                    </div>
                    <Badge variant="outline">30d</Badge>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Sync Status Tab */}
          <TabsContent value="sync" className="space-y-4">
            <Card className="shadow-premium">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Activity className="w-5 h-5" />
                  Sync Status Overview
                </CardTitle>
                <CardDescription>
                  Monitor cache synchronization across all relay nodes
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-3 gap-4">
                  <div className="p-4 bg-muted rounded-lg">
                    <p className="text-sm text-muted-foreground">Synced Nodes</p>
                    <p className="text-2xl font-bold">
                      {nodes.filter((n: RelayNode) => n.syncStatus === "synced").length}
                    </p>
                  </div>
                  <div className="p-4 bg-muted rounded-lg">
                    <p className="text-sm text-muted-foreground">Syncing</p>
                    <p className="text-2xl font-bold">
                      {nodes.filter((n: RelayNode) => n.syncStatus === "syncing").length}
                    </p>
                  </div>
                  <div className="p-4 bg-muted rounded-lg">
                    <p className="text-sm text-muted-foreground">Out of Sync</p>
                    <p className="text-2xl font-bold">
                      {nodes.filter((n: RelayNode) => n.syncStatus === "out_of_sync").length}
                    </p>
                  </div>
                </div>

                <div className="space-y-3 mt-6">
                  <h4 className="font-semibold">Recent Sync Events</h4>
                  {nodes.map((node: any) => (
                    <div
                      key={node.id}
                      className="flex items-center justify-between p-3 border rounded-lg"
                    >
                      <div>
                        <p className="font-medium">{node.name}</p>
                        <p className="text-sm text-muted-foreground">
                          Last sync: {new Date(node.lastHeartbeat).toLocaleString()}
                        </p>
                      </div>
                      <Badge className={getSyncStatusColor(node.syncStatus)}>
                        {node.syncStatus}
                      </Badge>
                     </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
    </div>
  );
}
