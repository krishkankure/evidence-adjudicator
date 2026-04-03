# Evidence Adjudicator Frontend

A light-themed Next.js interface for the Evidence Adjudicator backend. It provides a structured biomedical evidence chat workflow that calls the backend claim + adjudication API.

## Stack
- Next.js (App Router)
- TypeScript
- Tailwind CSS
- shadcn-style component primitives
- lucide-react icons

## Run locally
```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

Open `http://localhost:3000`.

## Environment variables
- `NEXT_PUBLIC_API_BASE_URL` (required): backend base URL, for example `http://localhost:8000`.

## Backend contract used
- `POST /claims`
- `POST /claims/{claim_id}/adjudicate`
- `GET /adjudications/{adjudication_id}`
- `GET /adjudications/{adjudication_id}/evidence`
- `GET /adjudications/{adjudication_id}/citations`

## Screenshots
_Add polished screenshots of empty state and adjudication result here._

## Notes
- This UI is for research exploration and product prototyping.
- Not medical advice.
