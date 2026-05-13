/**
 * Phoenix Agent SDK (Scaffold)
 * Unified typed interface for the Phoenix Core Platform.
 */

import type { AppRouter } from "../server/routers";
import type { 
  Device, 
  Recipe, 
  Deployment, 
  RelayNode, 
  Notification,
  OperationMetadata,
  OperationState
} from "./types";

export interface PhoenixSDK {
  /**
   * Phoenix Agent Operation Lifecycle (PR8 Hardened)
   * All destructive operations MUST follow this flow.
   */
  operations: {
    /**
     * Stage 1: Preview the proposed changes.
     * TODO: Connect to Rust-based dry-run logic.
     */
    preview: (opId: string, params: any) => Promise<{
      metadata: OperationMetadata;
      proposedChanges: string[];
      risks: string[];
    }>;

    /**
     * Stage 3: Evaluate safety against policy.
     */
    evaluate: (opId: string, params: any) => Promise<{
      allowed: boolean;
      requirements: string[];
      reason?: string;
    }>;

    /**
     * Stage 4: Explicit target confirmation.
     * Returns a confirmation token valid for a short window.
     */
    confirm: (opId: string, manifestHash: string) => Promise<{
      confirmationToken: string;
      expiresAt: string;
    }>;

    /**
     * Stage 5: Execute the operation.
     * REQUIRES: confirmationToken (and PHX-TOKEN if destructive).
     */
    execute: (opId: string, params: any, tokens: { confirmation: string; phx?: string }) => Promise<{
      jobId: string;
      initialState: OperationState;
    }>;

    /**
     * Stage 6: Monitor status and logs.
     */
    status: (jobId: string) => Promise<{
      state: OperationState;
      progressPercent: number;
      logs: string[];
    }>;

    /**
     * Terminate an active operation.
     */
    cancel: (jobId: string) => Promise<{
      success: boolean;
    }>;

    /**
     * Stage 7: Retrieve signed report bundle.
     */
    bundle: (jobId: string) => Promise<{
      bundleId: string;
      downloadUrl: string;
      hash: string;
    }>;

    /**
     * Stage 8: Retrieve audit record.
     */
    audit: (jobId: string) => Promise<{
      record: any;
      signedBy: string;
    }>;
  };

  hardware: {
    detect: () => Promise<{ devices: Device[]; count: number }>;
    generateRecipe: (deviceId: number) => Promise<Recipe>;
  };
  fleet: {
    list: (filters?: any) => Promise<Device[]>;
    getDetails: (deviceId: number) => Promise<{ device: Device; deploymentHistory: Deployment[] }>;
  };
  recipes: {
    list: () => Promise<Recipe[]>;
    create: (data: Partial<Recipe>) => Promise<Recipe>;
    estimate: (data: any) => Promise<{ totalSizeGB: string }>;
  };
  deployments: {
    list: (status?: string) => Promise<Deployment[]>;
    create: (recipeId: number, deviceId?: number) => Promise<Deployment>;
    status: (deploymentId: number) => Promise<{ deployment: Deployment; logs: any[] }>;
  };
  relay: {
    list: () => Promise<RelayNode[]>;
    sync: (nodeId: number) => Promise<{ success: boolean }>;
  };
  notifications: {
    list: (unreadOnly?: boolean) => Promise<Notification[]>;
    markRead: (id: number) => Promise<{ success: boolean }>;
  };
}

/**
 * Placeholder for the actual tRPC-backed implementation.
 * This can be used to generate mocks or for typed contract mapping.
 */
export const createPhoenixAgentClient = (trpcClient: any): PhoenixSDK => {
  return {
    operations: {
      preview: (opId, params) => trpcClient.operation.preview.mutate({ opId, params }),
      evaluate: (opId, params) => trpcClient.operation.evaluate.query({ opId, params }),
      confirm: (opId, manifestHash) => trpcClient.operation.confirm.mutate({ opId, manifestHash }),
      execute: (opId, params, tokens) => trpcClient.operation.execute.mutate({ opId, params, tokens }),
      status: (jobId) => trpcClient.operation.status.query({ jobId }),
      bundle: (jobId) => trpcClient.operation.bundle.query({ jobId }),
      audit: (jobId) => trpcClient.operation.audit.query({ jobId }),
      cancel: (jobId) => trpcClient.operation.cancel.mutate({ jobId }),
    },
    hardware: {
      detect: () => trpcClient.hardware.detectConnected.query({}),
      generateRecipe: (deviceId) => trpcClient.hardware.generateRecipe.mutate({ deviceId }),
    },
    fleet: {
      list: (filters) => trpcClient.fleet.listDevices.query(filters),
      getDetails: (deviceId) => trpcClient.fleet.getDeviceDetails.query({ deviceId }),
    },
    recipes: {
      list: () => trpcClient.recipe.list.query(),
      create: (data) => trpcClient.recipe.create.mutate(data),
      estimate: (data) => trpcClient.recipe.estimateSize.query(data),
    },
    deployments: {
      list: (status) => trpcClient.deployment.list.query({ status }),
      create: (recipeId, deviceId) => trpcClient.deployment.create.mutate({ recipeId, deviceId }),
      status: (deploymentId) => trpcClient.deployment.getProgress.query({ deploymentId }),
    },
    relay: {
      list: () => trpcClient.relay.listNodes.query(),
      sync: (nodeId) => trpcClient.relay.syncImageCache.mutate({ nodeId }),
    },
    notifications: {
      list: (unreadOnly) => trpcClient.notification.list.query({ unreadOnly }),
      markRead: (notificationId) => trpcClient.notification.markAsRead.mutate({ notificationId }),
    },
  };
};
