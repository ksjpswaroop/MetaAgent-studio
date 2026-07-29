import { useEffect, useState } from "react";
import { copy } from "../copy/en";
import {
  apiClient,
  type ConnectorItem,
  type McpServerItem,
  type McpTransport,
} from "../lib/apiClient";
import { GlassPanel } from "../components/ui/GlassPanel";
import { VapButton } from "../components/ui/VapButton";
import { VapInput } from "../components/ui/VapInput";

type Tab = "apps" | "mcp";

type Props = {
  setStatus: (s: string) => void;
};

export function ConnectionsView({ setStatus }: Props) {
  const [tab, setTab] = useState<Tab>("apps");
  const [connectors, setConnectors] = useState<ConnectorItem[]>([]);
  const [mcp, setMcp] = useState<McpServerItem[]>([]);
  const [flash, setFlash] = useState<string>("");
  const [testingId, setTestingId] = useState<string | null>(null);

  const [appName, setAppName] = useState("");
  const [appUrl, setAppUrl] = useState("");

  const [mcpName, setMcpName] = useState("");
  const [mcpTransport, setMcpTransport] = useState<McpTransport>("stdio");
  const [mcpCommand, setMcpCommand] = useState("npx");
  const [mcpArgs, setMcpArgs] = useState("");
  const [mcpUrl, setMcpUrl] = useState("");

  async function refresh() {
    const [c, m] = await Promise.all([
      apiClient.listConnectors(),
      apiClient.listMcpServers(),
    ]);
    setConnectors(c);
    setMcp(m);
  }

  useEffect(() => {
    void refresh();
  }, []);

  function showFlash(msg: string) {
    setFlash(msg);
    window.setTimeout(() => setFlash(""), 2500);
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <h2 className="font-display text-2xl font-semibold">{copy.connections.title}</h2>
        <p className="mt-2 text-sm text-[var(--vap-muted)]">{copy.connections.support}</p>
      </div>

      <div className="flex flex-wrap gap-2">
        {(
          [
            ["apps", copy.connections.tabApps],
            ["mcp", copy.connections.tabMcp],
          ] as const
        ).map(([id, label]) => (
          <button
            key={id}
            type="button"
            onClick={() => setTab(id)}
            className={`rounded-full px-4 py-1.5 text-sm font-medium ${
              tab === id
                ? "bg-[var(--li-blue)] text-white"
                : "border border-[var(--li-border)] bg-white/80 text-[var(--vap-muted)]"
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {flash && (
        <p className="text-sm font-medium text-[var(--li-blue)]" role="status">
          {flash}
        </p>
      )}

      {tab === "apps" && (
        <div className="space-y-4">
          <p className="text-sm text-[var(--vap-muted)]">{copy.connections.appsBlurb}</p>
          <ul className="space-y-3">
            {connectors.map((c) => (
              <li key={c.id}>
                <GlassPanel className="flex flex-wrap items-center justify-between gap-3 p-4">
                  <div className="min-w-0">
                    <p className="font-display font-semibold">{c.name}</p>
                    <p className="text-sm text-[var(--vap-muted)]">{c.description}</p>
                    {c.baseUrl && (
                      <p className="mt-1 truncate font-mono text-xs text-[var(--li-blue-dark)]">
                        {c.baseUrl}
                      </p>
                    )}
                    <p
                      className={`mt-1 text-xs font-medium ${
                        c.connected
                          ? "text-[var(--li-success)]"
                          : "text-[var(--vap-muted)]"
                      }`}
                    >
                      {c.connected
                        ? copy.connections.connected
                        : copy.connections.notConnected}
                    </p>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <VapButton
                      variant="ghost"
                      disabled={testingId === c.id}
                      onClick={async () => {
                        setTestingId(c.id);
                        setStatus(copy.statusThinking);
                        const res = await apiClient.testConnector(c.id);
                        setStatus(copy.statusReady);
                        setTestingId(null);
                        showFlash(
                          res.ok ? copy.connections.testOk : copy.connections.testFail,
                        );
                      }}
                    >
                      {testingId === c.id
                        ? copy.connections.testing
                        : copy.connections.test}
                    </VapButton>
                    <VapButton
                      variant={c.connected ? "ghost" : "primary"}
                      onClick={async () => {
                        setStatus(copy.statusThinking);
                        const next = await apiClient.setConnectorConnected(
                          c.id,
                          !c.connected,
                        );
                        setConnectors((list) =>
                          list.map((x) => (x.id === next.id ? next : x)),
                        );
                        setStatus(copy.statusReady);
                      }}
                    >
                      {c.connected
                        ? copy.connections.disconnect
                        : copy.connections.connect}
                    </VapButton>
                  </div>
                </GlassPanel>
              </li>
            ))}
          </ul>

          <GlassPanel className="space-y-3 p-6">
            <h3 className="font-display text-lg font-semibold">
              {copy.connections.addApp}
            </h3>
            <label className="block text-sm text-[var(--vap-muted)]">
              {copy.connections.name}
            </label>
            <VapInput
              value={appName}
              onChange={(e) => setAppName(e.target.value)}
              placeholder="My API"
            />
            <label className="block text-sm text-[var(--vap-muted)]">
              {copy.connections.baseUrl}
            </label>
            <VapInput
              value={appUrl}
              onChange={(e) => setAppUrl(e.target.value)}
              placeholder="https://api.example.com"
            />
            <VapButton
              variant="cyan"
              disabled={!appName.trim() || !appUrl.trim()}
              onClick={async () => {
                setStatus(copy.statusThinking);
                const item = await apiClient.addCustomConnector({
                  name: appName.trim(),
                  baseUrl: appUrl.trim(),
                });
                setConnectors((list) => [item, ...list]);
                setAppName("");
                setAppUrl("");
                setStatus(copy.statusReady);
                showFlash(copy.connections.connected);
              }}
            >
              {copy.connections.save}
            </VapButton>
          </GlassPanel>
        </div>
      )}

      {tab === "mcp" && (
        <div className="space-y-4">
          <p className="text-sm text-[var(--vap-muted)]">{copy.connections.mcpBlurb}</p>
          {!mcp.length && (
            <GlassPanel className="p-6 text-sm text-[var(--vap-muted)]">
              {copy.connections.emptyMcp}
            </GlassPanel>
          )}
          <ul className="space-y-3">
            {mcp.map((s) => (
              <li key={s.id}>
                <GlassPanel className="space-y-3 p-4">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div className="min-w-0">
                      <p className="font-display font-semibold">{s.name}</p>
                      <p className="text-xs text-[var(--vap-muted)]">
                        {s.transport === "stdio"
                          ? copy.connections.transportStdio
                          : s.transport === "sse"
                            ? copy.connections.transportSse
                            : copy.connections.transportHttp}
                      </p>
                      <p className="mt-1 truncate font-mono text-xs text-[var(--li-blue-dark)]">
                        {s.transport === "stdio"
                          ? `${s.command ?? ""} ${s.args ?? ""}`.trim()
                          : s.url}
                      </p>
                      <p
                        className={`mt-1 text-xs font-medium ${
                          s.enabled
                            ? "text-[var(--li-success)]"
                            : "text-[var(--vap-muted)]"
                        }`}
                      >
                        {s.enabled
                          ? copy.connections.enabled
                          : copy.connections.disabled}
                      </p>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      <VapButton
                        variant="ghost"
                        disabled={testingId === s.id}
                        onClick={async () => {
                          setTestingId(s.id);
                          setStatus(copy.statusThinking);
                          const res = await apiClient.testMcpServer(s.id);
                          setStatus(copy.statusReady);
                          setTestingId(null);
                          showFlash(
                            res.ok
                              ? copy.connections.testOk
                              : copy.connections.testFail,
                          );
                        }}
                      >
                        {testingId === s.id
                          ? copy.connections.testing
                          : copy.connections.test}
                      </VapButton>
                      <VapButton
                        variant={s.enabled ? "ghost" : "primary"}
                        onClick={async () => {
                          setStatus(copy.statusThinking);
                          const next = await apiClient.setMcpEnabled(
                            s.id,
                            !s.enabled,
                          );
                          setMcp((list) =>
                            list.map((x) => (x.id === next.id ? next : x)),
                          );
                          setStatus(copy.statusReady);
                        }}
                      >
                        {s.enabled
                          ? copy.connections.turnOff
                          : copy.connections.turnOn}
                      </VapButton>
                      <VapButton
                        variant="danger"
                        onClick={async () => {
                          await apiClient.removeMcpServer(s.id);
                          setMcp((list) => list.filter((x) => x.id !== s.id));
                        }}
                      >
                        {copy.connections.remove}
                      </VapButton>
                    </div>
                  </div>
                </GlassPanel>
              </li>
            ))}
          </ul>

          <GlassPanel className="space-y-3 p-6">
            <h3 className="font-display text-lg font-semibold">
              {copy.connections.addMcp}
            </h3>
            <label className="block text-sm text-[var(--vap-muted)]">
              {copy.connections.name}
            </label>
            <VapInput
              value={mcpName}
              onChange={(e) => setMcpName(e.target.value)}
              placeholder="My tools"
            />
            <p className="text-sm text-[var(--vap-muted)]">
              {copy.connections.transport}
            </p>
            <div className="flex flex-wrap gap-2">
              {(
                [
                  ["stdio", copy.connections.transportStdio],
                  ["sse", copy.connections.transportSse],
                  ["http", copy.connections.transportHttp],
                ] as const
              ).map(([id, label]) => (
                <button
                  key={id}
                  type="button"
                  onClick={() => setMcpTransport(id)}
                  className={`rounded-full px-3 py-1 text-xs ${
                    mcpTransport === id
                      ? "bg-[var(--li-blue)] text-white"
                      : "border border-[var(--li-border)] text-[var(--vap-muted)]"
                  }`}
                >
                  {label}
                </button>
              ))}
            </div>
            {mcpTransport === "stdio" ? (
              <>
                <label className="block text-sm text-[var(--vap-muted)]">
                  {copy.connections.command}
                </label>
                <VapInput
                  value={mcpCommand}
                  onChange={(e) => setMcpCommand(e.target.value)}
                  placeholder="npx"
                />
                <label className="block text-sm text-[var(--vap-muted)]">
                  {copy.connections.args}
                </label>
                <VapInput
                  value={mcpArgs}
                  onChange={(e) => setMcpArgs(e.target.value)}
                  placeholder="-y @modelcontextprotocol/server-fetch"
                />
              </>
            ) : (
              <>
                <label className="block text-sm text-[var(--vap-muted)]">
                  {copy.connections.baseUrl}
                </label>
                <VapInput
                  value={mcpUrl}
                  onChange={(e) => setMcpUrl(e.target.value)}
                  placeholder="http://127.0.0.1:3100/mcp"
                />
              </>
            )}
            <VapButton
              variant="cyan"
              disabled={
                !mcpName.trim() ||
                (mcpTransport === "stdio"
                  ? !mcpCommand.trim()
                  : !mcpUrl.trim())
              }
              onClick={async () => {
                setStatus(copy.statusThinking);
                const item = await apiClient.addMcpServer({
                  name: mcpName.trim(),
                  transport: mcpTransport,
                  command:
                    mcpTransport === "stdio" ? mcpCommand.trim() : undefined,
                  args: mcpTransport === "stdio" ? mcpArgs.trim() : undefined,
                  url: mcpTransport !== "stdio" ? mcpUrl.trim() : undefined,
                });
                setMcp((list) => [item, ...list]);
                setMcpName("");
                setMcpArgs("");
                setMcpUrl("");
                setStatus(copy.statusReady);
                showFlash(copy.connections.enabled);
              }}
            >
              {copy.connections.save}
            </VapButton>
          </GlassPanel>
        </div>
      )}
    </div>
  );
}
