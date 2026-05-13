import { startPhoenixAgentServer } from "./server";

export { createPhoenixAgentRequestHandler, routeRequest, startPhoenixAgentServer } from "./server";
export { BLOCKED_OPERATION_IDS, REQUIRED_FUTURE_GATES } from "./policy/blocked-operations";

if (require.main === module) {
  const port = Number.parseInt(process.env.PHOENIX_AGENT_PORT ?? process.env.PORT ?? "7788", 10);

  startPhoenixAgentServer({ port, logger: console }).catch((error) => {
    console.error("Failed to start Phoenix Agent mock service", error);
    process.exitCode = 1;
  });
}
