import pandas as pd
from datetime import datetime
import time
import threading
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import seaborn as sns


from utils import *

class StudyTracker:
    def __init__(self, path:str="./Logs/study_sessions.csv") -> None:
        # Read df with sessions
        self.path = path
        self.data = pd.read_csv(self.path) 
        
        # Define is studying
        self.is_studying : bool = None
        
        # Validation
        self.valid_subjects = ["PIF", "Valuation", "DIV", "CBEL", "Thesis"]
        self.valid_sessions = ["Morning", "Afternoon", "Evening"]


    def start_session(self, subject: str = None, session:str=None, begin_time=None):
        if self.is_studying != True:
            # Set Studying to True 
            self.is_studying = True
                    
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
            
            print(f"\nStudy session started at {self.start_time.strftime('%H:%M:%S')}")
            
            # Call function to upadate timer 
            self._display_timer()
        
        else:
            print(f"Session already started at {self.start_time.strftime('%H:%M:%S')}")


    def _display_timer(self):
        def update_timer():
            # retrieve time passsed today
            out = self._today_stats()
            time_today = out[1]
            pause_now = self.start_time - out[0].iloc[-1,2]
            pause_today = out[2]
            pause_today = pause_today + pause_now

            while self.is_studying:
                # Format the elapsed time
                current_time = datetime.now()
                elapsed = current_time - self.start_time
                total_seconds = int(elapsed.total_seconds())
                hours, remainder = divmod(total_seconds, 3600)
                minutes, seconds = divmod(remainder, 60)

                
                # Print total time today
                time_studying = time_today + elapsed
                total_seconds_studied = int(time_studying.total_seconds())
                hours_studied, remainder_studied = divmod(total_seconds_studied, 3600)
                minutes_studied, seconds_studied = divmod(remainder_studied, 60)

                # Print Pauses today
                total_seconds_pause = int(pause_today.total_seconds())
                hours_pause, remainder_pause = divmod(total_seconds_pause, 3600)
                minutes_pause, seconds_pause = divmod(remainder_pause, 60)


                # Print total time today
                mess_1 = f"Studying for: {hours:02}:{minutes:02}:{seconds:02}"
                mess_2 = f"Time spent studying today: {hours_studied:02}:{minutes_studied:02}:{seconds_studied:02}"
                mess_3 = f"Total pauses today: {hours_pause:02}:{minutes_pause:02}:{seconds_pause:02}"
                print(f"\r{mess_1} | {mess_2} | {mess_3}", end="")

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
            return

        # Compute total time
        total_time = (self.end_time - self.start_time)

        # Get the date
        date = self.start_time.date()

        # Format session data
        session_data = {"day":date, "start_time": self.start_time, "end_time": self.end_time,
                        "total_time": total_time, "session": self.session,"subject": self.subject}

        # save 
        self.save(session_data)


    def save(self, data: dict = None):
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


        # total time 
        total_time = (self.end_time - self.start_time)

        # get today stats to print
        _, studied, total_pauses, last_pause = self._today_stats()

        # print message
        mess_1 = f"Studied for: {format_timedelta_hms(total_time)}"
        mess_2 = f"Time studied today: {format_timedelta_hms(studied)}"
        mess_3 = f"Last pause: {format_timedelta_hms(last_pause)}"        
        mess_4 = f"Total pauses: {format_timedelta_hms(total_pauses)}"        
        eff = studied.total_seconds() / (
            studied.total_seconds() + total_pauses.total_seconds()
        )        
        mess_5 = f"Efficiency: {eff:.2f}"
        print(f"{mess_1}\n{mess_2} | {mess_3} | {mess_4} | {mess_5}")



    def _open_log(self):
        """Open the log file parsing the dates"""
        df_log = pd.read_csv("./Logs/study_sessions.csv", index_col=0, parse_dates=['start_time', 'end_time'])
        df_log['total_time'] = pd.to_timedelta(df_log['total_time'])
        return df_log


    def _today_stats(self):
        """Get the stats for today"""
        df_log = self._open_log()

        
        # filter 
        today = datetime.now().date().strftime("%Y-%m-%d")
        df_today = df_log[df_log['day'] == today]
        
        # if not first time of the day
        if len(df_today) != 0:        

            # get total time studied
            total_studied = df_today["total_time"].sum()

            # compute total pauses
            total_pauses = max(df_today["end_time"]) - min(df_today["start_time"]) - total_studied

            # last begin - penultimate end
            try:
                last_pause = df_today.iloc[-1,1] - df_today.iloc[-2,2]
            
            except IndexError:
                last_pause = timedelta(0)

        else:
            total_studied = timedelta(0)
            total_pauses = timedelta(0)
            last_pause = timedelta(0)
        
        return df_today, total_studied, total_pauses, last_pause
    
    def plot_all_sessions(self):
        # Setting plot context 
        sns.set_context("notebook")  
        sns.set_style("darkgrid")

        df_ex = self._open_log()

        # Computing total seconds
        df_ex['total_time_seconds'] = df_ex['total_time'].dt.total_seconds()

        # Create the plot
        plt.figure(figsize=(10, 6))
        sns.lineplot(data=df_ex, x=df_ex.index, y="total_time_seconds")

        # Format the y-axis to show time in HH:MM:SS
        formatter = FuncFormatter(seconds_to_hms)
        plt.gca().yaxis.set_major_formatter(formatter)

        plt.xlabel('Index')
        plt.ylabel('Total Time (HH:MM:SS)')
        plt.title('Time per Session')
        plt.show()


    def plot_days_total(self, figsize:tuple=(15,9)):
        # Setting plot context 
        sns.set_context("notebook")  
        sns.set_style("darkgrid")

        df_ex = self._open_log()

        # Aggregate days
        df_grouped = df_ex.groupby(["day"]).agg({"total_time": "sum"})

        # Find time for each 
        df_grouped['total_time_seconds'] = df_grouped['total_time'].dt.total_seconds()

        # Create the plot
        plt.figure(figsize=figsize)
        sns.barplot(data=df_grouped, x=df_grouped.index, y="total_time_seconds")

        # Format the y-axis to show time in HH:MM:SS
        formatter = FuncFormatter(seconds_to_hms)
        plt.gca().yaxis.set_major_formatter(formatter)

        plt.xlabel('Day')
        plt.ylabel('Total Time (HH:MM:SS)')
        plt.title('Total Time Spent Studying')
        plt.show()


    def display_time_by(self, by="subject"):

        df = self._open_log()

        # Group by subject and sum the total_time
        total_time_by_subject = df.groupby(by)['total_time'].sum()

        # Optionally, format the total time as HH:MM:SS
        total_time_by_subject = total_time_by_subject.apply(
            lambda x: f"{int(x.total_seconds() // 3600):02}:{int((x.total_seconds() % 3600) // 60):02}:{int(x.total_seconds() % 60):02}"
        )

        print(total_time_by_subject)


