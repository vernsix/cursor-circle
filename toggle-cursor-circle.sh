#!/bin/bash
if pgrep -f "cursor_circle.py" > /dev/null; then
    pkill -f "cursor_circle.py"
    # uncomment following line for desktop notification popup
    # notify-send "Cursor Circle" "Disabled" -i input-mouse
else
    python3 ~/cursor_circle.py &
    # uncomment following line for desktop notification popup
    #notify-send "Cursor Circle" "Enabled" -i input-mouse
fi
