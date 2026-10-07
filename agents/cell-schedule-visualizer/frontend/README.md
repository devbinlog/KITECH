# Manufacturing Schedule Visualizer Frontend

Next.js-based interactive frontend for visualizing manufacturing schedules.

## Features

- 📊 **Metrics Dashboard** - Real-time schedule metrics display
- 📈 **Gantt Chart** - Interactive task timeline visualization
- ⚙️ **Machine Utilization** - Bar chart showing machine usage
- 📅 **Work Order Lateness** - Lateness analysis by work order
- 🔄 **Auto-refresh** - Live data updates every 5 seconds
- 🎨 **Tailwind CSS** - Modern responsive design
- 📱 **Mobile Responsive** - Works on all screen sizes

## Prerequisites

- Node.js 18+ and npm
- Python API server running (see parent README)

## Installation

```bash
npm install
```

## Configuration

Create `.env.local` from `.env.example`:

```bash
cp .env.example .env.local
```

Edit `.env.local` to point to your API server:

```
NEXT_PUBLIC_API_URL=http://localhost:5000
```

## Development

Start the development server:

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## Build

```bash
npm run build
npm run start
```

## API Endpoints

The frontend expects the following endpoints from the Python API:

- `GET /api/health` - Health check
- `GET /api/schedule` - Full schedule data
- `GET /api/schedule/gantt` - Gantt chart data
- `GET /api/schedule/metrics` - Quality metrics
- `GET /api/schedule/tasks` - Scheduled tasks
- `GET /api/schedule/utilization` - Machine utilization
- `GET /api/schedule/lateness` - Work order lateness

## Components

- **MetricsGrid** - Displays key metrics in a grid layout
- **GanttChart** - Custom Gantt chart implementation using Recharts
- **UtilizationChart** - Machine utilization bar chart
- **LatenessChart** - Work order lateness analysis

## Styling

Uses Tailwind CSS with custom color scheme:

- Primary: `#667eea`
- Secondary: `#764ba2`

## License

MIT
