import tempfile
import os
import re
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import NoTranscriptFound
import yt_dlp
from app.core.logger import logger

_whisper_model = None

def get_whisper_model():
    global _whisper_model
    if _whisper_model is None:
        from faster_whisper import WhisperModel
        logger.info("Loading Whisper model (tiny)")
        _whisper_model = WhisperModel("tiny", device="cpu", compute_type="int8")
    return _whisper_model

class TranscriptService:
    def extract_transcript(self, url: str, video_id: str = "A") -> dict:
        logger.info(f"Extracting transcript for {url} (video_id={video_id})")
        try:
            result = self._get_youtube_transcript_api(url)
            logger.info("Transcript obtained via YouTube Transcript API")
            return {"video_id": video_id, **result}
        except Exception as e:
            logger.warning(f"YouTube Transcript API failed: {e}. Falling back to Whisper.")

        try:
            result = self._get_whisper_transcript(url)
            logger.info("Transcript obtained via Whisper")
            return {"video_id": video_id, **result}
        except Exception as e:
            logger.error(f"Whisper fallback failed: {e}")
            raise RuntimeError(f"Transcript extraction failed for {url}") from e

    def _compute_semantic_features(self, text: str) -> dict:
        """Extract richer semantic signals using heuristic rules."""
        text_lower = text.lower()

        # Questions
        question_words = ['?', 'what', 'how', 'why', 'who', 'when', 'where', 'which']
        question_count = sum(1 for w in question_words if w in text_lower)
        has_question = question_count > 0

        # Conflict / tension
        conflict_terms = ['but', 'however', 'no ', 'not ', 'fight', 'against', 'problem', 'issue',
                          'bad', 'wrong', 'anger', 'angry', 'hate', 'enemy', 'challenge', 'conflict',
                          'disagree', 'argue', 'debate', 'tension']
        conflict_count = sum(1 for term in conflict_terms if term in text_lower)
        has_conflict = conflict_count > 0

        # Emotional intensity
        emotion_words = ['!', 'very', 'really', 'so ', 'extremely', 'amazing', 'awesome', 'terrible',
                         'incredible', 'love', 'hate', 'happy', 'sad', 'angry', 'excited', 'scared',
                         'wow', 'omg', 'fantastic', 'horrible']
        emotion_score = sum(1 for w in emotion_words if w in text_lower)

        # Humor
        humor_words = ['lol', 'haha', 'funny', 'joke', 'laugh', 'comedy', 'humor', 'hilarious',
                       'fun', 'entertainment', '😂', '🤣', 'rofl', 'lmao']
        humor_score = sum(1 for w in humor_words if w in text_lower)

        # Curiosity gap
        curiosity_words = ['?', 'wait', 'imagine', 'what if', 'secret', 'surprise', 'reveal', 'truth',
                           'unexpected', 'twist', 'discover', 'find out', 'see what happens']
        curiosity_score = sum(1 for w in curiosity_words if w in text_lower)

        # Character introduction (crude name detection)
        name_pattern = re.compile(r'\b[A-Z][a-z]+\b')
        names = name_pattern.findall(text)
        entity_count = len(set(names))

        # Call to action (CTA)
        cta_phrases = ['subscribe', 'like', 'share', 'comment', 'follow', 'click', 'link',
                       'check out', 'visit', 'watch till the end']
        cta_count = sum(1 for phrase in cta_phrases if phrase in text_lower)

        # Hook score composite (0-10)
        hook_score = min(10, (has_question * 3 + has_conflict * 2 + curiosity_score * 1.5 + entity_count * 0.5) / 1.5)
        hook_score = round(min(10, max(0, hook_score)), 1)

        return {
            "question": has_question,
            "conflict": has_conflict,
            "emotion": min(10, emotion_score),
            "humor_score": min(10, humor_score * 2),
            "curiosity_score": min(10, curiosity_score * 2),
            "cta_score": min(10, cta_count * 2),
            "hook_score": hook_score,
            "entity_count": entity_count
        }

    def _get_youtube_transcript_api(self, url: str) -> dict:
        video_id = self._extract_video_id(url)
        api = YouTubeTranscriptApi()

        for lang in ['en', 'hi']:
            try:
                transcript_list = api.fetch(video_id, languages=[lang])
                segments = []
                full_text_parts = []
                for snippet in transcript_list:
                    start = snippet.start
                    duration = snippet.duration
                    end = start + duration
                    text = snippet.text
                    features = self._compute_semantic_features(text)
                    segments.append({
                        "start": start,
                        "end": end,
                        "text": text,
                        "semantic_features": features
                    })
                    full_text_parts.append(text)
                logger.info(f"Found transcript for language: {lang}")
                return {
                    "transcript": " ".join(full_text_parts),
                    "segments": segments
                }
            except NoTranscriptFound:
                continue
            except Exception as e:
                logger.debug(f"Language {lang} failed: {e}")
                continue

        # Fallback to default
        try:
            transcript_list = api.fetch(video_id)
            segments = []
            full_text_parts = []
            for snippet in transcript_list:
                start = snippet.start
                duration = snippet.duration
                end = start + duration
                text = snippet.text
                features = self._compute_semantic_features(text)
                segments.append({
                    "start": start,
                    "end": end,
                    "text": text,
                    "semantic_features": features
                })
                full_text_parts.append(text)
            return {
                "transcript": " ".join(full_text_parts),
                "segments": segments
            }
        except NoTranscriptFound:
            raise RuntimeError("No transcript available for this video")
        except Exception as e:
            raise RuntimeError(f"Transcript API error: {e}")

    def _get_whisper_transcript(self, url: str) -> dict:
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

            actual_audio = base_path + '.mp3'
            if not os.path.exists(actual_audio):
                raise FileNotFoundError(f"Audio file not created: {actual_audio}")

            model = get_whisper_model()
            segments_raw, _ = model.transcribe(actual_audio, beam_size=5)
            segments = []
            full_text_parts = []
            for seg in segments_raw:
                features = self._compute_semantic_features(seg.text)
                segments.append({
                    "start": seg.start,
                    "end": seg.end,
                    "text": seg.text,
                    "semantic_features": features
                })
                full_text_parts.append(seg.text)
            return {
                "transcript": " ".join(full_text_parts),
                "segments": segments
            }
        finally:
            if os.path.exists(audio_path):
                os.unlink(audio_path)
            mp3_path = audio_path.replace('.mp3', '.mp3')
            if os.path.exists(mp3_path):
                os.unlink(mp3_path)

    def _extract_video_id(self, url: str) -> str:
        if "youtu.be/" in url:
            return url.split("youtu.be/")[1].split("?")[0]
        if "watch?v=" in url:
            return url.split("watch?v=")[1].split("&")[0]
        if "/shorts/" in url:
            return url.split("/shorts/")[1].split("?")[0]
        raise ValueError(f"Could not extract video ID from {url}")