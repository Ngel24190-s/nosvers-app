import { useMemo } from 'react';

/**
 * Form genérico derivado de un JSON Schema generado por Pydantic.
 * Soporta primitivos (string/number/boolean), enums, dict free-form (textarea JSON)
 * y arrays simples. Suficiente para los Trigger/Action de v1.
 */

type JsonSchema = {
  type?: string;
  enum?: unknown[];
  properties?: Record<string, JsonSchema>;
  items?: JsonSchema;
  required?: string[];
  title?: string;
  default?: unknown;
  pattern?: string;
  minimum?: number;
  maximum?: number;
  description?: string;
  anyOf?: JsonSchema[];
  $ref?: string;
};

interface Props {
  schema: JsonSchema;
  value: Record<string, unknown>;
  onChange: (v: Record<string, unknown>) => void;
  hideTipo?: boolean;
}

function resolveType(schema: JsonSchema): string {
  if (schema.type) return schema.type;
  if (schema.enum) return 'enum';
  if (schema.anyOf) {
    const t = schema.anyOf.find((s) => s.type);
    if (t?.type) return t.type;
  }
  return 'string';
}

function renderField(
  name: string,
  fieldSchema: JsonSchema,
  value: unknown,
  onChange: (v: unknown) => void,
  required: boolean,
): JSX.Element {
  const type = resolveType(fieldSchema);
  const id = `f_${name}`;
  const label = (
    <label htmlFor={id} className="block text-[11px] cockpit-mono text-cockpit-textDim mb-1">
      {fieldSchema.title || name}
      {required && <span className="text-accent-orange">*</span>}
    </label>
  );

  if (fieldSchema.enum) {
    return (
      <div className="mb-3" key={name}>
        {label}
        <select
          id={id}
          className="w-full bg-cockpit-bg border border-cockpit-border rounded px-2 py-1 text-sm text-cockpit-text"
          value={(value as string) ?? (fieldSchema.default as string) ?? ''}
          onChange={(e) => onChange(e.target.value)}
        >
          {fieldSchema.enum.map((opt) => (
            <option key={String(opt)} value={String(opt)}>
              {String(opt)}
            </option>
          ))}
        </select>
        {fieldSchema.description && (
          <p className="text-[10px] text-cockpit-dim mt-0.5">{fieldSchema.description}</p>
        )}
      </div>
    );
  }

  if (type === 'boolean') {
    return (
      <div className="mb-3 flex items-center gap-2" key={name}>
        <input
          id={id}
          type="checkbox"
          checked={Boolean(value)}
          onChange={(e) => onChange(e.target.checked)}
        />
        <label htmlFor={id} className="text-[11px] cockpit-mono text-cockpit-textDim">
          {fieldSchema.title || name}
        </label>
      </div>
    );
  }

  if (type === 'integer' || type === 'number') {
    return (
      <div className="mb-3" key={name}>
        {label}
        <input
          id={id}
          type="number"
          className="w-full bg-cockpit-bg border border-cockpit-border rounded px-2 py-1 text-sm text-cockpit-text"
          value={(value as number) ?? (fieldSchema.default as number) ?? 0}
          onChange={(e) => onChange(type === 'integer' ? parseInt(e.target.value, 10) : parseFloat(e.target.value))}
          min={fieldSchema.minimum}
          max={fieldSchema.maximum}
        />
        {fieldSchema.description && (
          <p className="text-[10px] text-cockpit-dim mt-0.5">{fieldSchema.description}</p>
        )}
      </div>
    );
  }

  if (type === 'array') {
    const items = (value as unknown[]) ?? [];
    return (
      <div className="mb-3" key={name}>
        {label}
        <textarea
          id={id}
          className="w-full bg-cockpit-bg border border-cockpit-border rounded px-2 py-1 text-sm text-cockpit-text font-mono"
          rows={3}
          value={items.join('\n')}
          onChange={(e) => onChange(e.target.value.split('\n').filter((x) => x.length > 0))}
          placeholder="una entrada por línea"
        />
      </div>
    );
  }

  if (type === 'object') {
    return (
      <div className="mb-3" key={name}>
        {label}
        <textarea
          id={id}
          className="w-full bg-cockpit-bg border border-cockpit-border rounded px-2 py-1 text-sm text-cockpit-text font-mono"
          rows={3}
          value={value ? JSON.stringify(value, null, 2) : ''}
          onChange={(e) => {
            try {
              onChange(e.target.value ? JSON.parse(e.target.value) : {});
            } catch {
              /* keep raw — invalid JSON; UI no marca aún */
            }
          }}
          placeholder='{"key": "value"}'
        />
        <p className="text-[10px] text-cockpit-dim mt-0.5">JSON</p>
      </div>
    );
  }

  // string default
  const isLong = (value as string)?.length > 60;
  return (
    <div className="mb-3" key={name}>
      {label}
      {isLong ? (
        <textarea
          id={id}
          className="w-full bg-cockpit-bg border border-cockpit-border rounded px-2 py-1 text-sm text-cockpit-text"
          rows={3}
          value={(value as string) ?? ''}
          onChange={(e) => onChange(e.target.value)}
        />
      ) : (
        <input
          id={id}
          type="text"
          className="w-full bg-cockpit-bg border border-cockpit-border rounded px-2 py-1 text-sm text-cockpit-text"
          value={(value as string) ?? (fieldSchema.default as string) ?? ''}
          onChange={(e) => onChange(e.target.value)}
          placeholder={fieldSchema.description || ''}
        />
      )}
      {fieldSchema.description && !isLong && (
        <p className="text-[10px] text-cockpit-dim mt-0.5">{fieldSchema.description}</p>
      )}
    </div>
  );
}

export function JsonSchemaForm({ schema, value, onChange, hideTipo = true }: Props) {
  const required = useMemo(() => new Set(schema.required || []), [schema.required]);
  const props = schema.properties || {};
  return (
    <div>
      {Object.entries(props).map(([name, fieldSchema]) => {
        if (hideTipo && name === 'tipo') return null;
        return renderField(
          name,
          fieldSchema,
          value[name],
          (v) => onChange({ ...value, [name]: v }),
          required.has(name),
        );
      })}
    </div>
  );
}
