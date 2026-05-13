import {
  int,
  mysqlEnum,
  mysqlTable,
  text,
  timestamp,
  varchar,
  decimal,
  boolean,
  json,
  longtext,
  index,
} from "drizzle-orm/mysql-core";

/**
 * Core user table backing auth flow with role-based access control.
 */
export const users = mysqlTable(
  "users",
  {
    id: int("id").autoincrement().primaryKey(),
    openId: varchar("openId", { length: 64 }).notNull().unique(),
    name: text("name"),
    email: varchar("email", { length: 320 }),
    loginMethod: varchar("loginMethod", { length: 64 }),
    role: mysqlEnum("role", ["user", "admin", "owner"]).default("user").notNull(),
    createdAt: timestamp("createdAt").defaultNow().notNull(),
    updatedAt: timestamp("updatedAt").defaultNow().onUpdateNow().notNull(),
    lastSignedIn: timestamp("lastSignedIn").defaultNow().notNull(),
  },
  (table) => ({
    roleIdx: index("role_idx").on(table.role),
  })
);

export type User = typeof users.$inferSelect;
export type InsertUser = typeof users.$inferInsert;

/**
 * Hardware devices in the fleet.
 * Tracks physical machines and their hardware profiles.
 */
export const devices = mysqlTable(
  "devices",
  {
    id: int("id").autoincrement().primaryKey(),
    deviceId: varchar("deviceId", { length: 128 }).notNull().unique(), // UUID or MAC-based identifier
    name: varchar("name", { length: 255 }).notNull(),
    status: mysqlEnum("status", ["online", "offline", "error", "deploying"]).default("offline").notNull(),
    hardwareProfile: json("hardwareProfile").notNull(), // { cpu, ram, storage, gpu, chipset, etc. }
    osType: mysqlEnum("osType", ["windows", "macos", "linux"]).notNull(),
    macAddress: varchar("macAddress", { length: 17 }),
    ipAddress: varchar("ipAddress", { length: 45 }),
    lastHeartbeat: timestamp("lastHeartbeat"),
    createdAt: timestamp("createdAt").defaultNow().notNull(),
    updatedAt: timestamp("updatedAt").defaultNow().onUpdateNow().notNull(),
  },
  (table) => ({
    statusIdx: index("device_status_idx").on(table.status),
    deviceIdIdx: index("device_id_idx").on(table.deviceId),
  })
);

export type Device = typeof devices.$inferSelect;
export type InsertDevice = typeof devices.$inferInsert;

/**
 * USB deployment recipes.
 * Stores configurations for bootable USB builds.
 */
export const recipes = mysqlTable(
  "recipes",
  {
    id: int("id").autoincrement().primaryKey(),
    recipeId: varchar("recipeId", { length: 128 }).notNull().unique(),
    userId: int("userId").notNull(),
    name: varchar("name", { length: 255 }).notNull(),
    description: text("description"),
    osImage: json("osImage").notNull(), // { name, version, url, size }
    drivers: json("drivers").notNull(), // Array of driver objects
    tools: json("tools").notNull(), // Array of tool objects
    estimatedSize: decimal("estimatedSize", { precision: 10, scale: 2 }).notNull(),
    compatibility: json("compatibility"), // { supportedHardware, excludedModels }
    createdAt: timestamp("createdAt").defaultNow().notNull(),
    updatedAt: timestamp("updatedAt").defaultNow().onUpdateNow().notNull(),
  },
  (table) => ({
    userIdIdx: index("recipe_user_idx").on(table.userId),
  })
);

export type Recipe = typeof recipes.$inferSelect;
export type InsertRecipe = typeof recipes.$inferInsert;

/**
 * Deployment jobs tracking.
 * Records all USB builds and device deployments.
 */
export const deployments = mysqlTable(
  "deployments",
  {
    id: int("id").autoincrement().primaryKey(),
    deploymentId: varchar("deploymentId", { length: 128 }).notNull().unique(),
    recipeId: int("recipeId").notNull(),
    deviceId: int("deviceId"),
    userId: int("userId").notNull(),
    status: mysqlEnum("status", ["pending", "building", "deploying", "completed", "failed", "cancelled"]).default("pending").notNull(),
    progressPercent: int("progressPercent").default(0).notNull(),
    startedAt: timestamp("startedAt"),
    completedAt: timestamp("completedAt"),
    errorMessage: text("errorMessage"),
    createdAt: timestamp("createdAt").defaultNow().notNull(),
    updatedAt: timestamp("updatedAt").defaultNow().onUpdateNow().notNull(),
  },
  (table) => ({
    statusIdx: index("deployment_status_idx").on(table.status),
    deviceIdIdx: index("deployment_device_idx").on(table.deviceId),
    userIdIdx: index("deployment_user_idx").on(table.userId),
  })
);

