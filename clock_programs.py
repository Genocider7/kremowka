from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from check_duplicates import main as Check_duplicates
from prepare_files import main as Prepare_files

def main():
    scheduler = BlockingScheduler()
    scheduler.add_job(Check_duplicates, CronTrigger(minute='*/10'))
    scheduler.add_job(Prepare_files, CronTrigger(minute='2-59/10'))
    scheduler.start()

if __name__ == '__main__':
    main()