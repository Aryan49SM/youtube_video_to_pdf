import os
import tempfile
import re
import cv2
from fpdf import FPDF
from PIL import Image
import yt_dlp
from skimage.metrics import structural_similarity as compare_ssim
from youtube_transcript_api import YouTubeTranscriptApi

def download_video(url, output_file):
    if os.path.exists(output_file):
        os.remove(output_file)
    ydl_opts = {
        'outtmpl': output_file,
        'format': 'best',
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

def get_video_id(url):
    # Match YouTube Shorts URLs
    video_id_match = re.search(r"shorts\/(\w+)", url)
    if video_id_match:
        return video_id_match.group(1)
    # Match youtu.be shortened URLs
    video_id_match = re.search(r"youtu\.be\/([\w\-_]+)(\?.*)?", url)
    if video_id_match:
        return video_id_match.group(1)
    # Match regular YouTube URLs
    video_id_match = re.search(r"v=([\w\-_]+)", url)
    if video_id_match:
        return video_id_match.group(1)
    # Match YouTube live stream URLs
    video_id_match = re.search(r"live\/(\w+)", url)
    if video_id_match:
        return video_id_match.group(1)
    return None

def get_video_title(url):
    ydl_opts = {
        'skip_download': True,
        'ignoreerrors': True
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        video_info = ydl.extract_info(url, download=False)
        title = video_info['title']
        # Clean title to remove characters that are invalid in file names
        title = re.sub(r'[\\/*?:"<>|]', "", title)
        return title.strip()

def extract_unique_frames(video_file, output_folder, n=3, ssim_threshold=0.8):
    cap = cv2.VideoCapture(video_file)
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    last_frame = None
    saved_frame = None
    frame_number = 0
    last_saved_frame_number = -1
    timestamps = []

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        if frame_number % n == 0:
            gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray_frame = cv2.resize(gray_frame, (128, 72))

            if last_frame is not None:
                similarity = compare_ssim(gray_frame, last_frame, data_range=gray_frame.max() - gray_frame.min())

                if similarity < ssim_threshold:
                    if saved_frame is not None and frame_number - last_saved_frame_number > fps:
                        frame_path = os.path.join(output_folder, f'frame{frame_number:04d}_{frame_number // fps}.png')
                        cv2.imwrite(frame_path, saved_frame)
                        timestamps.append((frame_number, frame_number // fps))
                    saved_frame = frame
                    last_saved_frame_number = frame_number
                else:
                    saved_frame = frame
            else:
                frame_path = os.path.join(output_folder, f'frame{frame_number:04d}_{frame_number // fps}.png')
                cv2.imwrite(frame_path, frame)
                timestamps.append((frame_number, frame_number // fps))
                last_saved_frame_number = frame_number

            last_frame = gray_frame

        frame_number += 1

    cap.release()
    return timestamps

def convert_frames_to_pdf(input_folder, output_file, timestamps):
    frame_files = sorted(os.listdir(input_folder), key=lambda x: int(x.split('_')[0].split('frame')[-1]))
    pdf = FPDF("L")
    pdf.set_auto_page_break(0)

    for i, (frame_file, (frame_number, timestamp_seconds)) in enumerate(zip(frame_files, timestamps)):
        frame_path = os.path.join(input_folder, frame_file)
        image = Image.open(frame_path)
        pdf.add_page()
        pdf.image(frame_path, x=0, y=0, w=pdf.w, h=pdf.h)

        timestamp = f"{timestamp_seconds // 3600:02d}:{(timestamp_seconds % 3600) // 60:02d}:{timestamp_seconds % 60:02d}"

        # Determine text color based on brightness of a region
        x, y, width, height = 5, 5, 60, 15
        region = image.crop((x, y, x + width, y + height)).convert("L")
        mean_pixel_value = region.resize((1, 1)).getpixel((0, 0))
        if mean_pixel_value < 64:
            pdf.set_text_color(255, 255, 255)
        else:
            pdf.set_text_color(0, 0, 0)

        pdf.set_xy(x, y)
        pdf.set_font("Arial", size=12)
        pdf.cell(0, 0, timestamp)

    pdf.output(output_file)

def convert_youtube_to_pdf(youtube_url):
    video_id = get_video_id(youtube_url)
    if not video_id:
        raise ValueError("Invalid YouTube URL.")
    
    video_title = get_video_title(youtube_url)
    video_file = f"video_{video_id}.mp4"
    
    # Download the video
    download_video(youtube_url, video_file)
    
    output_pdf_filename = f"{video_title}.pdf"
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        frames_folder = os.path.join(tmp_dir, "frames")
        os.makedirs(frames_folder, exist_ok=True)
        
        timestamps = extract_unique_frames(video_file, frames_folder)
        convert_frames_to_pdf(frames_folder, output_pdf_filename, timestamps)
    
    # Remove the downloaded video file to clean up
    if os.path.exists(video_file):
        os.remove(video_file)
    
    # Read the PDF file as bytes to return for download
    with open(output_pdf_filename, "rb") as f:
        pdf_bytes = f.read()
    
    # Optionally remove the generated PDF file after reading
    if os.path.exists(output_pdf_filename):
        os.remove(output_pdf_filename)
    
    return pdf_bytes, output_pdf_filename
