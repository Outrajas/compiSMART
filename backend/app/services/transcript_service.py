import tempfile
import os
from youtube_transcript_api import YouTubeTranscriptApi
import yt_dlp
from app.core.logger import logger

class TranscriptService:
    def extract_transcript(self, url: str, video_id: str = "A") -> dict:
        """
        Extract transcript for a given YouTube URL.
        Tries the fast path (official API) first, falls back to audio + Whisper.
        Returns: {"video_id": str, "transcript": str}
        """
        logger.info(f"Extracting transcript for {url} (video_id={video_id})")
        try:
            # Fast path: YouTube's own transcript API
            transcript_text = self._get_youtube_transcript_api(url)
            logger.info("Transcript obtained via YouTube Transcript API")
            return {"video_id": video_id, "transcript": transcript_text}
        except Exception as e:
            logger.warning(f"YouTube Transcript API failed: {e}. Falling back to Whisper.")

        try:
            # Fallback: download audio and transcribe with Whisper
            transcript_text = self._get_whisper_transcript(url)
            logger.info("Transcript obtained via Whisper")
            return {"video_id": video_id, "transcript": transcript_text}
        except Exception as e:
            logger.error(f"Whisper fallback failed: {e}")
            raise RuntimeError(f"Transcript extraction failed for {url}") from e

    def _get_youtube_transcript_api(self, url: str) -> str:
        """Extract transcript using youtube-transcript-api (newer version)."""
        video_id = self._extract_video_id(url)
        try:
            transcript_list = YouTubeTranscriptApi.fetch(video_id)
            full_text = " ".join([entry["text"] for entry in transcript_list])
        except AttributeError:
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
            full_text = " ".join([entry["text"] for entry in transcript_list])
            return full_text
                
                
                    

    def _get_whisper_transcript(self, url: str) -> str:
        """
        Download audio with yt-dlp, then transcribe with faster-whisper.
        Removes the temp audio file afterwards.
        """
        from faster_whisper import WhisperModel
        
        tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
        audio_path = tmp.name
        tmp.close()
        try:
            base_path = audio_path.replace('.mp3', '')
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': base_path,
                'quiet': True,
                'no_warnings': True,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            # The actual output file after yt-dlp processing
            actual_audio = base_path + '.mp3'
            if not os.path.exists(actual_audio):
                raise FileNotFoundError(f"Audio file not created: {actual_audio}")

            model = WhisperModel("tiny", device="cpu", compute_type="int8")
            segments, _ = model.transcribe(actual_audio, beam_size=5)
            transcript = " ".join([seg.text for seg in segments])
            return transcript
        finally:
            # Clean up both possible files
            if os.path.exists(audio_path):
                os.unlink(audio_path)
            mp3_path = audio_path.replace('.mp3', '.mp3') 
            if os.path.exists(mp3_path):
                os.unlink(mp3_path)

    def _extract_video_id(self, url: str) -> str:
        """Extract the YouTube video ID from various URL formats."""
        if "youtu.be/" in url:
            return url.split("youtu.be/")[1].split("?")[0]
        if "watch?v=" in url:
            return url.split("watch?v=")[1].split("&")[0]
        if "/shorts/" in url:
            return url.split("/shorts/")[1].split("?")[0]
        raise ValueError(f"Could not extract video ID from {url}")