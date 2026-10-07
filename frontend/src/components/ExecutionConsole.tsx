import React, { useEffect, useRef, useState } from "react";
import type { ExecutionEvent } from "../types/workflow";

interface ExecutionConsoleProps {
  events: ExecutionEvent[];
  onClear?: () => void;
}

export const ExecutionConsole: React.FC<ExecutionConsoleProps> = ({
  events,
  onClear,
}) => {
  const [autoScroll, setAutoScroll] = useState<boolean>(true);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (autoScroll && bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [events, autoScroll]);

  const getEventBadge = (type: string) => {
    switch (type) {
      case "step_thought":
        return <span className="event-badge badge-thought">THOUGHT</span>;
      case "step_tool_call":
        return <span className="event-badge badge-tool">TOOL CALL</span>;
      case "step_observation":
        return <span className="event-badge badge-obs">OBSERVATION</span>;
      case "step_result":
      case "task_completed":
        return <span className="event-badge badge-res">RESULT</span>;
      case "approval_requested":
        return <span className="event-badge badge-appr">APPROVAL GATE</span>;
      case "workflow_completed":
        return <span className="event-badge badge-success">COMPLETED</span>;
      default:
        return <span className="event-badge badge-info">{type.toUpperCase()}</span>;
    }
  };

  const formatTime = (isoString: string) => {
    try {
      const d = new Date(isoString);
      return d.toLocaleTimeString([], { hour12: false, hour: "2-digit", minute: "2-digit", second: "2-digit" });
    } catch {
      return "";
    }
  };

  return (
    <div className="console-wrapper">
      <div className="console-header">
        <div className="console-title-group">
          <span className="console-dot-group">
            <span className="dot-red" />
            <span className="dot-yellow" />
            <span className="dot-green" />
          </span>
          <span className="console-title">Live Execution Telemetry Stream (SSE)</span>
          <span className="event-counter">{events.length} events logged</span>
        </div>

        <div className="console-controls">
          <label className="autoscroll-toggle">
            <input
              type="checkbox"
              checked={autoScroll}
              onChange={(e) => setAutoScroll(e.target.checked)}
            />
            <span>Auto-scroll</span>
          </label>
          {onClear && (
            <button type="button" className="console-btn" onClick={onClear}>
              Clear
            </button>
          )}
        </div>
      </div>

      <div className="console-body">
        {events.length === 0 ? (
          <div className="console-empty">
            <span className="terminal-cursor">_</span> Awaiting execution events...
          </div>
        ) : (
          events.map((evt) => (
            <div key={evt.id} className="console-row">
              <span className="log-time">{formatTime(evt.created_at)}</span>
              <span className="log-agent">[{evt.agent_name}]</span>
              {getEventBadge(evt.event_type)}
              <span className="log-msg">{evt.message}</span>

              {evt.payload && Object.keys(evt.payload).length > 0 && (
                <pre className="log-payload">
                  {JSON.stringify(evt.payload, null, 2)}
                </pre>
              )}
            </div>
          ))
        )}
        <div ref={bottomRef} />
      </div>
    </div>
  );
};
