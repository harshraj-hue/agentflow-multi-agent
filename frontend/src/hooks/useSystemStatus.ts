import { useCallback, useEffect, useState } from "react";
import { getHealth, getReadiness } from "../services/api";
import type { HealthResponse, ReadinessResponse } from "../types/health";

export type SystemStatusState =
  | { phase: "loading" }
  | { phase: "error"; message: string }
  | { phase: "ready"; health: HealthResponse; readiness: ReadinessResponse };

export function useSystemStatus() {
  const [state, setState] = useState<SystemStatusState>({ phase: "loading" });

  const refresh = useCallback(async () => {
    setState({ phase: "loading" });
    try {
      const [health, readiness] = await Promise.all([getHealth(), getReadiness()]);
      setState({ phase: "ready", health, readiness });
    } catch (error) {
      const message = error instanceof Error ? error.message : "Unexpected error.";
      setState({ phase: "error", message });
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  return { state, refresh };
}
