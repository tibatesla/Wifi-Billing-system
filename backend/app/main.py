# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

#
from app.api.v1.endpoints import auth, mpesa, admin

app = FastAPI(
    title="Wi-Fi Billing SaaS API",
    description="Multi-tenant backend for ISP hotspot management.",
    version="1.0.0"
)

# Configure CORS for the React Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "https://production-frontend.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(mpesa.router, prefix="/api/v1/mpesa", tags=["M-Pesa Integration"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["Admin Dashboard"])
# app.include_router(routers.router, prefix="/api/v1/routers", tags=["Router Management"])

@app.get("/health")
async def health_check():
    return {"status": "online", "message": "Wi-Fi SaaS Backend is running."}