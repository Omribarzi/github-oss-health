# Nadlan IL - Israeli Commercial Real Estate Marketplace

A comprehensive commercial real estate (CRE) platform for the Israeli market, inspired by VTS. Manages property listings, deal pipelines, tenant interactions, and market analytics.

## Features

### Property Management
- Full property lifecycle management with Hebrew/English bilingual support
- Support for office, retail, industrial, logistics, coworking, and mixed-use properties
- Property units, floor plans, and building specifications
- Israeli-specific fields: arnona zones, building classification, accessibility

### Listings & Search
- Advanced search with filters: city, property type, price range, area, amenities
- Listing types: lease, sublease, sale
- Israeli pricing: monthly rent in ILS, management fees, arnona
- Engagement tracking: views, inquiries, tours

### Deal Pipeline
- Full deal lifecycle: Inquiry -> Tour -> Proposal -> Negotiation -> LOI -> Legal Review -> Signed
- Pipeline visualization with stage-by-stage tracking
- Activity logging for complete deal history
- Role-based access: landlords, tenants, brokers

### Market Analytics
- City-level and property-type breakdowns
- Price trends and market snapshots
- Deal pipeline analytics with total value tracking
- Occupancy rates and days-on-market metrics

### Israeli Market Focus
- RTL (Right-to-Left) Hebrew UI
- All 20 major Israeli cities
- Prices in ILS (Israeli New Shekel)
- Area in square meters
- Israeli property standards and classifications

## Architecture

- **Backend**: Python + FastAPI + PostgreSQL + SQLAlchemy + Alembic
- **Frontend**: React 19 + Vite + Recharts
- **Auth**: JWT-based with role support (landlord, tenant, broker, admin)
- **Database**: PostgreSQL with full migration support

## Quick Start

### Docker (Recommended)
```bash
docker compose up
```

Services:
- Backend API: http://localhost:8000
- API Docs (Swagger): http://localhost:8000/docs
- Frontend: http://localhost:5173

### Manual Setup

#### Backend
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
python3 app/main.py
```

#### Frontend
```bash
cd frontend
npm install
npm run dev
```

## API Endpoints

### Auth
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login
- `GET /api/auth/me` - Current user profile

### Properties
- `GET /api/properties` - List with filtering
- `GET /api/properties/{id}` - Property details
- `POST /api/properties` - Create property
- `PUT /api/properties/{id}` - Update property

### Listings
- `GET /api/listings` - Search listings
- `GET /api/listings/{id}` - Listing detail
- `POST /api/listings` - Create listing
- `PUT /api/listings/{id}` - Update listing

### Deals
- `GET /api/deals` - List deals
- `GET /api/deals/pipeline` - Pipeline view
- `POST /api/deals` - Create deal (inquiry)
- `PUT /api/deals/{id}` - Update deal stage

### Tours
- `GET /api/tours` - List tours
- `POST /api/tours` - Schedule tour
- `PUT /api/tours/{id}` - Update tour

### Analytics
- `GET /api/analytics/overview` - Market overview KPIs
- `GET /api/analytics/by-city` - City breakdown
- `GET /api/analytics/by-type` - Property type breakdown
- `GET /api/analytics/deal-pipeline` - Deal pipeline stats
- `GET /api/analytics/price-trends` - Historical price data

### Favorites
- `GET /api/favorites` - User favorites
- `POST /api/favorites/{listing_id}` - Add favorite
- `DELETE /api/favorites/{listing_id}` - Remove favorite

## Database Schema

| Table | Description |
|-------|-------------|
| `users` | Landlords, tenants, brokers, admins |
| `properties` | Commercial properties with Israeli location data |
| `property_units` | Individual units within properties |
| `listings` | Active listings for lease/sublease/sale |
| `deals` | Deal pipeline with full stage tracking |
| `tours` | Property tour scheduling |
| `favorites` | User saved listings |
| `market_snapshots` | Historical market analytics data |

## License

MIT
