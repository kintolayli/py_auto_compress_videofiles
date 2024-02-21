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
            f"Скрипт запущен и находиться в ожидании.\nДля обработки видео "
            f"поместите файлы формата .webm или .mp4. в директорию:\n\n"
            f"{folder_to_watch}\n\nДождитесь завершения обработки, это может "
            f"занять около 15 минут."
        )

    def on_created(self, event):
        if event.is_directory:
            return
        if allowed_video_formats(event.src_path):
            input_filename_full = event.src_path.split("\\")[-1]
            input_filename, _ = os.path.splitext(input_filename_full)
            current_date = time.strftime("%Y-%m-%d-%H%M%S")
            new_filename = (
                f"{input_filename}_compressed_from_{current_date}.mp4"
            )

            new_filepath_folder = os.path.join(folder_to_watch, "video_output")
            if not os.path.exists(new_filepath_folder):
                os.makedirs(new_filepath_folder)

            new_filepath = os.path.join(new_filepath_folder, new_filename)

            while True:
                try:
                    current_size = os.path.getsize(event.src_path)
                    if current_size == self.last_size:
                        time_start = time.time()
                        convert_video(event.src_path, new_filepath)

                        original_file_size = round(current_size / 1024, 0)
                        compressed_file_size = round(
                            os.path.getsize(new_filepath) / 1024, 0
                        )
                        compression_value = round(
                            original_file_size / compressed_file_size, 2
                        )
                        time_end = time.time()
                        processing_time = time_end - time_start
                        result = f"Название оригинального файла: {input_filename_full}\nРазмер оригинального файла: {original_file_size} МБ\nНазвание нового файла: {new_filename}\nРазмер нового файла: {compressed_file_size} МБ\nВеличина сжатия (в ед.): {compression_value}\nОбработка начата: {format_time(time_start)}\nОбработка закончена: {format_time(time_end)}\nВремя обработки: {timedelta(seconds=(processing_time)).split('.')[0]}"
                        result_string_array.append(result)

                        os.unlink(event.src_path)
                        break
                    else:
                        self.last_size = current_size
                        self.last_change_time = time.time()
                        time.sleep(1)
                except Exception as e:
                    print(f"Ошибка при проверке размера файла: {e}")

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
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
