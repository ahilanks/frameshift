# Frameshift - AI-Powered Product Placement 🎬✨

A production-quality Next.js application that seamlessly integrates AI-powered product placement into videos using **Veo 3.1** as the primary engine and **Grok** for optional context enhancement.

## 🌟 Features

- **🎥 Video Upload**: Drag-and-drop interface supporting MP4, WebM, and MOV files
- **🎯 Smart Product Selection**: Extensive product catalog with custom product creation
- **🧠 AI Context Analysis**: Optional Grok-powered scene understanding
- **⚡ Advanced Video Processing**: Veo 3.1-driven seamless product integration
- **📊 Performance Metrics**: Detailed visibility and exposure analytics
- **🔄 Project Management**: Track and manage multiple video projects
- **💻 Modern UI**: Beautiful, responsive design inspired by Figma/Notion aesthetics

## 🏗️ Architecture

### Core Principles
- **Veo 3.1**: Primary engine for video understanding, placement logic, and generation
- **Grok**: Optional lightweight context extraction and scene analysis
- **No Mocks**: Real API integrations throughout the application
- **Production-Ready**: Built with enterprise-grade patterns and error handling

### Tech Stack
- **Frontend**: Next.js 15+ (App Router), TypeScript, Tailwind CSS v4
- **UI Components**: Radix UI primitives with custom styling
- **State Management**: React hooks with sessionStorage persistence
- **API Integration**: Real HTTP clients for Grok and Veo services

## 🚀 Getting Started

### Prerequisites
- Node.js 18+
- npm, yarn, or pnpm
- API keys for Grok and Veo 3.1

### Installation

1. **Clone and Install**:
```bash
git clone <repository-url>
cd frameshift
npm install
```

2. **Environment Setup**:
```bash
cp .env.example .env.local
```

Edit `.env.local` with your API keys:
```env
GROK_API_KEY=your_grok_api_key_here
GROK_API_BASE=https://api.x.ai

VEO_API_KEY=your_veo_api_key_here
VEO_API_BASE=https://generativelanguage.googleapis.com
```

3. **Start Development Server**:
```bash
npm run dev
```

4. **Open Application**:
Visit [http://localhost:3000](http://localhost:3000)

## 🔧 API Configuration

### Grok Integration (Optional Context)
- **Purpose**: Scene analysis and natural language context extraction
- **Fallback**: Application continues without Grok if unavailable
- **Location**: `src/lib/grokClient.ts`

### Veo 3.1 Integration (Primary Engine)
- **Purpose**: Main video processing, product placement, and generation
- **Criticality**: Required for core functionality
- **Location**: `src/lib/veoClient.ts`

## 📁 Project Structure

```
src/
├── app/                    # Next.js App Router pages
│   ├── page.tsx           # Upload & configuration page
│   ├── analysis/          # AI processing & progress page
│   ├── result/            # Results with metrics & download
│   ├── projects/          # Project management dashboard
│   └── api/               # API routes for processing
├── components/            # Reusable UI components
│   ├── ui/                # Base UI components
│   ├── upload/            # Upload-specific components
│   └── layout/            # Layout components
├── lib/                   # Core utilities and clients
│   ├── grokClient.ts      # Grok API integration
│   ├── veoClient.ts       # Veo 3.1 API integration
│   └── utils.ts           # Shared utilities
└── types/                 # TypeScript type definitions
```

## 🎯 User Flow

1. **Upload Video**: Drag-and-drop video file with real-time validation
2. **Configure Preferences**: Set target audience and brand preferences (optional)
3. **Select Product**: Choose from catalog or create custom product
4. **AI Analysis**:
   - Grok extracts optional scene context
   - Veo 3.1 analyzes video and determines placement strategy
5. **Processing**: Veo 3.1 generates enhanced video with product placement
6. **Results**: View metrics, download enhanced video, manage projects

## 🔄 Processing Pipeline

### Step 1: Optional Context Extraction (Grok)
- Analyzes uploaded video content
- Provides scene description and context
- Gracefully degrades if unavailable

### Step 2: Video Intelligence (Veo 3.1)
- Semantic understanding of video content
- Identifies optimal placement opportunities
- Determines timing and positioning

### Step 3: Product Integration (Veo 3.1)
- Natural product placement within scene
- Maintains lighting and physics consistency
- Preserves temporal continuity

### Step 4: Output Generation (Veo 3.1)
- Generates complete edited video
- Calculates performance metrics
- Provides downloadable result

## 📊 Metrics & Analytics

- **Visibility Percentage**: How much of the video features the product
- **Exposure Duration**: Total time product is visible
- **Scene Modification Range**: Specific timestamps of edits
- **Processing Performance**: Time and efficiency metrics

## 🛠️ Development

### Build for Production
```bash
npm run build
npm start
```

### Linting
```bash
npm run lint
```

### Type Checking
```bash
npx tsc --noEmit
```

## 🚀 Deployment

### Vercel (Recommended)
```bash
npm i -g vercel
vercel
```

### Environment Variables for Production
Ensure all environment variables are configured in your deployment platform:
- `GROK_API_KEY`
- `GROK_API_BASE`
- `VEO_API_KEY`
- `VEO_API_BASE`

## 🔧 Customization

### Adding New Products
Edit `src/components/upload/product-selector.tsx` to modify the product catalog.

### UI Theming
Tailwind configuration can be customized via the CSS variables in `src/app/globals.css`.

### API Endpoints
Extend processing capabilities by modifying `src/app/api/process/route.ts`.

## 📝 License

This project is built for demonstration purposes. Ensure you have proper licensing for Grok and Veo 3.1 APIs in production.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

**Built with ❤️ using Next.js, Veo 3.1, and Grok AI**
