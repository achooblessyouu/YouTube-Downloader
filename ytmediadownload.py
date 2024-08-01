import yt_dlp
import ffmpeg
import pathlib
import logging
from shutil import which
import os

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def sanitize_filename(title):
    """
    Sanitize the filename by replacing invalid characters.
    """
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        title = title.replace(char, '_')
    return title

def download_media(url, download_path, format_choice):
    """
    Download video or audio from a YouTube video.
    """
    if format_choice == 'mp3':
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': str(download_path / 'audio.%(ext)s'),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'm4a',
                'preferredquality': '192',
            }],
        }
    else:  # 'mp4'
        ydl_opts = {
            'format': 'bestvideo+bestaudio/best',
            'outtmpl': str(download_path / 'video.%(ext)s'),
            'merge_output_format': 'mp4',
        }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
            title = info.get('title', 'video')
            title = sanitize_filename(title)
            ydl.download([url])
            logging.info("Download complete.")
            return (download_path / 'audio.m4a', title) if format_choice == 'mp3' else (download_path / 'video.mp4', title)
        except yt_dlp.DownloadError as e:
            logging.error(f"Download error: {e}")
            return None, None

def generate_unique_filename(output_path, title, extension):
    """
    Generate a unique filename by appending a number if the file already exists.
    """
    base_file = output_path / f"{title}.{extension}"
    i = 1
    while base_file.exists():
        base_file = output_path / f"{title}_{i}.{extension}"
        i += 1
    return base_file

def convert_to_mp3(input_file, output_path, title):
    """
    Convert an M4A file to MP3 format using ffmpeg with the best available quality.
    """
    output_file = generate_unique_filename(output_path, title, 'mp3')
    try:
        ffmpeg.input(str(input_file)).output(str(output_file), audio_bitrate='192k').run()
        logging.info("Conversion to MP3 complete.")
        return output_file
    except ffmpeg.Error as e:
        logging.error(f"Conversion error: {e}")
        return None

def reencode_to_mp4(input_file, output_file):
    """
    Re-encode the video and audio to ensure compatibility with MP4.
    """
    try:
        ffmpeg.input(str(input_file)).output(str(output_file), vcodec='libx264', acodec='aac', audio_bitrate='192k').run()
        logging.info("Re-encoding to MP4 complete.")
        return output_file
    except ffmpeg.Error as e:
        logging.error(f"Re-encoding error: {e}")
        return None

def prompt_user_input():
    """
    Prompt user for input and return the values.
    """
    while True:
        url = input("Enter the URL of the YouTube video: ")
        if url.startswith("https://www.youtube.com/"):
            break
        logging.error("Invalid YouTube URL. Please provide a valid URL.")
    
    while True:
        format_choice = input("Choose format (mp3/mp4): ").strip().lower()
        if format_choice in ['mp3', 'mp4']:
            break
        logging.error("Invalid choice. Please choose 'mp3' or 'mp4'.")
    
    return url, format_choice

def prompt_continue():
    """
    Prompt user to continue or exit.
    """
    while True:
        continue_choice = input("Do you want to download another video? (yes/no): ").strip().lower()
        if continue_choice in ['yes', 'no']:
            return continue_choice
        logging.error("Invalid input. Please enter 'yes' or 'no'.")

def main():
    download_path = pathlib.Path.home() / "Downloads"
    download_path.mkdir(parents=True, exist_ok=True)

    if not which("ffmpeg"):
        logging.error("ffmpeg is not installed. Please install it to use this script.")
        return

    while True:
        url, format_choice = prompt_user_input()
        file_path, title = download_media(url, download_path, format_choice)
        if file_path and title:
            if format_choice == 'mp3':
                logging.info(f"Attempting to convert {file_path} to MP3...")
                mp3_file = convert_to_mp3(file_path, download_path, title)
                if mp3_file:
                    logging.info(f"MP3 file saved as: {mp3_file}")
                else:
                    logging.error("Failed to convert to MP3.")
                
                try:
                    file_path.unlink()
                except Exception as e:
                    logging.error(f"Error removing temporary file: {e}")
            else:
                # For MP4, re-encode the file to ensure compatibility
                output_file = generate_unique_filename(download_path, title, 'mp4')
                if reencode_to_mp4(file_path, output_file):
                    os.remove(file_path)
                    logging.info(f"MP4 file saved as: {output_file}")
                else:
                    logging.error("Failed to re-encode MP4 file.")

        if prompt_continue() != 'yes':
            break

if __name__ == "__main__":
    main()
