import { useState } from "react";
import { trpc } from "@/lib/trpc";
import { useAuth } from "@/_core/hooks/useAuth";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Link } from "wouter";
import { AlertCircle, Users, Settings, FileText, Shield, Trash2, Edit, ArrowRight } from "lucide-react";
import { toast } from "sonner";

export default function AdminDashboard() {
  const { user } = useAuth();
  const [selectedUserId, setSelectedUserId] = useState<number | null>(null);

  const { data: users, isLoading: usersLoading } = trpc.admin.listUsers.useQuery();
  const { data: auditLogs, isLoading: logsLoading } = trpc.admin.getAuditLogs.useQuery({});

  const promoteUserMutation = trpc.admin.updateUserRole.useMutation();

  const handlePromoteUser = async (userId: number) => {
    try {
      await promoteUserMutation.mutateAsync({ userId, role: "admin" });
      toast.success("User promoted to admin");
    } catch (error) {
      toast.error("Failed to promote user");
    }
  };



  // Check if user is owner
  const isOwner = user?.role === "owner";

  if (!isOwner) {
    return (
      <div className="flex items-center justify-center py-20">
        <Card className="shadow-premium max-w-md w-full border-red-500/20 bg-red-500/5">
          <CardHeader>
            <CardTitle className="flex items-center gap-3 text-red-600 tracking-tight">
              <AlertCircle className="w-6 h-6" />
              Access Restricted
            </CardTitle>
            <CardDescription className="text-red-600/70 font-medium">
              Administrative Authorization Required
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm text-muted-foreground leading-relaxed">
              The Admin Console is reserved for system owners. Your current role (<span className="font-bold uppercase text-foreground">{user?.role || "user"}</span>) does not have the required permissions.
            </p>
            <Link href="/">
              <Button variant="outline" className="w-full gap-2 border-red-500/20 hover:bg-red-500/10">
                Return to Dashboard
                <ArrowRight className="w-4 h-4" />
              </Button>
            </Link>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-4xl font-bold text-foreground flex items-center gap-3 tracking-tight">
          <Shield className="w-8 h-8 text-primary" />
          Admin Console
        </h1>
        <p className="text-muted-foreground mt-2 text-lg">Manage users, audit logs, and deployment policies</p>
      </div>

        <Tabs defaultValue="users" className="w-full">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="users" className="gap-2">
              <Users className="w-4 h-4" />
              Users
            </TabsTrigger>
            <TabsTrigger value="audit" className="gap-2">
              <FileText className="w-4 h-4" />
              Audit Logs
            </TabsTrigger>
            <TabsTrigger value="policies" className="gap-2">
              <Settings className="w-4 h-4" />
              Policies
            </TabsTrigger>
          </TabsList>

          {/* Users Tab */}
          <TabsContent value="users" className="space-y-4">
            <Card className="shadow-premium">
              <CardHeader>
                <CardTitle>User Management</CardTitle>
                <CardDescription>View and manage all system users</CardDescription>
              </CardHeader>
              <CardContent>
                {usersLoading ? (
                  <p className="text-muted-foreground text-center py-8">Loading users...</p>
                ) : !users || users.length === 0 ? (
                  <p className="text-muted-foreground text-center py-8">No users found</p>
                ) : (
                  <div className="space-y-3">
                    {users.map((u: any) => (
                      <div
                        key={u.id}
                        className="p-4 border rounded-lg hover:bg-muted/50 transition-colors flex items-center justify-between"
                      >
                        <div className="flex-1">
                          <p className="font-semibold">{u.name || "Unknown"}</p>
                          <p className="text-sm text-muted-foreground">{u.email}</p>
                          <div className="flex gap-2 mt-2">
                            <Badge
                              className={
                                u.role === "owner"
                                  ? "bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200"
                                  : u.role === "admin"
                                    ? "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200"
                                    : "bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200"
                              }
                            >
                              {u.role}
                            </Badge>
                            <p className="text-xs text-muted-foreground">
                              Joined {new Date(u.createdAt).toLocaleDateString()}
                            </p>
                          </div>
                        </div>
                        <div className="flex gap-2">
                          {u.role !== "admin" && u.role !== "owner" && (
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => handlePromoteUser(u.id)}
                              disabled={promoteUserMutation.isPending}
                            >
                              <Edit className="w-4 h-4" />
                            </Button>
                          )}

                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Audit Logs Tab */}
          <TabsContent value="audit" className="space-y-4">
            <Card className="shadow-premium">
              <CardHeader>
                <CardTitle>Audit Logs</CardTitle>
                <CardDescription>Track all system actions and changes</CardDescription>
              </CardHeader>
              <CardContent>
                {logsLoading ? (
                  <p className="text-muted-foreground text-center py-8">Loading audit logs...</p>
                ) : !auditLogs || auditLogs.length === 0 ? (
                  <p className="text-muted-foreground text-center py-8">No audit logs found</p>
                ) : (
                  <div className="space-y-3 max-h-96 overflow-y-auto">
                    {auditLogs.map((log: any, idx: number) => (
                      <div key={idx} className="p-3 border rounded-lg text-sm">
                        <div className="flex items-center justify-between mb-2">
                          <p className="font-semibold">{log.action}</p>
                          <p className="text-xs text-muted-foreground">
                            {new Date(log.createdAt).toLocaleString()}
                          </p>
                        </div>
                        <p className="text-muted-foreground text-xs">
                          Resource: {log.resourceType} ({log.resourceId})
                        </p>
                        {log.details && (
                          <p className="text-xs text-muted-foreground mt-1">
                            Details: {JSON.stringify(log.details).substring(0, 100)}...
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Policies Tab */}
          <TabsContent value="policies" className="space-y-4">
            <Card className="shadow-premium">
              <CardHeader>
                <CardTitle>Deployment Policies</CardTitle>
                <CardDescription>Configure global deployment settings</CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground text-center py-8">Deployment policies management coming soon</p>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
    </div>
  );
}
