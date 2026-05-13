import { describe, it, expect, beforeEach, vi } from "vitest";
import { appRouter } from "./routers";
import type { TrpcContext } from "./_core/context";

// ========== TEST CONTEXT BUILDERS ==========

function createOwnerContext(): TrpcContext {
  return {
    user: {
      id: 1,
      openId: "owner-001",
      email: "owner@phoenix-core.io",
      name: "Owner User",
      loginMethod: "manus",
      role: "owner",
      createdAt: new Date(),
      updatedAt: new Date(),
      lastSignedIn: new Date(),
    },
    req: {
      protocol: "https",
      headers: {},
    } as TrpcContext["req"],
    res: {} as TrpcContext["res"],
  };
}

function createAdminContext(): TrpcContext {
  return {
    user: {
      id: 2,
      openId: "admin-001",
      email: "admin@phoenix-core.io",
      name: "Admin User",
      loginMethod: "manus",
      role: "admin",
      createdAt: new Date(),
      updatedAt: new Date(),
      lastSignedIn: new Date(),
    },
    req: {
      protocol: "https",
      headers: {},
    } as TrpcContext["req"],
    res: {} as TrpcContext["res"],
  };
}

function createUserContext(): TrpcContext {
  return {
    user: {
      id: 3,
      openId: "user-001",
      email: "user@phoenix-core.io",
      name: "Regular User",
      loginMethod: "manus",
      role: "user",
      createdAt: new Date(),
      updatedAt: new Date(),
      lastSignedIn: new Date(),
    },
    req: {
      protocol: "https",
      headers: {},
    } as TrpcContext["req"],
    res: {} as TrpcContext["res"],
  };
}

// ========== HARDWARE ROUTER TESTS ==========

describe("Hardware Router", () => {
  it("should detect connected devices with filters", async () => {
    const ctx = createUserContext();
    const caller = appRouter.createCaller(ctx);

    const result = await caller.hardware.detectConnected({
      filters: { osType: "windows" },
    });

    expect(result).toBeDefined();
    expect(result.devices).toBeDefined();
    expect(Array.isArray(result.devices)).toBe(true);
    expect(result.count).toBe(result.devices.length);
    expect(result.timestamp).toBeInstanceOf(Date);
  });

  it("should generate recipe for device", async () => {
    const ctx = createUserContext();
    const caller = appRouter.createCaller(ctx);

    const result = await caller.hardware.generateRecipe({
      deviceId: 1,
    });

    expect(result).toBeDefined();
    expect(result.id).toBeDefined();
    expect(result.name).toContain("Auto-Recipe");
  });
});

// ========== FLEET ROUTER TESTS ==========

describe("Fleet Router", () => {
  it("should list devices with filters", async () => {
    const ctx = createAdminContext();
    const caller = appRouter.createCaller(ctx);

    const result = await caller.fleet.listDevices({
      filters: { status: "online" },
    });

    expect(result).toBeDefined();
    expect(Array.isArray(result.devices)).toBe(true);
    expect(result.count).toBeGreaterThanOrEqual(0);
  });

  it("should get device details or return null", async () => {
    const ctx = createAdminContext();
    const caller = appRouter.createCaller(ctx);

    const result = await caller.fleet.getDeviceDetails({ deviceId: 1 });

    if (result) {
      expect(result.id).toBe(1);
      expect(result.name).toBeDefined();
      expect(result.status).toMatch(/online|offline|deploying|error/);
    }
  });
});

// ========== RECIPE ROUTER TESTS ==========

