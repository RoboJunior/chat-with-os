import sqlite3
import contextlib
import platform
import cpuinfo
import socket
import re
import uuid
import psutil
from datetime import datetime
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
# Path to store the db created
DB_PATH = os.path.join(script_dir, "os_data.db")


class Information_Collector:
    def __init__(self) -> None:
        self._cpu_freq = psutil.cpu_freq()
        self._svem = psutil.virtual_memory()
        self._swap = psutil.swap_memory()
        self._sys_id = ":".join(re.findall("..", "%012x" % uuid.getnode()))

    def _create_system_information(self):
        with contextlib.closing(sqlite3.connect(DB_PATH)) as conn:
            with conn as cur:
                cur.execute("""
                CREATE TABLE IF NOT EXISTS system_information
                (Mac_ID TEXT PRIMARY KEY, System TEXT, Node_Name TEXT, Machine TEXT, 
                Processor TEXT, Processor_Model TEXT, Physcial_cores INT, 
                Total_cores INT, Max_Frequency REAL, Min_Frequency REAL, 
                Total_Memory REAL, Total_Swap_Memory REAL, Ip_Address TEXT);
                """)
                conn.commit()

    def get_size(self, bytes, suffix="B"):
        """
        Scale bytes to its proper format
        e.g:
            1253656 => '1.20MB'
            1253656678 => '1.17GB'
        """
        factor = 1024
        for unit in ["", "K", "M", "G", "T", "P"]:
            if bytes < factor:
                return f"{bytes:.2f}{unit}{suffix}"
            bytes /= factor

    def insert_system_information(self):
        self._create_system_information()
        uname = platform.uname()
        with contextlib.closing(sqlite3.connect(DB_PATH)) as conn:
            with conn as cur:
                exists = cur.execute(
                    "SELECT 1 FROM system_information WHERE Mac_ID = ?", (self._sys_id,)
                ).fetchone()
                if not exists:
                    cur.execute(
                        """
                    INSERT INTO system_information
                    (Mac_ID, System, Node_Name, Machine, Processor, 
                    Processor_Model, Physcial_cores,  
                    Total_cores, Max_Frequency, Min_Frequency, 
                    Total_Memory, Total_Swap_Memory, Ip_Address)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            self._sys_id,
                            uname.system,
                            uname.node,
                            uname.machine,
                            uname.processor,
                            cpuinfo.get_cpu_info().get("brand_raw", "Unknown"),
                            psutil.cpu_count(logical=False) or 0,
                            psutil.cpu_count(logical=True) or 0,
                            f"{self._cpu_freq.max:.2f}Mhz"
                            if self._cpu_freq
                            else "0.00Mhz",
                            f"{self._cpu_freq.min:.2f}Mhz"
                            if self._cpu_freq
                            else "0.00Mhz",
                            self.get_size(self._svem.total) if self._svem else "0B",
                            self.get_size(self._swap.total) if self._swap else "0B",
                            socket.gethostbyname(socket.gethostname()),
                        ),
                    )
                    conn.commit()

    def _create_cpu_usage(self):
        cpu_columns = []
        for i, _ in enumerate(psutil.cpu_percent(percpu=True, interval=1)):
            cpu_columns.append((f"Core_{i}", "REAL"))
        self._columns_definition = ", ".join(
            [f"{name} {dtype}" for name, dtype in cpu_columns]
        )
        self._column_names = ", ".join([f"{name}" for name, _ in cpu_columns])
        with contextlib.closing(sqlite3.connect(DB_PATH)) as conn:
            with conn as cur:
                cur.execute(f"""
                    CREATE TABLE IF NOT EXISTS cpu_usage 
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                    Current_Frequency REAL, {self._columns_definition}, Total_Cpu_Usage REAL, 
                    Extracted_Time TEXT DEFAULT (datetime('now')), Sys_ID TEXT, 
                    FOREIGN KEY (Sys_ID) REFERENCES system_information (Mac_ID))
                """)
                conn.commit()

    def _get_process_disk_usage(self):
        disk_usage = {}
        for proc in psutil.process_iter(["pid", "name"]):
            try:
                process = psutil.Process(proc.info["pid"])
                open_files = process.open_files()
                total_disk_usage = 0
                for file in open_files:
                    file_path = file.path
                    total_disk_usage += os.path.getsize(file_path)
                disk_usage[process.name()] = total_disk_usage
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        return disk_usage

    def _create_ram_usage(self):
        with contextlib.closing(sqlite3.connect(DB_PATH)) as conn:
            with conn as cur:
                cur.execute("""
                CREATE TABLE IF NOT EXISTS ram_usage 
                (id INTEGER PRIMARY KEY AUTOINCREMENT,
                Free REAL, Used REAL, Percentage REAL,
                Swap_Free REAL, Swap_Used REAL, Swap_Percentage REAL, 
                Extracted_Time TEXT DEFAULT (datetime('now')), Sys_ID TEXT,
                FOREIGN KEY (Sys_ID) REFERENCES system_information (Mac_ID))
                """)
                conn.commit()

    def _create_disk_usage(self):
        with contextlib.closing(sqlite3.connect(DB_PATH)) as conn:
            with conn as cur:
                cur.execute("""
                CREATE TABLE IF NOT EXISTS disk_usage
                (id INTEGER PRIMARY KEY AUTOINCREMENT,
                Device TEXT, Mount_Point TEXT, File_System_Type TEXT ,
                Total_Size REAL, Used REAL,
                Free REAL, Percentage REAL, 
                Extracted_Time TEXT DEFAULT (datetime('now')), Sys_ID TEXT,
                FOREIGN KEY (Sys_ID) REFERENCES system_information (Mac_ID))
                """)
                conn.commit()

    def _create_total_disk_usage(self):
        with contextlib.closing(sqlite3.connect(DB_PATH)) as conn:
            with conn as cur:
                cur.execute("""
                CREATE TABLE IF NOT EXISTS total_disk_usage
                (id INTEGER PRIMARY KEY AUTOINCREMENT,
                Total_Read REAL, Total_Write REAL, Boot_Time TEXT,
                Extracted_Time TEXT DEFAULT (datetime('now')), Sys_ID TEXT,
                FOREIGN KEY (Sys_ID) REFERENCES system_information (Mac_ID))
                """)
                conn.commit()

    def _create_task_manager(self):
        with contextlib.closing(sqlite3.connect(DB_PATH)) as conn:
            with conn as cur:
                cur.execute("""
                CREATE TABLE IF NOT EXISTS task_manager (
                Process_Name TEXT, PID INTEGER, CPU_Usage REAL, Memory_Usage REAL,
                Memory_Percentage REAL, Disk_Usage INTEGER, 
                Network_Sent REAL, Network_Received REAL,
                Extracted_Time TEXT DEFAULT (datetime('now')), Sys_ID TEXT,
                FOREIGN KEY (Sys_ID) REFERENCES system_information (Mac_ID))
                """)
                conn.commit()

    def _collect_cpu_data(self):
        cpu_info = {}
        for i, percentage in enumerate(psutil.cpu_percent(percpu=True, interval=1)):
            cpu_info[f"Core_{i}"] = f"{percentage}%"
        return cpu_info

    def cpu_usage(self):
        self._create_cpu_usage()
        cpu_info = self._collect_cpu_data()
        values = len(self._columns_definition.split(",")) * "?,"
        with contextlib.closing(sqlite3.connect(DB_PATH)) as conn:
            with conn as cur:
                sql = f"""
                    INSERT INTO cpu_usage (Current_Frequency, {self._column_names}, Total_Cpu_Usage, Sys_ID) 
                    VALUES (?, {', '.join(['?'] * len(cpu_info))}, ?, ?)
                """
                values = (
                    f"{self._cpu_freq.current:.2f}Mhz",
                    *cpu_info.values(),
                    f"{psutil.cpu_percent()}%",
                    self._sys_id,
                )
                cur.execute(sql, values)
                conn.commit()

    def ram_usage(self):
        self._create_ram_usage()
        with contextlib.closing(sqlite3.connect(DB_PATH)) as conn:
            with conn as cur:
                cur.execute(
                    """
                INSERT INTO ram_usage (Free , Used , Percentage ,
                Swap_Free , Swap_Used , Swap_Percentage , Sys_ID) VALUES 
                (?, ?, ?, ?, ?, ?, ?)""",
                    (
                        f"{self.get_size(self._svem.available)}",
                        f"{self.get_size(self._svem.used)}",
                        f"{self._svem.percent}%",
                        f"{self.get_size(self._swap.free)}",
                        f"{self.get_size(self._swap.used)}",
                        f"{self._swap.percent}%",
                        self._sys_id,
                    ),
                )
                conn.commit()

    def _collect_disk_data(self):
        disk_data = []
        partitions = psutil.disk_partitions()
        for partition in partitions:
            disk_dict = {}
            disk_dict["device"] = partition.device
            disk_dict["mountpoint"] = partition.mountpoint
            disk_dict["filesystem"] = partition.fstype
            try:
                usage = psutil.disk_usage(partition.mountpoint)
            except PermissionError:
                continue
            disk_dict["total"] = self.get_size(usage.total)
            disk_dict["used"] = self.get_size(usage.used)
            disk_dict["free"] = self.get_size(usage.free)
            disk_dict["percent"] = f"{usage.percent}%"
            disk_data.append(disk_dict)
        return disk_data

    def disk_usage(self):
        self._create_disk_usage()
        disk_datas = self._collect_disk_data()
        for disk_data in disk_datas:
            with contextlib.closing(sqlite3.connect(DB_PATH)) as conn:
                with conn as cur:
                    sql = """
                    INSERT INTO disk_usage (Device , Mount_Point, 
                    File_System_Type, Total_Size , Used,
                    Free , Percentage, Sys_ID ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)"""
                    values = (*disk_data.values(), self._sys_id)
                    cur.execute(sql, values)
                    conn.commit()

    def total_disk_usage(self):
        self._create_total_disk_usage()
        disk_io = psutil.disk_io_counters()
        boot_time_timestamp = psutil.boot_time()
        bt = datetime.fromtimestamp(boot_time_timestamp)
        boot_time = f"{bt.year}/{bt.month}/{bt.day} {bt.hour}:{bt.minute}:{bt.second}"
        with contextlib.closing(sqlite3.connect(DB_PATH)) as conn:
            with conn as cur:
                exists = cur.execute(
                    "SELECT 1 FROM total_disk_usage WHERE Boot_Time = ?", (boot_time,)
                ).fetchone()
                if not exists:
                    cur.execute(
                        """INSERT INTO total_disk_usage (Total_Read, 
                    Total_Write, Boot_Time, Sys_ID) VALUES (?, ?, ?, ?)""",
                        (
                            self.get_size(disk_io.read_bytes),
                            self.get_size(disk_io.write_bytes),
                            boot_time,
                            self._sys_id,
                        ),
                    )
                    conn.commit()

    def task_manager(self):
        self._create_task_manager()
        for proc in psutil.process_iter(attrs=["pid", "name"]):
            try:
                # Fetch process info
                process_name = proc.info["name"]
                process_id = proc.info["pid"]
                process = psutil.Process(process_id)

                # CPU usage percentage
                cpu_usage = process.cpu_percent(interval=0.1)

                # Memory (RAM) usage in bytes and percentage
                mem_info = process.memory_info()
                mem_usage = mem_info.rss  # Resident Set Size (physical memory)
                mem_usage_percent = process.memory_percent()

                # Disk usage (Read/Write)
                disk_usage = self._get_process_disk_usage().get(process_name, 0)

                # Network usage (Sent/Received) - system-wide stats
                # Individual process network stats are not available
                net_io = psutil.net_io_counters(pernic=False)
                bytes_sent = net_io.bytes_sent
                bytes_received = net_io.bytes_recv

                with contextlib.closing(sqlite3.connect(DB_PATH)) as conn:
                    with conn as cur:
                        cur.execute(
                            """INSERT INTO task_manager (
                        Process_Name, PID, CPU_Usage, Memory_Usage,
                        Memory_Percentage, Disk_Usage, 
                        Network_Sent, Network_Received, Sys_ID)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                            (
                                process_name,
                                process_id,
                                f"{cpu_usage}%",
                                f"{mem_usage / (1024 ** 2):.2f} MB%",
                                f"{mem_usage_percent:.2f}%",
                                f"{disk_usage} bytes",
                                f"{bytes_sent / (1024 ** 2):.2f} MB",
                                f"{bytes_received / (1024 ** 2):.2f} MB",
                                self._sys_id,
                            ),
                        )
                        conn.commit()
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                # Skip processes that no longer exist or cannot be accessed
                continue


if __name__ == "__main__":
    # Creating the instance of the Information Collector class
    j = Information_Collector()
    # Extraction all the system information
    j.insert_system_information()
    # Extracting Cpu Usage
    j.cpu_usage()
    # Extracting Ram Usage
    j.ram_usage()
    # Extracting Disk Usage
    j.disk_usage()
    # Extracting the total disk usage
    j.total_disk_usage()
    # Extracting all the process and usage
    j.task_manager()
