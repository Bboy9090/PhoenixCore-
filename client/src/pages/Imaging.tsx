import { useState, useEffect } from "react";
import { 
  Zap, 
  ShieldCheck, 
  Search, 
  AlertTriangle, 
  Activity, 
  FileText, 
  CheckCircle2, 
  XCircle,
  HardDrive,
  ArrowRight,
  ShieldAlert,
  Loader2,
  Clock
} from "lucide-react";
import { trpc } from "../lib/trpc";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { toast } from "sonner";
import { nanoid } from "nanoid";

type Step = "request" | "preview" | "evaluate" | "confirm" | "execute" | "status" | "report";

export default function ImagingPage() {
  const [currentStep, setCurrentStep] = useState<Step>("request");
  const [opId] = useState(() => nanoid());
  const [selectedRecipe, setSelectedRecipe] = useState<any>(null);
  const [selectedTarget, setSelectedTarget] = useState<any>(null);
  const [previewData, setPreviewData] = useState<any>(null);
  const [evaluation, setEvaluation] = useState<any>(null);
  const [confirmationToken, setConfirmationToken] = useState<string | null>(null);
  const [jobId, setJobId] = useState<string | null>(null);
  const [jobStatus, setJobStatus] = useState<any>(null);
  const [auditRecord, setAuditRecord] = useState<any>(null);

  const recipes = trpc.recipe.list.useQuery();
  const hardware = trpc.hardware.detectConnected.useQuery({});
  
  const previewMutation = trpc.operation.preview.useMutation();
  const evaluateQuery = trpc.operation.evaluate.useQuery(
    { opId, params: { recipeId: selectedRecipe?.id, target: selectedTarget } },
    { enabled: !!selectedTarget && !!selectedRecipe }
  );
  const confirmMutation = trpc.operation.confirm.useMutation();
  const executeMutation = trpc.operation.execute.useMutation();
  const statusQuery = trpc.operation.status.useQuery(
    { jobId: jobId! },
    { enabled: !!jobId && currentStep === "status", refetchInterval: 1000 }
  );
  const auditQuery = trpc.operation.audit.useQuery(
    { jobId: jobId! },
    { enabled: !!jobId && currentStep === "report" }
  );

  const handleStartPreview = async () => {
    if (!selectedRecipe || !selectedTarget) return;
    try {
      const data = await previewMutation.mutateAsync({
        opId,
        params: { recipeId: selectedRecipe.id, target: selectedTarget }
      });
      setPreviewData(data);
      setCurrentStep("preview");
    } catch (e: any) {
      toast.error("Preview Failed", { description: e.message });
    }
  };

  const handleConfirmTarget = async () => {
    if (!previewData?.manifestHash) return;
    try {
      const data = await confirmMutation.mutateAsync({
        opId,
        manifestHash: previewData.manifestHash
      });
      setConfirmationToken(data.confirmationToken);
      setCurrentStep("confirm");
    } catch (e: any) {
      toast.error("Confirmation Failed", { description: e.message });
    }
  };

  const handleExecute = async () => {
    if (!confirmationToken) return;
    try {
      const data = await executeMutation.mutateAsync({
        opId,
        params: { recipeId: selectedRecipe.id, target: selectedTarget },
        tokens: { confirmation: confirmationToken }
      });
      setJobId(data.jobId);
      setCurrentStep("status");
    } catch (e: any) {
      toast.error("Execution Failed", { description: e.message });
    }
  };

  useEffect(() => {
    if (currentStep === "status" && statusQuery.data) {
      setJobStatus(statusQuery.data);
      if (statusQuery.data.progressPercent >= 100 || (statusQuery.data.state as string) === "completed") {
        const timer = setTimeout(() => setCurrentStep("report"), 1000);
        return () => clearTimeout(timer);
      }
    }
  }, [statusQuery.data, currentStep]);

  useEffect(() => {
    if (auditQuery.data) {
      setAuditRecord(auditQuery.data);
    }
  }, [auditQuery.data]);

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      <div className="flex flex-col gap-2">
        <h1 className="text-3xl font-bold tracking-tight">Governed Imaging</h1>
        <p className="text-muted-foreground">
          Secure, policy-driven OS deployment through the Phoenix Agent.
        </p>
      </div>

      <Alert variant="default" className="bg-primary/5 border-primary/20">
        <ShieldCheck className="h-4 w-4 text-primary" />
        <AlertTitle>Non-Destructive Simulation Mode</AlertTitle>
        <AlertDescription>
          This dashboard is currently in **Mock Execution** mode. No real disk writes will be performed. 
          The **Removable-Only** policy is active.
        </AlertDescription>
      </Alert>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Step Indicator */}
        <div className="lg:col-span-1 space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-sm font-medium uppercase tracking-wider text-muted-foreground">
                Lifecycle Progress
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {[
                  { id: "request", label: "Request", icon: Zap },
                  { id: "preview", label: "Preview", icon: Search },
                  { id: "evaluate", label: "Evaluation", icon: ShieldCheck },
                  { id: "confirm", label: "Confirmation", icon: ShieldAlert },
                  { id: "status", label: "Simulation", icon: Activity },
                  { id: "report", label: "Audit", icon: FileText },
                ].map((s, idx) => {
                  const Icon = s.icon;
                  const isActive = currentStep === s.id;
                  const isDone = ["request", "preview", "evaluate", "confirm", "status", "report"].indexOf(currentStep) > idx;
                  
                  return (
                    <div key={s.id} className="flex items-center gap-3">
                      <div className={`p-2 rounded-full ${
                        isActive ? "bg-primary text-primary-foreground shadow-lg" : 
                        isDone ? "bg-green-500/20 text-green-500" : 
                        "bg-muted text-muted-foreground"
                      }`}>
                        {isDone ? <CheckCircle2 className="h-4 w-4" /> : <Icon className="h-4 w-4" />}
                      </div>
                      <span className={`text-sm font-medium ${isActive ? "text-foreground" : "text-muted-foreground"}`}>
                        {s.label}
                      </span>
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Main Interface */}
        <div className="lg:col-span-3">
          {currentStep === "request" && (
            <div className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <Card className={selectedRecipe ? "ring-2 ring-primary" : ""}>
                  <CardHeader>
                    <CardTitle className="text-lg">1. Select Recipe</CardTitle>
                    <CardDescription>Choose the OS image and driver bundle.</CardDescription>
                  </CardHeader>
                  <CardContent className="max-h-[300px] overflow-y-auto space-y-2">
                    {recipes.data?.map(r => (
                      <div 
                        key={r.id} 
                        onClick={() => setSelectedRecipe(r)}
                        className={`p-3 rounded-md border cursor-pointer hover:bg-accent transition-colors ${selectedRecipe?.id === r.id ? "bg-accent border-primary" : ""}`}
                      >
                        <div className="font-medium">{r.name}</div>
                        <div className="text-xs text-muted-foreground">{(r.osImage as any)?.name} • {r.estimatedSize} GB</div>
                      </div>
                    ))}
                  </CardContent>
                </Card>

                <Card className={selectedTarget ? "ring-2 ring-primary" : ""}>
                  <CardHeader>
                    <CardTitle className="text-lg">2. Select Target Device</CardTitle>
                    <CardDescription>Select a connected removable drive.</CardDescription>
                  </CardHeader>
                  <CardContent className="max-h-[300px] overflow-y-auto space-y-2">
                    {hardware.data?.devices.map(d => (
                      <div 
                        key={d.id} 
                        onClick={() => setSelectedTarget(d)}
                        className={`p-3 rounded-md border cursor-pointer hover:bg-accent transition-colors ${selectedTarget?.id === d.id ? "bg-accent border-primary" : ""}`}
                      >
                        <div className="flex items-center gap-2">
                          <HardDrive className="h-4 w-4" />
                          <div className="font-medium">{d.name}</div>
                        </div>
                        <div className="text-xs text-muted-foreground">{d.osType?.toUpperCase()} • {d.status?.toUpperCase()}</div>
                      </div>
                    ))}
                  </CardContent>
                </Card>
              </div>

              <div className="flex justify-end">
                <Button 
                  disabled={!selectedRecipe || !selectedTarget || previewMutation.isPending}
                  onClick={handleStartPreview}
                  size="lg"
                  className="gap-2"
                >
                  {previewMutation.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
                  Generate Preview <ArrowRight className="h-4 w-4" />
                </Button>
              </div>
            </div>
          )}

          {currentStep === "preview" && previewData && (
            <Card className="animate-in slide-in-from-right duration-300">
              <CardHeader>
                <div className="flex justify-between items-start">
                  <div>
                    <CardTitle className="text-xl">Operation Preview</CardTitle>
                    <CardDescription>Manifest generated for {opId}</CardDescription>
                  </div>
                  <Badge variant="outline" className="bg-yellow-500/10 text-yellow-500 border-yellow-500/20">
                    PREVIEW ONLY
                  </Badge>
                </div>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="bg-muted/50 p-4 rounded-lg border">
                  <h4 className="text-sm font-semibold mb-2">Proposed Changes:</h4>
                  <ul className="space-y-1">
                    {previewData.proposedChanges.map((c: string, i: number) => (
                      <li key={i} className="text-sm flex items-center gap-2 text-muted-foreground">
                        <div className="h-1 w-1 bg-primary rounded-full" /> {c}
                      </li>
                    ))}
                  </ul>
                </div>

                <div className="space-y-2">
                  <h4 className="text-sm font-semibold flex items-center gap-2 text-destructive">
                    <AlertTriangle className="h-4 w-4" /> Risk Assessment:
                  </h4>
                  {previewData.risks.map((r: string, i: number) => (
                    <div key={i} className="text-sm text-destructive bg-destructive/10 p-2 rounded border border-destructive/20 font-medium">
                      {r}
                    </div>
                  ))}
                </div>
              </CardContent>
              <CardFooter className="flex justify-between">
                <Button variant="outline" onClick={() => setCurrentStep("request")}>Back</Button>
                <Button onClick={() => setCurrentStep("evaluate")} className="gap-2">
                  Run Safety Evaluation <ShieldCheck className="h-4 w-4" />
                </Button>
              </CardFooter>
            </Card>
          )}

          {currentStep === "evaluate" && (
            <Card className="animate-in slide-in-from-bottom duration-300">
              <CardHeader>
                <CardTitle>Safety Evaluation</CardTitle>
                <CardDescription>Verifying operation against Phoenix Safety Policy</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {evaluateQuery.isLoading ? (
                  <div className="flex flex-col items-center justify-center py-12 gap-4">
                    <Loader2 className="h-12 w-12 animate-spin text-primary" />
                    <p className="text-muted-foreground animate-pulse">Consulting platform policy engine...</p>
                  </div>
                ) : evaluateQuery.data?.allowed ? (
                  <div className="space-y-4">
                    <div className="flex items-center gap-4 p-6 bg-green-500/10 border border-green-500/20 rounded-xl text-green-500">
                      <div className="p-3 bg-green-500 text-white rounded-full">
                        <ShieldCheck className="h-8 w-8" />
                      </div>
                      <div>
                        <h3 className="text-xl font-bold">Policy Cleared</h3>
                        <p className="text-sm opacity-90">Target matches Removable-Only policy. No system disk modification detected.</p>
                      </div>
                    </div>
                    <div className="space-y-2">
                      <h4 className="text-sm font-semibold">Post-Evaluation Requirements:</h4>
                      {evaluateQuery.data.requirements.map((r: string, i: number) => (
                        <div key={i} className="text-sm flex items-center gap-2">
                          <CheckCircle2 className="h-4 w-4 text-green-500" /> {r}
                        </div>
                      ))}
                    </div>
                  </div>
                ) : (
                  <div className="space-y-4">
                    <div className="flex items-center gap-4 p-6 bg-destructive/10 border border-destructive/20 rounded-xl text-destructive">
                      <div className="p-3 bg-destructive text-white rounded-full shadow-lg">
                        <XCircle className="h-8 w-8" />
                      </div>
                      <div>
                        <h3 className="text-xl font-bold">Operation Blocked</h3>
                        <p className="text-sm opacity-90">{evaluateQuery.data?.reason}</p>
                      </div>
                    </div>
                    <Alert variant="destructive">
                      <ShieldAlert className="h-4 w-4" />
                      <AlertTitle>Safety Violation</AlertTitle>
                      <AlertDescription>
                        Direct imaging of internal/system disks is disabled in the current runtime environment. 
                        Please boot into Phoenix Recovery or use an authorized override token.
                      </AlertDescription>
                    </Alert>
                  </div>
                )}
              </CardContent>
              <CardFooter className="flex justify-between">
                <Button variant="outline" onClick={() => setCurrentStep("preview")}>Back</Button>
                {evaluateQuery.data?.allowed && (
                  <Button onClick={handleConfirmTarget} className="gap-2 bg-yellow-600 hover:bg-yellow-700">
                    {confirmMutation.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
                    Confirm Target <ShieldAlert className="h-4 w-4" />
                  </Button>
                )}
              </CardFooter>
            </Card>
          )}

          {currentStep === "confirm" && (
            <Card className="animate-in zoom-in duration-300 border-yellow-500/50 shadow-xl shadow-yellow-500/5">
              <CardHeader className="bg-yellow-500/5">
                <CardTitle className="text-yellow-600 flex items-center gap-2">
                  <ShieldAlert className="h-6 w-6" /> Destructive Confirmation
                </CardTitle>
                <CardDescription>A token has been issued for this operation.</CardDescription>
              </CardHeader>
              <CardContent className="py-8 space-y-6 text-center">
                <div className="space-y-2">
                  <p className="text-lg font-medium text-foreground">
                    You are about to simulate imaging to:
                  </p>
                  <p className="text-2xl font-bold text-primary">
                    {selectedTarget?.name}
                  </p>
                </div>
                
                <div className="p-4 bg-muted rounded-lg font-mono text-xs break-all">
                  TOKEN: {confirmationToken}
                </div>

                <div className="max-w-md mx-auto p-4 border rounded-lg bg-yellow-50 text-yellow-800 text-sm flex gap-3 text-left">
                  <Activity className="h-5 w-5 shrink-0 mt-0.5" />
                  <div>
                    <strong>MOCK EXECUTION NOTICE:</strong> No bits will actually be written to the sector map. 
                    The process will only verify data integrity and simulate partition creation.
                  </div>
                </div>
              </CardContent>
              <CardFooter className="flex justify-center gap-4 bg-yellow-500/5">
                <Button variant="ghost" onClick={() => setCurrentStep("evaluate")}>Cancel</Button>
                <Button 
                  onClick={handleExecute} 
                  className="bg-red-600 hover:bg-red-700 px-8 py-6 text-lg font-bold"
                  disabled={executeMutation.isPending}
                >
                  {executeMutation.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
                  ARM & EXECUTE MOCK
                </Button>
              </CardFooter>
            </Card>
          )}

          {currentStep === "status" && jobStatus && (
            <Card className="animate-in fade-in duration-500">
              <CardHeader>
                <div className="flex justify-between items-center">
                  <div>
                    <CardTitle>Mock Execution Activity</CardTitle>
                    <CardDescription>Job: {jobId} • {jobStatus.state.toUpperCase()}</CardDescription>
                  </div>
                  <Badge variant="secondary" className="animate-pulse">
                    STREAMING
                  </Badge>
                </div>
              </CardHeader>
              <CardContent className="space-y-8">
                <div className="space-y-2">
                  <div className="flex justify-between text-sm font-medium">
                    <span>Overall Progress</span>
                    <span>{jobStatus.progressPercent}%</span>
                  </div>
                  <Progress value={jobStatus.progressPercent} className="h-3" />
                </div>

                <div className="bg-black/90 p-4 rounded-lg font-mono text-xs text-green-400 min-h-[200px] max-h-[300px] overflow-y-auto space-y-1">
                  {jobStatus.logs.map((log: string, i: number) => (
                    <div key={i} className="flex gap-2">
                      <span className="opacity-50">[{new Date().toLocaleTimeString()}]</span>
                      <span>{log}</span>
                    </div>
                  ))}
                  <div className="animate-pulse">_</div>
                </div>
              </CardContent>
              <CardFooter className="text-muted-foreground text-xs justify-center italic">
                <Activity className="h-3 w-3 mr-1" /> Data is being simulated through the Phoenix Agent Governor.
              </CardFooter>
            </Card>
          )}

          {currentStep === "report" && auditRecord && (
            <Card className="animate-in slide-in-from-top duration-500 border-green-500/30">
              <CardHeader className="bg-green-500/5">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-green-500 text-white rounded-full">
                    <CheckCircle2 className="h-6 w-6" />
                  </div>
                  <div>
                    <CardTitle>Operation Complete</CardTitle>
                    <CardDescription>Mock imaging cycle finalized and audited.</CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="py-8 space-y-6">
                <div className="grid grid-cols-2 gap-6">
                  <div className="p-4 border rounded-lg space-y-1">
                    <p className="text-xs text-muted-foreground uppercase font-bold tracking-tighter">Status</p>
                    <p className="font-semibold text-green-600">SUCCESS (SIMULATED)</p>
                  </div>
                  <div className="p-4 border rounded-lg space-y-1">
                    <p className="text-xs text-muted-foreground uppercase font-bold tracking-tighter">Verified By</p>
                    <p className="font-semibold truncate">{auditRecord.signedBy}</p>
                  </div>
                </div>

                <div className="p-4 bg-muted/30 border rounded-lg">
                  <h4 className="text-sm font-semibold mb-3 flex items-center gap-2">
                    <FileText className="h-4 w-4" /> Audit Summary:
                  </h4>
                  <pre className="text-xs font-mono whitespace-pre-wrap">
                    {JSON.stringify(auditRecord.record, null, 2)}
                  </pre>
                </div>

                <Alert className="bg-primary/5">
                  <Clock className="h-4 w-4" />
                  <AlertTitle>Audit Retained</AlertTitle>
                  <AlertDescription>
                    The complete manifest and execution log have been persisted to the platform's audit ledger for compliance.
                  </AlertDescription>
                </Alert>
              </CardContent>
              <CardFooter className="flex justify-center">
                <Button onClick={() => {
                  setCurrentStep("request");
                  setSelectedRecipe(null);
                  setSelectedTarget(null);
                  setJobId(null);
                }}>Return to Dashboard</Button>
              </CardFooter>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
