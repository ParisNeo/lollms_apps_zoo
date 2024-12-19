import os
import platform
import shutil
import subprocess
import sys
import urllib.request
import zipfile


def is_admin():
    try:
        if platform.system() == "Windows":
            import ctypes

            return ctypes.windll.shell32.IsUserAnAdmin()
        else:
            return os.geteuid() == 0
    except:
        return False


def elevate_privileges():
    if platform.system() == "Windows":
        import ctypes

        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, " ".join(sys.argv), None, 1
        )
    else:
        args = ["sudo", sys.executable] + sys.argv + [os.environ]
        os.execlpe("sudo", *args)


def download_ffmpeg():
    if platform.system() == "Windows":
        url = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
        filename = "ffmpeg.zip"
    elif platform.system() == "Darwin":  # macOS
        url = "https://evermeet.cx/ffmpeg/ffmpeg-4.4.zip"
        filename = "ffmpeg.zip"
    else:  # Linux
        print(
            "For Linux, it's recommended to use the package manager. Run: sudo apt-get install ffmpeg"
        )
        sys.exit(1)

    print("Downloading FFmpeg...")
    urllib.request.urlretrieve(url, filename)
    return filename


def extract_ffmpeg(filename):
    print("Extracting FFmpeg...")
    with zipfile.ZipFile(filename, "r") as zip_ref:
        zip_ref.extractall("ffmpeg_temp")


def install_ffmpeg():
    if platform.system() == "Windows":
        dest_dir = "C:\\ffmpeg"
        if not os.path.exists(dest_dir):
            os.makedirs(dest_dir)
        for file in os.listdir("ffmpeg_temp"):
            if file.endswith(".exe"):
                shutil.move(
                    os.path.join("ffmpeg_temp", file), os.path.join(dest_dir, file)
                )
        add_to_path_windows(dest_dir)
    elif platform.system() == "Darwin":  # macOS
        dest_dir = "/usr/local/bin"
        shutil.move("ffmpeg_temp/ffmpeg", dest_dir)
        os.chmod(os.path.join(dest_dir, "ffmpeg"), 0o755)
    else:  # Linux
        print("For Linux, please use the package manager to install FFmpeg.")


def add_to_path_windows(path):
    import winreg

    key = winreg.OpenKey(
        winreg.HKEY_LOCAL_MACHINE,
        r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment",
        0,
        winreg.KEY_ALL_ACCESS,
    )
    current_path = winreg.QueryValueEx(key, "Path")[0]
    if path not in current_path:
        new_path = current_path + ";" + path
        winreg.SetValueEx(key, "Path", 0, winreg.REG_EXPAND_SZ, new_path)
    winreg.CloseKey(key)


def cleanup(filename):
    print("Cleaning up...")
    os.remove(filename)
    shutil.rmtree("ffmpeg_temp")


def main():
    if not is_admin():
        print("Elevating privileges...")
        elevate_privileges()
        return

    filename = download_ffmpeg()
    extract_ffmpeg(filename)
    install_ffmpeg()
    cleanup(filename)

    print("FFmpeg has been successfully installed!")
    if platform.system() == "Windows":
        print("Please restart your command prompt or PowerShell to use FFmpeg.")


def install_ffmpeg_if_needed():
    if shutil.which("ffmpeg") is not None:
        print("FFmpeg is already installed.")
        return True

    print("FFmpeg not found. Installing...")
    if not is_admin():
        print("Elevating privileges...")
        elevate_privileges()
        return False  # Script will restart with elevated privileges

    filename = download_ffmpeg()
    extract_ffmpeg(filename)
    install_ffmpeg()
    cleanup(filename)

    print("FFmpeg has been successfully installed!")
    if platform.system() == "Windows":
        print("Please restart your command prompt or PowerShell to use FFmpeg.")

    return True


if __name__ == "__main__":
    main()
