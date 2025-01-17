import pandas as pd
from datetime import datetime
import time
import threading

class Logger:
    def __init__(self, path:str="./Logs/study_sessions.csv") -> None:
        self.path = path
        self.data = pd.read_csv(self.path) 
        self.valid_subjects = ["MFI", "Valuation", "IB"]
        self.valid_sessions = ["Morning", "Afternoon", "Evening"]

        print(f"\nThe available subjects are: {self.valid_subjects}\n")
        print(f"\nThe available sessions are: {self.valid_sessions}\n")

    def start_session(self, subject: str = None, session:str=None, begin_time=None):
        # Validate subject and session
        assert subject is not None, "Input a Subject!"
        self.subject = subject
        if self.subject not in self.valid_subjects:
            raise ValueError(f"{self.subject} is not a valid subject. Please choose from: {self.valid_subjects}")

        assert session is not None, "Input a Session!"
        self.session = session
        if self.session not in self.valid_sessions:
            raise ValueError(f"{self.subject} is not a valid subject. Please choose from: {self.valid_sessions}")
        
        # Capture the start time
        self.start_time = datetime.now() if begin_time == None else begin_time
        
        # Set Studying to True 
        self.is_studying = True

        print(f"\nStudy session started at {self.start_time.strftime('%H:%M:%S')}")
        
        # Call function to upadate timer 
        self._display_timer()


    def _display_timer(self):
        def update_timer():
            # retrieve time passsed today
            _, time_today = self._today_stats()

            while self.is_studying:
                # Format the elapsed time
                current_time = datetime.now()
                elapsed = current_time - self.start_time
                total_seconds = int(elapsed.total_seconds())
                hours, remainder = divmod(total_seconds, 3600)
                minutes, seconds = divmod(remainder, 60)

                
                # Print total time today
                time_studying = time_today + elapsed
                total_seconds_today = int(time_studying.total_seconds())
                hours_today, remainder_today = divmod(total_seconds_today, 3600)
                minutes_today, seconds_today = divmod(remainder_today, 60)

                # Print total time today
                print(f"\r{' ' * 30}\rStudying for: {hours:02}:{minutes:02}:{seconds:02}\tTime spent studying today: {hours_today:02}:{minutes_today:02}:{seconds_today:02}", end="")

                # Wait until next iteration
                time.sleep(1)

        timer_thread = threading.Thread(target=update_timer, daemon=True)
        timer_thread.start()

    def abort_session(self):
        if self.is_studying == True:
            self.is_studying = False
            print(f"Study session of {self.start_time.strftime('%H:%M:%S')} aborted")
        else:
            print(f"Study session of {self.start_time.strftime('%H:%M:%S')} already aborted")


    def end_session(self):
        if self.is_studying == True:
            self.end_time = datetime.now()
            self.is_studying = False
            print(f"Study session ended at {self.end_time.strftime('%H:%M:%S')}")
        else:
            print(f"Session already ended at: {self.end_time.strftime('%H:%M:%S')}")


        # Compute total time and print message
        total_time = (self.end_time - self.start_time)


        # Get the date
        date = self.start_time.date()

        # Format session data
        session_data = {"day":date, "start_time": self.start_time, "end_time": self.end_time,
                        "total_time": total_time, "session": self.session,"subject": self.subject}
        
        print(session_data)

        # Save df
        self._save(data=session_data)
        

    def _save(self, data: dict = None):
        # Build df
        df_cache = pd.DataFrame(data, index=[0])

        # Convert to datetime
        df_cache['total_time'] = pd.to_timedelta(df_cache['total_time'])
        df_cache['start_time'] = pd.to_datetime(df_cache['start_time'])
        df_cache['end_time'] = pd.to_datetime(df_cache['end_time'])

        # Read df
        df_study = pd.read_csv("./Logs/study_sessions.csv", index_col=0)

        # concat and save
        df_study = pd.concat([df_study, df_cache], axis=0, ignore_index=False)
        df_study.reset_index(drop=True, inplace=True)
        df_study.to_csv("./Logs/study_sessions.csv", index=True)        
        
        print(f"File saved at: ./Logs/study_sessions.csv")


    def _open_log(self):
        """Open the log file parsing the dates"""
        df_log = pd.read_csv("./Logs/study_sessions.csv", index_col=0, parse_dates=['start_time', 'end_time'])
        df_log['total_time'] = pd.to_timedelta(df_log['total_time'])
        return df_log


    def _today_stats(self):
        """Get the stats for today"""
        df_log = self._open_log()
        today = datetime.now().date().strftime("%Y-%m-%d")
        df_today = df_log[df_log['day'] == today]

        time_today = df_today["total_time"].sum()
        
        return df_today, time_today