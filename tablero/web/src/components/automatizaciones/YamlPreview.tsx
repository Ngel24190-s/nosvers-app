import Editor from '@monaco-editor/react';

interface Props {
  yaml: string;
  height?: number | string;
}

export function YamlPreview({ yaml, height = 300 }: Props) {
  return (
    <div className="rounded border border-cockpit-border overflow-hidden bg-cockpit-bg">
      <div className="px-3 py-1 border-b border-cockpit-border cockpit-mono text-[10px] text-cockpit-textDim">
        YAML PREVIEW (read-only)
      </div>
      <Editor
        height={height}
        defaultLanguage="yaml"
        value={yaml}
        theme="vs-dark"
        options={{
          readOnly: true,
          minimap: { enabled: false },
          fontSize: 12,
          lineNumbers: 'off',
          scrollBeyondLastLine: false,
        }}
      />
    </div>
  );
}
