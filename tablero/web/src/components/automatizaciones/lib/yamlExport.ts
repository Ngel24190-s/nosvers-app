/**
 * Serializa trigger + acciones a string YAML (subset suficiente para preview).
 * Para guardar usamos JSON al backend; el YAML es sólo para mostrar al usuario.
 */
function indent(level: number): string {
  return '  '.repeat(level);
}

function isPrimitive(v: unknown): boolean {
  return v === null || ['string', 'number', 'boolean'].includes(typeof v);
}

function yamlValue(v: unknown, level: number): string {
  if (v === null || v === undefined) return 'null';
  if (typeof v === 'string') {
    if (v.includes('\n') || v.length > 60) {
      return `|\n${indent(level + 1)}${v.replace(/\n/g, `\n${indent(level + 1)}`)}`;
    }
    if (/[:#&*!|>'"%@`{}[\],]/.test(v) || v.trim() !== v) {
      return JSON.stringify(v);
    }
    return v;
  }
  if (typeof v === 'number' || typeof v === 'boolean') return String(v);
  if (Array.isArray(v)) {
    if (v.length === 0) return '[]';
    return '\n' + v.map((it) => `${indent(level)}- ${yamlBlock(it, level + 1, true)}`).join('\n');
  }
  if (typeof v === 'object') {
    return '\n' + yamlBlock(v, level);
  }
  return String(v);
}

function yamlBlock(obj: unknown, level: number, inline = false): string {
  if (obj === null || obj === undefined) return 'null';
  if (isPrimitive(obj) || Array.isArray(obj)) return yamlValue(obj, level);
  const entries = Object.entries(obj as Record<string, unknown>);
  if (entries.length === 0) return '{}';
  return entries
    .map(([k, v], i) => {
      const lineIndent = inline && i === 0 ? '' : indent(level);
      const valStr = yamlValue(v, level);
      if (valStr.startsWith('\n')) {
        return `${lineIndent}${k}:${valStr}`;
      }
      return `${lineIndent}${k}: ${valStr}`;
    })
    .join('\n');
}

export interface ExportInput {
  nombre: string;
  activo: boolean;
  autor?: string;
  trigger: Record<string, unknown> | null;
  acciones: Array<Record<string, unknown>>;
}

export function exportToYaml(input: ExportInput): string {
  const obj: Record<string, unknown> = {
    nombre: input.nombre,
    autor: input.autor ?? 'angel',
    activo: input.activo,
    trigger: input.trigger ?? null,
    acciones: input.acciones,
  };
  return yamlBlock(obj, 0);
}
