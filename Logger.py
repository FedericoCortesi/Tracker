import pandas as pd
from datetime import datetime
import time
import threading
import os

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

        print(f"Study session started at {self.start_time.strftime('%H:%M:%S')}")
        
        # Call function to upadate timer 
        self._display_timer()


    def _display_timer(self):
        def update_timer():
            while self.is_studying:
                current_time = datetime.now()
                elapsed = current_time - self.start_time
                total_seconds = int(elapsed.total_seconds())
                hours, remainder = divmod(total_seconds, 3600)
                minutes, seconds = divmod(remainder, 60)

                # Clear the line and print the elapsed time
                print(f"\r{' ' * 30}\rStudying for: {hours:02}:{minutes:02}:{seconds:02}", end="")
                time.sleep(1)

        timer_thread = threading.Thread(target=update_timer, daemon=True)
        timer_thread.start()


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




