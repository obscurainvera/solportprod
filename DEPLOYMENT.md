# Deployment Guide for SolPort

This guide outlines the steps to deploy the SolPort application to a production environment (AWS EC2, DigitalOcean, or similar).

## Prerequisites

- A Linux server (Ubuntu recommended) with at least 2GB RAM
- Docker and Docker Compose installed
- Domain name pointing to your server IP
- SSL certificates for your domain

## Deployment Steps

### 1. Clone the Repository

```bash
git clone https://your-repository-url/solportprod.git
cd solportprod
```

### 2. Set up SSL Certificates

Create required directories:

```bash
mkdir -p nginx/ssl
```

Place your SSL certificates in the `nginx/ssl` directory:
- `server.crt` - Your certificate file
- `server.key` - Your private key file

For Let's Encrypt certificates:

```bash
sudo certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com
cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem nginx/ssl/server.crt
cp /etc/letsencrypt/live/yourdomain.com/privkey.pem nginx/ssl/server.key
```

### 3. Configure Environment Variables

Copy the production environment template and update it:

```bash
cp .env.production .env
```

Edit the `.env` file and update all values with your production settings:
- Database configuration
- API configuration
- Allowed origins (your domain names)

### 4. Build and Deploy

Build and start the Docker containers:

```bash
docker-compose build
docker-compose up -d
```

### 5. Verify Deployment

Check if containers are running:

```bash
docker-compose ps
```

Verify logs for any errors:

```bash
docker-compose logs -f app
```

Access your application at `https://yourdomain.com`

## Database Migration

If you need to migrate your database from a development to production environment:

1. Backup your development database:
   ```bash
   pg_dump -h dev-db-host -U dev-user -d dev-db-name > db_backup.sql
   ```

2. Restore to production database:
   ```bash
   psql -h your-production-db-host -U your-db-user -d your-db-name < db_backup.sql
   ```

## Maintenance and Updates

### Updating the Application

```bash
git pull
docker-compose down
docker-compose build
docker-compose up -d
```

### Backup

Set up a cron job to regularly backup your database:

```bash
0 0 * * * pg_dump -h your-production-db-host -U your-db-user -d your-db-name > /path/to/backups/solport_$(date +\%Y\%m\%d).sql
```

### Monitoring

You can set up monitoring using Prometheus and Grafana:

1. Install Prometheus
2. Configure it to scrape metrics from `yourdomain.com/metrics`
3. Set up Grafana to visualize the metrics

## Troubleshooting

### Database Connection Issues

Check if your database is accessible:

```bash
psql -h your-production-db-host -U your-db-user -d your-db-name
```

### Application Not Loading

Check Nginx logs:

```bash
docker-compose logs nginx
```

### API Errors

Check application logs:

```bash
docker-compose logs app
``` 