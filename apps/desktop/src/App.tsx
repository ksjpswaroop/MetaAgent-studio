import { useState, useEffect } from "react";
import { invoke } from "@tauri-apps/api/core";
import { Cpu, Layers, Sparkles, Terminal, CheckCircle2, Bot } from "lucide-react";

export default function App() {
  const [greetMsg, setGreetMsg] = useState("");
  const [name, setName] = useState("");
  const [status, setStatus] = useState("Connected to Tauri v2 Rust backend");

  async function greet() {
    try {
      const response = await invoke<string>("greet", { name: name || "System Architect" });
      setGreetMsg(response);
      setStatus("IPC Command Execution Successful");
    } catch (err) {
      setGreetMsg(`Error invoking Tauri command: ${err}`);
      setStatus("IPC Command Failed");
    }
  }

  useEffect(() => {
    greet();
  }, []);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      {/* Top Header */}
      <header className="border-b border-slate-800 bg-slate-900/50 px-6 py-4 flex items-center justify-between backdrop-blur">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-xl bg-indigo-600/20 text-indigo-400 border border-indigo-500/30">
            <Bot className="w-6 h-6" />
          </div>
          <div>
            <h1 className="font-bold text-lg tracking-tight bg-gradient-to-r from-white via-slate-200 to-indigo-300 bg-clip-text text-transparent">
              MetaAgent Studio
            </h1>
            <p className="text-xs text-slate-400">Interactive Multi-Agent System Designer & Scaffolder</p>
          </div>
        </div>

        <div className="flex items-center gap-2 text-xs text-emerald-400 bg-emerald-950/40 border border-emerald-500/30 px-3 py-1.5 rounded-full">
          <CheckCircle2 className="w-3.5 h-3.5" />
          <span>{status}</span>
        </div>
      </header>

      {/* Main Workspace */}
      <main className="flex-1 p-8 max-w-5xl mx-auto w-full grid gap-8 grid-cols-1 md:grid-cols-3">
        {/* Left Column: Greeting & Interactive Bridge */}
        <div className="md:col-span-2 space-y-6">
          <section className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 space-y-4">
            <div className="flex items-center gap-2 text-indigo-400 font-semibold text-sm">
              <Sparkles className="w-4 h-4" />
              <h2>Rust IPC Bridge Test</h2>
            </div>
            <p className="text-sm text-slate-300 leading-relaxed">
              Test execution flow between the React frontend and the native Tauri v2 Rust core.
            </p>

            <form
              onSubmit={(e) => {
                e.preventDefault();
                greet();
              }}
              className="flex gap-3"
            >
              <input
                id="greet-input"
                className="flex-1 bg-slate-950 border border-slate-800 rounded-xl px-4 py-2 text-sm focus:outline-none focus:border-indigo-500 transition"
                onChange={(e) => setName(e.currentTarget.value)}
                placeholder="Enter architect or project name..."
                value={name}
              />
              <button
                type="submit"
                className="bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-sm px-5 py-2 rounded-xl transition shadow-lg shadow-indigo-600/20"
              >
                Invoke Command
              </button>
            </form>

            {greetMsg && (
              <div className="bg-slate-950/80 border border-indigo-500/30 p-4 rounded-xl text-sm text-indigo-200 flex items-start gap-3">
                <Terminal className="w-5 h-5 text-indigo-400 mt-0.5 shrink-0" />
                <div>
                  <div className="text-xs text-slate-500 font-mono mb-1">OUTPUT FROM RUST BACKEND</div>
                  <p className="font-mono text-indigo-300">{greetMsg}</p>
                </div>
              </div>
            )}
          </section>

          {/* 3-Tier Matrix Card */}
          <section className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 space-y-4">
            <h3 className="font-semibold text-slate-200 text-sm flex items-center gap-2">
              <Layers className="w-4 h-4 text-indigo-400" />
              <span>3-Tier Intelligence Allocation Matrix</span>
            </h3>
            <div className="grid grid-cols-3 gap-3 text-xs">
              <div className="bg-slate-950 border border-slate-800 p-3 rounded-xl">
                <div className="font-bold text-slate-300 mb-1">Tier 1: Code</div>
                <div className="text-slate-400">Strict rules, auth, schema coercion, math & REST writes.</div>
              </div>
              <div className="bg-slate-950 border border-slate-800 p-3 rounded-xl">
                <div className="font-bold text-slate-300 mb-1">Tier 2: ML/Stats</div>
                <div className="text-slate-400">Vector similarity, risk scoring & ranking.</div>
              </div>
              <div className="bg-slate-950 border border-slate-800 p-3 rounded-xl">
                <div className="font-bold text-slate-300 mb-1">Tier 3: LLM</div>
                <div className="text-slate-400">Unstructured reasoning, tool planning & synthesis.</div>
              </div>
            </div>
          </section>
        </div>

        {/* Right Column: Status & Stack Card */}
        <aside className="space-y-6">
          <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 space-y-4">
            <h3 className="font-semibold text-slate-200 text-sm flex items-center gap-2">
              <Cpu className="w-4 h-4 text-indigo-400" />
              <span>System Stack</span>
            </h3>

            <div className="space-y-3 text-xs">
              <div className="flex justify-between items-center py-1.5 border-b border-slate-800/60">
                <span className="text-slate-400">Framework</span>
                <span className="font-mono text-indigo-300">Tauri v2.1</span>
              </div>
              <div className="flex justify-between items-center py-1.5 border-b border-slate-800/60">
                <span className="text-slate-400">Frontend Core</span>
                <span className="font-mono text-indigo-300">React 18 + Vite 6</span>
              </div>
              <div className="flex justify-between items-center py-1.5 border-b border-slate-800/60">
                <span className="text-slate-400">Styles</span>
                <span className="font-mono text-indigo-300">Tailwind CSS</span>
              </div>
              <div className="flex justify-between items-center py-1.5">
                <span className="text-slate-400">Rust Core</span>
                <span className="font-mono text-indigo-300">Edition 2021</span>
              </div>
            </div>
          </div>
        </aside>
      </main>

      <footer className="border-t border-slate-800/60 py-3 px-6 text-center text-xs text-slate-500">
        MetaAgent Studio Starter • Tauri v2 Desktop Engine
      </footer>
    </div>
  );
}
