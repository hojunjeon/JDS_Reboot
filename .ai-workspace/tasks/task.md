# Task Checklist — Ouroboros Lite Evolve Phase (Phase 5)

- [x] `ouroboros/evolution.py` 모듈 신규 구현
  - [x] Mechanical (컴파일, 테스트 실패 로그) 및 Semantic (합의 요구사항 누락) 진화 대상 진단 분석기 구현
  - [x] Stagnation (정체 역사) 데이터 기반 정체 위험 요소 추출
  - [x] LLM 프로바이더 및 룰 기반 자동 패치 생성기 설계 (Constraint & Session Rule)
  - [x] `ouroboros_seed.yaml` 제약 조건 자동 추가/수정 파서 작성
  - [x] `AGENTS.md` 파일 `## Anti-Regression Rules` 섹션 자동 연장 연계 구현
- [x] `ouroboros/cli.py` 인터페이스 통합
  - [x] `@app.command() def evolve` 명령어 추가
  - [x] `welcome` 가이드 온보딩 도움말 명령어 업데이트
- [x] 단위 테스트 작성 및 무결성 검증
  - [x] `tests/test_evolution.py` (또는 `tests/test_ouroboros.py` 통합) 작성
  - [x] pytest 전체 테스트 통과 검증 (Windows 인코딩 대응 포함)
- [x] 개발 완료 리포트 및 회고록 기록
  - [x] `.ai-workspace/walkthroughs/walkthrough.md` 작성
  - [x] devlog 생성 스킬을 활용하여 개발 경험 일지 기록
