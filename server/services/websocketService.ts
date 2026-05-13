import { Server as SocketIOServer } from "socket.io";
import { Server as HTTPServer } from "http";

interface WebSocketEvent {
  type: string;
  timestamp: Date;
  data: any;
}

interface FleetUpdate {
  deviceId: number;
  status: "online" | "offline" | "deploying" | "error";
  lastHeartbeat: Date;
  healthMetrics?: {
    cpu: number;
    memory: number;
    disk: number;
  };
}

interface DeploymentUpdate {
  jobId: string;
  deviceId: number;
  progress: number;
  status: "pending" | "running" | "completed" | "failed";
  currentStep?: string;
  logs?: string[];
}

interface RelayNodeUpdate {
  nodeId: number;
  status: "healthy" | "degraded" | "offline";
  syncStatus: "synced" | "syncing" | "out_of_sync";
  cacheHealth: number;
  lastHeartbeat: Date;
}

export class WebSocketService {
  private io: SocketIOServer;
  private deviceSubscriptions: Map<number, Set<string>> = new Map();
  private deploymentSubscriptions: Map<string, Set<string>> = new Map();
  private relaySubscriptions: Map<number, Set<string>> = new Map();

  constructor(httpServer: HTTPServer) {
    this.io = new SocketIOServer(httpServer, {
      cors: {
        origin: "*",
        methods: ["GET", "POST"],
      },
      transports: ["websocket", "polling"],
    });

    this.setupConnectionHandlers();
  }

  private setupConnectionHandlers() {
    this.io.on("connection", (socket: any) => {
      console.log(`[WebSocket] Client connected: ${socket.id}`);

      socket.on("subscribe:device", (deviceId: number) => {
        if (!this.deviceSubscriptions.has(deviceId)) {
          this.deviceSubscriptions.set(deviceId, new Set());
        }
        this.deviceSubscriptions.get(deviceId)!.add(socket.id);
        socket.join(`device:${deviceId}`);
      });

      socket.on("subscribe:deployment", (jobId: string) => {
        if (!this.deploymentSubscriptions.has(jobId)) {
          this.deploymentSubscriptions.set(jobId, new Set());
        }
        this.deploymentSubscriptions.get(jobId)!.add(socket.id);
        socket.join(`deployment:${jobId}`);
      });

      socket.on("subscribe:relay", (nodeId: number) => {
        if (!this.relaySubscriptions.has(nodeId)) {
          this.relaySubscriptions.set(nodeId, new Set());
        }
        this.relaySubscriptions.get(nodeId)!.add(socket.id);
        socket.join(`relay:${nodeId}`);
      });

      socket.on("unsubscribe:device", (deviceId: number) => {
        this.deviceSubscriptions.get(deviceId)?.delete(socket.id);
        socket.leave(`device:${deviceId}`);
      });

      socket.on("unsubscribe:deployment", (jobId: string) => {
        this.deploymentSubscriptions.get(jobId)?.delete(socket.id);
        socket.leave(`deployment:${jobId}`);
      });

      socket.on("unsubscribe:relay", (nodeId: number) => {
        this.relaySubscriptions.get(nodeId)?.delete(socket.id);
        socket.leave(`relay:${nodeId}`);
      });

      socket.on("disconnect", () => {
        console.log(`[WebSocket] Client disconnected: ${socket.id}`);
        this.deviceSubscriptions.forEach((clients) => clients.delete(socket.id));
        this.deploymentSubscriptions.forEach((clients) => clients.delete(socket.id));
        this.relaySubscriptions.forEach((clients) => clients.delete(socket.id));
      });
    });
  }

  public broadcastDeviceUpdate(update: FleetUpdate) {
    const event: WebSocketEvent = {
      type: "device:update",
      timestamp: new Date(),
      data: update,
    };
    this.io.to(`device:${update.deviceId}`).emit("device:update", event);
  }

  public broadcastDeploymentProgress(update: DeploymentUpdate) {
    const event: WebSocketEvent = {
      type: "deployment:progress",
      timestamp: new Date(),
      data: update,
    };
    this.io.to(`deployment:${update.jobId}`).emit("deployment:progress", event);
  }

  public broadcastRelayNodeUpdate(update: RelayNodeUpdate) {
    const event: WebSocketEvent = {
      type: "relay:update",
      timestamp: new Date(),
      data: update,
    };
    this.io.to(`relay:${update.nodeId}`).emit("relay:update", event);
  }

  public broadcastFleetUpdate(devices: FleetUpdate[]) {
    const event: WebSocketEvent = {
      type: "fleet:update",
      timestamp: new Date(),
      data: { devices, count: devices.length },
    };
    this.io.emit("fleet:update", event);
  }

  public broadcastDeploymentLog(jobId: string, logLine: string) {
    const event: WebSocketEvent = {
      type: "deployment:log",
      timestamp: new Date(),
      data: { jobId, logLine },
    };
    this.io.to(`deployment:${jobId}`).emit("deployment:log", event);
  }

  public broadcastNotification(userId: number, notification: any) {
    const event: WebSocketEvent = {
      type: "notification:new",
      timestamp: new Date(),
      data: notification,
    };
    this.io.to(`user:${userId}`).emit("notification:new", event);
  }

  public getConnectedClients(): number {
    return this.io.engine.clientsCount;
  }

  public getDeviceSubscriberCount(deviceId: number): number {
    return this.deviceSubscriptions.get(deviceId)?.size || 0;
  }

  public getDeploymentSubscriberCount(jobId: string): number {
    return this.deploymentSubscriptions.get(jobId)?.size || 0;
  }

  public shutdown() {
    this.io.close();
  }
}

let wsService: WebSocketService | null = null;

export function initializeWebSocket(httpServer: HTTPServer): WebSocketService {
  if (!wsService) {
    wsService = new WebSocketService(httpServer);
  }
  return wsService;
}

export function getWebSocketService(): WebSocketService {
  if (!wsService) {
    throw new Error("WebSocket service not initialized");
  }
  return wsService;
}
