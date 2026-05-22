# T-26: Control API — GStreamer 이미지(T-25) 기반
# 별도 이미지가 필요할 경우 이 파일을 사용한다.
# 현재는 gstreamer.Dockerfile 이미지를 그대로 사용.
FROM live-pipeline-gstreamer:latest
# CMD는 gstreamer.Dockerfile에서 이미 설정됨:
# python3 -m uvicorn src.main:app --host 0.0.0.0 --port 8000
