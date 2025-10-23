# Railway PostgreSQL Setup Guide

This guide will help you set up PostgreSQL on Railway for persistent user storage.

## Prerequisites

- Railway account (https://railway.app)
- Your project already deployed on Railway
- Git repository connected to Railway

## Step 1: Add PostgreSQL to Your Railway Project

1. Go to your Railway project dashboard
2. Click **"+ New"** button
3. Select **"Database"**
4. Choose **"PostgreSQL"**
5. Railway will automatically provision a PostgreSQL database

## Step 2: Configure Environment Variables

Railway automatically creates a `DATABASE_URL` environment variable when you add PostgreSQL. You need to make sure your Node.js service can access it.

### Option A: Automatic (Recommended)

Railway should automatically link the database to your service. Verify by:

1. Click on your **Node.js service**
2. Go to **"Variables"** tab
3. Confirm `DATABASE_URL` is present (it should look like: `postgresql://user:password@host:port/database`)

### Option B: Manual

If `DATABASE_URL` is not automatically added:

1. Click on your **PostgreSQL database**
2. Go to **"Variables"** tab
3. Copy the `DATABASE_URL` value
4. Click on your **Node.js service**
5. Go to **"Variables"** tab
6. Click **"+ New Variable"**
7. Add:
   - **Name**: `DATABASE_URL`
   - **Value**: (paste the copied value)

## Step 3: Set Additional Environment Variables

Make sure these environment variables are set in your Node.js service:

```
NODE_ENV=production
SESSION_SECRET=<generate-a-random-secret>
LOGIN_USER=<your-admin-email>
LOGIN_PASS=<your-admin-password>
FASTAPI_BASE=<your-python-backend-url>
```

### Generate a Session Secret

Use a random string generator or run this in your terminal:
```bash
node -e "console.log(require('crypto').randomBytes(32).toString('hex'))"
```

## Step 4: Deploy the Changes

1. **Commit and push** your code changes:
   ```bash
   cd node-server
   git add .
   git commit -m "Migrate to PostgreSQL for user storage"
   git push
   ```

2. Railway will automatically detect the changes and redeploy

3. Monitor the deployment logs:
   - Click on your Node.js service
   - Go to **"Deployments"** tab
   - Click on the latest deployment
   - Check logs for:
     - `✓ Connected to PostgreSQL database`
     - `✓ Database schema initialized`
     - `✓ Admin user created: <your-email>`

## Step 5: Verify Everything Works

1. Visit your Railway app URL
2. Try to **sign up** with a new account
3. **Log out** and **log back in** with the new account
4. Restart your Railway service (to simulate a redeploy)
5. **Log in again** - if it works, your data is persisting! ✅

## Troubleshooting

### Error: "Connection refused" or "ECONNREFUSED"

- Check that `DATABASE_URL` is set correctly
- Verify the PostgreSQL service is running in Railway
- Check that both services are in the same project

### Error: "password authentication failed"

- The `DATABASE_URL` might be incorrect
- Try copying it again from the PostgreSQL service variables

### Database not initializing

- Check deployment logs for errors
- Ensure the `pg` package is installed (check `package.json`)
- Verify `NODE_ENV` is set to `production` for SSL

### Users not persisting after restart

- Confirm you're using PostgreSQL, not the old JSON file
- Check that `DATABASE_URL` is present in your service variables
- Look for database connection errors in logs

## Migration from JSON to PostgreSQL

If you had users in the old `users.json` file and want to migrate them:

1. Download your `users.json` file from your local development
2. Create a migration script (optional - contact support if needed)
3. Or simply have users re-register (if acceptable)

## Database Management

### View Database Contents

1. Click on your **PostgreSQL database** in Railway
2. Click **"Data"** tab to browse tables
3. Or use the **"Query"** tab to run SQL:
   ```sql
   SELECT email, first_name, last_name, roles, created_at FROM users;
   ```

### Backup Your Database

Railway provides automatic backups, but you can also:

1. Click on your **PostgreSQL database**
2. Go to **"Settings"** tab
3. Use the backup/restore features

### Connect with a Database Client

Use the connection details from the PostgreSQL service to connect with tools like:
- pgAdmin
- DBeaver
- TablePlus
- psql CLI

## Security Best Practices

1. ✅ Never commit `DATABASE_URL` to Git
2. ✅ Use strong passwords for `LOGIN_PASS`
3. ✅ Rotate `SESSION_SECRET` periodically
4. ✅ Enable SSL in production (already configured)
5. ✅ Regularly backup your database

## Next Steps

- Set up automated backups
- Monitor database performance in Railway dashboard
- Consider adding database indexes for better performance
- Implement password reset functionality
- Add email verification for new users

## Support

- Railway Docs: https://docs.railway.app/databases/postgresql
- Railway Discord: https://discord.gg/railway
- PostgreSQL Docs: https://www.postgresql.org/docs/

---

**Your users will now persist across deployments! 🎉**
