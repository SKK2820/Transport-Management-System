USE tnstc_booking_db;

-- Seed popular cities via routes
INSERT INTO routes (route_name, source, destination, distance_km, duration_hours, popular, active) VALUES
('Chennai → Madurai (via Trichy)', 'Chennai', 'Madurai', 460, 8.5, 1, 1),
('Chennai → Coimbatore (via Salem)', 'Chennai', 'Coimbatore', 510, 9.0, 1, 1),
('Chennai → Bangalore', 'Chennai', 'Bangalore', 350, 6.5, 1, 1),
('Madurai → Coimbatore', 'Madurai', 'Coimbatore', 215, 4.5, 0, 1),
('Trichy → Salem', 'Trichy', 'Salem', 140, 3.0, 0, 1),
('Vellore → Chennai', 'Vellore', 'Chennai', 140, 3.0, 0, 1),
('Tirunelveli → Madurai', 'Tirunelveli', 'Madurai', 170, 3.5, 0, 1),
('Kanyakumari → Chennai', 'Kanyakumari', 'Chennai', 705, 12.0, 1, 1);

-- Sample buses (12-15)
INSERT INTO buses (bus_number, bus_name, source, destination, departure_time, arrival_time, total_seats, available_seats, fare, bus_type, status) VALUES
('TN01AB1234', 'Chennai Express', 'Chennai', 'Madurai', '22:00', '06:00', 40, 40, 800.00, 'AC', 'Active'),
('TN02CD5678', 'Kovai Superfast', 'Chennai', 'Coimbatore', '21:30', '06:00', 44, 44, 750.00, 'Non-AC', 'Active'),
('TN03EF9012', 'Madurai Deluxe', 'Chennai', 'Madurai', '20:00', '04:30', 40, 40, 900.00, 'AC', 'Active'),
('TN04GH3456', 'Salem Special', 'Chennai', 'Salem', '19:00', '01:00', 42, 42, 550.00, 'Non-AC', 'Active'),
('TN05IJ7890', 'Vellore Fast', 'Vellore', 'Chennai', '07:00', '10:00', 40, 40, 250.00, 'AC', 'Active'),
('TN06KL1122', 'Bangalore Link', 'Chennai', 'Bangalore', '23:00', '05:30', 40, 40, 650.00, 'Semi-Sleeper', 'Active'),
('TN07MN3344', 'Gandhipuram Runner', 'Coimbatore', 'Chennai', '22:15', '06:30', 44, 44, 800.00, 'Sleeper', 'Active'),
('TN08OP5566', 'Tirchy Shuttle', 'Trichy', 'Salem', '08:00', '11:00', 40, 40, 180.00, 'Non-AC', 'Active'),
('TN09QR7788', 'Tirunelveli Star', 'Tirunelveli', 'Madurai', '06:00', '09:30', 40, 40, 220.00, 'Non-AC', 'Active'),
('TN10ST9900', 'Cape Connector', 'Kanyakumari', 'Chennai', '17:00', '05:00', 42, 42, 1100.00, 'Sleeper', 'Active'),
('TN11UV2233', 'Chennai Dayliner', 'Chennai', 'Madurai', '09:00', '17:30', 40, 40, 700.00, 'Non-AC', 'Active'),
('TN12WX4455', 'Kovai AC Lux', 'Chennai', 'Coimbatore', '22:30', '07:00', 40, 40, 950.00, 'AC', 'Active'),
('TN13YZ6677', 'Madurai Night', 'Chennai', 'Madurai', '23:15', '07:30', 40, 40, 820.00, 'Semi-Sleeper', 'Active'),
('TN14AA8899', 'Salem Sprinter', 'Trichy', 'Salem', '17:15', '20:00', 40, 40, 200.00, 'Non-AC', 'Active'),
('TN15BB1010', 'Vellore Comfort', 'Vellore', 'Chennai', '18:00', '21:00', 40, 40, 260.00, 'AC', 'Active');


