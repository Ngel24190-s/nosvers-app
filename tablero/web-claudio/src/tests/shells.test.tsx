/// <reference types="vitest/globals" />
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render } from '@testing-library/react';

// JWT mock: lib/auth.getToken devuelve un token válido lo suficientemente
// largo para que la PWA crea estar autenticada.
vi.mock('../lib/auth', () => ({
  getToken: () => 'fake.jwt.token',
  getSub: () => 'angel',
  clearToken: () => {},
  setToken: () => {},
  hasContext: () => true,
  getAvailableContexts: () => ['casa', 'nosvers', 'trabajo'],
}));

// useChannel mock — devuelve siempre un snapshot vacío.
// Cada shell entonces se renderiza con EmptyState pero sin crash.
vi.mock('../lib/ws', () => ({
  useChannel: () => ({ data: null, connected: false }),
}));

// apiJson mock por si algún tab vestigial lo usa
vi.mock('../lib/api', () => ({
  apiJson: vi.fn(() => Promise.resolve({})),
  ApiError: class ApiError extends Error {
    code = 'mock';
  },
}));

import CasaShell from '../components/casa/CasaShell';
import NosVersShell from '../components/nosvers/NosVersShell';
import TrabajoShell from '../components/trabajo/TrabajoShell';

describe('shells render smoke', () => {
  beforeEach(() => {
    document.documentElement.dataset.context = 'casa';
  });

  it('CasaShell renders without crash', () => {
    document.documentElement.dataset.context = 'casa';
    const { container } = render(<CasaShell />);
    expect(container.textContent).toMatch(/Hoy|Casa|Saludo|Recordatorios/i);
  });

  it('NosVersShell renders without crash', () => {
    document.documentElement.dataset.context = 'nosvers';
    const { container } = render(<NosVersShell />);
    expect(container.textContent).toMatch(/Granja|ingresos|huerto/i);
  });

  it('TrabajoShell renders without crash', () => {
    document.documentElement.dataset.context = 'trabajo';
    const { container } = render(<TrabajoShell />);
    expect(container.textContent).toMatch(/AUJOURD|CHANTIER|ÉQUIPE/i);
  });
});
