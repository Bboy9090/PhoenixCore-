import { TRPCError } from "@trpc/server";
import { nanoid } from "nanoid";
import {
  listDevices,
  getDeviceById,
  createDevice,
  updateDeviceStatus,
  listRecipes,
  getRecipeById,
  createRecipe,
  deleteRecipe,
  listDeployments,
  getDeploymentById,
  createDeployment,
  updateDeploymentProgress,
  addDeploymentLog,
  getDeploymentLogs,
  listRelayNodes,
  getRelayNodeById,
  createRelayNode,
  updateRelayNodeStatus,
  listBootcampDrivers,
  getBootcampDriverById,
  listNotifications,
  createNotification,
  markNotificationAsRead,
  getNotificationPreferences,
  updateNotificationPreferences,
  logAuditEvent,
  listAuditLogs,
  getDeploymentPolicy,
  setDeploymentPolicy,
  updateHealthMetric,
  getHealthMetrics,

} from "./db";
import { COOKIE_NAME } from "@shared/const";
import { getSessionCookieOptions } from "./_core/cookies";
import { systemRouter } from "./_core/systemRouter";
import { publicProcedure, protectedProcedure, router } from "./_core/trpc";

// ========== ROLE-BASED PROCEDURES ==========

const adminProcedure = protectedProcedure.use(({ ctx, next }) => {
  if (ctx.user.role !== "admin" && ctx.user.role !== "owner") {
    throw new TRPCError({ code: "FORBIDDEN", message: "Admin access required" });
  }
  return next({ ctx });
});

const ownerProcedure = protectedProcedure.use(({ ctx, next }) => {
  if (ctx.user.role !== "owner") {
    throw new TRPCError({ code: "FORBIDDEN", message: "Owner access required" });
  }
  return next({ ctx });
});

// ========== HARDWARE INTELLIGENCE ROUTER ==========

const hardwareRouter = router({
  detectConnected: protectedProcedure
    .input((val: unknown) => val as { filters?: { osType?: string } })
    .query(async ({ input }) => {
      const devices = await listDevices(input.filters);
      return {
        devices,
        count: devices.length,
        timestamp: new Date(),
      };
    }),

  generateRecipe: protectedProcedure
    .input((val: unknown) => val as { deviceId: number })
    .mutation(async ({ input, ctx }) => {
      const device = await getDeviceById(input.deviceId);
      if (!device) {
        throw new TRPCError({ code: "NOT_FOUND", message: "Device not found" });
      }

      const recipeId = nanoid();
      const recipe = await createRecipe({
        recipeId,
        userId: ctx.user.id,
        name: `Auto-Recipe for ${device.name}`,
        osImage: {
          name: device.osType,
          version: "latest",
          url: "",
          size: 0,
        },
        drivers: [],
        tools: [],
        estimatedSize: "0.00",
        compatibility: {
          supportedHardware: [device.osType],
        },
      });

      await logAuditEvent(ctx.user.id, "recipe_generated", "recipe", recipeId, {
        deviceId: input.deviceId,
      });

      return recipe;
    }),

  getCompatibleDrivers: protectedProcedure
    .input((val: unknown) => val as { macModel: string })
    .query(async ({ input }) => {
      const drivers = await listBootcampDrivers({
        search: input.macModel,
      });
      return drivers;
    }),
});

// ========== FLEET MANAGEMENT ROUTER ==========

