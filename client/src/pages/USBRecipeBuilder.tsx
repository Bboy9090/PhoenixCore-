import { useState } from "react";
import { trpc } from "@/lib/trpc";
import { useAuth } from "@/_core/hooks/useAuth";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { AlertCircle, Plus, Trash2, HardDrive, Package, Zap } from "lucide-react";
import { toast } from "sonner";

interface RecipeComponent {
  id: string;
  name: string;
  size: number; // in GB
  url: string;
}

export default function USBRecipeBuilder() {
  const { user } = useAuth();
  const [recipeName, setRecipeName] = useState("");
  const [recipeDescription, setRecipeDescription] = useState("");
  const [osImage, setOsImage] = useState<RecipeComponent | null>(null);
  const [drivers, setDrivers] = useState<RecipeComponent[]>([]);
  const [tools, setTools] = useState<RecipeComponent[]>([]);
  const [estimatedSize, setEstimatedSize] = useState(0);

  const createRecipeMutation = trpc.recipe.create.useMutation();
  const estimateSizeMutation = trpc.recipe.estimateSize.useQuery(
    { osImage: osImage || {}, drivers, tools },
    { enabled: !!osImage }
  );

  const handleAddDriver = () => {
    const newDriver: RecipeComponent = {
      id: `driver-${Date.now()}`,
      name: "",
      size: 0,
      url: "",
    };
    setDrivers([...drivers, newDriver]);
  };

  const handleAddTool = () => {
    const newTool: RecipeComponent = {
      id: `tool-${Date.now()}`,
      name: "",
      size: 0,
      url: "",
    };
    setTools([...tools, newTool]);
  };

  const handleRemoveDriver = (id: string) => {
    setDrivers(drivers.filter((d) => d.id !== id));
  };

  const handleRemoveTool = (id: string) => {
    setTools(tools.filter((t) => t.id !== id));
  };

  const handleCreateRecipe = async () => {
    if (!recipeName.trim()) {
      toast.error("Please enter a recipe name");
      return;
    }

    if (!osImage) {
      toast.error("Please select an OS image");
      return;
    }

    try {
      await createRecipeMutation.mutateAsync({
        name: recipeName,
        description: recipeDescription,
        osImage,
        drivers,
        tools,
        estimatedSize: estimateSizeMutation.data?.totalSizeGB || "0.00",
      });

      toast.success("Recipe created successfully!");
      setRecipeName("");
      setRecipeDescription("");
      setOsImage(null);
      setDrivers([]);
      setTools([]);
    } catch (error) {
      toast.error("Failed to create recipe");
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-4xl font-bold text-foreground tracking-tight flex items-center gap-3">
          <Package className="w-8 h-8 text-primary" />
          USB Recipe Builder
        </h1>
        <p className="text-muted-foreground mt-2 text-lg">Compose bootable USB configurations with drag-and-drop ease</p>
      </div>

        {/* Recipe Details */}
        <Card className="shadow-premium">
          <CardHeader>
            <CardTitle>Recipe Details</CardTitle>
            <CardDescription>Name and describe your deployment recipe</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label htmlFor="recipe-name">Recipe Name</Label>
              <Input
                id="recipe-name"
                placeholder="e.g., Windows 11 Pro with Boot Camp Drivers"
                value={recipeName}
                onChange={(e) => setRecipeName(e.target.value)}
                className="mt-2"
              />
            </div>
            <div>
              <Label htmlFor="recipe-desc">Description (Optional)</Label>
              <Input
                id="recipe-desc"
                placeholder="Add notes about this recipe..."
                value={recipeDescription}
                onChange={(e) => setRecipeDescription(e.target.value)}
                className="mt-2"
              />
            </div>
          </CardContent>
        </Card>

        {/* OS Image Selection */}
        <Card className="shadow-premium border-2 border-primary/20">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <HardDrive className="w-5 h-5" />
              OS Image
            </CardTitle>
            <CardDescription>Select the base operating system image</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {osImage ? (
              <div className="p-4 bg-primary/10 rounded-lg border border-primary/20 flex items-center justify-between">
                <div>
                  <p className="font-semibold">{osImage.name}</p>
                  <p className="text-sm text-muted-foreground">{osImage.size} GB</p>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setOsImage(null)}
                >
                  <Trash2 className="w-4 h-4" />
                </Button>
              </div>
            ) : (
              <div className="p-8 border-2 border-dashed border-muted-foreground/30 rounded-lg text-center">
                <HardDrive className="w-8 h-8 mx-auto mb-2 text-muted-foreground" />
                <p className="text-muted-foreground">No OS image selected</p>
                <Button
                  className="mt-4"
                  variant="outline"
                  onClick={() =>
                    setOsImage({
                      id: "os-1",
                      name: "Windows 11 Pro 23H2",
                      size: 5.2,
                      url: "https://example.com/windows11.iso",
                    })
                  }
                >
                  Browse OS Images
                </Button>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Drivers Section */}
        <Card className="shadow-premium">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Package className="w-5 h-5" />
              Drivers
            </CardTitle>
            <CardDescription>Add device drivers for hardware compatibility</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {drivers.length === 0 ? (
              <div className="p-8 border-2 border-dashed border-muted-foreground/30 rounded-lg text-center">
                <Package className="w-8 h-8 mx-auto mb-2 text-muted-foreground" />
                <p className="text-muted-foreground">No drivers added yet</p>
              </div>
            ) : (
              <div className="space-y-3">
                {drivers.map((driver) => (
                  <div key={driver.id} className="p-3 bg-muted rounded-lg flex items-center justify-between">
                    <div>
                      <p className="font-medium">{driver.name || "Unnamed Driver"}</p>
                      <p className="text-sm text-muted-foreground">{driver.size} MB</p>
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleRemoveDriver(driver.id)}
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                ))}
              </div>
            )}
            <Button onClick={handleAddDriver} variant="outline" className="w-full gap-2">
              <Plus className="w-4 h-4" />
              Add Driver
            </Button>
          </CardContent>
        </Card>

        {/* Tools Section */}
        <Card className="shadow-premium">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Zap className="w-5 h-5" />
              Tools
            </CardTitle>
            <CardDescription>Include utilities and system tools</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {tools.length === 0 ? (
              <div className="p-8 border-2 border-dashed border-muted-foreground/30 rounded-lg text-center">
                <Zap className="w-8 h-8 mx-auto mb-2 text-muted-foreground" />
                <p className="text-muted-foreground">No tools added yet</p>
              </div>
            ) : (
              <div className="space-y-3">
                {tools.map((tool) => (
                  <div key={tool.id} className="p-3 bg-muted rounded-lg flex items-center justify-between">
                    <div>
                      <p className="font-medium">{tool.name || "Unnamed Tool"}</p>
                      <p className="text-sm text-muted-foreground">{tool.size} MB</p>
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleRemoveTool(tool.id)}
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                ))}
              </div>
            )}
            <Button onClick={handleAddTool} variant="outline" className="w-full gap-2">
              <Plus className="w-4 h-4" />
              Add Tool
            </Button>
          </CardContent>
        </Card>

        {/* Size Estimation */}
        {estimateSizeMutation.data && (
          <Card className="shadow-premium bg-accent/5 border-accent/20">
            <CardHeader>
              <CardTitle className="text-lg">Size Estimation</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div>
                  <p className="text-sm text-muted-foreground">Total Size</p>
                  <p className="text-2xl font-bold">{estimateSizeMutation.data.totalSizeGB} GB</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">OS Image</p>
                  <p className="text-lg font-semibold">{estimateSizeMutation.data.components.osImage.toFixed(2)} GB</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Drivers</p>
                  <p className="text-lg font-semibold">{estimateSizeMutation.data.components.drivers}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Tools</p>
                  <p className="text-lg font-semibold">{estimateSizeMutation.data.components.tools}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Action Buttons */}
        <div className="flex gap-3 justify-end">
          <Button variant="outline">Cancel</Button>
          <Button
            onClick={handleCreateRecipe}
            disabled={createRecipeMutation.isPending || !osImage}
            className="gap-2"
          >
            {createRecipeMutation.isPending ? "Creating..." : "Create Recipe"}
          </Button>
        </div>
    </div>
  );
}
