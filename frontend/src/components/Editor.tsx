interface EditorProps {
  value: string;
  onChange: (next: string) => void;
}

export default function Editor({ value, onChange }: EditorProps) {
  return (
    <textarea
      value={value}
      onChange={(event) => onChange(event.target.value)}
      className="min-h-64 w-full rounded border border-gray-300 p-3 font-mono"
      spellCheck={false}
    />
  );
}
