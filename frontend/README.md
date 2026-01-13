# PAMS Frontend (Next.js 14)

Frontend dashboard for the Personal Asset Management System application.

## Setup

1. Install dependencies:
   ```bash
   npm install
   ```

2. Start development server:
   ```bash
   npm run dev
   ```

3. Open browser:
   ```
   http://localhost:3000
   ```

## Project Structure

- `app/` - Next.js App Router pages
  - `layout.tsx` - Root layout with navigation and QueryProvider
  - `page.tsx` - Dashboard home page
- `components/` - Reusable React components
  - `charts/` - Chart components (Phase 3+)
- `lib/hooks/` - React Query hooks for API calls
  - `useHealth.ts` - Health check hook
- `lib/types.ts` - TypeScript type definitions
- `lib/query-provider.tsx` - React Query configuration
- `next.config.ts` - API proxy configuration (CRITICAL)

## Important: API Proxy Configuration

**CRITICAL:** All API calls use the `/api/*` prefix, which is proxied to the backend at `http://localhost:8000`.

The proxy is configured in `next.config.ts`:
```typescript
async rewrites() {
  return [
    {
      source: '/api/:path*',
      destination: 'http://localhost:8000/api/:path*',
    },
  ];
}
```

**This eliminates CORS issues.** Never call `http://localhost:8000` directly from frontend code.

**Important:** After changing `next.config.ts`, you must restart the dev server.

## Environment Variables (.env.local)

```bash
NEXT_PUBLIC_API_URL=/api
```

## Development Workflow

1. Ensure backend is running on port 8000
2. Start frontend dev server (port 3000)
3. Open http://localhost:3000
4. Check DevTools Network tab to verify API calls go to `/api/*` (not `localhost:8000`)

## React Query

All data fetching uses `@tanstack/react-query`:
- Automatic caching and background refetching
- Loading and error states
- Optimistic updates (Phase 2+)

## TypeScript

- Strict mode enabled
- All types defined in `lib/types.ts`
- Types mirror backend Pydantic schemas
- No `any` types allowed

## Phase 1 Status

Current implementation:
- ✅ Next.js 14 with App Router
- ✅ TypeScript strict mode
- ✅ Tailwind CSS
- ✅ React Query setup
- ✅ API proxy configured
- ✅ Health check page

Not yet implemented (Phase 2+):
- ❌ Account management UI
- ❌ Transaction entry forms
- ❌ Charts and visualizations
- ❌ Account detail pages
