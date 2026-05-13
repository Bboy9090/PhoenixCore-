import { eq, desc, and, like } from "drizzle-orm";
import { drizzle } from "drizzle-orm/mysql2";
import {
  InsertUser,
  users,
  devices,
  recipes,
  deployments,
  deploymentLogs,
  relayNodes,
  bootcampDrivers,
  notifications,
  notificationPreferences,
  auditLogs,
  deploymentPolicies,
  healthMetrics,
} from "../drizzle/schema";
import { ENV } from "./_core/env";

let _db: ReturnType<typeof drizzle> | null = null;

export async function getDb() {
  if (!_db && process.env.DATABASE_URL) {
    try {
      _db = drizzle(process.env.DATABASE_URL);
    } catch (error) {
      console.warn("[Database] Failed to connect:", error);
      _db = null;
    }
  }
  return _db;
}

export async function upsertUser(user: InsertUser): Promise<void> {
  if (!user.openId) {
    throw new Error("User openId is required for upsert");
  }

  const db = await getDb();
  if (!db) {
    console.warn("[Database] Cannot upsert user: database not available");
    return;
  }

  try {
    const values: InsertUser = {
      openId: user.openId,
    };
    const updateSet: Record<string, unknown> = {};

    const textFields = ["name", "email", "loginMethod"] as const;
    type TextField = (typeof textFields)[number];

    const assignNullable = (field: TextField) => {
      const value = user[field];
      if (value === undefined) return;
      const normalized = value ?? null;
      values[field] = normalized;
      updateSet[field] = normalized;
    };

    textFields.forEach(assignNullable);

    if (user.lastSignedIn !== undefined) {
      values.lastSignedIn = user.lastSignedIn;
      updateSet.lastSignedIn = user.lastSignedIn;
    }
    if (user.role !== undefined) {
      values.role = user.role;
      updateSet.role = user.role;
    } else if (user.openId === ENV.ownerOpenId) {
      values.role = 'admin';
      updateSet.role = 'admin';
    }

    if (!values.lastSignedIn) {
      values.lastSignedIn = new Date();
    }

    if (Object.keys(updateSet).length === 0) {
      updateSet.lastSignedIn = new Date();
    }

    await db.insert(users).values(values).onDuplicateKeyUpdate({
      set: updateSet,
    });
  } catch (error) {
    console.error("[Database] Failed to upsert user:", error);
    throw error;
  }
}

export async function getUserByOpenId(openId: string) {
  const db = await getDb();
  if (!db) {
    console.warn("[Database] Cannot get user: database not available");
    return undefined;
  }

  const result = await db.select().from(users).where(eq(users.openId, openId)).limit(1);
  return result.length > 0 ? result[0] : undefined;
}

// ========== DEVICE MANAGEMENT ==========

export async function listDevices(filters?: { status?: string; osType?: string }) {
  const db = await getDb();
  if (!db) return [];

  const conditions = [];

  if (filters?.status) {
    conditions.push(eq(devices.status, filters.status as any));
  }
  if (filters?.osType) {
    conditions.push(eq(devices.osType, filters.osType as any));
  }

  if (conditions.length > 0) {
    return await db.select().from(devices).where(and(...conditions)).orderBy(desc(devices.lastHeartbeat));
  }
  return await db.select().from(devices).orderBy(desc(devices.lastHeartbeat));
}

export async function getDeviceById(deviceId: number) {
  const db = await getDb();
  if (!db) return null;

  const result = await db.select().from(devices).where(eq(devices.id, deviceId)).limit(1);
  return result.length > 0 ? result[0] : null;
}

export async function createDevice(data: typeof devices.$inferInsert) {
  const db = await getDb();
  if (!db) throw new Error("Database not available");

  const result = await db.insert(devices).values(data);
  return result;
}

export async function updateDeviceStatus(deviceId: number, status: string) {
  const db = await getDb();
  if (!db) throw new Error("Database not available");

  return await db.update(devices).set({ status: status as any }).where(eq(devices.id, deviceId));
}

// ========== RECIPE MANAGEMENT ==========

export async function listRecipes(userId: number) {
  const db = await getDb();
  if (!db) return [];

  return await db.select().from(recipes).where(eq(recipes.userId, userId)).orderBy(desc(recipes.createdAt));
}

export async function getRecipeById(recipeId: number) {
  const db = await getDb();
  if (!db) return null;

  const result = await db.select().from(recipes).where(eq(recipes.id, recipeId)).limit(1);
  return result.length > 0 ? result[0] : null;
}

export async function createRecipe(data: typeof recipes.$inferInsert) {
  const db = await getDb();
  if (!db) throw new Error("Database not available");

  return await db.insert(recipes).values(data);
}