const fleetRouter = router({
  listDevices: protectedProcedure
    .input((val: unknown) => val as { status?: string; osType?: string })
    .query(async ({ input }) => {
      const devices = await listDevices(input);
      return {
        devices,
        totalCount: devices.length,
        onlineCount: devices.filter((d) => d.status === "online").length,
        offlineCount: devices.filter((d) => d.status === "offline").length,
        errorCount: devices.filter((d) => d.status === "error").length,
      };
    }),

  getDeviceDetails: protectedProcedure
    .input((val: unknown) => val as { deviceId: number })
    .query(async ({ input }) => {
      const device = await getDeviceById(input.deviceId);
      if (!device) {
        throw new TRPCError({ code: "NOT_FOUND", message: "Device not found" });
      }

      const deploymentHistory = await listDeployments({ deviceId: input.deviceId });

      return {
        device,
        deploymentHistory,
        lastDeployment: deploymentHistory[0] || null,
      };
    }),

  updateDeviceStatus: adminProcedure
    .input((val: unknown) => val as { deviceId: number; status: string })
    .mutation(async ({ input, ctx }) => {
      await updateDeviceStatus(input.deviceId, input.status);
      await logAuditEvent(ctx.user.id, "device_status_updated", "device", String(input.deviceId), {
        newStatus: input.status,
      });
      return { success: true };
    }),

  getDeploymentHistory: protectedProcedure
    .input((val: unknown) => val as { deviceId: number })
    .query(async ({ input }) => {
      return await listDeployments({ deviceId: input.deviceId });
    }),
});

// ========== USB RECIPE BUILDER ROUTER ==========

const recipeRouter = router({
  list: protectedProcedure.query(async ({ ctx }) => {
    return await listRecipes(ctx.user.id);
  }),

  create: protectedProcedure
    .input(
      (val: unknown) =>
        val as {
          name: string;
          description?: string;
          osImage: any;
          drivers: any[];
          tools: any[];
          estimatedSize: string;
        }
    )
    .mutation(async ({ input, ctx }) => {
      const recipeId = nanoid();
      const result = await createRecipe({
        recipeId,
        userId: ctx.user.id,
        name: input.name,
        description: input.description,
        osImage: input.osImage,
        drivers: input.drivers,
        tools: input.tools,
        estimatedSize: input.estimatedSize,
      });

      await logAuditEvent(ctx.user.id, "recipe_created", "recipe", recipeId, {
        name: input.name,
      });

      return result;
    }),

  delete: protectedProcedure
    .input((val: unknown) => val as { recipeId: number })
    .mutation(async ({ input, ctx }) => {
      const recipe = await getRecipeById(input.recipeId);
      if (!recipe || recipe.userId !== ctx.user.id) {
        throw new TRPCError({ code: "FORBIDDEN", message: "Cannot delete this recipe" });
      }

      await deleteRecipe(input.recipeId);
      await logAuditEvent(ctx.user.id, "recipe_deleted", "recipe", String(input.recipeId));

      return { success: true };
    }),

  estimateSize: publicProcedure
    .input((val: unknown) => val as { osImage: any; drivers: any[]; tools: any[] })
    .query(({ input }) => {
      let totalSize = 0;
      if (input.osImage?.size) totalSize += input.osImage.size;
      if (input.drivers) {
        totalSize += input.drivers.reduce((sum: number, d: any) => sum + (d.size || 0), 0);
      }
      if (input.tools) {
        totalSize += input.tools.reduce((sum: number, t: any) => sum + (t.size || 0), 0);
      }
      return {
        totalSizeGB: (totalSize / 1024 / 1024 / 1024).toFixed(2),
        components: {
          osImage: (input.osImage?.size || 0) / 1024 / 1024 / 1024,
          drivers: input.drivers.length,
          tools: input.tools.length,
        },
      };
    }),
});

// ========== DEPLOYMENT ROUTER ==========

