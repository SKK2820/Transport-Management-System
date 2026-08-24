import os
import re
import sys
import time
from datetime import datetime, date, timedelta
import getpass

try:
    from prettytable import PrettyTable
except ImportError:
    print("Missing dependency: prettytable. Install with: pip install prettytable")
    sys.exit(1)

try:
    from pyfiglet import Figlet
except ImportError:
    print("Missing dependency: pyfiglet. Install with: pip install pyfiglet")
    sys.exit(1)

try:
    import mysql.connector as mysql
    from mysql.connector import Error
except ImportError:
    print("Missing dependency: mysql-connector-python. Install with: pip install mysql-connector-python")
    sys.exit(1)


# =============================
# Configuration
# =============================
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'skkdharsh',
    'database': 'tnstc_booking_db'
}

# Color codes (optional aesthetics)
class C:
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    END = "\033[0m"


OPERATOR_NAME = None
CLEAR_SCREENS = False  # Keep outputs visible by default
COMMAND_HISTORY: list[str] = []


# =============================
# Database Helpers
# =============================
def create_connection(retries: int = 2, delay_seconds: int = 1):
    last_err = None
    for _ in range(retries + 1):
        try:
            conn = mysql.connect(**DB_CONFIG)
            return conn
        except Error as e:
            last_err = e
            time.sleep(delay_seconds)
    print(f"{C.RED}Database connection failed:{C.END} {last_err}")
    return None


def close_connection(conn):
    try:
        if conn and conn.is_connected():
            conn.close()
    except Exception:
        pass


def execute_query(query: str, params: tuple = (), commit: bool = False):
    conn = create_connection()
    if not conn:
        return False
    try:
        cur = conn.cursor()
        cur.execute(query, params)
        if commit:
            conn.commit()
        return True
    except Error as e:
        print(f"{C.RED}Error:{C.END} {e}")
        return False
    finally:
        close_connection(conn)


def fetch_data(query: str, params: tuple = (), many: bool = True):
    conn = create_connection()
    if not conn:
        return []
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(query, params)
        if many:
            rows = cur.fetchall()
        else:
            rows = cur.fetchone()
        return rows
    except Error as e:
        print(f"{C.RED}Error:{C.END} {e}")
        return [] if many else None
    finally:
        close_connection(conn)


# =============================
# ASCII Art & UI
# =============================
def clear_screen():
    if not CLEAR_SCREENS:
        return
    os.system('cls' if os.name == 'nt' else 'clear')


def display_banner():
    clear_screen()
    try:
        fig = Figlet(font='slant')
        print(f"{C.GREEN}{C.BOLD}{fig.renderText('TNSTC')}{C.END}", end='')
        sub = Figlet(font='mini')
        print(f"{C.CYAN}{sub.renderText('Booking Counter')}{C.END}")
    except Exception:
        art = [
            "╔═══════════════════════════════════════════════════════════════╗",
            "║                 TAMIL NADU STATE TRANSPORT (TNSTC)            ║",
            "║                        BOOKING COUNTER                         ║",
            "╚═══════════════════════════════════════════════════════════════╝",
        ]
        for line in art:
            print(f"{C.GREEN}{C.BOLD}{line}{C.END}")
    if OPERATOR_NAME:
        print(f"Operator: {C.CYAN}{OPERATOR_NAME}{C.END}\n")


def display_bus_art():
    bus = [
        "      ________________________________",
        " ____/_______________________________|",
        "|    |  TNSTC                         |",
        "|____|________________________________|",
        "  O                                O  ",
    ]
    for line in bus:
        print(f"{C.YELLOW}{line}{C.END}")


def generate_ticket_border(width: int = 48):
    return "╔" + "═" * width + "╗", "╚" + "═" * width + "╝", "╠" + "═" * width + "╣"


def press_enter_to_continue():
    input(f"\n{C.BLUE}Press ENTER to continue...{C.END}")


def display_menu():
    print("========== TNSTC BOOKING COUNTER ==========")
    print("1. View All Routes")
    print("2. Search Available Buses")
    print("3. Book New Ticket (for passenger)")
    print("4. Search Booking Details")
    print("5. Cancel Booking")
    print("6. View Today's Bookings")
    print("7. Generate Daily Report")
    print("8. Bus Management")
    print("9. Route Management")
    print("10. Exit")


def add_history(entry: str):
    # No-op to disable separate history feature while keeping code references safe
    return


def view_command_history():
    # Deprecated feature intentionally disabled
    print(f"{C.YELLOW}History view disabled. Outputs remain on screen now.{C.END}")
    press_enter_to_continue()


def display_buses_table(rows):
    table = PrettyTable()
    table.field_names = [
        "Bus Number", "Bus Name", "Type", "From", "To",
        "Dep", "Arr", "Avail", "Fare", "Status"
    ]
    for r in rows:
        status = "FULL"
        if r['available_seats'] > 10:
            status = "AVAILABLE"
        elif 1 <= r['available_seats'] <= 10:
            status = "FEW SEATS"
        table.add_row([
            r['bus_number'], r['bus_name'], r['bus_type'], r['source'], r['destination'],
            str(r['departure_time'])[:-3], str(r['arrival_time'])[:-3], r['available_seats'],
            f"₹{r['fare']:.2f}", status
        ])
    print(table)


