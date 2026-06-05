USERS = [
    {
        "id": "user_client_1",
        "email": "alice@example.com",
        "password": "password123",
        "role": "client",
        "name": "Alice Chen",
    },
    {
        "id": "user_client_2",
        "email": "bob@example.com",
        "password": "password123",
        "role": "client",
        "name": "Bob Martinez",
    },
    {
        "id": "user_advisor_1",
        "email": "advisor@aurawealth.com",
        "password": "advisor123",
        "role": "advisor",
        "name": "Sarah Kim",
    },
]

PORTFOLIOS = {
    "user_client_1": {
        "total_value": 485000.00,
        "risk_profile": "moderate",
        "holdings": [
            {"symbol": "AAPL", "name": "Apple Inc.", "shares": 50, "price": 189.50, "value": 9475.00, "allocation": 1.95},
            {"symbol": "VTI", "name": "Vanguard Total Market ETF", "shares": 200, "price": 245.30, "value": 49060.00, "allocation": 10.12},
            {"symbol": "BND", "name": "Vanguard Bond ETF", "shares": 300, "price": 72.10, "value": 21630.00, "allocation": 4.46},
            {"symbol": "GOOGL", "name": "Alphabet Inc.", "shares": 30, "price": 175.80, "value": 5274.00, "allocation": 1.09},
            {"symbol": "MSFT", "name": "Microsoft Corp.", "shares": 40, "price": 415.20, "value": 16608.00, "allocation": 3.43},
            {"symbol": "CASH", "name": "Cash & Equivalents", "shares": 1, "price": 382953.00, "value": 382953.00, "allocation": 79.0},
        ],
        "goals": [
            {"id": "g1", "name": "Retirement", "target": 2000000, "current": 485000, "target_year": 2045, "progress": 24.25},
            {"id": "g2", "name": "House Down Payment", "target": 150000, "current": 85000, "target_year": 2027, "progress": 56.67},
            {"id": "g3", "name": "Kids College Fund", "target": 200000, "current": 42000, "target_year": 2035, "progress": 21.0},
        ],
    },
    "user_client_2": {
        "total_value": 1250000.00,
        "risk_profile": "aggressive",
        "holdings": [
            {"symbol": "NVDA", "name": "NVIDIA Corp.", "shares": 200, "price": 875.40, "value": 175080.00, "allocation": 14.01},
            {"symbol": "TSLA", "name": "Tesla Inc.", "shares": 150, "price": 248.50, "value": 37275.00, "allocation": 2.98},
            {"symbol": "QQQ", "name": "Invesco QQQ ETF", "shares": 400, "price": 495.20, "value": 198080.00, "allocation": 15.85},
            {"symbol": "SPY", "name": "SPDR S&P 500 ETF", "shares": 500, "price": 545.80, "value": 272900.00, "allocation": 21.83},
            {"symbol": "BTC-USD", "name": "Bitcoin", "shares": 2.5, "price": 67500.00, "value": 168750.00, "allocation": 13.50},
            {"symbol": "CASH", "name": "Cash & Equivalents", "shares": 1, "price": 397915.00, "value": 397915.00, "allocation": 31.83},
        ],
        "goals": [
            {"id": "g1", "name": "Early Retirement", "target": 5000000, "current": 1250000, "target_year": 2035, "progress": 25.0},
            {"id": "g2", "name": "Vacation Home", "target": 800000, "current": 320000, "target_year": 2028, "progress": 40.0},
        ],
    },
}

MARKET_PRICES = {
    "AAPL": 189.50,
    "VTI": 245.30,
    "BND": 72.10,
    "GOOGL": 175.80,
    "MSFT": 415.20,
    "NVDA": 875.40,
    "TSLA": 248.50,
    "QQQ": 495.20,
    "SPY": 545.80,
    "BTC-USD": 67500.00,
}
