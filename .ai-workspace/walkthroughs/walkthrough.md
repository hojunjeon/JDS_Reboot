# Ouroboros Phase 0 Walkthrough: Jiyoon Debug Survival (JDS) Specification

JDS 게임 reboot의 핵심 요구사항 수집 및 명세서 작성을 완료하고, 이를 기반으로 Ouroboros Double Diamond Execution Plan을 도출해 낸 과정을 기록한 완료 보고서입니다.

## 1. 수행 결과 요약

- **Socratic Interview Simulation**: `.ai-workspace/scratch/run_interview.py` 스크립트를 성공적으로 설계 및 실행하여 `docs/00-reboot-start.md`에 기재된 게임 디자인을 정확히 추출 및 crystallize하였습니다.
- **Specification (Seed Spec)**: Pydantic `SeedSpec` 모델 형식에 100% 부합하는 `ouroboros_seed.yaml` 명세서를 생성했습니다. 총 24개의 세부 수락 기준(Acceptance Criteria)과 Phaser 3 기술 제약 사양을 수록하고 있습니다.
- **Double Diamond Plan**: Kahn의 위상 정렬 알고리즘을 활용하여 4레벨의 병렬 실행 단위로 정렬된 `ouroboros_plan.md` 실행 계획서와 Mermaid 다이어그램을 성공적으로 갱신해 냈습니다.
- **무결성 검증**: pytest suite (`tests/test_ouroboros.py`의 14개 단위 테스트)를 실행하여 14/14 전체 통과를 달성했습니다.

---

## 2. Jiyoon Debug Survival (JDS) 명세 요약 (`ouroboros_seed.yaml`)

### 6대 핵심 요구사항 트리 (Acceptance Criteria)
1. **메뉴 및 씬 구조 (`AC-100` 계열)**:
   - Monospace/Terminal 테마의 메인 화면, 부팅 애니메이션 (`AC-102`), 시작 무기 3종 선택 화면 (`AC-103`), 게임오버/클리어 결과 화면 (`AC-104`).
2. **이동 메커니즘 (`AC-200` 계열)**:
   - arrow key/WASD를 활용한 캐릭터 2D 평면 자유 이동 및 캔버스 영역 내 충돌 바운더리 제한 (`AC-202`).
3. **자동 무기 시스템 (`AC-300` 계열)**:
   - `Python` (유도형 고속 탄환), `C/C++` (직선 관통형 강격 탄환), `Java` (플레이어 주변 궤도 보호막).
4. **몬스터 및 웨이브 (`AC-400` 계열)**:
   - `SyntaxError` (기본 추적적), `NullPointer` (고속 유리몸), `SegFault` (느린 탱커/고피해), `HealBug` (도망치는 도구 상자).
   - **스테이지 이벤트**: 30초 시점에 발생하여 들여쓰기 테마의 적들이 몰려오는 `Indentation Panic` (`AC-405`).
5. **보스 레이드 및 클리어 조건 (`AC-500` 계열)**:
   - 60초 생존 시 라이벌 디버거 보스 `Jang Seonhyeong` 소환 (`AC-501`) 및 보스 퇴치 시 웨이브 중단 및 클리어 (`AC-502`).
6. **디바이스 HUD 및 그래픽 (`AC-600` 계열)**:
   - HP, 타이머, 킬 수, 현재 장착 무기 상태를 보여주는 HUD 구축 (`AC-601`). Monospace 폰트, Glitch 필터, CRT 스캔라인 아웃라인 연출 (`AC-602`).

### 기술 제약 사양 (Constraints)
- **Engine**: Phaser 3 framework 필수 사용.
- **Aesthetic**: Retro ASCII / Monospace terminal visual.
- **Platform**: Web browser execution (no-install required).
- **Rule**: `No Placeholders` (임시 방편용 stub, pass, ..., TODO 코드 절대 금지 규칙).

---

## 3. Double Diamond 실행 단계 계획 (`ouroboros_plan.md`)

- **Level 1 (병렬 실행 3개 태스크)**:
  - `AC100` (Discover), `AC200` (Discover), `AC600` (Discover)
- **Level 2 (병렬 실행 11개 태스크)**:
  - 메뉴 입력 (`AC101`), 부팅 연출 (`AC102`), 시작무기 노출 (`AC103`), 결과창 처리 (`AC104`), 키보드 입력 (`AC201`), 영역 충돌 (`AC202`), 자동사격 베이스 (`AC300`), 적 스폰 베이스 (`AC400`), 보스 이벤트 베이스 (`AC500`), HUD 레이아웃 (`AC601`), CRT 필터 (`AC602`).
- **Level 3 (병렬 실행 9개 태스크)**:
  - Python 무기 (`AC301`), C++ 무기 (`AC302`), Java 무기 (`AC303`), SyntaxError 적 (`AC401`), NullPointer 적 (`AC402`), SegFault 적 (`AC403`), HealBug 적 (`AC404`), Indentation Panic (`AC405`), Boss 소환 (`AC501`).
- **Level 4 (최종 1개 태스크)**:
  - 보스 처치 클리어 조건 판정 (`AC502`).

---

## 4. 검증 결과

```bash
>> [pytest tests/test_ouroboros.py]
collected 14 items
tests\test_ouroboros.py ..............                                   [100%]
============================= 14 passed in 0.50s ==============================
```
모든 단위 테스트가 완벽히 통과하여 Ouroboros 개발 환경의 일관성 및 사양 적합성이 100% 검증되었습니다.
이제 도출된 `ouroboros_plan.md` 순서에 따라 **Phase 2: Develop (본격적인 Phaser 3 게임 코드 구현)** 단계를 진행할 준비를 마쳤습니다!
