# Implementation Plan — Ouroboros Lite

## Goal
Q00/ouroboros의 핵심 기능을 antigravity CLI에서 활용할 수 있도록 최적화하여 로컬 Python 패키지로 구현.

## 핵심 컴포넌트

| 모듈 | 역할 | 구현 상태 |
|------|------|----------|
| `ouroboros/config.py` | LLM 프로바이더 & 폴백 | ✅ 완료 |
| `ouroboros/seed.py` | YAML Spec & AC 트리 모델 | ✅ 완료 |
| `ouroboros/interview.py` | 소크라테스식 인터뷰 엔진 | ✅ 완료 |
| `ouroboros/execution.py` | Double Diamond + Kahn's Sort | ✅ 완료 |
| `ouroboros/evaluation.py` | 3단계 검증 파이프라인 | ✅ 완료 |
| `ouroboros/resilience.py` | 스태그네이션 감지 & 페르소나 | ✅ 완료 |
| `ouroboros/cli.py` | Typer/Rich 통합 CLI | ✅ 완료 |

## 구현된 6단계 Ouroboros 루프

```
Phase 0 (Big Bang)    → interview   : 소크라테스식 질문으로 모호성 <= 0.20 달성
Phase 1 (PAL Router)  → config.py   : 복잡도 기반 LLM 티어 선택 (Frugal/Standard/Frontier)
Phase 2 (Double Diamond) → plan     : Kahn's 위상정렬로 병렬 실행 레벨 분류
Phase 3 (Resilience)  → status      : SPINNING/OSCILLATION/NO_DRIFT 감지 + 페르소나 추천
Phase 4 (Evaluation)  → evaluate    : Mechanical($0) → Semantic($$) → Consensus($$$)
Phase 5 (Evolution)   → 다음 iteration
```

## 검증 결과

- pytest 14개 테스트 전체 통과 (0.29초)
- Windows CP949 인코딩 호환성 해결
- LLM 키 없이도 규칙 기반 폴백으로 100% 동작
