from datetime import time as dt_time

START_TIME = dt_time(16, 0)
END_TIME = dt_time(18, 0)
SLOT_INTERVAL = 10  # minutes
DEBT_WEEKDAY = 4 # friday
DEBT_COOLDOWN = 15  # minutes (def: 15)
MAX_TICKETS = 9999