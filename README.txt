TNSTC Booking Counter - Terminal App
====================================

Requirements
------------
- Python 3.9+
- MySQL Server 8+
- Python packages: prettytable, mysql-connector-python, pyfiglet

Install dependencies
--------------------
pip install prettytable mysql-connector-python pyfiglet

Database setup
--------------
1) Open MySQL client and run:
   SOURCE setup.sql;
   SOURCE sample_data.sql;

2) Update DB password in main.py (DB_CONFIG['password']).

Run
---
python main.py

Notes
-----
- Operator name is asked on start and printed on tickets.
- Login credentials: login=admin, password=admin@123 (password masked)
- Date inputs use DD-MM-YYYY.
- Bookings allowed today to +30 days.
- Cancellations blocked for past journey dates (simplified policy).
- Command history available in menu option 11.