export type Deployment = typeof deployments.$inferSelect;
export type InsertDeployment = typeof deployments.$inferInsert;

/**
 * Deployment logs with streaming support.
 * Stores real-time log entries for active deployments.
 */
export const deploymentLogs = mysqlTable(
  "deployment_logs",
  {
    id: int("id").autoincrement().primaryKey(),
    deploymentId: int("deploymentId").notNull(),
    timestamp: timestamp("timestamp").defaultNow().notNull(),
    level: mysqlEnum("level", ["info", "warning", "error", "debug"]).default("info").notNull(),
    message: longtext("message").notNull(),
  },
  (table) => ({
    deploymentIdIdx: index("log_deployment_idx").on(table.deploymentId),
  })
);

export type DeploymentLog = typeof deploymentLogs.$inferSelect;
export type InsertDeploymentLog = typeof deploymentLogs.$inferInsert;

/**
 * Phoenix Relay nodes for hybrid cloud-edge architecture.
 * Tracks relay servers and their health/sync status.
 */
export const relayNodes = mysqlTable(
  "relay_nodes",
  {
    id: int("id").autoincrement().primaryKey(),
    nodeId: varchar("nodeId", { length: 128 }).notNull().unique(),
    name: varchar("name", { length: 255 }).notNull(),
    location: varchar("location", { length: 255 }),
    status: mysqlEnum("status", ["healthy", "degraded", "offline"]).default("offline").notNull(),
    syncStatus: mysqlEnum("syncStatus", ["synced", "syncing", "out_of_sync"]).default("out_of_sync").notNull(),
    cacheHealth: decimal("cacheHealth", { precision: 5, scale: 2 }).default("0.00"), // Percentage
    lastHeartbeat: timestamp("lastHeartbeat"),
    configuredAt: timestamp("configuredAt"),
    createdAt: timestamp("createdAt").defaultNow().notNull(),
    updatedAt: timestamp("updatedAt").defaultNow().onUpdateNow().notNull(),
  },
  (table) => ({
    statusIdx: index("relay_status_idx").on(table.status),
  })
);

export type RelayNode = typeof relayNodes.$inferSelect;
export type InsertRelayNode = typeof relayNodes.$inferInsert;

/**
 * Boot Camp drivers database.
 * Stores Windows drivers for Mac hardware deployment.
 */
export const bootcampDrivers = mysqlTable(
  "bootcamp_drivers",
  {
    id: int("id").autoincrement().primaryKey(),
    driverId: varchar("driverId", { length: 128 }).notNull().unique(),
    name: varchar("name", { length: 255 }).notNull(),
    category: varchar("category", { length: 128 }).notNull(), // chipset, audio, graphics, etc.
    version: varchar("version", { length: 64 }).notNull(),
    downloadUrl: text("downloadUrl").notNull(),
    fileSize: decimal("fileSize", { precision: 10, scale: 2 }).notNull(),
    compatibleModels: json("compatibleModels").notNull(), // Array of Mac models
    releaseDate: timestamp("releaseDate"),
    createdAt: timestamp("createdAt").defaultNow().notNull(),
    updatedAt: timestamp("updatedAt").defaultNow().onUpdateNow().notNull(),
  },
  (table) => ({
    categoryIdx: index("driver_category_idx").on(table.category),
  })
);

export type BootcampDriver = typeof bootcampDrivers.$inferSelect;
export type InsertBootcampDriver = typeof bootcampDrivers.$inferInsert;

/**
 * Notifications for users.
 * Tracks in-app and email notifications.
 */
