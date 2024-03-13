import os
import subprocess
import time
from configparser import ConfigParser
from datetime import datetime, timedelta

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

script_dir = os.path.dirname(os.path.realpath(__file__))
input_dir_name = "to_compress_video"
input_dir_path = os.path.join(script_dir, input_dir_name)
config_filepath = os.path.join(script_dir, "config.ini")

config = ConfigParser()

if os.path.exists(config_filepath):
    config.read(config_filepath)
else:
    if not os.path.exists(input_dir_path):
        os.makedirs(input_dir_path)

    config["Settings"] = {"folder_to_watch": input_dir_path}
    with open(config_filepath, "w") as config_file:
        config.write(config_file)

os.startfile(input_dir_path)
folder_to_watch = config.get("Settings", "folder_to_watch")
result_string_array = []


def get_file_size(path: str) -> int:
    return os.path.getsize(path)


def format_file_size(bytes: int) -> str:

    bytes_in_kb = 2 ** 10
    bytes_in_mb = bytes_in_kb * (2 ** 10)
    bytes_in_gb = bytes_in_mb * (2 ** 10)
    bytes_in_tb = bytes_in_gb * (2 ** 10)

    if bytes < bytes_in_kb:
        file_size, units = bytes, "Б"
    elif bytes < bytes_in_mb:
        file_size, units = bytes / bytes_in_kb, "КБ"
    elif bytes < bytes_in_gb:
        file_size, units = bytes / bytes_in_mb, "МБ"
    elif bytes < bytes_in_tb:
        file_size, units = bytes / bytes_in_gb, "ГБ"
    else:
        file_size, units = bytes / bytes_in_tb, "ТБ"

    return f"{round(file_size, 2)} {units}"


def allowed_video_formats(path):
    path_endswith = path.split(".")[-1]
    return path_endswith in ("webm",)


def convert_video(input_files_path, output_files_path):
    command = [
        "ffmpeg",
        "-i",
        input_files_path,
        "-c:v",
        "libx264",
        "-crf",
        "24",
        "-c:a",
        "libmp3lame",
        "-q:a",
        "2",
        "-vsync",
        "2",
        output_files_path,
    ]
    process = subprocess.Popen(command)
    process.wait()


def print_separator():
    print(100 * "-")


def format_time(time):
    return datetime.fromtimestamp(time).strftime("%H:%M:%S")


class MyHandler(FileSystemEventHandler):
    def __init__(self):
        self.last_size = 0
        self.last_change_time = time.time()
        print(
            f"Скрипт запущен и находится в ожидании.\nДля обработки видео "
            f"поместите файлы формата .webm или .mp4. в директорию:\n\n"
            f"{folder_to_watch}\n\nДождитесь завершения обработки, это может "
            f"занять около 15 минут."
        )
        self.files = []

    def on_created(self, event):
        if event.is_directory:
            return
        if allowed_video_formats(event.src_path):
            input_filename_full = event.src_path.split("\\")[-1]
            input_filename, _ = os.path.splitext(input_filename_full)
            current_date = time.strftime("%Y-%m-%d-%H%M%S")
            # new_filename = f"{input_filename}_compressed_from_{current_date}.mp4"
            new_filename = f"{input_filename}.mp4"

            new_filepath_folder = os.path.join(folder_to_watch, "compressed_video_output")
            if not os.path.exists(new_filepath_folder):
                os.makedirs(new_filepath_folder)

            new_filepath = os.path.join(new_filepath_folder, new_filename)

            while True:
                try:
                    current_size = get_file_size(event.src_path)
                    if current_size == self.last_size:
                        time_start = time.time()
                        convert_video(event.src_path, new_filepath)

                        original_file_size = current_size
                        compressed_file_size = get_file_size(new_filepath)

                        compression_value = round(original_file_size / compressed_file_size, 2)

                        time_end = time.time()
                        processing_time = time_end - time_start
                        processing_time_timedelta = timedelta(
                            seconds=(processing_time))
                        processing_time_timedelta_str = \
                            str(processing_time_timedelta).split('.')[0]
                        result = f"Название оригинального файла: {input_filename_full}\nРазмер оригинального файла: {format_file_size(original_file_size)}\nНазвание нового файла: {new_filename}\nРазмер нового файла: {format_file_size(compressed_file_size)}\nВеличина сжатия (в ед.): {compression_value}\nОбработка начата: {format_time(time_start)}\nОбработка закончена: {format_time(time_end)}\nВремя обработки: {processing_time_timedelta_str}"
                        result_string_array.append(result)

                        os.unlink(event.src_path)
                        break
                    else:
                        self.last_size = current_size
                        self.last_change_time = time.time()
                        time.sleep(1)
                except Exception as e:
                    print(e)
                    time.sleep(1)

            if len(result_string_array) != 0:
                print(
                    f"\n\n\nОбработка завершена.\nОбработано файлов: {len(result_string_array)}\nФайл(ы) можно найти по пути:\n{new_filepath_folder}"
                )
                print_separator()
                for number, line in enumerate(result_string_array, 1):
                    print(f"Файл {number}:\n")
                    print(line)
                    print_separator()


if __name__ == "__main__":
    event_handler = MyHandler()
    observer = Observer()
    observer.schedule(event_handler, path=folder_to_watch, recursive=False)
    observer.start()

    try:
        while observer.is_alive():
            # Метод `observer.join(timeout=None)` - принимает `timeout` в
            # секундах, блокирующий операцию на указанное время.
            # Если `timeout` отсутствует, то операция будет блокироваться
            # до тех пор, пока поток не завершится.
            observer.join(1)
    finally:
        observer.stop()
        observer.join()
