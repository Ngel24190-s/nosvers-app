-- ============================================================
--  NosVers · Base de données MySQL
--  À importer dans Hostinger → phpMyAdmin
--  Nom suggéré de la base : nosvers_db
-- ============================================================

-- Base de datos ya creada en Hostinger: u859094205_zqrpl
-- No hace falta CREATE DATABASE, Hostinger la gestiona
USE u859094205_zqrpl;

-- ------------------------------------------------------------
-- Journal de bord (entrées IA + notes manuelles)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS journal (
  id         INT AUTO_INCREMENT PRIMARY KEY,
  domain     VARCHAR(20) NOT NULL,
  action     TEXT        NOT NULL,
  completed  TINYINT(1)  DEFAULT 0,
  created_at DATETIME    DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ------------------------------------------------------------
-- Inventaire (clé / valeur numérique)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS inventaire (
  cle        VARCHAR(50) PRIMARY KEY,
  valeur     DECIMAL(10,2) DEFAULT 0,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Valeurs initiales NosVers
INSERT INTO inventaire (cle, valeur) VALUES
  ('vers',         10),
  ('compost_stock', 0),
  ('bacs',          2),
  ('ibc',           1),
  ('poules',       12),
  ('canards',       6),
  ('lapins',        4),
  ('brebis',        3),
  ('sku_10kg',      0),
  ('sku_20l',       0),
  ('sku_kit',       0),
  ('sku_vers500',   0),
  ('sku_vers1k',    0)
ON DUPLICATE KEY UPDATE cle = cle;

-- ------------------------------------------------------------
-- Checklist (état des tâches par jour)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS checklist (
  id         INT AUTO_INCREMENT PRIMARY KEY,
  task_id    VARCHAR(10) NOT NULL,
  jour       DATE        NOT NULL,
  done       TINYINT(1)  DEFAULT 0,
  updated_at DATETIME    DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY unique_task_day (task_id, jour)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
