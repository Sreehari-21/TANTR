import { useCallback } from 'react';
import dynamic from 'next/dynamic';

const MonacoEditor = dynamic(() => import('@monaco-editor/react'), { ssr: false });

type Props = {
  value: string;
  onChange: (value: string) => void;
  path?: string;
  height?: string | number;
};

export default function CodeEditor({ value, onChange, path = 'main.py', height = 400 }: Props) {
  const handleChange = useCallback(
    (val: string | undefined) => {
      onChange(val ?? '');
    },
    [onChange]
  );

  return (
    <div className="overflow-hidden rounded-lg border border-slate-700">
      <div className="bg-slate-800 px-3 py-1 text-xs text-slate-500">{path}</div>
      <MonacoEditor
        height={height}
        defaultLanguage="python"
        value={value}
        onChange={handleChange}
        theme="vs-dark"
        options={{
          minimap: { enabled: false },
          fontSize: 14,
          padding: { top: 12 },
          scrollBeyondLastLine: false,
        }}
      />
    </div>
  );
}
