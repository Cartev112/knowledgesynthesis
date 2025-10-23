Node server (Phase 2 MVP)

## 🎉 UI Migration Complete!

The frontend has been successfully migrated from Python to Node.js with proper separation of concerns.
- Login at /login, logout via POST /logout.
- Signup at /signup with **PostgreSQL database** for persistent user storage.

## 🗄️ Database Migration

**User storage has been migrated from JSON files to PostgreSQL** for production deployments.

### For Railway Deployment
See **[RAILWAY_POSTGRESQL_SETUP.md](./RAILWAY_POSTGRESQL_SETUP.md)** for complete setup instructions.

### For Local Development

1. Install PostgreSQL locally
2. Create a database: `createdb knowledgesynthesis`
3. Copy `.env.example` to `.env` and update `DATABASE_URL`
4. Run `npm install` to install dependencies including `pg`
5. Start the server: `npm start`

The database schema will be automatically created on first run.

## Setup


