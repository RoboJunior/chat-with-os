from crontab import CronTab
import getpass
import os


class Schedular:
    def __init__(self) -> None:
        self._user_name = getpass.getuser()
        self._python_version = os.popen("which python").read().strip()
        self._script_path = "/Users/jeyaramanr/Documents/pc-resource-monitor/duck_db.py"

    def is_numeric_string(self, s):
        if s.startswith("-"):
            return s[1:].isdigit()
        return s.isdigit()

    def is_valid_crontab_value(self, s):
        return all(self.is_numeric_string(s) or c == "*" for c in s)

    def _validate_crontab(self, time_data: str) -> bool:
        """Validate crontab time format"""
        crontab_format = time_data.split()
        if not isinstance(time_data, str):
            raise ValueError("Time should be a valid string")

        if not len(crontab_format) == 5:
            raise ValueError("Enter a valid crontab time format")

        if not all(self.is_valid_crontab_value(item) for item in crontab_format):
            raise ValueError("Crontab cannot have other string values except '*' ")

        if self.is_numeric_string(crontab_format[0]):
            minutes = int(crontab_format[0])
            if not (0 <= minutes <= 59):
                raise ValueError("Minutes must be between 0 and 59")

        if self.is_numeric_string(crontab_format[1]):
            if not (0 <= int(crontab_format[1]) <= 23):
                raise ValueError("Hours must be between 0 and 23")

        if self.is_numeric_string(crontab_format[2]):
            if not (1 <= int(crontab_format[2]) <= 31):
                raise ValueError("Day must be between 1 and 31")

        if self.is_numeric_string(crontab_format[3]):
            if not (1 <= int(crontab_format[3]) <= 12):
                raise ValueError("Month must be between 1 and 12")

        if self.is_numeric_string(crontab_format[4]):
            if not (1 <= int(crontab_format[4]) <= 6):
                raise ValueError("Day of the week must between 1 and 6")

    def _remove_existing_jobs(self, job_schedular):
        """Remove existing jobs with the same command"""
        for job in job_schedular:
            if job.command == f"{self._python_version} {self._script_path}":
                job_schedular.remove(job)
        job_schedular.write()

    def _remove_cron_jobs(self, job_schedular):
        """Remove cron jobs running in the background"""
        for job in job_schedular:
            if job.command == f"{self._python_version} {self._script_path}":
                job_schedular.remove(job)
        job_schedular.write()

    def _find_job(self, job_schedular):
        """Find a job with the specific command"""
        for job in job_schedular:
            if job.command == f"{self._python_version} {self._script_path}":
                return job
        return None

    def schedule_cron_job(self, time_data: str):
        """Schedule a cron job"""
        self._validate_crontab(time_data)
        job_schedular = CronTab(user=self._user_name)
        # Remove existing jobs with the same command
        self._remove_existing_jobs(job_schedular)
        job = job_schedular.new(command=f"{self._python_version} {self._script_path}")
        job.setall(time_data)
        job_schedular.write()

    def remove_cron_job(self):
        """Remove a cron job"""
        job_schedular = CronTab(user=self._user_name)
        job = self._find_job(job_schedular)
        if job:
            self._remove_cron_jobs(job_schedular)
        else:
            raise ValueError("Job not found")

    def reschedule_cron_job(self, new_time_data: str):
        """Reschedule an existing cron job"""
        self._validate_crontab(new_time_data)
        job_schedular = CronTab(user=self._user_name)
        job = self._find_job(job_schedular)
        if job:
            job.setall(new_time_data)
            job_schedular.write()
        else:
            raise ValueError("No job found with the specified old schedule")
