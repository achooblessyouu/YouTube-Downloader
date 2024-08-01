import yt_dlp
import ffmpeg
import pathlib
import logging
from shutil import which
import os

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def download_video(url, download_path, format_choice, audio_quality, video_quality):
    """
    Download video or audio from a YouTube video.
    """
    ydl_opts_audio = {
        'format': 'bestaudio/best',
        'outtmpl': str(download_path / 'audio.%(ext)s'),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'm4a',
            'preferredquality': '192',
        }],
    }

    quality_formats = {
        '720p': 'bestvideo[height<=720]+bestaudio/best',
        '1080p': 'bestvideo[height<=1080]+bestaudio/best',
        '1440p': 'bestvideo[height<=1440]+bestaudio/best'
    }

    ydl_opts_video = {
        'format': quality_formats.get(video_quality, 'bestvideo+bestaudio/best'),
        'outtmpl': str(download_path / 'video.%(ext)s'),
        'merge_output_format': 'mp4',
    }

    ydl_opts = ydl_opts_audio if format_choice == 'mp3' else ydl_opts_video

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
            title = info.get('title', 'video').replace('/', '_').replace('\\', '_')
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

def convert_to_mp3(input_file, output_path, title, quality):
    """
    Convert an M4A file to MP3 format using ffmpeg with the chosen quality settings.
    """
    bitrates = {
        'low': '128k',
        'medium': '192k',
        'high': '320k'
    }
    
    bitrate = bitrates.get(quality, '192k')

    output_file = generate_unique_filename(output_path, title, 'mp3')
    try:
        ffmpeg.input(str(input_file)).output(str(output_file), audio_bitrate=bitrate).run()
        logging.info(f"Conversion to MP3 with {quality} quality complete.")
        return output_file
    except ffmpeg.Error as e:
        logging.error(f"Conversion error: {e}")
        return None

def prompt_user_input():
    """
    Prompt user for input and return the values.
    """
    url = input("Enter the URL of the YouTube video: ")
    if not url.startswith("https://www.youtube.com/"):
        logging.error("Invalid YouTube URL. Please provide a valid URL.")
        return None, None, None, None

    format_choice = input("Choose format (mp3/mp4): ").strip().lower()
    if format_choice not in ['mp3', 'mp4']:
        logging.error("Invalid choice. Please choose 'mp3' or 'mp4'.")
        return None, None, None, None

    audio_quality = 'medium'
    video_quality = None
    if format_choice == 'mp3':
        audio_quality = input("Choose audio quality (low/medium/high): ").strip().lower()
        if audio_quality not in ['low', 'medium', 'high']:
            logging.error("Invalid choice. Please choose 'low', 'medium', or 'high'.")
            return None, None, None, None
    else:
        video_quality = input("Choose video quality (720p/1080p/1440p): ").strip().lower()
        if video_quality not in ['720p', '1080p', '1440p']:
            logging.error("Invalid choice. Please choose '720p', '1080p', or '1440p'.")
            return None, None, None, None

    return url, format_choice, audio_quality, video_quality

def main():
    download_path = pathlib.Path.home() / "Downloads"
    download_path.mkdir(parents=True, exist_ok=True)

    if not which("ffmpeg"):
        logging.error("ffmpeg is not installed. Please install it to use this script.")
        return

    while True:
        url, format_choice, audio_quality, video_quality = prompt_user_input()
        if not url:
            continue

        file_path, title = download_video(url, download_path, format_choice, audio_quality, video_quality)
        if file_path and title:
            if format_choice == 'mp3':
                mp3_file = convert_to_mp3(file_path, download_path, title, audio_quality)
                if mp3_file:
                    logging.info(f"MP3 file saved as: {mp3_file}")
                else:
                    logging.error("Failed to convert to MP3.")
                
                try:
                    file_path.unlink()
                except Exception as e:
                    logging.error(f"Error removing temporary file: {e}")
            else:
                output_file = generate_unique_filename(download_path, title, 'mp4')
                file_path.rename(output_file)
                os.utime(output_file, None)
                logging.info(f"MP4 file saved as: {output_file}")

        if input("Do you want to convert another video? (yes/no): ").strip().lower() != 'yes':
            break

if __name__ == "__main__":
    main()
