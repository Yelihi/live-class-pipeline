# Live Class Pipeline Lab — Claude 지침

## 프로젝트 개요

GStreamer + MediaMTX 기반 실시간 라이브 강의 파이프라인 실험 레포.

## 사용자 컨텍스트

- React에 익숙, Python / GStreamer / Docker / MediaPipe는 처음
- GStreamer 개념 설명 시 React 컴포넌트 조합 구조로 비유하면 이해가 빠름
- 개발 환경: macOS (로컬) + Ubuntu 22.04 Dev Container

## 태스크 진행 규칙

사용자가 "T-XX 진행" 형태로 구현을 요청하면 `/task` 스킬의 5-역할 워크플로우를 자동 적용한다:

1. **[시니어 개발자]** 구현 방향 설계
2. **[아키텍쳐]** 설계 검증 (프로젝트 구조·버전·호환성)
3. **[리뷰어]** 보완 및 최종 사양 확정
4. **[테스터]** 검증 시나리오 (비즈니스 로직이 있을 때만)
5. **[참고 문헌 작성자]** 활용 문서 정리

## 질문 원칙

아래 상황에서는 반드시 구현 전에 사용자에게 질문한다:
- 완료 기준이 모호하거나 범위가 불명확할 때
- 설계 방향이 두 가지 이상으로 갈릴 때
- 라이브러리·도구 선택이 필요할 때

## 기술 주의사항

- GStreamer Python 바인딩은 `pip install` 불가 → `python3-gst-1.0` 시스템 패키지 필수
- venv는 반드시 `--system-site-packages` 옵션으로 생성
- 스크립트 파일 shebang: `#!/usr/bin/env bash`, `set -euo pipefail` 필수
- 파이프라인 스크립트 파일명: `t{번호}_{설명}.sh` 컨벤션 준수
