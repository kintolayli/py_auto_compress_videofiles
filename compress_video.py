import os
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from configparser import ConfigParser

# Получаем путь к текущей директории
script_dir = os.path.dirname(os.path.realpath(__file__))
config_filepath = os.path.join(script_dir, "config.ini")

# Создаем объект конфигурации
config = ConfigParser()

# Если файл конфигурации существует, читаем его
if os.path.exists(config_filepath):
    config.read(config_filepath)
else:
    # Иначе создаем новый файл конфигурации с базовыми значениями
    new_folder_path = os.path.join(script_dir, "to_compress_video")
    os.makedirs(new_folder_path)
    config["Settings"] = {"folder_to_watch": new_folder_path}
    with open(config_filepath, "w") as config_file:
        config.write(config_file)

# Папка, которую мы будем отслеживать
folder_to_watch = config.get("Settings", "folder_to_watch")
# folder_to_watch2 = r'D:\dev\py_auto_compress_video\to_compress_video'
allowed_video_formats_array = ("webm", "mp4")


def allowed_video_formats(path):
    path_endswith = path.split('.')[-1]
    return path_endswith in allowed_video_formats_array


def convert_video(input_files_path, output_files_path):
    command = f'ffmpeg -i "{input_files_path}" -c:v libx264 -crf 24 -c:a libmp3lame -q:a 2 "{output_files_path}"'
    os.system(command)


class MyHandler(FileSystemEventHandler):
    def __init__(self):
        self.last_size = 0
        self.last_change_time = time.time()
        print(
            f"Скрипт запущен. Для обработки видео поместите файлы формата .webm или .mp4. в директорию:\n\n{folder_to_watch}\n\nДождитесь завершения обработки, это может занять около 15 минут.")

    def on_created(self, event):
        if event.is_directory:
            return
        if allowed_video_formats(event.src_path):
            input_filename = event.src_path.split("\\")[-1].split(".")[0]
            current_date = time.strftime("%Y-%m-%d-%H%M%S")
            new_filename = f"{input_filename}_compressed_from_{current_date}.mp4"
            new_filepath = os.path.join(folder_to_watch, new_filename)

            while True:
                try:
                    current_size = os.path.getsize(event.src_path)
                    if current_size == self.last_size:
                        convert_video(event.src_path, new_filepath)
                        print(f"Обработка завершена. Итоговый файл можно найти по пути {new_filepath}")
                        break
                    else:
                        self.last_size = current_size
                        self.last_change_time = time.time()
                        time.sleep(1)
                except Exception as e:
                    print(f"Ошибка при проверке размера файла: {e}")


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
