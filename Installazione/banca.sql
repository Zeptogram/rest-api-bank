CREATE DATABASE IF NOT EXISTS banca;

USE banca;

CREATE TABLE `account` (
  `account_id` varchar(20) PRIMARY KEY,
  `name` varchar(40) NOT NULL,
  `surname` varchar(40) NOT NULL,
  `saldo` decimal(24,2) NOT NULL DEFAULT 0.00
);

CREATE TABLE `transazioni` (
  `transactionId` varchar(36) PRIMARY KEY,
  `from` varchar(20) NOT NULL,
  `to` varchar(20) NOT NULL,
  `amount` decimal(24,2) NOT NULL,
  `diverted` boolean NOT NULL DEFAULT 0,
  `date` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP
);



