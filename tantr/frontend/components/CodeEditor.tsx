import { useCallback } from 'react';
import dynamic from 'next/dynamic';

const MonacoEditor = dynamic(() => import('@monaco-editor/react'), { ssr: false });

type Props = {
  value: string;
  onChange: (value: string) => void;
  path?: string;
  height?: string | number;
};

export default function CodeEditor({ value, onChange, path = 'main.py', height = 420 }: Props) {
  const handleChange = useCallback(
    (val: string | undefined) => {
      onChange(val ?? '');
    },
    [onChange]
  );

  return (
    <div className="overflow-hidden rounded-xl border border-violet-500/20 shadow-[0_0_30px_rgba(139,92,246,0.08)]">
      <div className="flex items-center gap-2 border-b border-violet-500/15 bg-[#0a0520]/90 px-4 py-2.5">
        <span className="h-2.5 w-2.5 rounded-full bg-rose-500/70 shadow-[0_0_6px_rgba(244,63,94,0.5)]" />
        <span className="h-2.5 w-2.5 rounded-full bg-amber-500/70 shadow-[0_0_6px_rgba(245,158,11,0.5)]" />
        <span className="h-2.5 w-2.5 rounded-full bg-cyan-500/70 shadow-[0_0_6px_rgba(34,211,238,0.5)]" />
        <span className="ml-2 font-mono text-xs text-cyan-400/60">◈ {path}</span>
      </div>
      <MonacoEditor
        height={height}
        defaultLanguage="python"
        value={value}
        onChange={handleChange}
        theme="vs-dark"
        options={{
          minimap: { enabled: false },
          fontSize: 14,
          fontFamily: 'var(--font-mono), ui-monospace, monospace',
          padding: { top: 16 },
          scrollBeyondLastLine: false,
          lineNumbers: 'on',
          roundedSelection: true,
          cursorBlinking: 'smooth',
          smoothScrolling: true,
        }}
      />
    </div>
  );
}