describe("Recipe Router", () => {
  it("should create recipe", async () => {
    const ctx = createUserContext();
    const caller = appRouter.createCaller(ctx);

    const result = await caller.recipe.create({
      name: "Test Recipe",
      osImage: "ubuntu-22.04",
      drivers: ["driver1"],
      tools: ["tool1"],
      estimatedSize: "4.5GB",
    });

    expect(result).toBeDefined();
    expect(result.id).toBeDefined();
    expect(result.name).toBe("Test Recipe");
    expect(result.osImage).toBe("ubuntu-22.04");
  });

  it("should list user recipes", async () => {
    const ctx = createUserContext();
    const caller = appRouter.createCaller(ctx);

    const result = await caller.recipe.list();

    expect(Array.isArray(result)).toBe(true);
  });

  it("should estimate recipe size", async () => {
    const ctx = createUserContext();
    const caller = appRouter.createCaller(ctx);

    const result = await caller.recipe.estimateSize({
      osImage: "windows-11",
      drivers: ["driver1", "driver2"],
      tools: ["tool1"],
    });

    expect(result).toBeDefined();
    expect(result.estimatedSize).toBeDefined();
    expect(typeof result.estimatedSize).toBe("string");
  });
});

// ========== DEPLOYMENT ROUTER TESTS ==========

describe("Deployment Router", () => {
  it("should list deployments", async () => {
    const ctx = createAdminContext();
    const caller = appRouter.createCaller(ctx);

    const result = await caller.deployment.list();

    expect(Array.isArray(result)).toBe(true);
  });

  it("should get deployment progress or return null", async () => {
    const ctx = createAdminContext();
    const caller = appRouter.createCaller(ctx);

    const result = await caller.deployment.getProgress({ jobId: "job-001" });

    if (result) {
      expect(result.jobId).toBe("job-001");
      expect(result.status).toMatch(/pending|running|completed|failed/);
    }
  });
});

// ========== RELAY ROUTER TESTS ==========

describe("Relay Router", () => {
  it("should list relay nodes (admin only)", async () => {
    const ctx = createAdminContext();
    const caller = appRouter.createCaller(ctx);

    const result = await caller.relay.listNodes();

    expect(Array.isArray(result)).toBe(true);
  });

  it("should deny relay access to non-admin users", async () => {
    const ctx = createUserContext();
    const caller = appRouter.createCaller(ctx);

    try {
      await caller.relay.listNodes();
      expect.fail("Should have thrown FORBIDDEN error");
    } catch (error: any) {
      expect(error.code).toBe("FORBIDDEN");
    }
  });

  it("should configure relay node (owner only)", async () => {
    const ctx = createOwnerContext();
    const caller = appRouter.createCaller(ctx);

    const result = await caller.relay.configureNode({
      nodeId: 1,
      config: { name: "Test Node", location: "us-east-1" },
    });

    expect(result.success).toBe(true);
  });

  it("should sync image cache", async () => {
    const ctx = createAdminContext();
    const caller = appRouter.createCaller(ctx);

    const result = await caller.relay.syncImageCache({ nodeId: 1 });

    expect(result.success).toBe(true);
  });
});

// ========== BOOT CAMP ROUTER TESTS ==========

describe("Boot Camp Router", () => {
  it("should list drivers", async () => {
    const ctx = createUserContext();
    const caller = appRouter.createCaller(ctx);

    const result = await caller.bootcamp.listDrivers({
      category: "graphics",
    });

    expect(Array.isArray(result)).toBe(true);
  });

  it("should get compatible drivers for Mac model", async () => {
    const ctx = createUserContext();
    const caller = appRouter.createCaller(ctx);

    const result = await caller.bootcamp.getCompatibleDrivers({
      macModel: "MacBook Pro",
    });

    expect(Array.isArray(result)).toBe(true);
  });
});

// ========== NOTIFICATION ROUTER TESTS ==========

describe("Notification Router", () => {
  it("should list notifications", async () => {
    const ctx = createUserContext();
    const caller = appRouter.createCaller(ctx);

    const result = await caller.notification.list({ unreadOnly: false });

    expect(Array.isArray(result)).toBe(true);
  });

  it("should mark notification as read", async () => {
    const ctx = createUserContext();
    const caller = appRouter.createCaller(ctx);

    const result = await caller.notification.markAsRead({ notificationId: 1 });

    expect(result.success).toBe(true);
  });

  it("should get notification preferences", async () => {
    const ctx = createUserContext();
    const caller = appRouter.createCaller(ctx);

    const result = await caller.notification.getPreferences();

    expect(result).toBeDefined();
    expect(result.deploymentAlerts).toBeDefined();
  });
});

