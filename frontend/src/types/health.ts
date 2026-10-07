export interface HealthResponse {
  status: "ok";
  app: string;
  version: string;
  environment: string;
}

export interface ReadinessResponse {
  status: "ready" | "not_ready";
  checks: Record<string, "ok" | "unavailable">;
}
