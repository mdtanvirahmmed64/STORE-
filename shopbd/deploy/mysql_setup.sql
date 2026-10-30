-- MySQL এ ডাটাবেস ও ইউজার তৈরি:  sudo mysql < deploy/mysql_setup.sql
CREATE DATABASE IF NOT EXISTS shopbd_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'shopbd_user'@'localhost' IDENTIFIED BY 'ChangeThisPassword123!';
GRANT ALL PRIVILEGES ON shopbd_db.* TO 'shopbd_user'@'localhost';
FLUSH PRIVILEGES;
