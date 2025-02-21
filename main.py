from datetime import datetime
import os
import uuid

from fastapi import FastAPI, Request
from dotenv import load_dotenv
import uvicorn
from netopia_sdk.config import Config
from netopia_sdk.client import PaymentClient
from netopia_sdk.payment import PaymentService
from netopia_sdk.requests.models import (
    StartPaymentRequest, ConfigData, PaymentData, PaymentOptions, Instrument,
    OrderData, BillingData, ShippingData, ProductsData
)

# ✅ Load environment variables
load_dotenv()

# ✅ Read values from .env file
API_KEY = os.getenv("API_KEY")
POS_SIGNATURE = os.getenv("POS_SIGNATURE")
IS_LIVE = os.getenv("IS_LIVE", "False").lower() in ["true", "1", "yes"]
NOTIFY_URL = os.getenv("NOTIFY_URL")
REDIRECT_URL = os.getenv("REDIRECT_URL")
PUBLIC_KEY = os.getenv("PUBLIC_KEY")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")

# ✅ Configure Netopia Payment SDK using environment variables
config = Config(
    api_key=API_KEY,
    pos_signature=POS_SIGNATURE,
    is_live=IS_LIVE,
    notify_url=NOTIFY_URL,
    redirect_url=REDIRECT_URL,
    public_key_str=PUBLIC_KEY,
    pos_signature_set=[PRIVATE_KEY],  # Ensure correct formatting
)

client = PaymentClient(config)
payment_service = PaymentService(client)

# ✅ Define payment request data
start_payment_request = StartPaymentRequest(
    config=ConfigData(
        emailTemplate="default",
        emailSubject="Order Confirmation",
        cancelUrl=REDIRECT_URL,
        notifyUrl=config.notify_url,
        redirectUrl=config.redirect_url,
        language="ro",
    ),
    payment=PaymentData(
        options=PaymentOptions(installments=1, bonus=0),
        data={"ceva cheie": "ceva valoare"},
        instrument=Instrument(
            type="card",
            account="4111111111111111",  # ✅ Use a valid test card
            expMonth=12,
            expYear=2025,
            secretCode="123",
            token="ceva",
            clientID="123",
        ),
    ),
    order=OrderData(
        orderID=str(uuid.uuid4()),  # ✅ Ensure orderID is unique
        amount=1.0,
        currency="RON",
        description="Comanda de plata test",
        ntpID="",  # Let Netopia generate it
        posSignature=POS_SIGNATURE,  # ✅ Ensure this is correct
        dateTime=datetime.now().isoformat(),  # ✅ Use ISO timestamp
        shipping=ShippingData(
            email="customer@example.com",
            phone="1234567890",
            firstName="John",
            lastName="Doe",
            city="Bucharest",
            country=642,
            countryName="ROMANIA",
            state="romania state",
            postalCode="550055",
            details="ceva detalii aici"
        ),
        installments={},  # ✅ Ensure correct format
        data={"order data key": "order data value"},
        billing=BillingData(
            email="customer@example.com",
            phone="1234567890",
            firstName="John",
            lastName="Doe",
            city="Bucharest",
            country=642,
            countryName="ROMANIA",
            state="romania state",
            postalCode="550055",
            details="ceva detalii aici"
        ),
        products=[
            ProductsData(name="Product1", code="P001", category="Category1", price=1.0, vat=0),
        ],
    ),
)

# ✅ Start Payment
response = payment_service.start_payment(start_payment_request)
print("Start Payment Response:", response)

# ✅ Get Payment Status
response = payment_service.get_status(ntpID=str(uuid.uuid4()), orderID="R12345")
print("Order Status Response:", response)

# ✅ Verify 3D Secure Auth
response = payment_service.verify_auth(
    authenticationToken="authToken123",
    ntpID="ntpID-123456",
    formData={"paRes": "paResData"},
)
print("VerifyAuth Response:", response)

# ✅ Initialize FastAPI for IPN Verification
app = FastAPI()

@app.post("/ipn")
async def ipn_handler(request: Request):
    """Handles Netopia IPN (Instant Payment Notification) verification."""
    try:
        ipn_data = await request.body()
        result = payment_service.verify_ipn(ipn_data)
        return {"message": "IPN verified", "data": result}
    except Exception as e:
        return {"error": str(e)}

# ✅ Run Uvicorn when executing this script directly
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)