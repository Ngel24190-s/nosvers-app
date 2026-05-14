# documentos/

Facturas, contratos, seguros, papeles de impuestos. Archivado estructurado.

## Subcarpetas

- `facturas/YYYY/` — facturas por año.
- `contratos/` — contratos vigentes.
- `seguros/` — pólizas (hogar, coche, salud).
- `impuestos/` — declaraciones, recibos del Trésor Public.

## Archivos raíz

- `INDEX.md` — índice automantenido por `documento_anotar`.

## Formato

Cada documento es un `.md` con frontmatter:
```yaml
---
tipo: factura | contrato | seguro | impuesto
fecha: YYYY-MM-DD
fuente: <emisor>
autor: angel | africa
creado: ISO timestamp
---
<texto del documento o transcripción>
```

## Tools MCP

- `documento_anotar`, `documentos_buscar`

## Futuro (Fase 7)

OCR automático de PDFs/fotos → archivado sin teclear.
