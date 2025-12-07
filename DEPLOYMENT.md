# Frameshift Deployment Guide 🚀

## Quick Start (Development)

The application is currently running at **http://localhost:3000**

```bash
cd frameshift
npm install
npm run dev
```

## Environment Configuration

Create `.env.local` with your API keys:

```env
# Required for Grok (optional context analysis)
GROK_API_KEY=your_grok_api_key_here
GROK_API_BASE=https://api.x.ai

# Required for Veo 3.1 (primary video processing engine)
VEO_API_KEY=your_veo_api_key_here
VEO_API_BASE=https://generativelanguage.googleapis.com

# Next.js configuration
NEXTAUTH_SECRET=your_nextauth_secret_here
NEXTAUTH_URL=http://localhost:3000
```

## Production Deployment

### 1. Vercel (Recommended)

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel

# Set environment variables in Vercel dashboard
vercel env add GROK_API_KEY
vercel env add VEO_API_KEY
# ... etc
```

### 2. Manual Build

```bash
npm run build
npm start
```

### 3. Docker (Optional)

```dockerfile
FROM node:18-alpine

WORKDIR /app
COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

EXPOSE 3000
CMD ["npm", "start"]
```

## API Integration Notes

### Grok Integration
- **Graceful Degradation**: App works without Grok
- **Rate Limiting**: Implement appropriate limits for production
- **Error Handling**: All failures are logged but don't break the flow

### Veo 3.1 Integration
- **Critical Component**: Required for core functionality
- **Timeout Handling**: Long-running video processing may need timeout adjustments
- **File Upload Limits**: Configure for your expected video file sizes

## Security Checklist

- [ ] API keys stored securely in environment variables
- [ ] CORS configured for production domains
- [ ] File upload validation implemented
- [ ] Rate limiting configured for API endpoints
- [ ] HTTPS enabled in production

## Performance Optimization

### Next.js Optimizations
- Static generation for marketing pages
- Image optimization for thumbnails
- Code splitting for large components

### Video Processing
- Stream processing for large files
- Background job processing for long operations
- CDN integration for video storage

## Monitoring & Analytics

Recommended integrations:
- **Vercel Analytics**: Built-in performance monitoring
- **Sentry**: Error tracking and performance monitoring
- **LogRocket**: User session recording
- **Mixpanel/Amplitude**: Product analytics

## Scaling Considerations

### Database Layer (Future)
- PostgreSQL for project persistence
- Redis for session management
- S3/CloudFlare R2 for video storage

### Microservices (Future)
- Separate video processing service
- Queue system for background jobs
- Load balancing for multiple instances

---

🎬 **Your Frameshift application is ready for production!**