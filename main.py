#!/usr/bin/env python3
import argparse
import sys
import time
import signal
from datetime import datetime
import os
import pandas as pd
import threading

# Import the Logger class from the provided file
from study_tracker import StudyTracker
from utils import format_timedelta_hms

# Global variables to track state
study_logger = None
session_active = False
exit_app = False

def setup_environment():
    """Set up the necessary directory structure and files"""
    # Create Logs directory if it doesn't exist
    if not os.path.exists("./Logs"):
        os.makedirs("./Logs")
    
    # Create study_sessions.csv if it doesn't exist
    if not os.path.exists("./Logs/study_sessions.csv"):
        # Create an empty DataFrame with the required columns
        df = pd.DataFrame(columns=["day", "start_time", "end_time", "total_time", "session", "subject"])
        df.to_csv("./Logs/study_sessions.csv", index=True)
        print("Created new study sessions log file.")

def signal_handler(sig, frame):
    """Handle interrupt signal (Ctrl+C)"""
    global study_logger, session_active, exit_app
    
    if session_active:
        print("\nEnding study session...")
        study_logger.end_session()
        session_active = False
    
    exit_app = True
    sys.exit(0)

def session_controller():
    """Monitor for commands during a study session"""
    global study_logger, session_active, exit_app
    
    print("\n", "="*25, "Session Control", "="*25, "\n")
    print("Commands: 'end' to end session, 'abort' to abort without saving")
    #print("Or press Ctrl+C to end the session")
    
    while session_active and not exit_app:
        try:
            command = input("> ").strip().lower()
            
            if command == "end":
                study_logger.end_session()
                session_active = False
                break
            elif command == "abort":
                study_logger.abort_session()
                session_active = False
                break
            elif command == "q":
                session_active = False
                exit_app = True
                break
            elif command:
                print("Unknown command. Use 'end' or 'abort'")
        except EOFError:
            # Handle EOF (Ctrl+D on Unix)
            print("\nEnding session...")
            study_logger.end_session()
            session_active = False
            break

def main():
    """Main function to handle CLI arguments and run the appropriate logger functions"""
    global study_logger, session_active, exit_app
    
    # Set up environment
    setup_environment()
    
    # Register signal handler for Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)
    
    # Create the main parser
    parser = argparse.ArgumentParser(description="Study Session Logger CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Start command
    start_parser = subparsers.add_parser("start", help="Start a new study session")
    start_parser.add_argument("-s", "--subject", required=True, help="Subject you are studying")
    start_parser.add_argument("-p", "--period", required=True, help="Study period (Morning/Afternoon/Evening)")
    
    # End command
    subparsers.add_parser("end", help="End the current study session")
    
    # Abort command
    subparsers.add_parser("abort", help="Abort the current study session without logging it")
    
    # Status command
    subparsers.add_parser("status", help="Check if a study session is currently active")
    
    # Stats command
    stats_parser = subparsers.add_parser("stats", help="Show statistics")
    stats_parser.add_argument("--today", action="store_true", help="Show today's statistics")
    stats_parser.add_argument("--by", choices=["subject", "session", "day"], default="subject", 
                             help="Group statistics by subject, session, or day period")
    
    # Plot command
    plot_parser = subparsers.add_parser("plot", help="Generate plots of study data")
    plot_parser.add_argument("--sessions", action="store_true", help="Plot all study sessions")
    plot_parser.add_argument("--days", action="store_true", help="Plot total study time by day")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Create logger instance
    study_logger = StudyTracker()
    
    # Check for existing session file
    session_file = "./.session_active"
    
    # Process commands
    if args.command == "start":
        # Check if a session is already running
        if os.path.exists(session_file):
            with open(session_file, 'r') as f:
                session_info = f.read().strip().split(',')
                if len(session_info) >= 2:
                    subject, period = session_info[0], session_info[1]
                    print(f"A session is already active for subject '{subject}' ({period}).")
                    print("End or abort it before starting a new one.")
                    return
        
        try:
            study_logger.start_session(subject=args.subject, session=args.period)
            session_active = True
            
            # Create session marker file
            with open(session_file, 'w') as f:
                f.write(f"{args.subject},{args.period},{datetime.now().isoformat()}")
            
            # Start thread for session controller
            controller_thread = threading.Thread(target=session_controller)
            controller_thread.daemon = True
            controller_thread.start()
            
            # Keep the main thread running
            while session_active and not exit_app:
                time.sleep(0.5)
            
            # Clean up session marker file
            if os.path.exists(session_file):
                os.remove(session_file)
                
        except ValueError as e:
            print(f"Error: {e}")
        except AssertionError as e:
            print(f"Error: {e}")
    
    elif args.command == "end":
        if os.path.exists(session_file):
            study_logger.end_session()
            os.remove(session_file)
        else:
            print("No active study session found.")
    
    elif args.command == "abort":
        if os.path.exists(session_file):
            study_logger.abort_session()
            os.remove(session_file)
        else:
            print("No active study session found.")
    
    elif args.command == "status":
        if os.path.exists(session_file):
            with open(session_file, 'r') as f:
                session_info = f.read().strip().split(',')
                if len(session_info) >= 3:
                    subject, period, start_time = session_info[0], session_info[1], session_info[2]
                    start_dt = datetime.fromisoformat(start_time)
                    elapsed = datetime.now() - start_dt
                    hours, remainder = divmod(int(elapsed.total_seconds()), 3600)
                    minutes, seconds = divmod(remainder, 60)
                    
                    print(f"Active session: {subject} ({period})")
                    print(f"Started at: {start_dt.strftime('%H:%M:%S')}")
                    print(f"Elapsed time: {hours:02}:{minutes:02}:{seconds:02}")
                else:
                    print("Session active but details unavailable.")
        else:
            print("No active study session.")
    
    elif args.command == "stats":
        if args.today:
            today_data, total_time, total_pauses, last_pause = study_logger._today_stats()
            print(f"\nToday's Statistics:")
            print(f"Total time studied: {format_timedelta_hms(total_time)}")
            print(f"Total pauses: {format_timedelta_hms(total_pauses)}")
            print(f"Last pause duration: {format_timedelta_hms(last_pause)}")
            if total_time.total_seconds() > 0 and total_pauses.total_seconds() > 0:
                efficiency = total_time.total_seconds() / (total_time.total_seconds() + total_pauses.total_seconds())
                print(f"Efficiency: {efficiency:.2f}")
            print("\nToday's sessions:")
            if len(today_data) > 0:
                print(today_data)
            else:
                print("No study sessions recorded today.")
        else:
            study_logger.display_time_by(by=args.by)
    
    elif args.command == "plot":
        if args.sessions:
            study_logger.plot_all_sessions()
        elif args.days:
            study_logger.plot_days_total()
        else:
            print("Please specify a plot type: --sessions or --days")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()