# 3D Folder Explorer

Python + Panda3D 기반의 3D 폴더 탐색기 프로젝트.

## 환경

- **Python**: venv 사용 (`venv/Scripts/activate`)
- **패키지**: `panda3d`, `send2trash`, `pyinstaller`
- **설치**: `pip install -r requirements.txt`
- **절대 전역 Python 환경에 pip install 금지** — venv 안에서만

## 모듈 구조

```
3d_folder_explorer/
├── main.py                  # 앱 진입점, Panda3D 초기화
├── core/
│   ├── filesystem.py        # 파일시스템 스캔 (스레드 포함)
│   ├── layout.py            # JSON 배치 저장/불러오기 (APPDATA)
│   └── config.py            # 상수, 크기 설정 등
├── scene/
│   ├── scene.py             # 씬 전체 구성 및 전환
│   ├── node.py              # 폴더/파일 노드 클래스
│   ├── camera.py            # 카메라 컨트롤
│   └── layout_algo.py       # 황금각 기반 구면 배치 알고리즘
├── ui/
│   ├── hud.py               # 라벨, 툴팁, 로딩 표시, 빈 폴더 안내
│   ├── context_menu.py      # 우클릭 컨텍스트 메뉴
│   └── fade.py              # 페이드 인/아웃 효과
├── requirements.txt
└── icon.ico
```

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

1. **1단계 (MVP)**: 폴더 선택 다이얼로그 → 3단계 렌더링 → 회전/줌/폴더 진입/ESC 복귀
2. **2단계**: 노드 드래그 배치 + JSON 저장, 파일 더블클릭 열기, 호버 툴팁, config.json
3. **3단계**: 우클릭 컨텍스트 메뉴, orphan 키 정리, 페이드 효과, PyInstaller 빌드

## 현재 진행 상태

- [x] 환경 세팅 완료: Python 3.11 venv, panda3d + send2trash 설치, requirements.txt 생성
- [x] .vscode/settings.json + launch.json 설정 완료 (venv 자동 활성화)
- [ ] **다음 작업: MVP 1단계 구현 시작**
  - 폴더 구조 생성 (core/, scene/, ui/)
  - main.py — Panda3D 초기화 + 폴더 선택 다이얼로그
  - core/filesystem.py — 백그라운드 스캔
  - core/config.py — 상수 정의
  - scene/layout_algo.py — 황금각 구면 배치
  - scene/node.py — 폴더/파일 노드 클래스
  - scene/scene.py — 씬 구성 및 전환
  - scene/camera.py — 마우스 회전/줌
  - ui/hud.py — 기본 라벨