def display_bookings_table(rows):
    table = PrettyTable()
    table.field_names = [
        "Booking ID", "Passenger", "Phone", "Bus No", "Seats",
        "Seat No(s)", "Journey Date", "Total", "Status"
    ]
    for r in rows:
        table.add_row([
            r['booking_id'], r['passenger_name'], r['passenger_phone'], r['bus_number'],
            r['seats_booked'], r['seat_numbers'], r['journey_date'].strftime('%d-%b-%Y'),
            f"₹{r['total_amount']:.2f}", r['status']
        ])
    print(table)


# =============================
# Validation
# =============================
def input_with_retry(prompt: str, validator, error_message: str, transform=None, allow_quit: bool = True):
    while True:
        value = input(prompt).strip()
        if allow_quit and value.lower() == 'q':
            return None
        if transform:
            try:
                value_t = transform(value)
            except Exception:
                print(f"{C.RED}{error_message}{C.END}")
                continue
        else:
            value_t = value
        try:
            valid = validator(value_t)
        except Exception:
            valid = False
        if valid:
            return value_t
        print(f"{C.RED}{error_message}{C.END}")

def validate_phone(phone: str) -> bool:
    return re.fullmatch(r"[6-9][0-9]{9}", phone or "") is not None


def validate_name(name: str) -> bool:
    return re.fullmatch(r"[A-Za-z ]{2,50}", name or "") is not None


def validate_age(age_str: str) -> int:
    if not age_str.isdigit():
        return -1
    age = int(age_str)
    return age if 1 <= age <= 120 else -1


def validate_date(date_str: str) -> date | None:
    try:
        d = datetime.strptime(date_str, "%d-%m-%Y").date()
        if d < date.today():
            return None
        if d > date.today() + timedelta(days=30):
            return None
        return d
    except Exception:
        return None


def validate_bus_number(bus_no: str) -> bool:
    return re.fullmatch(r"TN\d{2}[A-Z]{2}\d{4}", bus_no or "") is not None


# =============================
# Core Operations
# =============================
def view_all_routes():
    display_banner()
    print(f"{C.BOLD}Active Routes:{C.END}")
    q = """
        SELECT route_id, route_name, source, destination, distance_km,
               duration_hours, popular, active
        FROM routes
        WHERE active = 1
        ORDER BY popular DESC, route_name ASC
    """
    rows = fetch_data(q)
    if not rows:
        print(f"{C.YELLOW}No active routes found.{C.END}")
        press_enter_to_continue()
        return
    table = PrettyTable()
    table.field_names = ["Route", "Source", "Destination", "Distance(km)", "Duration(h)", "Popular"]
    for r in rows:
        table.add_row([r['route_name'], r['source'], r['destination'], r['distance_km'], r['duration_hours'], "★" if r['popular'] else "-"])
    display_bus_art()
    print(table)
    press_enter_to_continue()


def _search_buses_by_filters(source=None, destination=None, jdate: date | None = None, bus_type=None, route_name=None):
    clauses = ["status = 'Active'"]
    params = []
    if source:
        clauses.append("LOWER(source) = LOWER(%s)")
        params.append(source)
    if destination:
        clauses.append("LOWER(destination) = LOWER(%s)")
        params.append(destination)
    if bus_type:
        clauses.append("bus_type = %s")
        params.append(bus_type)
    if route_name:
        # route filter matches based on source/destination of route name
        clauses.append("CONCAT(source, ' → ', destination) = %s")
        params.append(route_name)

    where = " AND ".join(clauses)
    q = f"""
        SELECT bus_id, bus_number, bus_name, source, destination, departure_time,
               arrival_time, total_seats, available_seats, fare, bus_type
        FROM buses
        WHERE {where}
        ORDER BY departure_time ASC
    """
    rows = fetch_data(q, tuple(params))

    # If journey date given, we might compute day-specific availability in future; for now, use available_seats
    return rows


def search_buses():
    display_banner()
    print(f"{C.BOLD}Search Available Buses{C.END}")
    print("1) By source & destination")
    print("2) By journey date")
    print("3) By bus type")
    print("4) By route name (e.g., Chennai → Madurai)")
    ch = input("Choose option: ").strip()

    rows = []
    if ch == '1':
        s = input("Source: ").strip()
        d = input("Destination: ").strip()
        rows = _search_buses_by_filters(s, d)
    elif ch == '2':
        jd = input("Journey Date (DD-MM-YYYY): ").strip()
        jdate = validate_date(jd)
        if not jdate:
            print(f"{C.RED}Invalid date. Bookings allowed today to next 30 days.{C.END}")
        else:
            rows = _search_buses_by_filters(jdate=jdate)
    elif ch == '3':
        bt = input("Bus Type (AC/Non-AC/Sleeper/Semi-Sleeper): ").strip()
        rows = _search_buses_by_filters(bus_type=bt)
    elif ch == '4':
        rn = input("Route (e.g., Chennai → Madurai): ").strip()
        rows = _search_buses_by_filters(route_name=rn)
    else:
        print(f"{C.YELLOW}Invalid choice.{C.END}")

    if rows:
        display_buses_table(rows)
    else:
        print(f"{C.YELLOW}No buses found for given criteria.{C.END}")
    add_history(f"Searched buses option={ch}")
    press_enter_to_continue()


