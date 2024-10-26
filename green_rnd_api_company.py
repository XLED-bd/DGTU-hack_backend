from fastapi import FastAPI, HTTPException, Query
from typing import Optional, List
from pydantic import BaseModel, Field
import time
from datetime import datetime

app = FastAPI(title="Зелёный Ростов - API")

class ReceiptItem(BaseModel):
    name: str
    count: float
    price: float

class Receipt(BaseModel):
    id: str
    time: str
    items: List[ReceiptItem]
    total_price: float

class Purchaser(BaseModel):
    id: str
    access: bool

purchasers_db = {
    "user1": {
        "id": "user1",
        "email": "user1@example.com",
        "phone": "79001234567",
        "access": False,
        "verification_code": None,
        "code_expires_at": None
    }
}

receipts_db = {
    "user1": [
        {
            "id": "receipt1",
            "time": "1729686754",
            "items": [
                {"name": "Джем вишнёвый дой-пак", "count": 2.0, "price": 64.50, "category": "food"},
                {"name": "Куриная грудка охлаждённая", "count": 0.980, "price": 299.99, "category": "food"}
            ],
            "total_price": 402.99
        }
    ]
}

@app.middleware("http")
async def check_auth_token(request, call_next):
    auth_token = request.headers.get("X-Auth-Token")
    if not auth_token or len(auth_token) != 2:
        raise HTTPException(status_code=401, detail="Invalid auth token")
    return await call_next(request)

# Endpoints
@app.get("/purchasers", response_model=Purchaser)
async def get_purchaser(
    email: Optional[str] = None,
    phone_number: Optional[str] = None
):
    if not email and not phone_number:
        raise HTTPException(status_code=400, detail="Either email or phone_number must be provided")
    
    # Search for purchaser
    for purchaser in purchasers_db.values():
        if (email and purchaser["email"] == email) or \
           (phone_number and purchaser["phone"] == phone_number):
            return Purchaser(id=purchaser["id"], access=purchaser["access"])
    
    raise HTTPException(status_code=404, detail="Purchaser not found")

@app.post("/purchasers/{purchaser_id}/grantAccess", status_code=204)
async def send_verification_code(purchaser_id: str):
    if purchaser_id not in purchasers_db:
        raise HTTPException(status_code=404, detail="Purchaser not found")
    
    # Generate and save verification code (in real app would send via email/SMS)
    purchasers_db[purchaser_id]["verification_code"] = "123456"
    purchasers_db[purchaser_id]["code_expires_at"] = time.time() + 300  # 5 minutes expiration
    
    return None

@app.post("/purchasers/{purchaser_id}/grantAccess/{code}", status_code=204)
async def verify_access_code(purchaser_id: str, code: str):
    if purchaser_id not in purchasers_db:
        raise HTTPException(status_code=404, detail="Purchaser not found")
    
    purchaser = purchasers_db[purchaser_id]
    current_time = time.time()
    
    if (not purchaser["verification_code"] or 
        purchaser["verification_code"] != code or 
        current_time > purchaser["code_expires_at"]):
        raise HTTPException(status_code=403, detail="Invalid or expired verification code")
    
    # Grant access and clear verification data
    purchaser["access"] = True
    purchaser["verification_code"] = None
    purchaser["code_expires_at"] = None
    
    return None

@app.get("/purchasers/{purchaser_id}/receipts", response_model=List[Receipt])
async def get_receipts(
    purchaser_id: str,
):
    
    if purchaser_id not in purchasers_db:
        raise HTTPException(status_code=404, detail="Purchaser not found")
    
    if not purchasers_db[purchaser_id]["access"]:
        raise HTTPException(status_code=403, detail="Access not granted")
    
    if purchaser_id not in receipts_db:
        raise HTTPException(status_code=404, detail="No receipts found")


    
    # Filter receipts by time range
    filtered_receipts = [
        receipt for receipt in receipts_db[purchaser_id]
    ]
    
    if not filtered_receipts:
        raise HTTPException(status_code=404, detail="No receipts found in specified time range")
    
    return filtered_receipts

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000)