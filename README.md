# Whisper SRT Web

`whisper.cpp`를 사용해 영상/음성 파일을 업로드하면 SRT 자막 파일로 변환해 내려받는 간단한 웹 앱입니다.

## 기능
- 파일 업로드
- 언어 선택(자동 감지 포함)
- 클릭 한 번으로 SRT 생성 및 다운로드

## 사전 준비
1. `whisper.cpp` 빌드
2. 모델 파일 다운로드(예: `ggml-base.bin`)
3. `ffmpeg` 설치

## 실행 방법
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

브라우저에서 `http://localhost:5000` 접속.

## 환경 변수
- `WHISPER_CPP_DIR` (기본값: `./whisper.cpp`)
- `WHISPER_BINARY` (기본값: `./whisper.cpp/build/bin/whisper-cli`)
- `WHISPER_MODEL` (기본값: `./whisper.cpp/models/ggml-base.bin`)
- `FLASK_SECRET_KEY` (선택)

## 체크
`/health` 엔드포인트에서 `ffmpeg`, `whisper-cli`, 모델 파일 존재 여부 확인 가능.