const deploymentRouter = router({
  list: protectedProcedure
    .input((val: unknown) => val as { status?: string })
    .query(async ({ input, ctx }) => {
      return await listDeployments({ userId: ctx.user.id, status: input.status });
    }),

  create: protectedProcedure
    .input((val: unknown) => val as { recipeId: number; deviceId?: number })
    .mutation(async ({ input, ctx }) => {
      const recipe = await getRecipeById(input.recipeId);
      if (!recipe) {
        throw new TRPCError({ code: "NOT_FOUND", message: "Recipe not found" });
      }

      const deploymentId = nanoid();
      const result = await createDeployment({
        deploymentId,
        recipeId: input.recipeId,
        deviceId: input.deviceId || null,
        userId: ctx.user.id,
        status: "pending",
      });

      await logAuditEvent(ctx.user.id, "deployment_created", "deployment", deploymentId, {
        recipeId: input.recipeId,
        deviceId: input.deviceId,
      });

      return result;
    }),

  getProgress: protectedProcedure
    .input((val: unknown) => val as { deploymentId: number })
    .query(async ({ input }) => {
      const deployment = await getDeploymentById(input.deploymentId);
      if (!deployment) {
        throw new TRPCError({ code: "NOT_FOUND", message: "Deployment not found" });
      }

      const logs = await getDeploymentLogs(input.deploymentId);
      return {
        deployment,
        logs,
      };
    }),

  updateProgress: adminProcedure
    .input((val: unknown) => val as { deploymentId: number; progressPercent: number; status?: string })
    .mutation(async ({ input, ctx }) => {
      await updateDeploymentProgress(input.deploymentId, input.progressPercent, input.status);
      await logAuditEvent(ctx.user.id, "deployment_progress_updated", "deployment", String(input.deploymentId), {
        progressPercent: input.progressPercent,
        status: input.status,
      });
      return { success: true };
    }),

  addLog: adminProcedure
    .input((val: unknown) => val as { deploymentId: number; level: string; message: string })
    .mutation(async ({ input, ctx }) => {
      await addDeploymentLog(input.deploymentId, input.level, input.message);
      return { success: true };
    }),
});

// ========== PHOENIX RELAY ROUTER ==========

const relayRouter = router({
  listNodes: adminProcedure.query(async () => {
    return await listRelayNodes();
  }),

  configureNode: ownerProcedure
    .input((val: unknown) => val as { nodeId: number; config: any })
    .mutation(async ({ input, ctx }) => {
      const node = await getRelayNodeById(input.nodeId);
      if (!node) {
        throw new TRPCError({ code: "NOT_FOUND", message: "Relay node not found" });
      }

      await logAuditEvent(ctx.user.id, "relay_node_configured", "relay_node", String(input.nodeId), {
        config: input.config,
      });

      return { success: true };
    }),

  getNodeHealth: adminProcedure
    .input((val: unknown) => val as { nodeId: number })
    .query(async ({ input }) => {
      const node = await getRelayNodeById(input.nodeId);
      if (!node) {
        throw new TRPCError({ code: "NOT_FOUND", message: "Relay node not found" });
      }

      return {
        node,
        health: {
          status: node.status,
          syncStatus: node.syncStatus,
          cacheHealth: node.cacheHealth,
          lastHeartbeat: node.lastHeartbeat,
        },
      };
    }),

  syncImageCache: adminProcedure
    .input((val: unknown) => val as { nodeId: number })
    .mutation(async ({ input, ctx }) => {
      await updateRelayNodeStatus(input.nodeId, "healthy", "syncing");
      await logAuditEvent(ctx.user.id, "relay_cache_sync_started", "relay_node", String(input.nodeId));
      return { success: true };
    }),
});

// ========== BOOT CAMP DRIVER ROUTER ==========

const bootcampRouter = router({
  listDrivers: protectedProcedure
    .input((val: unknown) => val as { category?: string; search?: string })
    .query(async ({ input }) => {
      return await listBootcampDrivers(input);
    }),

  getCompatibleDrivers: protectedProcedure
    .input((val: unknown) => val as { macModel: string })
    .query(async ({ input }) => {
      return await listBootcampDrivers({ search: input.macModel });
    }),

  deployDriver: adminProcedure
    .input((val: unknown) => val as { deviceId: number; driverId: number })
    .mutation(async ({ input, ctx }) => {
      const driver = await getBootcampDriverById(input.driverId);
      if (!driver) {
        throw new TRPCError({ code: "NOT_FOUND", message: "Driver not found" });
      }

      await logAuditEvent(ctx.user.id, "driver_deployed", "bootcamp_driver", String(input.driverId), {
        deviceId: input.deviceId,
      });

      return { success: true };
    }),
});

