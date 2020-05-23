
CREATE DATABASE valartest CHARACTER SET = 'utf8mb4' COLLATE 'utf8mb4_unicode_520_ci';
USE valartest;
CREATE USER 'kaletest'@'localhost' IDENTIFIED BY 'kale123';
GRANT SELECT,INSERT,UPDATE,DELETE ON valartest.* TO 'kaletest'@'localhost';
