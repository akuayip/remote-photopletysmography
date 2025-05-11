# main_dashboard.py

from rppg_processor import RPPGProcessor
from respirasi_processor import RespirasiProcessor
from visualization import SignalDashboard

def main():
    rppg = RPPGProcessor()
    resp = RespirasiProcessor()
    dashboard = SignalDashboard(rppg, resp)
    dashboard.run()

if __name__ == "__main__":
    main()
