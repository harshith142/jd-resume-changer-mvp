# JD Resume Changer MVP - Production Readiness Issues

## 🔴 CRITICAL Issues (Must Fix)

### Backend
- [ ] **Port conflicts**: Multiple processes on 8000, 8002 - need single consistent port (using 8004 for local dev)
- [x] **datetime.utcnow() deprecation**: Fixed in api_keys.py and auth.py - all occurrences updated
- [ ] **Rate limiting middleware**: Added but needs Redis backend for production
- [x] **API key router prefix**: Changed from /api/v1/api-keys to /api-keys (consistent with main.py)

### Frontend
- [x] **Windows build EPERM error**: Fixed by enabling worker_threads in next.config.js
- [ ] **Font loading failure**: Inter font from Google Fonts fails during build
- [ ] **TypeScript config**: ignoreBuildErrors=true is workaround, not fix
- [x] **ESLint config**: Basic config added but @typescript-eslint not installed (optional)

### Security
- [x] **Hardcoded secrets in .env files**: Removed from server/.env and web/.env.local
- [x] **NVIDIA API key in server/.env.example**: Removed
- [x] **JWT_ALGORITHM**: Set to HS256 consistently

### Infrastructure
- [x] **Docker compose**: All env vars properly templated with ${VAR} syntax
- [x] **Extension manifest**: Updated to localhost:8004 for local dev
- [ ] **Alembic migration**: Missing migration for last_tested_at, is_valid fields

## 🟡 HIGH Priority Issues

### Backend
- [ ] **NVIDIA API connectivity**: Server can't reach integrate.api.nvidia.com (proxy/firewall) - Ollama fallback works
- [x] **Windows --reload fails**: PermissionError with watchfiles - run without --reload
- [x] **Missing __init__.py files**: Added for app/api, app/api/routes, app/services
- [x] **Health endpoint**: Works with pdflatex/pdfinfo/pdftotext detection

### Frontend
- [ ] **NextAuth URL mismatch**: NEXTAUTH_URL=http://localhost:3000 (ok for local dev)
- [x] **API URL config**: NEXT_PUBLIC_API_URL points to 8004 for local dev
- [ ] **Missing type-check**: tsc --noEmit passes but build skips it

### Extension
- [x] **Server URL defaults**: Updated to localhost:8004 in popup.js and options.js
- [x] **Host permissions**: manifest.json updated to localhost:8004

## 🟢 MEDIUM Priority Issues

### Backend
- [ ] **Rate limiting**: In-memory only, needs Redis for multi-instance
- [ ] **CORS origins**: Too permissive in development
- [ ] **OAuth state storage**: File-based, not suitable for multi-instance
- [ ] **Database**: SQLite for dev, PostgreSQL for prod - migration needed

### Frontend
- [ ] **Image optimization**: Using <img> instead of <Image /> in several places
- [ ] **React hooks warnings**: Missing dependencies in useEffect
- [ ] **Bundle size**: No analysis configured

### Testing
- [ ] **No unit tests**: Need test coverage for critical paths
- [ ] **No integration tests**: Auth flow, API key management, resume generation
- [ ] **No E2E tests**: Playwright/Cypress not configured

## 🔵 LOW Priority Issues

### Code Quality
- [ ] **Consistent quoting**: Mix of single/double quotes
- [ ] **Type hints**: Some functions missing return types
- [ ] **Documentation**: API docs need examples

### DevOps
- [ ] **CI/CD pipeline**: Not configured
- [ ] **Monitoring**: No logging/metrics setup
- [ ] **Backup strategy**: Database backup not configured

## ✅ COMPLETED Fixes

- [x] Removed hardcoded NVIDIA API key from server/.env and server/.env.example
- [x] Removed hardcoded OAuth secrets from web/.env.local
- [x] Fixed datetime.utcnow() → datetime.now(timezone.utc) in api_keys.py and auth.py
- [x] Added rate limiting middleware (in-memory)
- [x] Fixed API key router prefix consistency
- [x] Fixed frontend build EPERM error on Windows
- [x] Added ESLint config (basic)
- [x] Added missing __init__.py files
- [x] Updated docker-compose.yml JWT_ALGORITHM=HS256
- [x] Fixed .gitignore with comprehensive exclusions
- [x] Updated next.config.js for Windows compatibility
- [x] Health endpoint works with pdflatex/pdfinfo/pdftotext detection
- [x] Auth flow working (register/login/refresh/logout)
- [x] API key CRUD + test endpoints working
- [x] NVIDIA API key test passes (valid key)
- [x] Extension manifest/port config updated for local dev
- [x] Removed BOM from auth.py
- [x] Docker compose env vars properly templated
