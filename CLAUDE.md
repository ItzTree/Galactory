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

## 모듈 구조

```
Galactory/
├── main.py                  # 앱 진입점, Panda3D 초기화, 조명, 폰트 로드, last_path 복원
├── core/
│   ├── config.py            # 모든 상수 (창 크기, 색상, 카메라, 레이아웃)
│   ├── filesystem.py        # 백그라운드 스레드 디렉토리 스캔, FileEntry 데이터클래스 (name/path/is_dir/has_permission/size/mtime)
│   └── app_config.py        # config.json (last_path, nav_stack), layouts.json (노드 위치) 읽기/쓰기
├── scene/
│   ├── layout_algo.py       # 황금각 기반 구면 배치 (golden_sphere_positions)
│   ├── node.py              # ExplorerNode 클래스 (구 모델, 라벨, 충돌 구, 호버)
│   ├── camera.py            # 궤도 카메라 (드래그 회전, 스크롤 줌, 클릭 판별)
│   └── scene.py             # FolderScene (씬 빌드, 노드 드래그, 클릭/더블클릭, 툴팁, ESC 복귀)
├── ui/
│   └── hud.py               # HUD (경로 라벨, 로딩, 빈 폴더 안내, 힌트 바, 툴팁)
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
- `base.node_drag_active` — 노드 드래그 중 True, 카메라 드래그 억제에 사용
- 씬 구성 순서: `CameraController` → `HUD` → `FolderScene` (의존 관계)
- `mouse1` 이벤트: `scene._on_mouse_press`가 단일 핸들러 — 노드 히트 시 노드 드래그, 아니면 `camera_ctrl._on_press()` 위임
- 카메라 드래그: `isButtonDown(MouseButton.one())` 매 프레임 체크 (이벤트 누락 방지)
- 백그라운드 스캔 완료 후 `taskMgr.doMethodLater(0, ...)` 로 메인 스레드에 마샬링
- 노드 피킹: `CollisionRay` + `PICK_MASK = BitMask32.bit(1)`, `xnode` PythonTag로 객체 역참조
- 구 모델: `loader.loadModel("models/misc/sphere")`
- 중심 행성: `scene.py`의 `_build_center_planet()`에서 생성, 피킹 충돌 없음, `TransparencyAttrib.MAlpha` + `setDepthWrite(False)`로 반투명 처리
- 호버 하이라이트: 고정 색 대신 `_brighten()` (RGB +0.4, 흰색 방향 블렌드)
- 파일 색상: `config.py`의 `FILE_COLORS` 딕셔너리 (확장자 → 카테고리별 색), `node.py`의 `_file_color(name)`으로 조회
- 탐색 상태: `_navigate_to()` 호출마다 `set_nav_state()` → `config.json` 기록, 재시작 시 복원
- 노드 드래그: ray-sphere intersection으로 구 표면 위 이동, 드래그 완료 시만 `layouts.json` 저장
- 더블클릭: 0.35초 이내 동일 노드 2회 클릭 → 파일은 `os.startfile()`, 폴더는 첫 클릭에 진입
- 툴팁: 호버 변경 시 `hud.set_tooltip(entry)` 호출, 파일 크기·수정일 표시

## 코딩 규칙

- 파일시스템 스캔은 **반드시 백그라운드 스레드**에서 실행 (UI 블로킹 방지)
- `PermissionError`는 `try/except`로 조용히 처리 → 회색 노드로 표시
- 파일 삭제 시 `os.remove` 대신 **`send2trash`** 사용 (휴지통 이동)
- 노드 위치 변경 시에만 `layouts.json` 저장 (탐색만 하면 기록 안 남김)
- 저장 실패 시 오류 없이 조용히 무시

## 데이터 저장 경로

- 배치: `%APPDATA%\Galactory\layouts.json`
- 설정: `%APPDATA%\Galactory\config.json`

## 미구현 디자인 항목 (설계 문서 기준)

> 3단계 작업 전에 디자인 손볼 예정

- **폴더 노드 크기**: 현재 고정값 → `base_size + log(하위 항목 수 + 1) * scale_factor`로 변경
- **3단계 미니 노드**: 2단계 폴더 각각의 주변에 내부 항목 개수만큼 아주 작은 구체로 미리 표시 (실제 내용 없이 색상 구체만, 라벨 없음)

## 다음 작업: MVP 3단계

- 우클릭 컨텍스트 메뉴 (이름 변경, 삭제, 열기)
- orphan 키 정리 (`layouts.json`에서 실제로 존재하지 않는 경로 키 앱 시작 시 자동 제거)
- 페이드 인/아웃 전환 효과 (폴더 진입/복귀 시 0.3초)
- PyInstaller 빌드