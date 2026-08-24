-- MySQL Setup Script for TNSTC Booking System

CREATE DATABASE IF NOT EXISTS tnstc_booking_db;
USE tnstc_booking_db;

-- Drop existing tables (optional during development)
-- DROP TABLE IF EXISTS bookings;
-- DROP TABLE IF EXISTS buses;
-- DROP TABLE IF EXISTS routes;

-- Routes table
CREATE TABLE IF NOT EXISTS routes (
  route_id INT PRIMARY KEY AUTO_INCREMENT,
  route_name VARCHAR(100) NOT NULL,
  source VARCHAR(50) NOT NULL,
  destination VARCHAR(50) NOT NULL,
  distance_km INT NOT NULL,
  duration_hours DECIMAL(3,1) NOT NULL,
  popular BOOLEAN DEFAULT 0,
  active BOOLEAN DEFAULT 1,
  UNIQUE KEY uniq_route_name (route_name)
);

-- Buses table
CREATE TABLE IF NOT EXISTS buses (
  bus_id INT PRIMARY KEY AUTO_INCREMENT,
  bus_number VARCHAR(20) NOT NULL UNIQUE,
  bus_name VARCHAR(100) NOT NULL,
  source VARCHAR(50) NOT NULL,
  destination VARCHAR(50) NOT NULL,
  departure_time TIME NOT NULL,
  arrival_time TIME NOT NULL,
  total_seats INT NOT NULL,
  available_seats INT NOT NULL,
  fare DECIMAL(10,2) NOT NULL,
  bus_type ENUM('AC','Non-AC','Sleeper','Semi-Sleeper') NOT NULL,
  status ENUM('Active','Inactive') NOT NULL DEFAULT 'Active',
  INDEX idx_bus_route (source,destination),
  INDEX idx_bus_status (status)
);

-- Bookings table
CREATE TABLE IF NOT EXISTS bookings (
  booking_id INT PRIMARY KEY AUTO_INCREMENT,
  bus_id INT NOT NULL,
  passenger_name VARCHAR(100) NOT NULL,
  passenger_age INT NOT NULL,
  passenger_gender ENUM('Male','Female','Other') NOT NULL,
  passenger_phone VARCHAR(15) NOT NULL,
  seats_booked INT NOT NULL,
  seat_numbers VARCHAR(50) NOT NULL,
  booking_date DATETIME NOT NULL,
  journey_date DATE NOT NULL,
  total_amount DECIMAL(10,2) NOT NULL,
  status ENUM('Confirmed','Cancelled') NOT NULL DEFAULT 'Confirmed',
  booked_by VARCHAR(50) NOT NULL,
  CONSTRAINT fk_bookings_bus FOREIGN KEY (bus_id) REFERENCES buses(bus_id),
  INDEX idx_booking_date (booking_date),
  INDEX idx_journey_date (journey_date),
  INDEX idx_booking_phone (passenger_phone)
);


