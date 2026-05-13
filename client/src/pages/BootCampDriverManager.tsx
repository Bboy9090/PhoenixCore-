import { useState } from "react";
import { trpc } from "@/lib/trpc";
import { useAuth } from "@/_core/hooks/useAuth";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Search, Download, CheckCircle, AlertCircle, Package } from "lucide-react";
import { toast } from "sonner";

interface BootCampDriver {
  id: number;
  driverId: string;
  name: string;
  category: string;
  version: string;
  downloadUrl: string;
  fileSize: number;
  compatibleModels: string[];
  releaseDate?: Date;
}

const DRIVER_CATEGORIES = [
  { id: "chipset", label: "Chipset", icon: "🔌" },
  { id: "audio", label: "Audio", icon: "🔊" },
  { id: "graphics", label: "Graphics", icon: "🎨" },
  { id: "network", label: "Network", icon: "🌐" },
  { id: "storage", label: "Storage", icon: "💾" },
  { id: "usb", label: "USB", icon: "🔗" },
];

export default function BootCampDriverManager() {
  const { user } = useAuth();
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);

  const { data: drivers, isLoading } = trpc.bootcamp.listDrivers.useQuery({
    category: selectedCategory || undefined,
    search: searchTerm || undefined,
  });

  const deployDriverMutation = trpc.bootcamp.deployDriver.useMutation();

  const handleDeployDriver = async (driverId: number) => {
    try {
      await deployDriverMutation.mutateAsync({
        deviceId: 1, // Would come from device selection in real app
        driverId,
      });
      toast.success("Driver deployment initiated");
    } catch (error) {
      toast.error("Failed to deploy driver");
    }
  };

  const filteredDrivers = (drivers || []).filter((driver: any) => {
    const matchesSearch =
      driver.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      driver.category.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesCategory = !selectedCategory || driver.category === selectedCategory;

    return matchesSearch && matchesCategory;
  });

  return (
    <div className="min-h-screen bg-gradient-to-br from-background to-muted p-6">
      <div className="max-w-6xl mx-auto space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-4xl font-bold text-foreground">Boot Camp Driver Manager</h1>
          <p className="text-muted-foreground mt-2">Browse and deploy Windows drivers to Mac hardware</p>
        </div>

        {/* Search Bar */}
        <Card className="shadow-premium">
          <CardContent className="pt-6">
            <div className="relative">
              <Search className="absolute left-3 top-3 w-4 h-4 text-muted-foreground" />
              <Input
                placeholder="Search drivers by name or category..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
          </CardContent>
        </Card>

        {/* Category Tabs */}
        <Tabs defaultValue="all" className="w-full">
          <TabsList className="grid w-full grid-cols-4 lg:grid-cols-7">
            <TabsTrigger
              value="all"
              onClick={() => setSelectedCategory(null)}
              className="text-xs"
            >
              All
            </TabsTrigger>
            {DRIVER_CATEGORIES.map((cat) => (
              <TabsTrigger
                key={cat.id}
                value={cat.id}
                onClick={() => setSelectedCategory(cat.id)}
                className="text-xs"
              >
                {cat.icon} {cat.label}
              </TabsTrigger>
            ))}
          </TabsList>

          <TabsContent value="all" className="space-y-4 mt-6">
            {isLoading ? (
              <Card>
                <CardContent className="py-12 text-center">
                  <p className="text-muted-foreground">Loading drivers...</p>
                </CardContent>
              </Card>
            ) : filteredDrivers.length === 0 ? (
              <Card>
                <CardContent className="py-12 text-center">
                  <Package className="w-12 h-12 mx-auto mb-4 text-muted-foreground" />
                  <p className="text-muted-foreground">No drivers found</p>
                </CardContent>
              </Card>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {filteredDrivers.map((driver: any) => (
                  <Card key={driver.id} className="shadow-md hover:shadow-lg transition-shadow">
                    <CardHeader className="pb-3">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <CardTitle className="text-lg">{driver.name}</CardTitle>
                          <CardDescription className="text-xs mt-1">
                            {driver.driverId}
                          </CardDescription>
                        </div>
                        <Badge variant="outline" className="ml-2">
                          {driver.category}
                        </Badge>
                      </div>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      {/* Version and Size */}
                      <div className="grid grid-cols-2 gap-4 text-sm">
                        <div>
                          <p className="text-muted-foreground">Version</p>
                          <p className="font-medium">{driver.version}</p>
                        </div>
                        <div>
                          <p className="text-muted-foreground">File Size</p>
                          <p className="font-medium">{(driver.fileSize / 1024).toFixed(1)} MB</p>
                        </div>
                      </div>

                      {/* Compatible Models */}
                      {driver.compatibleModels && driver.compatibleModels.length > 0 && (
                        <div>
                          <p className="text-sm font-medium mb-2">Compatible Models</p>
                          <div className="flex flex-wrap gap-2">
                            {driver.compatibleModels.slice(0, 3).map((model: string, idx: number) => (
                              <Badge key={idx} variant="secondary" className="text-xs">
                                {model}
                              </Badge>
                            ))}
                            {driver.compatibleModels.length > 3 && (
                              <Badge variant="secondary" className="text-xs">
                                +{driver.compatibleModels.length - 3} more
                              </Badge>
                            )}
                          </div>
                        </div>
                      )}

                      {/* Release Date */}
                      {driver.releaseDate && (
                        <div className="text-xs text-muted-foreground">
                          Released: {new Date(driver.releaseDate).toLocaleDateString()}
                        </div>
                      )}

                      {/* Actions */}
                      <div className="flex gap-2 pt-2">
                        <Button
                          variant="outline"
                          size="sm"
                          className="flex-1 gap-2"
                          onClick={() => window.open(driver.downloadUrl, "_blank")}
                        >
                          <Download className="w-4 h-4" />
                          Download
                        </Button>
                        <Button
                          size="sm"
                          className="flex-1 gap-2"
                          onClick={() => handleDeployDriver(driver.id)}
                          disabled={deployDriverMutation.isPending}
                        >
                          <CheckCircle className="w-4 h-4" />
                          Deploy
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </TabsContent>
        </Tabs>

        {/* Driver Statistics */}
        <Card className="shadow-premium bg-accent/5 border-accent/20">
          <CardHeader>
            <CardTitle>Driver Statistics</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <p className="text-sm text-muted-foreground">Total Drivers</p>
                <p className="text-2xl font-bold">{drivers?.length || 0}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Categories</p>
                <p className="text-2xl font-bold">{DRIVER_CATEGORIES.length}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Latest Version</p>
                <p className="text-lg font-semibold">
                  {drivers?.[0]?.version || "N/A"}
                </p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Total Size</p>
                <p className="text-lg font-semibold">
                  {drivers
                    ? (
                        drivers.reduce((sum: number, d: any) => sum + d.fileSize, 0) /
                        1024 /
                        1024
                      ).toFixed(1)
                    : 0}{" "}
                  GB
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
