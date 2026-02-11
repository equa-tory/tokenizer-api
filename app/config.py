from datetime import time as dt_time

# TODO: add configuration via teacher's app (api?)
START_TIME = dt_time(16, 0) # (def: 16:00)
END_TIME = dt_time(18, 0) # (def: 18:00)
SLOT_INTERVAL = 10  # minutes (def: 10)
DEBT_WEEKDAY = 4 # friday (def: 4)
DEBT_COOLDOWN = 0  # minutes (def: 15)
MAX_TICKETS = 9999 # (def: 9999)
DEBT_BOOK_WINDOW = 20 # minutes (--++--+--) (def: 20)