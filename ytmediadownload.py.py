import yt_dlp
import ffmpeg
import pathlib
import logging
from shutil import which
from datetime import datetime
import os

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def download_video(url, download_path, format_choice, audio_quality, video_quality):
    """
    Download video or audio from a YouTube video.

    Args:
        url (str): The URL of the YouTube video.
        download_path (pathlib.Path): The directory where the file will be saved.
        format_choice (str): The chosen format ('mp3' or 'mp4').
        audio_quality (str): The chosen audio quality for MP3 ('low', 'medium', 'high').
        video_quality (str): The chosen video quality for MP4 ('720p', '1080p', '1440p').

    Returns:
        tuple: The path to the downloaded file and the title of the video.
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
            if format_choice == 'mp3':
                return download_path / 'audio.m4a', title
            else:
                return download_path / 'video.mp4', title
        except yt_dlp.DownloadError as e:
            logging.error(f"An error occurred during download: {e}")
            return None, None

def generate_unique_filename(output_path, title, extension):
    """
    Generate a unique filename by appending a number if the file already exists.

    Args:
        output_path (pathlib.Path): The directory where the file will be saved.
        title (str): The base title for the file.
        extension (str): The file extension (e.g., 'mp3').

    Returns:
        pathlib.Path: The unique file path.
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

    Args:
        input_file (pathlib.Path): The path to the input M4A file.
        output_path (pathlib.Path): The directory where the MP3 file will be saved.
        title (str): The title to use for the MP3 file.
        quality (str): The chosen audio quality ('low', 'medium', 'high').

    Returns:
        pathlib.Path: The path to the converted MP3 file.
    """
    bitrates = {
        'low': '128k',
        'medium': '192k',
        'high': '320k'
    }
    
    bitrate = bitrates.get(quality, '192k')  # Default to medium if invalid quality

    output_file = generate_unique_filename(output_path, title, 'mp3')
    try:
        ffmpeg.input(str(input_file)).output(str(output_file), audio_bitrate=bitrate).run()
        logging.info(f"Conversion to MP3 with {quality} quality complete.")
        return output_file
    except ffmpeg.Error as e:
        logging.error(f"An error occurred during conversion: {e}")
        return None

def main():
    download_path = pathlib.Path.home() / "Downloads"

    # Check if ffmpeg is installed
    if not which("ffmpeg"):
        logging.error("ffmpeg is not installed. Please install it to use this script.")
        return

    while True:
        url = input("Enter the URL of the YouTube video: ")
        
        # Validate URL (simple check)
        if not url.startswith("https://www.youtube.com/"):
            logging.error("Invalid YouTube URL. Please provide a valid URL.")
            continue

        # Prompt for format choice
        format_choice = input("Choose format (mp3/mp4): ").strip().lower()
        if format_choice not in ['mp3', 'mp4']:
            logging.error("Invalid choice. Please choose 'mp3' or 'mp4'.")
            continue

        audio_quality = 'medium'
        video_quality = None
        if format_choice == 'mp3':
            # Prompt for audio quality if the format is MP3
            audio_quality = input("Choose audio quality (low/medium/high): ").strip().lower()
            if audio_quality not in ['low', 'medium', 'high']:
                logging.error("Invalid choice. Please choose 'low', 'medium', or 'high'.")
                continue
        else:
            # Prompt for video quality if the format is MP4
            video_quality = input("Choose video quality (720p/1080p/1440p): ").strip().lower()
            if video_quality not in ['720p', '1080p', '1440p']:
                logging.error("Invalid choice. Please choose '720p', '1080p', or '1440p'.")
                continue

        file_path, title = download_video(url, download_path, format_choice, audio_quality, video_quality)
        if file_path and title:
            if format_choice == 'mp3':
                mp3_file = convert_to_mp3(file_path, download_path, title, audio_quality)
                if mp3_file:
                    logging.info(f"MP3 file saved as: {mp3_file}")
                else:
                    logging.error("Failed to convert to MP3.")
                
                # Cleanup temporary files
                try:
                    file_path.unlink()
                except Exception as e:
                    logging.error(f"An error occurred while removing the temporary file: {e}")
            else:
                output_file = generate_unique_filename(download_path, title, 'mp4')
                file_path.rename(output_file)
                os.utime(output_file, None)  # Update the file's timestamp to the current time
                logging.info(f"MP4 file saved as: {output_file}")

        # Ask if the user wants to convert another video
        while True:
            another = input("Do you want to convert another video? (yes/no): ").strip().lower()
            if another == 'yes':
                break
            elif another == 'no':
                return
            else:
                logging.error("Invalid input. Please enter 'yes' or 'no'.")

if __name__ == "__main__":
    main()
