import os
import shutil
import subprocess
import tempfile
import uuid
from pathlib import Path

from flask import Flask, flash, redirect, render_template, request, send_file, url_for
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "change-me")

UPLOAD_DIR = Path("uploads")
OUTPUT_DIR = Path("outputs")
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

WHISPER_CPP_DIR = Path(os.getenv("WHISPER_CPP_DIR", "./whisper.cpp"))
WHISPER_MODEL = Path(os.getenv("WHISPER_MODEL", "./whisper.cpp/models/ggml-base.bin"))
WHISPER_BINARY = Path(os.getenv("WHISPER_BINARY", str(WHISPER_CPP_DIR / "build/bin/whisper-cli")))

ALLOWED_EXTENSIONS = {
    "mp4", "mkv", "mov", "avi", "mp3", "wav", "m4a", "webm"
}

LANGUAGES = [
    ("auto", "자동 감지"),
    ("ko", "한국어"),
    ("en", "English"),
    ("ja", "日本語"),
    ("zh", "中文"),
    ("es", "Español"),
    ("fr", "Français"),
    ("de", "Deutsch"),
]


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def run_command(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def extract_audio(input_path: Path, output_wav: Path) -> None:
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(input_path),
        "-ar",
        "16000",
        "-ac",
        "1",
        str(output_wav),
    ]
    run_command(cmd)


def transcribe_to_srt(wav_path: Path, output_prefix: Path, language: str) -> Path:
    cmd = [
        str(WHISPER_BINARY),
        "-m",
        str(WHISPER_MODEL),
        "-f",
        str(wav_path),
        "-osrt",
        "-of",
        str(output_prefix),
    ]

    if language != "auto":
        cmd.extend(["-l", language])

    run_command(cmd)
    return output_prefix.with_suffix(".srt")


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        file = request.files.get("media_file")
        language = request.form.get("language", "auto")

        if not file or file.filename == "":
            flash("업로드할 파일을 선택해주세요.")
            return redirect(url_for("index"))

        if not allowed_file(file.filename):
            flash("지원하지 않는 파일 형식입니다.")
            return redirect(url_for("index"))

        safe_name = secure_filename(file.filename)
        media_id = uuid.uuid4().hex
        input_path = UPLOAD_DIR / f"{media_id}-{safe_name}"
        output_prefix = OUTPUT_DIR / media_id

        file.save(input_path)

        try:
            with tempfile.TemporaryDirectory() as tmp_dir:
                wav_path = Path(tmp_dir) / "audio.wav"
                extract_audio(input_path, wav_path)
                srt_path = transcribe_to_srt(wav_path, output_prefix, language)

            return send_file(
                srt_path,
                as_attachment=True,
                download_name=f"{Path(safe_name).stem}.srt",
                mimetype="application/x-subrip",
            )
        except FileNotFoundError as exc:
            flash(f"실행 파일을 찾을 수 없습니다: {exc}")
        except subprocess.CalledProcessError as exc:
            error_message = exc.stderr.decode("utf-8", errors="ignore") if exc.stderr else str(exc)
            flash(f"자막 생성 중 오류가 발생했습니다: {error_message}")
        finally:
            if input_path.exists():
                input_path.unlink(missing_ok=True)

    return render_template("index.html", languages=LANGUAGES)


@app.route("/health")
def health():
    status = {
        "whisper_binary": WHISPER_BINARY.exists(),
        "whisper_model": WHISPER_MODEL.exists(),
        "ffmpeg": shutil.which("ffmpeg") is not None,
    }
    return status, 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
