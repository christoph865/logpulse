# LogPulse Dashboard

A modern, real-time React dashboard for monitoring events and analytics.

## Features

- 📊 Real-time event analytics and statistics
- 🔴 Severity-based color coding (CRITICAL, ERROR, WARNING, INFO)
- 📈 Interactive charts (Pie charts, Bar charts, Time series)
- 🔔 Real-time alerts for critical events
- 📋 Filterable event table
- 🔐 JWT authentication
- 🎨 Responsive design (desktop and mobile)
- 🔄 Auto-refresh dashboard (every 10 seconds)

## Tech Stack

- **Frontend**: React 18 + Vite
- **Charts**: Recharts
- **Styling**: Tailwind CSS
- **HTTP Client**: Axios
- **Authentication**: JWT Bearer tokens

## Prerequisites

- Node.js 18+
- npm or yarn
- LogPulse backend running on `localhost:8000`

## Installation

### Option 1: Docker (Recommended)

The frontend is included in the docker-compose setup. Just run:

```bash
cd /Users/christoph/Desktop/PROJECTS/logpulse

# Start all services including frontend
docker-compose up -d

# Dashboard will be available at http://localhost:3000
```

### Option 2: Local Development

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev

# Dashboard will be available at http://localhost:5173
```

### Option 3: Production Build

```bash
cd frontend

# Install dependencies
npm install

# Build for production
npm run build

# Preview production build
npm run preview
```

## Configuration

### Environment Variables

Create `.env.local` file in the frontend directory (optional):

```
VITE_API_URL=http://localhost:8000
```

The frontend automatically detects the API URL from the browser location.

## Usage

### 1. Login

Open http://localhost:3000 in your browser

**Demo Credentials:**
- Username: `newuser`
- Password: `TestPass123`

Or register a new account:
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username":"your_username",
    "email":"your@email.com",
    "password":"YourPassword123"
  }'
```

### 2. Dashboard Layout

**Summary Cards (Top)**
- Total Events: Count of all events
- Critical: Count of CRITICAL severity events
- Errors: Count of ERROR severity events
- Warnings: Count of WARNING severity events

**Charts (Middle)**
- Events by Severity: Pie chart showing distribution
- Events by Type: Bar chart showing event types

**Critical Alerts (if any)**
- Recent CRITICAL severity events
- Quick action list for urgent items

**Recent Events (Bottom)**
- Table of last 10 events
- Sortable by severity, source, type
- Click to see full event details

### 3. Real-Time Updates

The dashboard automatically refreshes every 10 seconds to show:
- New events
- Updated statistics
- Latest alerts

No manual refresh needed!

## API Integration

The dashboard connects to LogPulse API endpoints:

```
GET  /api/v1/events                  → List all events
GET  /api/v1/analytics/summary       → Get summary statistics
POST /api/v1/auth/login              → Authenticate user
```

All requests include JWT token in `Authorization: Bearer {token}` header.

## Component Structure

```
Dashboard/
├── Login Screen
│   ├── Username input
│   ├── Password input
│   └── Login button
└── Main Dashboard
    ├── Header (with logout button)
    ├── Summary Cards
    │   ├── Total Events
    │   ├── Critical Count
    │   ├── Error Count
    │   └── Warning Count
    ├── Charts
    │   ├── Severity Pie Chart
    │   └── Events By Type Bar Chart
    ├── Critical Alerts Section
    └── Recent Events Table
```

## Styling

The dashboard uses Tailwind CSS for styling with:

- Blue gradient backgrounds
- Severity-based color scheme:
  - 🔴 CRITICAL: Red (#dc2626)
  - 🟠 ERROR: Orange (#ea580c)
  - 🟡 WARNING: Yellow (#eab308)
  - 🟢 INFO: Green (#22c55e)

## Responsive Design

- ✅ Desktop (1920px and above)
- ✅ Laptop (1024px - 1920px)
- ✅ Tablet (768px - 1024px)
- ✅ Mobile (< 768px)

Charts and tables automatically adapt to screen size.

## Performance

- Lightweight bundle size
- Efficient re-renders with React hooks
- Optimized chart rendering
- Automatic data refresh (10-second interval)
- JWT token stored in localStorage for persistence

## Security

- JWT authentication required for all API calls
- Bearer token validation on backend
- Password hashing with bcrypt
- No sensitive data stored in localStorage (only JWT token)
- CORS configured to allow frontend-backend communication

## Troubleshooting

### Dashboard shows "No data yet"

1. Check if backend is running: `curl http://localhost:8000/health`
2. Check if you've sent some events:
   ```bash
   TOKEN="your_jwt_token"
   curl -X POST http://localhost:8000/api/v1/events \
     -H "Authorization: Bearer $TOKEN" \
     -d '{"source":"test","event_type":"error","severity":"ERROR","message":"Test"}'
   ```
3. Wait 10 seconds for dashboard to refresh

### "Cannot connect to backend" error

1. Verify backend is running on `localhost:8000`
2. Check CORS configuration in `app/core/config.py`
3. Ensure frontend URL is in `CORS_ORIGINS` list
4. Check browser console for detailed error message

### Token expired

Simply logout and login again to get a new token.

### Chart not rendering

1. Check browser console for JavaScript errors
2. Ensure Recharts library is properly installed
3. Try clearing browser cache and hard refresh (Cmd+Shift+R)

## Development

### Available Scripts

```bash
# Start dev server with hot reload
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Run linter
npm run lint
```

### Adding New Features

1. Create new component in `src/` directory
2. Import into `Dashboard.jsx`
3. Add API call using axios
4. Add state management with useState/useEffect
5. Test with real events

### Example: Adding a New Chart

```jsx
// In Dashboard.jsx
const [customData, setCustomData] = useState([]);

useEffect(() => {
  if (isLoggedIn) {
    // Fetch your custom data
    const fetchCustomData = async () => {
      const res = await axios.get(
        `${API_BASE}/your-endpoint`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setCustomData(res.data);
    };
    fetchCustomData();
  }
}, [isLoggedIn, token]);

// In JSX
<div className="bg-white rounded-lg shadow p-6">
  <h2 className="text-xl font-bold mb-4">Your Chart Title</h2>
  <ResponsiveContainer width="100%" height={300}>
    {/* Your Recharts component */}
  </ResponsiveContainer>
</div>
```

## Docker Support

### Build Docker Image

```bash
docker build -f frontend/Dockerfile -t logpulse-dashboard:latest ./frontend
```

### Run Docker Container

```bash
docker run -p 3000:3000 logpulse-dashboard:latest
```

### With Docker Compose

```bash
docker-compose up -d frontend
```

## License

MIT

## Support

For issues or questions:
1. Check troubleshooting section above
2. Review browser console for errors
3. Check backend logs: `docker-compose logs app`
4. Check frontend logs: `docker-compose logs frontend`

---

**Happy monitoring! 🚀**