// ========== ADMIN ROUTER TESTS ==========

describe("Admin Router", () => {
  it("should list users (admin only)", async () => {
    const ctx = createAdminContext();
    const caller = appRouter.createCaller(ctx);

    const result = await caller.admin.listUsers();

    expect(Array.isArray(result)).toBe(true);
  });

  it("should deny admin access to non-admin users", async () => {
    const ctx = createUserContext();
    const caller = appRouter.createCaller(ctx);

    try {
      await caller.admin.listUsers();
      expect.fail("Should have thrown FORBIDDEN error");
    } catch (error: any) {
      expect(error.code).toBe("FORBIDDEN");
    }
  });

  it("should update user role (owner only)", async () => {
    const ctx = createOwnerContext();
    const caller = appRouter.createCaller(ctx);

    const result = await caller.admin.updateUserRole({
      userId: 3,
      role: "admin",
    });

    expect(result.success).toBe(true);
  });

  it("should get audit logs", async () => {
    const ctx = createAdminContext();
    const caller = appRouter.createCaller(ctx);

    const result = await caller.admin.getAuditLogs({
      filters: { action: "deployment_started" },
    });

    expect(Array.isArray(result)).toBe(true);
  });
});

// ========== MONITORING ROUTER TESTS ==========

describe("Monitoring Router", () => {
  it("should get system health", async () => {
    const ctx = createAdminContext();
    const caller = appRouter.createCaller(ctx);

    const result = await caller.monitoring.getSystemHealth();

    expect(result).toBeDefined();
    if (result.status) {
      expect(result.status).toMatch(/healthy|degraded|critical/);
    }
    expect(result.services).toBeDefined();
    expect(Array.isArray(result.services)).toBe(true);
  });

  it("should get relay node status or return null", async () => {
    const ctx = createAdminContext();
    const caller = appRouter.createCaller(ctx);

    const result = await caller.monitoring.getRelayNodeStatus({ nodeId: 1 });

    if (result) {
      expect(result.status).toMatch(/healthy|degraded|offline/);
    }
  });
});

// ========== ROLE-BASED ACCESS CONTROL TESTS ==========

describe("Role-Based Access Control", () => {
  it("should enforce owner-only procedures", async () => {
    const userCtx = createUserContext();
    const adminCtx = createAdminContext();

    const userCaller = appRouter.createCaller(userCtx);
    const adminCaller = appRouter.createCaller(adminCtx);

    // User should not access owner procedures
    try {
      await userCaller.relay.configureNode({
        nodeId: 1,
        config: {},
      });
      expect.fail("User should not access owner procedures");
    } catch (error: any) {
      expect(error.code).toBe("FORBIDDEN");
    }

    // Admin should not access owner procedures
    try {
      await adminCaller.relay.configureNode({
        nodeId: 1,
        config: {},
      });
      expect.fail("Admin should not access owner procedures");
    } catch (error: any) {
      expect(error.code).toBe("FORBIDDEN");
    }
  });

  it("should allow admin procedures for admin and owner", async () => {
    const adminCtx = createAdminContext();
    const ownerCtx = createOwnerContext();

    const adminCaller = appRouter.createCaller(adminCtx);
    const ownerCaller = appRouter.createCaller(ownerCtx);

    // Both should access admin procedures
    const adminResult = await adminCaller.relay.listNodes();
    expect(Array.isArray(adminResult)).toBe(true);

    const ownerResult = await ownerCaller.relay.listNodes();
    expect(Array.isArray(ownerResult)).toBe(true);
  });
});
