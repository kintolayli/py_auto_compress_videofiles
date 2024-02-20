import os
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from configparser import ConfigParser

# Получаем путь к текущей директории
script_dir = os.path.dirname(os.path.realpath(__file__))
input_dir_name = "to_compress_video"
input_dir_path = os.path.join(script_dir, input_dir_name)
config_filepath = os.path.join(script_dir, "config.ini")

# Создаем объект конфигурации
config = ConfigParser()

# Если файл конфигурации существует, читаем его
if os.path.exists(config_filepath):
    config.read(config_filepath)
else:
    # Иначе создаем новый файл конфигурации с базовыми значениями
    if not os.path.exists(input_dir_path):
        os.makedirs(input_dir_path)

    config["Settings"] = {"folder_to_watch": input_dir_path}
    with open(config_filepath, "w") as config_file:
        config.write(config_file)

# Открываем папку куда будем закидывать видео
os.startfile(input_dir_path)
# Папка, которую мы будем отслеживать
folder_to_watch = config.get("Settings", "folder_to_watch")
allowed_video_formats_array = ("webm",)
# allowed_video_formats_array = ("webm", "mp4")


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
            f"Скрипт запущен и находиться в ожидании.\nДля обработки видео "
            f"поместите файлы формата .webm или .mp4. в директорию:\n\n"
            f"{folder_to_watch}\n\nДождитесь завершения обработки, это может "
            f"занять около 15 минут.")

    def on_created(self, event):
        if event.is_directory:
            return
        if allowed_video_formats(event.src_path):
            input_filename = event.src_path.split("\\")[-1].split(".")[0]
            current_date = time.strftime("%Y-%m-%d-%H%M%S")
            new_filename = f"{input_filename}_compressed_from_{current_date}.mp4"

            new_filepath_folder = os.path.join(folder_to_watch, "video_output")
            if not os.path.exists(new_filepath_folder):
                os.makedirs(new_filepath_folder)

            new_filepath = os.path.join(new_filepath_folder, new_filename)

            while True:
                try:
                    current_size = os.path.getsize(event.src_path)
                    if current_size == self.last_size:
                        convert_video(event.src_path, new_filepath)
                        original_file_size = round(current_size / 1024, 2)
                        compressed_file_size = round(os.path.getsize(new_filepath) / 1024, 2)
                        compression_value = round(original_file_size / compressed_file_size, 2)
                        print(f"\n\nОбработка завершена. Итоговый файл можно "
                              f"найти по пути {new_filepath}\n\nНазвание оригинального файла: {input_filename}\nРазмер оригинального файла: {original_file_size} МБ\n\nНазвание нового файла: {new_filename}\nРазмер нового файла: {compressed_file_size} МБ\nВеличина сжатия (в ед.): {compression_value}")
                        os.unlink(event.src_path)
                        break
                    else:
                        self.last_size = current_size
                        self.last_change_time = time.time()
                        time.sleep(2)
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