// ========== ADMIN ROUTER ==========

const adminRouter = router({
  listUsers: ownerProcedure.query(async () => {
    return [];
  }),

  updateUserRole: ownerProcedure
    .input((val: unknown) => val as { userId: number; role: string })
    .mutation(async ({ input, ctx }) => {
      await logAuditEvent(ctx.user.id, "user_role_updated", "user", String(input.userId), {
        newRole: input.role,
      });
      return { success: true };
    }),

  getAuditLogs: adminProcedure
    .input((val: unknown) => val as { userId?: number; action?: string; limit?: number })
    .query(async ({ input }) => {
      return await listAuditLogs(input);
    }),

  updatePolicies: ownerProcedure
    .input((val: unknown) => val as { policies: Record<string, any> })
    .mutation(async ({ input, ctx }) => {
      for (const [key, value] of Object.entries(input.policies)) {
        await setDeploymentPolicy(key, value);
      }

      await logAuditEvent(ctx.user.id, "policies_updated", "system", "policies", {
        policyKeys: Object.keys(input.policies),
      });

      return { success: true };
    }),
});

// ========== NOTIFICATION ROUTER ==========

const notificationRouter = router({
  list: protectedProcedure
    .input((val: unknown) => val as { unreadOnly?: boolean })
    .query(async ({ input, ctx }) => {
      return await listNotifications(ctx.user.id, input.unreadOnly);
    }),

  markAsRead: protectedProcedure
    .input((val: unknown) => val as { notificationId: number })
    .mutation(async ({ input }) => {
      await markNotificationAsRead(input.notificationId);
      return { success: true };
    }),

  getPreferences: protectedProcedure.query(async ({ ctx }) => {
    return await getNotificationPreferences(ctx.user.id);
  }),

  updatePreferences: protectedProcedure
    .input((val: unknown) => val as { preferences: any })
    .mutation(async ({ input, ctx }) => {
      await updateNotificationPreferences(ctx.user.id, input.preferences);
      return { success: true };
    }),
});

// ========== IMAGING OPERATION ROUTER (PR15 CONVERGENCE) ==========