def _auto_assign_seats(bus_id: int, num_seats: int) -> list[str]:
    # Fetch already assigned seats from bookings for future robustness; for now use available_seats count
    q = "SELECT total_seats, total_seats - available_seats AS occupied FROM buses WHERE bus_id=%s"
    info = fetch_data(q, (bus_id,), many=False)
    if not info:
        return []
    start = int(info['occupied']) + 1
    return [str(s) for s in range(start, start + num_seats)]


def book_ticket():
    display_banner()
    print(f"{C.BOLD}Book New Ticket{C.END}")
    s = input_with_retry("Source: ", lambda x: len(x) > 0, "Source cannot be empty")
    if s is None:
        print(f"{C.YELLOW}Booking cancelled.{C.END}")
        press_enter_to_continue()
        return
    d = input_with_retry("Destination: ", lambda x: len(x) > 0, "Destination cannot be empty")
    if d is None:
        print(f"{C.YELLOW}Booking cancelled.{C.END}")
        press_enter_to_continue()
        return
    def _date_validator(ds):
        return validate_date(ds) is not None
    jd = input_with_retry("Journey Date (DD-MM-YYYY) [q to cancel]: ", _date_validator, "Enter a valid date within 30 days (DD-MM-YYYY)")
    if jd is None:
        print(f"{C.YELLOW}Booking cancelled.{C.END}")
        press_enter_to_continue()
        return
    jdate = validate_date(jd)
    rows = _search_buses_by_filters(s, d)
    rows = [r for r in rows if r['available_seats'] > 0]
    if not rows:
        print(f"{C.YELLOW}No available buses for the route.{C.END}")
        press_enter_to_continue()
        return
    display_buses_table(rows)
    while True:
        bus_no = input("Enter Bus Number to select [q to cancel]: ").strip()
        if bus_no.lower() == 'q':
            print(f"{C.YELLOW}Booking cancelled.{C.END}")
            press_enter_to_continue()
            return
        bus = next((r for r in rows if r['bus_number'] == bus_no), None)
        if bus:
            break
        print(f"{C.RED}Invalid bus number. Please choose from the table above.{C.END}")

    # Passenger details
    name = input_with_retry("Passenger Full Name [q to cancel]: ", validate_name, "Name must be 2-50 letters/spaces")
    if name is None:
        print(f"{C.YELLOW}Booking cancelled.{C.END}")
        press_enter_to_continue()
        return

    def _age_validator(a):
        return validate_age(str(a)) != -1
    age_val = input_with_retry("Age [1-120]: ", _age_validator, "Enter valid age 1-120", transform=lambda x: int(x))
    if age_val is None:
        print(f"{C.YELLOW}Booking cancelled.{C.END}")
        press_enter_to_continue()
        return
    age = int(age_val)

    def _gender_validator(g):
        return g.upper() in ("M", "F", "O")
    gender_in = input_with_retry("Gender (M/F/O): ", _gender_validator, "Enter M, F, or O")
    if gender_in is None:
        print(f"{C.YELLOW}Booking cancelled.{C.END}")
        press_enter_to_continue()
        return
    gender = gender_in.upper()

    phone = input_with_retry("Phone (10 digits): ", validate_phone, "Invalid phone (must start 6-9, 10 digits)")
    if phone is None:
        print(f"{C.YELLOW}Booking cancelled.{C.END}")
        press_enter_to_continue()
        return

    def _seats_validator(s):
        if not str(s).isdigit():
            return False
        si = int(s)
        return 1 <= si <= 6 and si <= bus['available_seats']
    seats_val = input_with_retry(f"Seats (1-6, avail {bus['available_seats']}): ", _seats_validator, "Invalid seats or exceeds availability")
    if seats_val is None:
        print(f"{C.YELLOW}Booking cancelled.{C.END}")
        press_enter_to_continue()
        return
    seats = int(seats_val)

    seat_numbers = ", ".join(_auto_assign_seats(bus['bus_id'], seats))
    fare_per = float(bus['fare'])
    total = fare_per * seats
    if age > 60:  # optional senior discount 10%
        total *= 0.9

    # Confirmation
    display_banner()
    top, bottom, mid = generate_ticket_border()
    print(top)
    print(f"║ Passenger: {name:<36}║")
    print(f"║ Age: {age:<3} Gender: {gender:<1}  Phone: {phone:<16}║")
    print(mid)
    print(f"║ Bus: {bus['bus_number']} - {bus['bus_name']:<28}║")
    print(f"║ Route: {bus['source']} → {bus['destination']:<28}║")
    print(mid)
    print(f"║ Journey Date: {jdate.strftime('%d-%b-%Y'):<31}║")
    print(f"║ Departure: {str(bus['departure_time'])[:-3]:<8} Arrival: {str(bus['arrival_time'])[:-3]:<8}      ║")
    print(f"║ Seat(s): {seat_numbers:<35}║")
    print(mid)
    print(f"║ Fare: ₹{fare_per:.0f} × {seats} = ₹{total:.0f}{' (10% senior disc.)' if age>60 else '':<8}║")
    print(bottom)
    while True:
        conf = input(f"\nConfirm booking? (Y/N): ").strip().upper()
        if conf in ('Y','N'):
            break
        print(f"{C.YELLOW}Please answer Y or N.{C.END}")
    if conf == 'N':
        print(f"{C.YELLOW}Booking cancelled by operator.{C.END}")
        press_enter_to_continue()
        return

    # Persist booking
    try:
        conn = create_connection()
        if not conn:
            print(f"{C.RED}Cannot connect to DB.{C.END}")
            press_enter_to_continue()
            return
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO bookings
              (bus_id, passenger_name, passenger_age, passenger_gender, passenger_phone,
               seats_booked, seat_numbers, booking_date, journey_date, total_amount, status, booked_by)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'Confirmed',%s)
            """,
            (
                bus['bus_id'], name, age,
                {'M': 'Male', 'F': 'Female', 'O': 'Other'}[gender], phone,
                seats, seat_numbers, datetime.now(), jdate, total, OPERATOR_NAME
            )
        )
        cur.execute(
            "UPDATE buses SET available_seats = available_seats - %s WHERE bus_id = %s",
            (seats, bus['bus_id'])
        )
        conn.commit()
        cur.execute("SELECT LAST_INSERT_ID()")
        booking_id = cur.fetchone()[0]
    except Error as e:
        print(f"{C.RED}DB Error:{C.END} {e}")
        booking_id = None
    finally:
        close_connection(conn)

    if not booking_id:
        print(f"{C.RED}Failed to store booking.{C.END}")
        press_enter_to_continue()
        return

    display_ticket(booking_id)
    add_history(f"Booked ticket ID={booking_id} bus={bus['bus_number']} seats={seats}")
    press_enter_to_continue()


def display_ticket(booking_id: int):
    q = """
        SELECT b.booking_id, b.passenger_name, b.passenger_age, b.passenger_gender, b.passenger_phone,
               b.seats_booked, b.seat_numbers, b.booking_date, b.journey_date, b.total_amount, b.status,
               bu.bus_number, bu.bus_name, bu.source, bu.destination, bu.departure_time, bu.arrival_time
        FROM bookings b
        JOIN buses bu ON bu.bus_id = b.bus_id
        WHERE b.booking_id = %s
    """
    r = fetch_data(q, (booking_id,), many=False)
    if not r:
        print(f"{C.RED}Booking not found.{C.END}")
        return
    display_banner()
    top, bottom, mid = generate_ticket_border(48)
    print(top)
    print("║         TAMIL NADU STATE TRANSPORT             ║")
    print("║              BUS TICKET                        ║")
    print(mid)
    print(f"║ Booking ID: TN{r['booking_id']:010d}{' ' * 19}║")
    print(f"║ Date: {r['booking_date'].strftime('%d-%b-%Y %H:%M'):<38}║")
    print(mid)
    print(f"║ Passenger: {r['passenger_name']:<36}║")
    print(f"║ Age: {r['passenger_age']:<3}  Gender: {r['passenger_gender'][0]:<1}  Phone: {r['passenger_phone']:<15}║")
    print(mid)
    print(f"║ Bus: {r['bus_number']} - {r['bus_name']:<28}║")
    print(f"║ Route: {r['source']} → {r['destination']:<28}║")
    print(mid)
    print(f"║ Journey Date: {r['journey_date'].strftime('%d-%b-%Y'):<31}║")
    print(f"║ Departure: {str(r['departure_time'])[:-3]:<8}  Arrival: {str(r['arrival_time'])[:-3]:<8}      ║")
    print(f"║ Seat(s): {r['seat_numbers']:<35}║")
    print(mid)
    print(f"║ Fare: ₹{r['total_amount']:.0f}{' ' * (39 - len(str(int(r['total_amount']))))}║")
    print("║                                                ║")
    print(f"║ Booked by: Operator-{OPERATOR_NAME:<28}║")
    print(f"║ Terms: Non-refundable within 2 hours of depart.║")
    print(bottom)


def search_bookings():
    display_banner()
    print(f"{C.BOLD}Search Bookings{C.END}")
    print("1) By Booking ID")
    print("2) By Phone Number")
    print("3) By Passenger Name")
    print("4) By Journey Date")
    ch = input("Choose option: ").strip()

    rows = []
    if ch == '1':
        bid = input("Booking ID: ").strip()
        if not bid.isdigit():
            print(f"{C.RED}Invalid ID.{C.END}")
        else:
            rows = _get_booking_rows("b.booking_id = %s", (int(bid),))
    elif ch == '2':
        ph = input("Phone: ").strip()
        if validate_phone(ph):
            rows = _get_booking_rows("b.passenger_phone = %s", (ph,))
        else:
            print(f"{C.RED}Invalid phone.{C.END}")
    elif ch == '3':
        nm = input("Passenger Name: ").strip()
        rows = _get_booking_rows("LOWER(b.passenger_name) LIKE LOWER(%s)", (f"%{nm}%",))
    elif ch == '4':
        jd = input("Journey Date (DD-MM-YYYY): ").strip()
        d = validate_date(jd)
        if d:
            rows = _get_booking_rows("b.journey_date = %s", (d,))
        else:
            print(f"{C.RED}Invalid date.{C.END}")
    else:
        print(f"{C.YELLOW}Invalid choice.{C.END}")

    if rows:
        display_bookings_table(rows)
    else:
        print(f"{C.YELLOW}No bookings found.{C.END}")
    add_history(f"Searched bookings by option={ch}")
    press_enter_to_continue()


def _get_booking_rows(where: str, params: tuple):
    q = f"""
        SELECT b.booking_id, b.passenger_name, b.passenger_phone, b.seats_booked,
               b.seat_numbers, b.journey_date, b.total_amount, b.status,
               bu.bus_number
        FROM bookings b
        JOIN buses bu ON bu.bus_id = b.bus_id
        WHERE {where}
        ORDER BY b.booking_date DESC
    """
    return fetch_data(q, params)


def cancel_booking():
    display_banner()
    print(f"{C.BOLD}Cancel Booking{C.END}")
    bid = input("Booking ID: ").strip()
    if not bid.isdigit():
        print(f"{C.RED}Invalid ID.{C.END}")
        press_enter_to_continue()
        return
    q = "SELECT booking_id, bus_id, seats_booked, status, journey_date FROM bookings WHERE booking_id=%s"
    r = fetch_data(q, (int(bid),), many=False)
    if not r:
        print(f"{C.YELLOW}Booking not found.{C.END}")
        press_enter_to_continue()
        return
    if r['status'] == 'Cancelled':
        print(f"{C.YELLOW}Booking already cancelled.{C.END}")
        press_enter_to_continue()
        return
    # policy: allowed until 2 hours before departure (approx; we check journey date only here)
    if r['journey_date'] < date.today():
        print(f"{C.RED}Cannot cancel past journey dates.{C.END}")
        press_enter_to_continue()
        return
    if input("Confirm cancel? (Y to proceed): ").strip().upper() != 'Y':
        print(f"{C.YELLOW}Cancellation aborted.{C.END}")
        press_enter_to_continue()
        return

    try:
        conn = create_connection()
        if not conn:
            print(f"{C.RED}DB connection failed.{C.END}")
            press_enter_to_continue()
            return
        cur = conn.cursor()
        cur.execute("UPDATE bookings SET status='Cancelled' WHERE booking_id=%s", (int(bid),))
        cur.execute("UPDATE buses SET available_seats = available_seats + %s WHERE bus_id=%s", (r['seats_booked'], r['bus_id']))
        conn.commit()
        print(f"{C.GREEN}Booking cancelled successfully.{C.END}")
        print(f"Cancellation Time: {datetime.now().strftime('%d-%b-%Y %H:%M')}")
    except Error as e:
        print(f"{C.RED}DB Error:{C.END} {e}")
    finally:
        close_connection(conn)
    add_history(f"Cancelled booking ID={bid}")
    press_enter_to_continue()


def view_today_bookings():
    display_banner()
    print(f"{C.BOLD}Today's Bookings{C.END}")
    q = """
        SELECT b.booking_id, b.passenger_name, b.passenger_phone, b.seats_booked,
               b.seat_numbers, b.journey_date, b.total_amount, b.status, bu.bus_number
        FROM bookings b
        JOIN buses bu ON bu.bus_id = b.bus_id
        WHERE DATE(b.booking_date) = CURDATE()
        ORDER BY b.booking_date DESC
    """
    rows = fetch_data(q)
    if rows:
        display_bookings_table(rows)
    else:
        print(f"{C.YELLOW}No bookings today.{C.END}")

    # stats
    q2 = """
        SELECT COUNT(*) cnt, SUM(seats_booked) seats, SUM(total_amount) revenue,
               SUM(CASE WHEN status='Cancelled' THEN 1 ELSE 0 END) cancelled
        FROM bookings WHERE DATE(booking_date) = CURDATE()
    """
    stats = fetch_data(q2, many=False) or {'cnt': 0, 'seats': 0, 'revenue': 0, 'cancelled': 0}
    print(f"\nTotal Bookings: {stats['cnt']}  Seats: {stats['seats'] or 0}  Revenue: ₹{stats['revenue'] or 0:.0f}  Cancelled: {stats['cancelled']}")
    add_history("Viewed today's bookings and stats")
    press_enter_to_continue()


def generate_daily_report():
    display_banner()
    print(f"{C.BOLD}Generate Daily Report{C.END}")
    ds = input("Report Date (DD-MM-YYYY): ").strip()
    d = None
    try:
        d = datetime.strptime(ds, "%d-%m-%Y").date()
    except Exception:
        print(f"{C.RED}Invalid date format.{C.END}")
        press_enter_to_continue()
        return

    # overall
    q1 = """
        SELECT COUNT(*) cnt, COALESCE(SUM(total_amount),0) revenue,
               SUM(seats_booked) seats,
               SUM(CASE WHEN status='Cancelled' THEN 1 ELSE 0 END) cancelled
        FROM bookings WHERE DATE(booking_date) = %s
    """
    overall = fetch_data(q1, (d,), many=False) or {'cnt': 0, 'revenue': 0, 'seats': 0, 'cancelled': 0}
    print(f"\nDate: {d.strftime('%d-%b-%Y')}  Total: {overall['cnt']}  Seats: {overall['seats'] or 0}  Revenue: ₹{overall['revenue'] or 0:.0f}  Cancelled: {overall['cancelled']}")

    # bus-wise
    q2 = """
        SELECT bu.bus_number, COUNT(*) bookings, COALESCE(SUM(b.total_amount),0) revenue
        FROM bookings b JOIN buses bu ON bu.bus_id = b.bus_id
        WHERE DATE(b.booking_date)=%s
        GROUP BY bu.bus_number
        ORDER BY revenue DESC
    """
    bw = fetch_data(q2, (d,))
    if bw:
        t = PrettyTable(["Bus Number", "Bookings", "Revenue"])
        for r in bw:
            t.add_row([r['bus_number'], r['bookings'], f"₹{r['revenue']:.0f}"])
        print("\nBus-wise:")
        print(t)

    # route-wise
    q3 = """
        SELECT CONCAT(bu.source,' → ',bu.destination) route, COUNT(*) bookings, COALESCE(SUM(b.total_amount),0) revenue
        FROM bookings b JOIN buses bu ON bu.bus_id = b.bus_id
        WHERE DATE(b.booking_date)=%s
        GROUP BY route
        ORDER BY bookings DESC
    """
    rw = fetch_data(q3, (d,))
    if rw:
        t = PrettyTable(["Route", "Bookings", "Revenue"])
        for r in rw:
            t.add_row([r['route'], r['bookings'], f"₹{r['revenue']:.0f}"])
        print("\nRoute-wise:")
        print(t)

    add_history(f"Generated daily report for {d.strftime('%d-%m-%Y')}")
    press_enter_to_continue()


# =============================
# Management
# =============================
def add_bus():
    display_banner()
    print(f"{C.BOLD}Add New Bus{C.END}")
    bus_number = input("Bus Number (TN##XX####): ").strip().upper()
    if not validate_bus_number(bus_number):
        print(f"{C.RED}Invalid format.{C.END}")
        press_enter_to_continue()
        return
    # ensure unique
    exists = fetch_data("SELECT bus_id FROM buses WHERE bus_number=%s", (bus_number,), many=False)
    if exists:
        print(f"{C.RED}Duplicate bus number.{C.END}")
        press_enter_to_continue()
        return
    bus_name = input("Bus Name: ").strip()
    source = input("Source: ").strip()
    destination = input("Destination: ").strip()
    dep = input("Departure Time (HH:MM 24h): ").strip()
    arr = input("Arrival Time (HH:MM 24h): ").strip()
    seats_s = input("Total Seats: ").strip()
    fare_s = input("Fare per seat: ").strip()
    btype = input("Type (AC/Non-AC/Sleeper/Semi-Sleeper): ").strip()
    try:
        seats = int(seats_s)
        fare = float(fare_s)
        datetime.strptime(dep, "%H:%M")
        datetime.strptime(arr, "%H:%M")
    except Exception:
        print(f"{C.RED}Invalid inputs for time/seats/fare.{C.END}")
        press_enter_to_continue()
        return
    q = """
        INSERT INTO buses (bus_number, bus_name, source, destination, departure_time, arrival_time,
                           total_seats, available_seats, fare, bus_type, status)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'Active')
    """
    ok = execute_query(q, (bus_number, bus_name, source, destination, dep, arr, seats, seats, fare, btype), True)
    print(f"{C.GREEN}Bus added.{C.END}" if ok else f"{C.RED}Failed to add bus.{C.END}")
    if ok:
        add_history(f"Added bus {bus_number}")
    press_enter_to_continue()


def update_bus():
    display_banner()
    print(f"{C.BOLD}Update Bus Details{C.END}")
    bus_number = input("Bus Number: ").strip().upper()
    bus = fetch_data("SELECT * FROM buses WHERE bus_number=%s", (bus_number,), many=False)
    if not bus:
        print(f"{C.YELLOW}Bus not found.{C.END}")
        press_enter_to_continue()
        return
    print("Leave blank to keep current.")
    dep = input(f"Departure ({bus['departure_time']}): ").strip() or str(bus['departure_time'])
    arr = input(f"Arrival   ({bus['arrival_time']}): ").strip() or str(bus['arrival_time'])
    fare_s = input(f"Fare      ({bus['fare']}): ").strip() or str(bus['fare'])
    status = input(f"Status (Active/Inactive) ({bus['status']}): ").strip() or bus['status']
    try:
        datetime.strptime(dep[:5], "%H:%M")
        datetime.strptime(arr[:5], "%H:%M")
        fare = float(fare_s)
    except Exception:
        print(f"{C.RED}Invalid values.{C.END}")
        press_enter_to_continue()
        return
    ok = execute_query("UPDATE buses SET departure_time=%s, arrival_time=%s, fare=%s, status=%s WHERE bus_number=%s",
                       (dep[:8], arr[:8], fare, status, bus_number), True)
    print(f"{C.GREEN}Updated.{C.END}" if ok else f"{C.RED}Update failed.{C.END}")
    if ok:
        add_history(f"Updated bus {bus_number}")
    press_enter_to_continue()


def remove_bus():
    display_banner()
    print(f"{C.BOLD}Deactivate Bus{C.END}")
    bus_number = input("Bus Number: ").strip().upper()
    if input("Confirm deactivation? (Y): ").strip().upper() != 'Y':
        print(f"{C.YELLOW}Operation cancelled.{C.END}")
        press_enter_to_continue()
        return
    ok = execute_query("UPDATE buses SET status='Inactive' WHERE bus_number=%s", (bus_number,), True)
    print(f"{C.GREEN}Bus deactivated.{C.END}" if ok else f"{C.RED}Failed.{C.END}")
    if ok:
        add_history(f"Deactivated bus {bus_number}")
    press_enter_to_continue()


def view_all_buses():
    display_banner()
    print(f"{C.BOLD}All Buses{C.END}")
    status = input("Filter by status (Active/Inactive/All): ").strip()
    where = "" if status.lower() == 'all' or status == '' else "WHERE status=%s"
    params = () if where == "" else (status,)
    q = f"SELECT * FROM buses {where} ORDER BY status DESC, departure_time ASC"
    rows = fetch_data(q, params)
    if not rows:
        print(f"{C.YELLOW}No buses found.{C.END}")
        press_enter_to_continue()
        return
    table = PrettyTable(["Bus No", "Name", "Type", "From", "To", "Dep", "Arr", "Seats", "Avail", "Fare", "Status"])
    for r in rows:
        occ = f"{(1 - (r['available_seats']/r['total_seats']))*100:.0f}%"
        table.add_row([r['bus_number'], r['bus_name'], r['bus_type'], r['source'], r['destination'],
                       str(r['departure_time'])[:-3], str(r['arrival_time'])[:-3], r['total_seats'], r['available_seats'], f"₹{r['fare']:.0f}", r['status']])
    print(table)
    add_history("Viewed all buses")
    press_enter_to_continue()


def add_route():
    display_banner()
    print(f"{C.BOLD}Add New Route{C.END}")
    route_name = input("Route Name (e.g., Chennai → Madurai): ").strip()
    source = input("Source: ").strip()
    destination = input("Destination: ").strip()
    dist_s = input("Distance (km): ").strip()
    dur_s = input("Duration (hours e.g., 8.0): ").strip()
    popular = 1 if input("Mark popular? (Y/N): ").strip().upper() == 'Y' else 0
    try:
        dist = int(dist_s)
        dur = float(dur_s)
    except Exception:
        print(f"{C.RED}Invalid distance/duration.{C.END}")
        press_enter_to_continue()
        return
    ok = execute_query(
        "INSERT INTO routes (route_name, source, destination, distance_km, duration_hours, popular, active) VALUES (%s,%s,%s,%s,%s,%s,1)",
        (route_name, source, destination, dist, dur, popular), True)
    print(f"{C.GREEN}Route added.{C.END}" if ok else f"{C.RED}Failed to add route.{C.END}")
    if ok:
        add_history(f"Added route {route_name}")
    press_enter_to_continue()


def update_route():
    display_banner()
    print(f"{C.BOLD}Update Route{C.END}")
    route_name = input("Route Name: ").strip()
    r = fetch_data("SELECT * FROM routes WHERE route_name=%s", (route_name,), many=False)
    if not r:
        print(f"{C.YELLOW}Route not found.{C.END}")
        press_enter_to_continue()
        return
    print("Leave blank to keep current.")
    dist = input(f"Distance ({r['distance_km']}): ").strip() or str(r['distance_km'])
    dur = input(f"Duration ({r['duration_hours']}): ").strip() or str(r['duration_hours'])
    active = input(f"Active (1/0) ({r['active']}): ").strip() or str(r['active'])
    popular = input(f"Popular (1/0) ({r['popular']}): ").strip() or str(r['popular'])
    try:
        ok = execute_query("UPDATE routes SET distance_km=%s, duration_hours=%s, active=%s, popular=%s WHERE route_id=%s",
                           (int(dist), float(dur), int(active), int(popular), r['route_id']), True)
        print(f"{C.GREEN}Updated.{C.END}" if ok else f"{C.RED}Failed.{C.END}")
    except Exception:
        print(f"{C.RED}Invalid values.{C.END}")
    else:
        add_history(f"Updated route {route_name}")
    press_enter_to_continue()


def view_all_routes_mgmt():
    display_banner()
    print(f"{C.BOLD}Routes (with stats){C.END}")
    q = """
        SELECT r.route_name, r.source, r.destination, r.distance_km, r.duration_hours, r.popular, r.active,
               COUNT(bu.bus_id) buses
        FROM routes r
        LEFT JOIN buses bu ON bu.source = r.source AND bu.destination = r.destination
        GROUP BY r.route_id
        ORDER BY r.active DESC, r.popular DESC, r.route_name ASC
    """
    rows = fetch_data(q)
    if not rows:
        print(f"{C.YELLOW}No routes found.{C.END}")
        press_enter_to_continue()
        return
    t = PrettyTable(["Route", "Source", "Destination", "Distance", "Duration", "Popular", "Active", "#Buses"])
    for r in rows:
        t.add_row([r['route_name'], r['source'], r['destination'], r['distance_km'], r['duration_hours'], 'Y' if r['popular'] else 'N', 'Y' if r['active'] else 'N', r['buses']])
    print(t)
    add_history("Viewed routes (management)")
    press_enter_to_continue()


# =============================
# Main Menu Controller
# =============================
def bus_management_menu():
    while True:
        display_banner()
        print(f"{C.BOLD}Bus Management{C.END}")
        print("1) Add New Bus")
        print("2) Update Bus Details")
        print("3) Deactivate Bus")
        print("4) View All Buses")
        print("5) Back")
        c = input("Choose: ").strip()
        if c == '1':
            add_bus()
        elif c == '2':
            update_bus()
        elif c == '3':
            remove_bus()
        elif c == '4':
            view_all_buses()
        elif c == '5':
            break
        else:
            print(f"{C.YELLOW}Invalid choice.{C.END}")
            press_enter_to_continue()


def route_management_menu():
    while True:
        display_banner()
        print(f"{C.BOLD}Route Management{C.END}")
        print("1) Add New Route")
        print("2) Update Route")
        print("3) View All Routes")
        print("4) Back")
        c = input("Choose: ").strip()
        if c == '1':
            add_route()
        elif c == '2':
            update_route()
        elif c == '3':
            view_all_routes_mgmt()
        elif c == '4':
            break
        else:
            print(f"{C.YELLOW}Invalid choice.{C.END}")
            press_enter_to_continue()


def main_menu():
    while True:
        display_banner()
        display_menu()
        choice = input("Select option: ").strip()
        add_history(f"Menu selected: {choice}")
        if choice == '1':
            view_all_routes()
        elif choice == '2':
            search_buses()
        elif choice == '3':
            book_ticket()
        elif choice == '4':
            search_bookings()
        elif choice == '5':
            cancel_booking()
        elif choice == '6':
            view_today_bookings()
        elif choice == '7':
            generate_daily_report()
        elif choice == '8':
            bus_management_menu()
        elif choice == '9':
            route_management_menu()
        elif choice == '10':
            print(f"{C.GREEN}Goodbye!{C.END}")
            break
        
        else:
            print(f"{C.YELLOW}Invalid option.{C.END}")
            press_enter_to_continue()


def main():
    global OPERATOR_NAME
    # Login with masked password
    attempts = 3
    while attempts > 0:
        clear_screen()
        try:
            fig = Figlet(font='slant')
            print(f"{C.GREEN}{fig.renderText('TNSTC Login')}{C.END}")
        except Exception:
            print("=== TNSTC LOGIN ===")
        username = input("Login: ").strip()
        password = getpass.getpass("Password: ")
        if username == 'admin' and password == 'admin@123':
            print(f"{C.GREEN}Login successful.{C.END}")
            time.sleep(0.8)
            break
        attempts -= 1
        print(f"{C.RED}Invalid credentials. Attempts left: {attempts}{C.END}")
        time.sleep(1.2)
    else:
        print(f"{C.RED}Too many failed attempts. Exiting.{C.END}")
        return

    OPERATOR_NAME = input("Enter Operator Name: ").strip() or "Operator"
    add_history("Operator logged in")
    main_menu()


if __name__ == '__main__':
    main()


