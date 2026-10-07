# Synology Drive Client — 동기화 제외 패턴 가이드

> **목적**: SynologyDrive 폴더에서 git을 함께 운영할 때 `.git/`, `.venv/`, `node_modules/`, `__pycache__/` 등을 동기화 대상에서 제외하여 충돌·손상을 방지.

## 왜 필요한가

SynologyDrive로 폴더를 동기화하면서 git을 쓰면 다음 문제가 발생할 수 있습니다:

| 문제 | 원인 | 결과 |
|---|---|---|
| `.git/index.lock` 충돌 | 양쪽 PC가 동시에 git 작업 | git 명령 실패, repo 손상 가능 |
| `.git/objects/` 충돌 | commit·branch 동시 생성 | history 깨짐 |
| `.venv/`, `node_modules/` 동기화 | 양쪽 OS에서 다른 binary | Python/Node가 못 읽는 깨진 라이브러리 |
| `mes.db` 동기화 | SQLite는 file lock 사용 | DB 파일 corrupt 가능 |
| `.next/`, `__pycache__/` 동기화 | 빌드 산출물 양쪽 다름 | 끝없는 변경 / 충돌 |

`.gitignore`만으로는 부족합니다 — git이 무시해도 SynologyDrive는 동기화하기 때문입니다. **SynologyDrive Client 자체에서 제외**해야 합니다.

## 제외해야 할 패턴

### 반드시 제외 (Critical)
```
.git/
.venv/
.venv-*/
node_modules/
__pycache__/
*.pyc
.next/
*.db
*.db.bak*
*Conflict.db
*.bak
.bkit-memory.json
.omc/
.visual-check/
```

### 권장 제외 (High)
```
.pytest_cache/
.ruff_cache/
.mypy_cache/
.turbo/
build/
dist/
*.egg-info/
.coverage
htmlcov/
.tox/
tsconfig.tsbuildinfo
.pre-commit-cache/
```

### 선택 제외 (Low)
```
.DS_Store          # Mac만 생성
Thumbs.db          # Windows만 생성
__MACOSX/          # Mac 압축 풀 때
```

## 설정 방법

### Windows (Synology Drive Client)

1. 시스템 트레이에서 Synology Drive Client 아이콘 우클릭 → **Settings**
2. **Sync Tasks** 탭 → 해당 동기화 작업 선택 → **Edit**
3. **Filters** (또는 **고급 설정**) 진입
4. **File Filter** / **Folder Filter** 항목에 위 패턴 추가
5. **Apply** → 동기화 재시작
6. 확인: 양쪽 PC에서 `.git/`, `.venv/` 폴더가 더 이상 동기화되지 않음

### Mac (Synology Drive Client)

1. 메뉴바의 Synology Drive 아이콘 클릭 → **환경설정** (⌘,)
2. **동기화 작업** 탭 → 해당 작업 선택 → **편집**
3. **필터 설정** 또는 **고급** 진입
4. **파일 필터** / **폴더 필터**에 위 패턴 추가
5. **저장** → 동기화 재시작

### NAS 측 설정 (선택)

NAS 본체의 Synology Drive Admin Console → **Team Folder** 또는 **Personal Folder** 설정에서 **Default Sync Filters**를 미리 등록하면 클라이언트마다 설정할 필요가 줄어듭니다.

## 검증

설정 후 다음 명령으로 양쪽 PC가 잘 분리되었는지 확인:

### Windows (PowerShell)
```powershell
# .git이 동기화되지 않으면 양쪽 PC의 .git/HEAD 파일 mtime 비교 시 불일치해야 함
Get-Item .git\HEAD | Select-Object FullName, LastWriteTime
```

### Mac (Terminal)
```bash
stat -f "%N  %Sm" .git/HEAD
```

양쪽 mtime이 즉시 따라가지 않으면(=수동 git 작업 후 분 단위 지연 없이 반영되지 않으면) `.git/`이 잘 제외된 것입니다.

## 참고

- **공식 문서**: [Synology Drive Client - Sync Filters](https://www.synology.com/en-global/dsm/feature/drive)
- **이 가이드의 한계**: SynologyDrive Client UI는 버전마다 다를 수 있음. 최신 버전 기준으로 작성됨.
- **궁극적 해결**: 진짜 안전한 방법은 git remote(GitHub/GitLab)로 분리하고 SynologyDrive에서 폴더를 빼는 것입니다 (Approach A). 본 프로젝트는 Approach B(가드레일)을 선택했음.

## 대체 방안: SynologyDrive 외부로 워크스페이스 이동

가드레일이 부족하다고 느끼면 언제든지 다음 절차로 외부 이동 가능:

### Windows
```powershell
# 1. 현재 동기화 중지 (SynologyDrive Client에서 일시정지)
# 2. 폴더 복사
Copy-Item -Recurse "C:\Users\xessi\SynologyDrive\Drive\Development\agents-workspace_260416" "C:\Dev\agents-workspace"
cd C:\Dev\agents-workspace
# 3. 정상 git 작업 + 외부 git remote 설정
```

### Mac
```bash
cp -R ~/SynologyDrive/Drive/Development/agents-workspace_260416 ~/Dev/agents-workspace
cd ~/Dev/agents-workspace
```

이후 SynologyDrive 폴더는 archive로 두거나 삭제.