export async function deleteRecipe(recipeId: number) {
  const db = await getDb();
  if (!db) throw new Error("Database not available");

  return await db.delete(recipes).where(eq(recipes.id, recipeId));
}

// ========== DEPLOYMENT MANAGEMENT ==========

export async function listDeployments(filters?: { userId?: number; status?: string; deviceId?: number }) {
  const db = await getDb();
  if (!db) return [];

  const conditions = [];

  if (filters?.userId) {
    conditions.push(eq(deployments.userId, filters.userId));
  }
  if (filters?.status) {
    conditions.push(eq(deployments.status, filters.status as any));
  }
  if (filters?.deviceId) {
    conditions.push(eq(deployments.deviceId, filters.deviceId));
  }

  if (conditions.length > 0) {
    return await db.select().from(deployments).where(and(...conditions)).orderBy(desc(deployments.createdAt));
  }
  return await db.select().from(deployments).orderBy(desc(deployments.createdAt));
}

export async function getDeploymentById(deploymentId: number) {
  const db = await getDb();
  if (!db) return null;

  const result = await db.select().from(deployments).where(eq(deployments.id, deploymentId)).limit(1);
  return result.length > 0 ? result[0] : null;
}

export async function createDeployment(data: typeof deployments.$inferInsert) {
  const db = await getDb();
  if (!db) throw new Error("Database not available");

  return await db.insert(deployments).values(data);
}

export async function updateDeploymentProgress(deploymentId: number, progressPercent: number, status?: string) {
  const db = await getDb();
  if (!db) throw new Error("Database not available");

  const updateData: any = { progressPercent };
  if (status) updateData.status = status;
  if (status === "completed") updateData.completedAt = new Date();

  return await db.update(deployments).set(updateData).where(eq(deployments.id, deploymentId));
}

export async function addDeploymentLog(deploymentId: number, level: string, message: string) {
  const db = await getDb();
  if (!db) throw new Error("Database not available");

  return await db.insert(deploymentLogs).values({
    deploymentId,
    level: level as any,
    message,
  });
}

export async function getDeploymentLogs(deploymentId: number) {
  const db = await getDb();
  if (!db) return [];

  return await db.select().from(deploymentLogs).where(eq(deploymentLogs.deploymentId, deploymentId)).orderBy(deploymentLogs.timestamp);
}

// ========== RELAY NODE MANAGEMENT ==========

export async function listRelayNodes() {
  const db = await getDb();
  if (!db) return [];

  return await db.select().from(relayNodes).orderBy(desc(relayNodes.lastHeartbeat));
}

export async function getRelayNodeById(nodeId: number) {
  const db = await getDb();
  if (!db) return null;

  const result = await db.select().from(relayNodes).where(eq(relayNodes.id, nodeId)).limit(1);
  return result.length > 0 ? result[0] : null;
}

export async function createRelayNode(data: typeof relayNodes.$inferInsert) {
  const db = await getDb();
  if (!db) throw new Error("Database not available");

  return await db.insert(relayNodes).values(data);
}

export async function updateRelayNodeStatus(nodeId: number, status: string, syncStatus?: string, cacheHealth?: string) {
  const db = await getDb();
  if (!db) throw new Error("Database not available");

  const updateData: any = { status: status as any, lastHeartbeat: new Date() };
  if (syncStatus) updateData.syncStatus = syncStatus;
  if (cacheHealth) updateData.cacheHealth = cacheHealth;

  return await db.update(relayNodes).set(updateData).where(eq(relayNodes.id, nodeId));
}

// ========== BOOT CAMP DRIVER MANAGEMENT ==========

export async function listBootcampDrivers(filters?: { category?: string; search?: string }) {
  const db = await getDb();
  if (!db) return [];

  const conditions = [];

  if (filters?.category) {
    conditions.push(eq(bootcampDrivers.category, filters.category));
  }
  if (filters?.search) {
    conditions.push(like(bootcampDrivers.name, `%${filters.search}%`));
  }

  if (conditions.length > 0) {
    return await db.select().from(bootcampDrivers).where(and(...conditions)).orderBy(desc(bootcampDrivers.releaseDate));
  }
  return await db.select().from(bootcampDrivers).orderBy(desc(bootcampDrivers.releaseDate));
}

export async function getBootcampDriverById(driverId: number) {
  const db = await getDb();
  if (!db) return null;

  const result = await db.select().from(bootcampDrivers).where(eq(bootcampDrivers.id, driverId)).limit(1);
  return result.length > 0 ? result[0] : null;
}

