#!/usr/bin/env python3
"""OMNIHACK MISSION CONTROL — launcher.

Usage:
    python run_mission_control.py            # serves on 0.0.0.0:7860
    OMNI_PORT=8080 python run_mission_control.py
"""

from mission_control.app import main

if __name__ == "__main__":
    main()
