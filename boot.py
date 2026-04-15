# boot.py — CircuitPython boot configuration
# Runs before code.py. Keep minimal.
# Uncomment the line below to disable USB drive (read-only mode for deployment).

import storage
# storage.disable_usb_drive()   # Uncomment for production; re-enable by holding button at boot
