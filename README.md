# 👑 핑거 프린스 (Finger Prince)

> **"검색도 안 하고 질문부터 한다고요? 네, 이제 그러셔도 됩니다."**

핑거 프린스는 디시인사이드, 아카라이브 등 주요 커뮤니티의 흩어진 정보를 AI로 찾아 요약해주는
**커뮤니티 특화 시맨틱 검색 + RAG 대시보드**입니다.

---

## 🏗️ 아키텍처

```
finger-prince/
├── apps/
│   ├── electron/          # 데스크톱 앱 (Electron 31 + React 18)
│   │   ├── main/          # Main process — 창 관리, IPC 핸들러
│   │   ├── preload/       # contextBridge API (window.fingerPrince)
│   │   └── python-bridge/ # Python 사이드카 프로세스 관리
│   ├── web/               # 웹 배포 (Vite + React)
│   └── shared/            # 공통 컴포넌트 & 훅
│       ├── components/    # DCBoard, DCPost, DCComment
│       ├── hooks/         # useSearch, useCrawl
│       └── utils/         # dateFormatter
├── backend/               # Python 코어 엔진
│   ├── api/               # FastAPI 라우터
│   ├── crawler/           # DCInside / ArcaLive 스크래퍼
│   └── engine/            # Vector DB + Embedding + Persona Prompt
└── packages/
    ├── tailwind-config/   # DC-스타일 Tailwind 테마
    └── typescript-config/ # 공통 TS 설정
```

---

## 🚀 빠른 시작

### 사전 요구사항
- Node.js 20+
- Python 3.11+
- OpenAI API Key (또는 로컬 HuggingFace 임베딩)

### 1. 의존성 설치

```bash
# JavaScript (monorepo root)
npm install

# Python
cd backend
pip install -r requirements.txt
```

### 2. 환경 변수 설정

```bash
cd backend
cp .env.example .env
# .env 파일에 OPENAI_API_KEY 입력
```

### 3. 백엔드 실행

```bash
python backend/main.py
# → http://localhost:8000
# → http://localhost:8000/docs  (Swagger UI)
```

### 4a. 웹 앱 실행

```bash
npm run dev:web
# → http://localhost:5173
```

### 4b. Electron 데스크톱 앱 실행

```bash
npm run dev:electron
# Python 백엔드를 자동으로 사이드카로 실행
```

---

## ✨ 주요 기능

| 기능 | 설명 | 구현 |
|------|------|------|
| **시맨틱 검색** | 자연어 쿼리 (예: "엘든링 현재 메타") | ChromaDB + cosine similarity |
| **AI 요약 답변** | 검색 결과를 하나의 답변으로 합성 | RAG + GPT-4o-mini |
| **페르소나 변환** | DC 말투로 답변 생성 | LLM Prompt Engineering |
| **갤러리 크롤링** | 게시글 + 댓글 계층 구조 인덱싱 | BeautifulSoup4 |
| **Electron 브릿지** | Python 사이드카 IPC 통신 | child_process.spawn + contextBridge |

### 지원 페르소나
- 🔴 **빡친도우미** — 짜증섞인 반말, 정확한 정보
- 🔵 **팩트체커** — 건조한 팩트봇, 출처 명시
- 🟣 **밈왕** — 밈 + ㅋㅋ, 핵심 정보 포함
- 🟢 **개념글봇** — 친절한 선배, 자세한 설명

---

## 🛠️ 기술 스택

| 레이어 | 기술 |
|--------|------|
| 데스크톱 | Electron 31 |
| 프론트엔드 | React 18 + TypeScript 5 + Vite 5 |
| 스타일링 | Tailwind CSS 3 (DC 다크 테마) |
| 모노레포 | npm workspaces |
| 백엔드 | FastAPI + uvicorn |
| 벡터 DB | ChromaDB (로컬 퍼시스턴트) |
| 임베딩 | OpenAI text-embedding-3-small / HuggingFace (선택) |
| LLM | GPT-4o-mini (RAG 합성) |
| 크롤러 | requests + BeautifulSoup4 |

---

## 🔌 API 엔드포인트

```
GET  /api/health          — 서버 상태 확인
POST /api/crawl           — 갤러리 크롤 & 인덱싱
POST /api/search          — 시맨틱 검색 + RAG 답변
```

자세한 API 문서: `http://localhost:8000/docs`

---

## ⚠️ 주의사항

본 프로젝트는 정보 검색의 편의를 돕기 위한 도구입니다.
각 커뮤니티의 이용 약관을 준수하며, 과도한 트래픽 유발로 인한 책임은 사용자 본인에게 있습니다.
크롤러는 기본적으로 요청 간 1초 이상의 딜레이를 적용합니다.