export const notifications = mysqlTable(
  "notifications",
  {
    id: int("id").autoincrement().primaryKey(),
    notificationId: varchar("notificationId", { length: 128 }).notNull().unique(),
    userId: int("userId").notNull(),
    type: mysqlEnum("type", ["deployment_complete", "deployment_failed", "fleet_alert", "system_alert"]).notNull(),
    title: varchar("title", { length: 255 }).notNull(),
    content: text("content").notNull(),
    relatedResourceId: varchar("relatedResourceId", { length: 128 }),
    read: boolean("read").default(false).notNull(),
    readAt: timestamp("readAt"),
    createdAt: timestamp("createdAt").defaultNow().notNull(),
  },
  (table) => ({
    userIdIdx: index("notification_user_idx").on(table.userId),
    readIdx: index("notification_read_idx").on(table.read),
  })
);

export type Notification = typeof notifications.$inferSelect;
export type InsertNotification = typeof notifications.$inferInsert;

/**
 * User notification preferences.
 * Stores email and in-app notification settings per user.
 */
export const notificationPreferences = mysqlTable(
  "notification_preferences",
  {
    id: int("id").autoincrement().primaryKey(),
    userId: int("userId").notNull().unique(),
    emailOnDeploymentComplete: boolean("emailOnDeploymentComplete").default(true).notNull(),
    emailOnDeploymentFailed: boolean("emailOnDeploymentFailed").default(true).notNull(),
    emailOnFleetAlert: boolean("emailOnFleetAlert").default(false).notNull(),
    inAppNotifications: boolean("inAppNotifications").default(true).notNull(),
    createdAt: timestamp("createdAt").defaultNow().notNull(),
    updatedAt: timestamp("updatedAt").defaultNow().onUpdateNow().notNull(),
  },
  (table) => ({
    userIdIdx: index("pref_user_idx").on(table.userId),
  })
);

export type NotificationPreference = typeof notificationPreferences.$inferSelect;
export type InsertNotificationPreference = typeof notificationPreferences.$inferInsert;

/**
 * Audit logs for compliance and troubleshooting.
 * Records all significant actions by users and system.
 */
export const auditLogs = mysqlTable(
  "audit_logs",
  {
    id: int("id").autoincrement().primaryKey(),
    userId: int("userId"),
    action: varchar("action", { length: 128 }).notNull(), // e.g., "deployment_started", "user_promoted"
    resourceType: varchar("resourceType", { length: 128 }).notNull(), // e.g., "deployment", "user", "relay_node"
    resourceId: varchar("resourceId", { length: 128 }).notNull(),
    details: json("details"), // Additional context
    createdAt: timestamp("createdAt").defaultNow().notNull(),
  },
  (table) => ({
    userIdIdx: index("audit_user_idx").on(table.userId),
    actionIdx: index("audit_action_idx").on(table.action),
  })
);

export type AuditLog = typeof auditLogs.$inferSelect;
export type InsertAuditLog = typeof auditLogs.$inferInsert;

/**
 * Global deployment policies.
 * Stores system-wide configuration for deployments and fleet management.
 */
export const deploymentPolicies = mysqlTable(
  "deployment_policies",
  {
    id: int("id").autoincrement().primaryKey(),
    policyKey: varchar("policyKey", { length: 128 }).notNull().unique(),
    value: json("value").notNull(),
    description: text("description"),
    createdAt: timestamp("createdAt").defaultNow().notNull(),
    updatedAt: timestamp("updatedAt").defaultNow().onUpdateNow().notNull(),
  }
);

export type DeploymentPolicy = typeof deploymentPolicies.$inferSelect;
export type InsertDeploymentPolicy = typeof deploymentPolicies.$inferInsert;

/**
 * System health metrics.
 * Tracks backend service health, uptime, and performance.
 */
export const healthMetrics = mysqlTable(
  "health_metrics",
  {
    id: int("id").autoincrement().primaryKey(),
    serviceName: varchar("serviceName", { length: 128 }).notNull(),
    status: mysqlEnum("status", ["healthy", "degraded", "offline"]).default("offline").notNull(),
    latency: int("latency"), // milliseconds
    uptime: decimal("uptime", { precision: 5, scale: 2 }), // percentage
    lastCheck: timestamp("lastCheck").defaultNow().notNull(),
  },
  (table) => ({
    serviceIdx: index("health_service_idx").on(table.serviceName),
  })
);

export type HealthMetric = typeof healthMetrics.$inferSelect;
export type InsertHealthMetric = typeof healthMetrics.$inferInsert;
