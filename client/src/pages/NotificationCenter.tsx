import { useState } from "react";
import { trpc } from "@/lib/trpc";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Bell, CheckCircle, AlertCircle, Info, Trash2 } from "lucide-react";
import { toast } from "sonner";

type NotificationType = "success" | "error" | "info" | "warning";

interface Notification {
  id: number;
  type: NotificationType;
  title: string;
  message: string;
  createdAt: Date;
  readAt?: Date;
  actionUrl?: string;
}

export default function NotificationCenter() {
  const [selectedTab, setSelectedTab] = useState<"all" | "unread">("all");

  const notificationsQuery = trpc.notification.list.useQuery({ unreadOnly: false });
  const markReadMutation = trpc.notification.markAsRead.useMutation();

  const notifications = notificationsQuery.data || [];
  const unreadCount = notifications.filter((n: any) => !n.read).length;

  const handleMarkAsRead = async (id: number) => {
    try {
      await markReadMutation.mutateAsync({ notificationId: id });
      notificationsQuery.refetch();
      toast.success("Marked as read");
    } catch (error) {
      toast.error("Failed to mark as read");
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await markReadMutation.mutateAsync({ notificationId: id });
      notificationsQuery.refetch();
      toast.success("Notification archived");
    } catch (error) {
      toast.error("Failed to archive notification");
    }
  };

  const getIcon = (type: NotificationType) => {
    switch (type) {
      case "success":
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case "error":
        return <AlertCircle className="w-5 h-5 text-red-500" />;
      case "warning":
        return <AlertCircle className="w-5 h-5 text-yellow-500" />;
      default:
        return <Info className="w-5 h-5 text-blue-500" />;
    }
  };

  const getBadgeVariant = (type: NotificationType) => {
    switch (type) {
      case "success":
        return "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200";
      case "error":
        return "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200";
      case "warning":
        return "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200";
      default:
        return "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200";
    }
  };

  const filteredNotifications =
    selectedTab === "unread"
      ? notifications.filter((n: any) => !n.read)
      : notifications;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-4xl font-bold text-foreground tracking-tight flex items-center gap-3">
          <Bell className="w-8 h-8 text-primary" />
          Notification Center
        </h1>
        <p className="text-muted-foreground mt-2 text-lg">
          Manage deployment alerts, fleet updates, and system notifications
        </p>
      </div>

        {/* Tabs */}
        <Tabs value={selectedTab} onValueChange={(v) => setSelectedTab(v as any)}>
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="all" className="flex items-center gap-2">
              All Notifications
              <Badge variant="secondary">{notifications.length}</Badge>
            </TabsTrigger>
            <TabsTrigger value="unread" className="flex items-center gap-2">
              Unread
              {unreadCount > 0 && (
                <Badge className="bg-red-500 text-white">{unreadCount}</Badge>
              )}
            </TabsTrigger>
          </TabsList>

          <TabsContent value={selectedTab} className="space-y-4">
            {filteredNotifications.length === 0 ? (
              <Card className="shadow-premium">
                <CardContent className="flex flex-col items-center justify-center py-12">
                  <Bell className="w-12 h-12 text-muted-foreground mb-4 opacity-50" />
                  <p className="text-muted-foreground text-center">
                    {selectedTab === "unread"
                      ? "No unread notifications"
                      : "No notifications yet"}
                  </p>
                </CardContent>
              </Card>
            ) : (
              filteredNotifications.map((notification: any) => (
                <Card
                  key={notification.id}
                  className={`shadow-premium cursor-pointer transition-all ${
                    !notification.read
                      ? "border-l-4 border-l-primary bg-primary/5"
                      : "opacity-75"
                  }`}
                  onClick={() =>
                    !notification.read &&
                    handleMarkAsRead(notification.id)
                  }
                >
                  <CardContent className="pt-6">
                    <div className="flex items-start gap-4">
                      <div className="mt-1">
                        {getIcon(notification.type)}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <h3 className="font-semibold text-foreground">
                            {notification.title}
                          </h3>
                          <Badge className={getBadgeVariant(notification.type as NotificationType)}>
                            {notification.type}
                          </Badge>
                          {!notification.read && (
                            <Badge className="bg-primary text-white">
                              New
                            </Badge>
                          )}
                        </div>
                        <p className="text-sm text-muted-foreground mb-3">
                          {notification.content}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          {new Date(notification.createdAt).toLocaleString()}
                        </p>
                      </div>
                      <div className="flex gap-2">
                        {notification.relatedResourceId && (
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={(e) => {
                              e.stopPropagation();
                              window.location.href = `/deployment/${notification.relatedResourceId}`;
                            }}
                          >
                            View
                          </Button>
                        )}
                        {notification.read && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleDelete(notification.id);
                            }}
                          >
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        )}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))
            )}
          </TabsContent>
        </Tabs>

        {/* Notification Settings Card */}
        <Card className="shadow-premium">
          <CardHeader>
            <CardTitle>Notification Preferences</CardTitle>
            <CardDescription>
              Configure how you receive notifications
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-3">
              <div className="flex items-center justify-between p-3 border rounded-lg">
                <div>
                  <p className="font-medium">Deployment Alerts</p>
                  <p className="text-sm text-muted-foreground">
                    Get notified when deployments complete or fail
                  </p>
                </div>
                <Badge className="bg-green-500">Enabled</Badge>
              </div>
              <div className="flex items-center justify-between p-3 border rounded-lg">
                <div>
                  <p className="font-medium">Fleet Anomalies</p>
                  <p className="text-sm text-muted-foreground">
                    Alert on device offline or health issues
                  </p>
                </div>
                <Badge className="bg-green-500">Enabled</Badge>
              </div>
              <div className="flex items-center justify-between p-3 border rounded-lg">
                <div>
                  <p className="font-medium">Email Notifications</p>
                  <p className="text-sm text-muted-foreground">
                    Receive critical alerts via email
                  </p>
                </div>
                <Badge className="bg-green-500">Enabled</Badge>
              </div>
            </div>
            <Button className="w-full">Edit Preferences</Button>
          </CardContent>
        </Card>
    </div>
  );
}