// ========== NOTIFICATION MANAGEMENT ==========

export async function listNotifications(userId: number, unreadOnly?: boolean) {
  const db = await getDb();
  if (!db) return [];

  const conditions = [eq(notifications.userId, userId)];
  if (unreadOnly) {
    conditions.push(eq(notifications.read, false));
  }

  return await db.select().from(notifications).where(and(...conditions)).orderBy(desc(notifications.createdAt));
}

export async function createNotification(data: typeof notifications.$inferInsert) {
  const db = await getDb();
  if (!db) throw new Error("Database not available");

  return await db.insert(notifications).values(data);
}

export async function markNotificationAsRead(notificationId: number) {
  const db = await getDb();
  if (!db) throw new Error("Database not available");

  return await db.update(notifications).set({ read: true, readAt: new Date() }).where(eq(notifications.id, notificationId));
}

export async function getNotificationPreferences(userId: number) {
  const db = await getDb();
  if (!db) return null;

  const result = await db.select().from(notificationPreferences).where(eq(notificationPreferences.userId, userId)).limit(1);
  return result.length > 0 ? result[0] : null;
}

export async function updateNotificationPreferences(userId: number, prefs: Partial<typeof notificationPreferences.$inferInsert>) {
  const db = await getDb();
  if (!db) throw new Error("Database not available");

  const existing = await getNotificationPreferences(userId);
  if (existing) {
    return await db.update(notificationPreferences).set(prefs).where(eq(notificationPreferences.userId, userId));
  } else {
    return await db.insert(notificationPreferences).values({ userId, ...prefs });
  }
}

// ========== AUDIT LOGGING ==========

export async function logAuditEvent(userId: number | null, action: string, resourceType: string, resourceId: string, details?: any) {
  const db = await getDb();
  if (!db) {
    console.warn("[Audit] Cannot log event: database not available");
    return;
  }

  try {
    await db.insert(auditLogs).values({
      userId,
      action,
      resourceType,
      resourceId,
      details,
    });
  } catch (error) {
    console.error("[Audit] Failed to log event:", error);
  }
}

export async function listAuditLogs(filters?: { userId?: number; action?: string; limit?: number }) {
  const db = await getDb();
  if (!db) return [];

  const conditions = [];

  if (filters?.userId) {
    conditions.push(eq(auditLogs.userId, filters.userId));
  }
  if (filters?.action) {
    conditions.push(eq(auditLogs.action, filters.action));
  }

  if (conditions.length > 0) {
    let query = db.select().from(auditLogs).where(and(...conditions)).orderBy(desc(auditLogs.createdAt));
    if (filters?.limit) {
      return await query.limit(filters.limit);
    }
    return await query;
  }
  
  let query = db.select().from(auditLogs).orderBy(desc(auditLogs.createdAt));
  if (filters?.limit) {
    return await query.limit(filters.limit);
  }
  return await query;
}

// ========== DEPLOYMENT POLICIES ==========

export async function getDeploymentPolicy(policyKey: string) {
  const db = await getDb();
  if (!db) return null;

  const result = await db.select().from(deploymentPolicies).where(eq(deploymentPolicies.policyKey, policyKey)).limit(1);
  return result.length > 0 ? result[0] : null;
}

export async function setDeploymentPolicy(policyKey: string, value: any, description?: string) {
  const db = await getDb();
  if (!db) throw new Error("Database not available");

  const existing = await getDeploymentPolicy(policyKey);
  if (existing) {
    return await db.update(deploymentPolicies).set({ value, description }).where(eq(deploymentPolicies.policyKey, policyKey));
  } else {
    return await db.insert(deploymentPolicies).values({ policyKey, value, description });
  }
}

// ========== HEALTH METRICS ==========

export async function updateHealthMetric(serviceName: string, status: string, latency?: number, uptime?: string) {
  const db = await getDb();
  if (!db) throw new Error("Database not available");

  const existing = await db.select().from(healthMetrics).where(eq(healthMetrics.serviceName, serviceName)).limit(1);

  const updateData: any = { status: status as any, lastCheck: new Date() };
  if (latency !== undefined) updateData.latency = latency;
  if (uptime !== undefined) updateData.uptime = uptime;

  if (existing.length > 0) {
    return await db.update(healthMetrics).set(updateData).where(eq(healthMetrics.serviceName, serviceName));
  } else {
    return await db.insert(healthMetrics).values({ serviceName, ...updateData });
  }
}

export async function getHealthMetrics() {
  const db = await getDb();
  if (!db) return [];

  return await db.select().from(healthMetrics).orderBy(desc(healthMetrics.lastCheck));
}