const operationRouter = router({
  preview: protectedProcedure
    .input((val: unknown) => val as { opId: string; params: any })
    .mutation(async ({ input, ctx }) => {
      // Mocking the preview-first doctrine
      const manifestHash = nanoid(32);
      
      // Safety Check: Removable-only default
      const target = input.params.target as { classification: string };
      const isDangerous = target && target.classification !== "removable";
      
      return {
        metadata: {
          operationId: input.opId,
          actorId: ctx.user.id,
          deviceIdentity: input.params.target,
          targetSummary: input.params.target?.model || "Unknown Target",
          previewSummary: `Imaging recipe ${input.params.recipeId} to ${input.params.target?.vendor} media`,
          riskLevel: isDangerous ? "system_protected" : "removable_only",
          timestamp: new Date().toISOString(),
          rollbackPossible: false,
        },
        proposedChanges: [
          "Format target partition as FAT32",
          "Copy BootForge bootloader",
          "Apply Phoenix Core runtime patches"
        ],
        risks: isDangerous ? ["SYSTEM DISK MODIFICATION DETECTED", "IRREVERSIBLE DATA LOSS"] : ["Data on target USB will be erased"],
        manifestHash,
      };
    }),

  evaluate: protectedProcedure
    .input((val: unknown) => val as { opId: string; params: any })
    .query(async ({ input }) => {
      const target = input.params.target as { classification: string };
      const isAllowed = target && target.classification === "removable";

      return {
        allowed: isAllowed,
        requirements: isAllowed ? ["User Confirmation"] : ["RECOVERY_MODE Required", "Physical Presence Verification"],
        reason: isAllowed ? undefined : "Direct imaging of system disks is blocked in current runtime mode.",
      };
    }),

  confirm: protectedProcedure
    .input((val: unknown) => val as { opId: string; manifestHash: string })
    .mutation(async ({ input }) => {
      // In a real implementation, this would verify the manifest hash against a signed blob
      return {
        confirmationToken: nanoid(16),
        expiresAt: new Date(Date.now() + 300000).toISOString(), // 5 min expiry
      };
    }),

  execute: protectedProcedure
    .input((val: unknown) => val as { opId: string; params: any; tokens: { confirmation: string; phx?: string } })
    .mutation(async ({ input, ctx }) => {
      // Runtime Convergence: Enforce preview-first
      if (!input.tokens.confirmation) {
        throw new TRPCError({ code: "PRECONDITION_FAILED", message: "Confirmation token required" });
      }

      const jobId = nanoid();
      await logAuditEvent(ctx.user.id, "operation_executed", "operation", input.opId, {
        jobId,
        mock: true
      });

      return {
        jobId,
        initialState: "executing" as const,
      };
    }),

  status: protectedProcedure
    .input((val: unknown) => val as { jobId: string })
    .query(async () => {
      return {
        state: "progress_streaming" as const,
        progressPercent: 45,
        logs: ["[MOCK] Partitioning disk...", "[MOCK] Extracting image blocks...", "[MOCK] Verifying checksums..."],
      };
    }),

  bundle: protectedProcedure
    .input((val: unknown) => val as { jobId: string })
    .query(async () => {
      return {
        bundleId: nanoid(),
        downloadUrl: "#",
        hash: "sha256:mock_hash",
      };
    }),

  audit: protectedProcedure
    .input((val: unknown) => val as { jobId: string })
    .query(async ({ input }) => {
      return {
        record: {
          jobId: input.jobId,
          status: "completed",
          verified: true,
          safetyGatePassed: true
        },
        signedBy: "PHOENIX-AGENT-MOCK-VERIFIER",
      };
    }),

  cancel: protectedProcedure
    .input((val: unknown) => val as { jobId: string })
    .mutation(async ({ input, ctx }) => {
      await logAuditEvent(ctx.user.id, "operation_cancelled", "operation", input.jobId);
      return { success: true };
    }),
});

// ========== MONITORING ROUTER ==========

const monitoringRouter = router({
  getSystemHealth: publicProcedure.query(async () => {
    const metrics = await getHealthMetrics();
    return {
      metrics,
      overallStatus: metrics.every((m) => m.status === "healthy") ? "healthy" : "degraded",
      timestamp: new Date(),
    };
  }),

  getServiceStatus: publicProcedure
    .input((val: unknown) => val as { serviceName: string })
    .query(async ({ input }) => {
      const metrics = await getHealthMetrics();
      const service = metrics.find((m) => m.serviceName === input.serviceName);
      return service || null;
    }),

  getRelayNodeStatus: adminProcedure
    .input((val: unknown) => val as { nodeId: number })
    .query(async ({ input }) => {
      const node = await getRelayNodeById(input.nodeId);
      return node || null;
    }),
});

// ========== MAIN ROUTER ==========

export const appRouter = router({
  system: systemRouter,
  auth: router({
    me: publicProcedure.query((opts) => opts.ctx.user),
    logout: publicProcedure.mutation(({ ctx }) => {
      const cookieOptions = getSessionCookieOptions(ctx.req);
      ctx.res.clearCookie(COOKIE_NAME, { ...cookieOptions, maxAge: -1 });
      return {
        success: true,
      } as const;
    }),
  }),

  hardware: hardwareRouter,
  fleet: fleetRouter,
  recipe: recipeRouter,
  deployment: deploymentRouter,
  relay: relayRouter,
  bootcamp: bootcampRouter,
  admin: adminRouter,
  notification: notificationRouter,
  monitoring: monitoringRouter,
  operation: operationRouter,
});

export type AppRouter = typeof appRouter;
