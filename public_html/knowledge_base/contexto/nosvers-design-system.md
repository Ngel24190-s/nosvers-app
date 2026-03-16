# nosvers-design-system
*2026-03-15 11:51*

# NosVers — Design System Oficial
*Extraído del Studio V2 aprobado por Angel · Referencia obligatoria para Code*

## TIPOGRAFÍA

| Uso | Fuente | Peso |
|---|---|---|
| Títulos H1/H2 | Playfair Display | 700 |
| Subtítulos editoriales | DM Serif Display | 400 italic |
| Cuerpo de texto | DM Sans | 400 / 500 |
| Navegación / UI | DM Sans | 500 |

Google Fonts import:
```html
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700&family=DM+Sans:wght@400;500&family=DM+Serif+Display:ital@0;1&display=swap" rel="stylesheet">
```

## PALETA DE COLORES

| Variable | Hex | Uso |
|---|---|---|
| `--crème` | `#FEFAF4` | Fondo principal |
| `--vert-vif` | `#5A7A2E` | Verde marca (botones, acentos) |
| `--vert-fonce` | `#3D6B20` | Verde oscuro (hover, CTA) |
| `--terre` | `#1c1510` | Texto principal |
| `--texte-doux` | `#7A7060` | Texto secundario |
| `--border` | `#e0d8cc` | Bordes, separadores |
| `--africa-violet` | `#7A3A6A` | Color exclusivo de África |
| `--bg-clair` | `#f4efe4` | Fondo secciones claras |

## CSS BASE — Copiar en todo nuevo archivo

```css
:root {
  --crème: #FEFAF4;
  --vert-vif: #5A7A2E;
  --vert-fonce: #3D6B20;
  --terre: #1c1510;
  --texte-doux: #7A7060;
  --border: #e0d8cc;
  --africa-violet: #7A3A6A;
  --bg-clair: #f4efe4;
  --font-titre: 'Playfair Display', Georgia, serif;
  --font-serif: 'DM Serif Display', Georgia, serif;
  --font-body: 'DM Sans', system-ui, sans-serif;
  --radius: 12px;
  --transition: all .2s ease;
}

body {
  font-family: var(--font-body);
  background: var(--crème);
  color: var(--terre);
  line-height: 1.7;
}

h1, h2, h3 { font-family: var(--font-titre); }
```

## ESTILO EDITORIAL — "Editorial Organique"

Principios visuales del Studio V2:
- **Luz natural** — fotos con luz cálida, sin filtros artificiales
- **Espacio blanco generoso** — no saturar la página
- **Tipografía como elemento de diseño** — títulos grandes, elegantes
- **Sin sombras de caja** — usar bordes sutiles en su lugar
- **Botones sin relleno agresivo** — bordes finos, hover suave

## BOTONES

```css
.btn-primary {
  background: var(--vert-fonce);
  color: var(--crème);
  border: none;
  border-radius: var(--radius);
  padding: 12px 24px;
  font-family: var(--font-body);
  font-weight: 500;
  cursor: pointer;
  transition: var(--transition);
}

.btn-outline {
  background: transparent;
  color: var(--vert-fonce);
  border: 1.5px solid var(--vert-fonce);
  border-radius: var(--radius);
  padding: 11px 23px;
  font-family: var(--font-body);
  font-weight: 500;
  cursor: pointer;
}
```

## LAYOUT WORDPRESS (theme.json)

Ancho máximo del contenido: **1400px**
Ancho del texto: **800px**
Tipografía registrada: Playfair Display + DM Sans + DM Serif Display

## NOTAS PARA CODE

- SIEMPRE importar las Google Fonts en cualquier HTML nuevo
- NUNCA usar Arial, Inter, Roboto, ni fuentes genéricas
- El verde principal es #5A7A2E — no #00ff00 ni variantes
- El fondo es #FEFAF4 (blanco cálido, no blanco puro #ffffff)
- Toda la UI de la app granja (index.html) debe respetar esta paleta
- nosvers.com debe usar esta tipografía — el tema actual usa Oswald que NO es correcto
