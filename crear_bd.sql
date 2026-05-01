-- ============================================================
--  Script de creación de base de datos para Golosinas
--  Ejecutar en MySQL: mysql -u root -p < crear_bd.sql
-- ============================================================

CREATE DATABASE IF NOT EXISTS golosinas_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

-- Opcional: crear un usuario dedicado (recomendado en producción)
-- CREATE USER 'golosinas_user'@'localhost' IDENTIFIED BY 'password_seguro';
-- GRANT ALL PRIVILEGES ON golosinas_db.* TO 'golosinas_user'@'localhost';
-- FLUSH PRIVILEGES;

USE golosinas_db;
