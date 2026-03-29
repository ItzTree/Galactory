# 3D Folder Explorer

Python + Panda3D 기반의 3D 폴더 탐색기 프로젝트.

## 실행 방법

```bash
venv/Scripts/activate
python main.py
```

## 환경

- **Python**: 3.11, venv 사용 (`venv/Scripts/activate`)
- **패키지**: `panda3d`, `send2trash`, `pyinstaller`
- **설치**: `pip install -r requirements.txt`
- **절대 전역 Python 환경에 pip install 금지** — venv 안에서만
- **한글 폰트**: `assets/fonts/NanumGothic.ttf` (프로젝트에 직접 포함)

## 모듈 구조 (현재 구현됨)

```
Galactory/
├── main.py                  # 앱 진입점, Panda3D 초기화, 조명, 폰트 로드
├── core/
│   ├── config.py            # 모든 상수 (창 크기, 색상, 카메라, 레이아웃)
│   └── filesystem.py        # 백그라운드 스레드 디렉토리 스캔, FileEntry 데이터클래스
├── scene/
│   ├── layout_algo.py       # 황금각 기반 구면 배치 (golden_sphere_positions)
│   ├── node.py              # ExplorerNode 클래스 (구 모델, 라벨, 충돌 구, 호버)
│   ├── camera.py            # 궤도 카메라 (드래그 회전, 스크롤 줌, 클릭 판별)
│   └── scene.py             # FolderScene (씬 빌드, 마우스 피킹, 폴더 진입/ESC 복귀)
├── ui/
│   └── hud.py               # HUD (경로 라벨, 로딩, 빈 폴더 안내, 힌트 바)
├── assets/
│   └── fonts/
│       └── NanumGothic.ttf  # 한글 폰트
└── requirements.txt
```

## 핵심 설계 메모

- `base.korean_font` — `main.py`의 `App.__init__`에서 로드, HUD와 노드 라벨 모두 참조
- `base.camera_ctrl` — `CameraController` 인스턴스, `was_click` 프로퍼티로 클릭/드래그 구분
- `base.hud` — `HUD` 인스턴스
- `base.folder_scene` — `FolderScene` 인스턴스
- 씬 구성 순서: `CameraController` → `HUD` → `FolderScene` (의존 관계)
- 카메라 드래그: `isButtonDown(MouseButton.one())` 매 프레임 체크 (이벤트 누락 방지)
- 백그라운드 스캔 완료 후 `taskMgr.doMethodLater(0, ...)` 로 메인 스레드에 마샬링
- 노드 피킹: `CollisionRay` + `PICK_MASK = BitMask32.bit(1)`, `xnode` PythonTag로 객체 역참조
- 구 모델: `loader.loadModel("models/misc/sphere")`

## 코딩 규칙

- 파일시스템 스캔은 **반드시 백그라운드 스레드**에서 실행 (UI 블로킹 방지)
- `PermissionError`는 `try/except`로 조용히 처리 → 회색 노드로 표시
- 파일 삭제 시 `os.remove` 대신 **`send2trash`** 사용 (휴지통 이동)
- 노드 위치 변경 시에만 `layouts.json` 저장 (탐색만 하면 기록 안 남김)
- 저장 실패 시 오류 없이 조용히 무시

## 데이터 저장 경로

- 배치: `%APPDATA%\3DExplorer\layouts.json`
- 설정: `%APPDATA%\3DExplorer\config.json`

## MVP 구현 우선순위

1. **1단계 (MVP)**: 폴더 선택 다이얼로그 → 3D 렌더링 → 회전/줌/폴더 진입/ESC 복귀 ✅
2. **2단계**: 노드 드래그 배치 + JSON 저장, 파일 더블클릭 열기, 호버 툴팁, config.json
3. **3단계**: 우클릭 컨텍스트 메뉴, orphan 키 정리, 페이드 효과, PyInstaller 빌드

## 현재 진행 상태

- [x] 환경 세팅 완료: Python 3.11 venv, panda3d + send2trash 설치, requirements.txt 생성
- [x] .vscode/settings.json + launch.json 설정 완료 (venv 자동 활성화)
- [x] **MVP 1단계 구현 완료** — 동작 확인됨
  - 폴더 구조 (core/, scene/, ui/) 및 전체 모듈 생성
  - tkinter 폴더 선택 다이얼로그 (Panda3D 시작 전 실행)
  - 황금각 구면 배치, 폴더/파일 노드 (색상·크기 구분, 호버 하이라이트)
  - 드래그 궤도 회전 + 스크롤 줌 (버튼 상태 직접 체크로 드래그 오작동 수정)
  - 마우스 피킹으로 폴더 클릭 진입, ESC 뒤로 가기
  - HUD: 경로, 로딩, 빈 폴더, 힌트 바 (한글 폰트 적용)
  - 창 크기 1920×1080
- [ ] **다음 작업: MVP 2단계**
  - 노드 드래그 배치 + `layouts.json` 저장 (`%APPDATA%\3DExplorer\`)
  - 파일 더블클릭 열기 (`os.startfile`)
  - 호버 툴팁 (파일 크기, 수정일)
  - `config.json` 지원