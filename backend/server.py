from fastapi import FastAPI, APIRouter, HTTPException, Depends, UploadFile, File, status, Header
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import uuid
from io import BytesIO
import secrets
import requests
import base64
from urllib.parse import urlencode

# Import our custom modules
from models import *
from auth import *
from document_generator import DocumentGenerator
from file_utils import *
from payroll_endpoints import payroll_router

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app
app = FastAPI(title="Misty Manufacturing Management System", version="1.0.0")

# Create router with /api prefix
api_router = APIRouter(prefix="/api")

# Initialize document generator
doc_generator = DocumentGenerator()

# Ensure upload directories exist
ensure_upload_dirs()

# ============= AUTHENTICATION ENDPOINTS =============

@api_router.post("/auth/login", response_model=Token)
async def login(user_credentials: UserLogin):
    """Authenticate user and return JWT token"""
    user_data = await db.users.find_one({"username": user_credentials.username})
    
    if not user_data or not verify_password(user_credentials.password, user_data["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    if not user_data.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is disabled"
        )
    
    # Update last login
    await db.users.update_one(
        {"id": user_data["id"]},
        {"$set": {"last_login": datetime.utcnow()}}
    )
    
    # Create JWT token
    access_token = create_access_token(
        data={"sub": user_data["username"], "role": user_data["role"], "user_id": user_data["id"]}
    )
    
    user_info = {
        "id": user_data["id"],
        "username": user_data["username"],
        "full_name": user_data["full_name"],
        "role": user_data["role"],
        "email": user_data["email"]
    }
    
    return {"access_token": access_token, "token_type": "bearer", "user": user_info}

@api_router.post("/auth/register", response_model=StandardResponse)
async def register_user(user_data: UserCreate, current_user: dict = Depends(require_admin)):
    """Register new user (Admin only)"""
    # Check if username already exists
    existing_user = await db.users.find_one({"username": user_data.username})
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    # Check if email already exists
    existing_email = await db.users.find_one({"email": user_data.email})
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already exists")
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,
        role=user_data.role,
        full_name=user_data.full_name
    )
    
    await db.users.insert_one(new_user.dict())
    
    return StandardResponse(success=True, message="User created successfully")

@api_router.get("/auth/me")
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current user information"""
    user_data = await db.users.find_one({"id": current_user["user_id"]})
    if not user_data:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "id": user_data["id"],
        "username": user_data["username"],
        "full_name": user_data["full_name"],
        "role": user_data["role"],
        "email": user_data["email"]
    }

# ============= CLIENT MANAGEMENT ENDPOINTS =============

@api_router.get("/clients", response_model=List[Client])
async def get_clients(current_user: dict = Depends(require_any_role)):
    """Get all clients"""
    clients = await db.clients.find({"is_active": True}).to_list(1000)
    return [Client(**client) for client in clients]

@api_router.post("/clients", response_model=StandardResponse)
async def create_client(client_data: ClientCreate, current_user: dict = Depends(require_admin_or_sales)):
    """Create new client"""
    new_client = Client(**client_data.dict())
    await db.clients.insert_one(new_client.dict())
    
    return StandardResponse(success=True, message="Client created successfully", data={"id": new_client.id})

@api_router.get("/clients/{client_id}", response_model=Client)
async def get_client(client_id: str, current_user: dict = Depends(require_any_role)):
    """Get specific client"""
    client = await db.clients.find_one({"id": client_id, "is_active": True})
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    return Client(**client)

@api_router.put("/clients/{client_id}", response_model=StandardResponse)
async def update_client(client_id: str, client_data: ClientCreate, current_user: dict = Depends(require_admin_or_sales)):
    """Update client"""
    update_data = client_data.dict()
    update_data["updated_at"] = datetime.utcnow()
    
    result = await db.clients.update_one(
        {"id": client_id, "is_active": True},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Client not found")
    
    return StandardResponse(success=True, message="Client updated successfully")

@api_router.post("/clients/{client_id}/logo")
async def upload_client_logo(client_id: str, file: UploadFile = File(...), current_user: dict = Depends(require_admin_or_sales)):
    """Upload client logo"""
    # Check if client exists
    client = await db.clients.find_one({"id": client_id, "is_active": True})
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Save logo file
    try:
        file_path = await save_logo_file(file, client_id)
        file_url = get_file_url(file_path)
        
        # Update client with logo path
        await db.clients.update_one(
            {"id": client_id},
            {"$set": {"logo_path": file_path, "updated_at": datetime.utcnow()}}
        )
        
        return StandardResponse(success=True, message="Logo uploaded successfully", data={"file_url": file_url})
    
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to upload logo")

# ============= PRODUCT MANAGEMENT ENDPOINTS =============

@api_router.get("/clients/{client_id}/products", response_model=List[Product])
async def get_client_products(client_id: str, current_user: dict = Depends(require_any_role)):
    """Get products for specific client"""
    products = await db.products.find({"client_id": client_id, "is_active": True}).to_list(1000)
    return [Product(**product) for product in products]

@api_router.post("/products", response_model=StandardResponse)
async def create_product(product_data: ProductCreate, current_user: dict = Depends(require_admin_or_sales)):
    """Create new product for client"""
    new_product = Product(**product_data.dict())
    await db.products.insert_one(new_product.dict())
    
    return StandardResponse(success=True, message="Product created successfully", data={"id": new_product.id})

@api_router.get("/products/{product_id}", response_model=Product)
async def get_product(product_id: str, current_user: dict = Depends(require_any_role)):
    """Get specific product"""
    product = await db.products.find_one({"id": product_id, "is_active": True})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return Product(**product)

@api_router.put("/products/{product_id}", response_model=StandardResponse)
async def update_product(product_id: str, product_data: ProductCreate, current_user: dict = Depends(require_admin_or_sales)):
    """Update product"""
    update_data = product_data.dict()
    update_data["updated_at"] = datetime.utcnow()
    
    result = await db.products.update_one(
        {"id": product_id, "is_active": True},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return StandardResponse(success=True, message="Product updated successfully")

# ============= ORDER MANAGEMENT ENDPOINTS =============

@api_router.get("/orders", response_model=List[Order])
async def get_orders(status_filter: Optional[str] = None, current_user: dict = Depends(require_any_role)):
    """Get all orders with optional status filter"""
    query = {}
    if status_filter:
        query["status"] = status_filter
    
    orders = await db.orders.find(query).sort("created_at", -1).to_list(1000)
    return [Order(**order) for order in orders]

@api_router.post("/orders", response_model=StandardResponse)
async def create_order(order_data: OrderCreate, current_user: dict = Depends(require_admin_or_production_manager)):
    """Create new order"""
    # Get client details
    client = await db.clients.find_one({"id": order_data.client_id, "is_active": True})
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Generate order number
    order_count = await db.orders.count_documents({})
    order_number = f"ADM-{datetime.now().year}-{order_count + 1:04d}"
    
    # Calculate totals
    subtotal = sum(item.total_price for item in order_data.items)
    gst = subtotal * 0.1
    total_amount = subtotal + gst
    
    new_order = Order(
        order_number=order_number,
        client_id=order_data.client_id,
        client_name=client["company_name"],
        items=order_data.items,
        subtotal=subtotal,
        gst=gst,
        total_amount=total_amount,
        due_date=order_data.due_date,
        delivery_address=order_data.delivery_address,
        delivery_instructions=order_data.delivery_instructions,
        notes=order_data.notes,
        created_by=current_user["user_id"]
    )
    
    await db.orders.insert_one(new_order.dict())
    
    # Log initial production stage
    production_log = ProductionLog(
        order_id=new_order.id,
        stage=ProductionStage.ORDER_ENTERED,
        updated_by=current_user["user_id"],
        notes="Order created"
    )
    await db.production_logs.insert_one(production_log.dict())
    
    return StandardResponse(success=True, message="Order created successfully", data={"id": new_order.id, "order_number": order_number})

@api_router.get("/orders/{order_id}", response_model=Order)
async def get_order(order_id: str, current_user: dict = Depends(require_any_role)):
    """Get specific order"""
    order = await db.orders.find_one({"id": order_id})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    return Order(**order)

@api_router.put("/orders/{order_id}/stage", response_model=StandardResponse)
async def update_production_stage(order_id: str, stage_update: ProductionStageUpdate, current_user: dict = Depends(require_production_access)):
    """Update order production stage"""
    # Check permissions for specific actions
    user_role = current_user.get("role")
    
    # Production team can only move stages forward, not create/delete orders
    if user_role == UserRole.PRODUCTION_TEAM.value:
        if stage_update.to_stage == ProductionStage.ORDER_ENTERED:
            raise HTTPException(status_code=403, detail="Cannot move back to order entry stage")
    
    # Only admin and production manager can invoice
    if stage_update.to_stage == ProductionStage.INVOICING and not can_invoice(user_role):
        raise HTTPException(status_code=403, detail="Insufficient permissions to invoice")
    
    # Update order stage
    update_data = {
        "current_stage": stage_update.to_stage,
        "updated_at": datetime.utcnow()
    }
    
    # If moving to completed, set completion date
    if stage_update.to_stage == ProductionStage.CLEARED:
        update_data["completed_at"] = datetime.utcnow()
        update_data["status"] = OrderStatus.COMPLETED
    
    result = await db.orders.update_one(
        {"id": order_id},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Log production stage change
    production_log = ProductionLog(
        order_id=order_id,
        stage=stage_update.to_stage,
        updated_by=current_user["user_id"],
        notes=stage_update.notes
    )
    await db.production_logs.insert_one(production_log.dict())
    
    return StandardResponse(success=True, message="Production stage updated successfully")

# ============= JOB SPECIFICATION ENDPOINTS =============

@api_router.post("/job-specifications", response_model=StandardResponse)
async def create_job_specification(spec_data: JobSpecificationCreate, current_user: dict = Depends(require_admin_or_production_manager)):
    """Create job specification"""
    new_spec = JobSpecification(**spec_data.dict(), created_by=current_user["user_id"])
    await db.job_specifications.insert_one(new_spec.dict())
    
    return StandardResponse(success=True, message="Job specification created successfully", data={"id": new_spec.id})

@api_router.get("/orders/{order_id}/job-specification", response_model=JobSpecification)
async def get_job_specification_by_order(order_id: str, current_user: dict = Depends(require_any_role)):
    """Get job specification for order"""
    spec = await db.job_specifications.find_one({"order_id": order_id})
    if not spec:
        raise HTTPException(status_code=404, detail="Job specification not found")
    
    return JobSpecification(**spec)

# ============= PRODUCTION BOARD ENDPOINTS =============

@api_router.get("/production/board")
async def get_production_board(current_user: dict = Depends(require_any_role)):
    """Get production board with orders grouped by stage"""
    # Get all active orders
    orders = await db.orders.find({"status": {"$ne": OrderStatus.COMPLETED}}).to_list(1000)
    
    # Group orders by production stage
    board = {}
    for stage in ProductionStage:
        if stage != ProductionStage.CLEARED:  # Don't show cleared orders on board
            board[stage.value] = []
    
    for order in orders:
        stage = order.get("current_stage", ProductionStage.ORDER_ENTERED.value)
        if stage in board:
            # Get client info for logo
            client = await db.clients.find_one({"id": order["client_id"]})
            order_info = {
                "id": order["id"],
                "order_number": order["order_number"],
                "client_name": order["client_name"],
                "client_logo": get_file_url(client.get("logo_path", "")) if client else None,
                "due_date": order["due_date"],
                "total_amount": order["total_amount"],
                "items": order["items"],
                "delivery_address": order.get("delivery_address"),
                "is_overdue": datetime.fromisoformat(order["due_date"].replace("Z", "+00:00")) < datetime.utcnow() if isinstance(order["due_date"], str) else order["due_date"] < datetime.utcnow()
            }
            board[stage].append(order_info)
    
    return {"success": True, "data": board}

@api_router.get("/production/logs/{order_id}")
async def get_production_logs(order_id: str, current_user: dict = Depends(require_any_role)):
    """Get production logs for order"""
    logs = await db.production_logs.find({"order_id": order_id}).sort("timestamp", 1).to_list(1000)
    return {"success": True, "data": logs}

# ============= REPORTS ENDPOINTS =============

@api_router.get("/reports/outstanding-jobs")
async def get_outstanding_jobs_report(current_user: dict = Depends(require_admin_or_production_manager)):
    """Generate outstanding jobs report"""
    # Count jobs by stage
    jobs_by_stage = {}
    total_jobs = 0
    overdue_jobs = 0
    jobs_due_today = 0
    jobs_due_this_week = 0
    
    now = datetime.utcnow()
    today_end = now.replace(hour=23, minute=59, second=59)
    week_end = now + timedelta(days=7)
    
    # Get all active orders
    orders = await db.orders.find({"status": {"$ne": OrderStatus.COMPLETED}}).to_list(1000)
    
    for order in orders:
        stage = order.get("current_stage", ProductionStage.ORDER_ENTERED.value)
        jobs_by_stage[stage] = jobs_by_stage.get(stage, 0) + 1
        total_jobs += 1
        
        due_date = order["due_date"]
        if isinstance(due_date, str):
            due_date = datetime.fromisoformat(due_date.replace("Z", "+00:00"))
        
        if due_date < now:
            overdue_jobs += 1
        elif due_date <= today_end:
            jobs_due_today += 1
        elif due_date <= week_end:
            jobs_due_this_week += 1
    
    report = OutstandingJobsReport(
        total_jobs=total_jobs,
        jobs_by_stage=jobs_by_stage,
        overdue_jobs=overdue_jobs,
        jobs_due_today=jobs_due_today,
        jobs_due_this_week=jobs_due_this_week
    )
    
    return {"success": True, "data": report.dict()}

@api_router.get("/reports/late-deliveries")
async def get_late_deliveries_report(current_user: dict = Depends(require_admin_or_production_manager)):
    """Generate late deliveries report"""
    # Get completed orders that were delivered late
    completed_orders = await db.orders.find({"status": OrderStatus.COMPLETED}).to_list(1000)
    
    late_deliveries = []
    for order in completed_orders:
        due_date = order["due_date"]
        completed_date = order.get("completed_at")
        
        if completed_date and due_date:
            if isinstance(due_date, str):
                due_date = datetime.fromisoformat(due_date.replace("Z", "+00:00"))
            if isinstance(completed_date, str):
                completed_date = datetime.fromisoformat(completed_date.replace("Z", "+00:00"))
            
            if completed_date > due_date:
                delay_days = (completed_date - due_date).days
                late_deliveries.append({
                    "order": order,
                    "delay_days": delay_days,
                    "client_name": order["client_name"]
                })
    
    # Calculate statistics
    total_late = len(late_deliveries)
    avg_delay = sum(ld["delay_days"] for ld in late_deliveries) / total_late if total_late > 0 else 0
    
    # Group by client
    late_by_client = {}
    for ld in late_deliveries:
        client = ld["client_name"]
        late_by_client[client] = late_by_client.get(client, 0) + 1
    
    # Group by month
    late_by_month = {}
    for ld in late_deliveries:
        completed_date = ld["order"]["completed_at"]
        if isinstance(completed_date, str):
            completed_date = datetime.fromisoformat(completed_date.replace("Z", "+00:00"))
        month_key = completed_date.strftime("%Y-%m")
        late_by_month[month_key] = late_by_month.get(month_key, 0) + 1
    
    report = LateDeliveryReport(
        total_late_deliveries=total_late,
        average_delay_days=avg_delay,
        late_deliveries_by_client=late_by_client,
        late_deliveries_by_month=late_by_month
    )
    
    return {"success": True, "data": report.dict()}

@api_router.get("/reports/customer-annual/{client_id}")
async def get_customer_annual_report(client_id: str, year: int, current_user: dict = Depends(require_admin_or_production_manager)):
    """Generate customer annual report"""
    # Get client info
    client = await db.clients.find_one({"id": client_id})
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Get orders for the year
    start_date = datetime(year, 1, 1)
    end_date = datetime(year + 1, 1, 1)
    
    orders = await db.orders.find({
        "client_id": client_id,
        "created_at": {"$gte": start_date, "$lt": end_date}
    }).to_list(1000)
    
    # Calculate statistics
    total_orders = len(orders)
    total_revenue = sum(order["total_amount"] for order in orders)
    avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
    
    # Orders by month
    orders_by_month = {}
    revenue_by_month = {}
    for i in range(1, 13):
        month_key = f"{year}-{i:02d}"
        orders_by_month[month_key] = 0
        revenue_by_month[month_key] = 0
    
    for order in orders:
        created_date = order["created_at"]
        if isinstance(created_date, str):
            created_date = datetime.fromisoformat(created_date.replace("Z", "+00:00"))
        month_key = created_date.strftime("%Y-%m")
        if month_key in orders_by_month:
            orders_by_month[month_key] += 1
            revenue_by_month[month_key] += order["total_amount"]
    
    # Top products
    product_stats = {}
    for order in orders:
        for item in order["items"]:
            product_name = item["product_name"]
            if product_name not in product_stats:
                product_stats[product_name] = {"quantity": 0, "revenue": 0, "orders": 0}
            product_stats[product_name]["quantity"] += item["quantity"]
            product_stats[product_name]["revenue"] += item["total_price"]
            product_stats[product_name]["orders"] += 1
    
    top_products = sorted(
        [{"product": k, **v} for k, v in product_stats.items()],
        key=lambda x: x["revenue"],
        reverse=True
    )[:5]
    
    # On-time delivery rate
    completed_orders = [o for o in orders if o.get("completed_at")]
    on_time_orders = 0
    for order in completed_orders:
        due_date = order["due_date"]
        completed_date = order["completed_at"]
        
        if isinstance(due_date, str):
            due_date = datetime.fromisoformat(due_date.replace("Z", "+00:00"))
        if isinstance(completed_date, str):
            completed_date = datetime.fromisoformat(completed_date.replace("Z", "+00:00"))
        
        if completed_date <= due_date:
            on_time_orders += 1
    
    on_time_rate = (on_time_orders / len(completed_orders)) * 100 if completed_orders else 0
    
    report = CustomerAnnualReport(
        client_id=client_id,
        client_name=client["company_name"],
        year=year,
        total_orders=total_orders,
        total_revenue=total_revenue,
        average_order_value=avg_order_value,
        orders_by_month=orders_by_month,
        revenue_by_month=revenue_by_month,
        top_products=top_products,
        on_time_delivery_rate=on_time_rate
    )
    
    return {"success": True, "data": report.dict()}

# ============= DOCUMENT GENERATION ENDPOINTS =============

@api_router.get("/documents/acknowledgment/{order_id}")
async def generate_acknowledgment(order_id: str, current_user: dict = Depends(require_any_role)):
    """Generate order acknowledgment PDF"""
    # Get order and client data
    order = await db.orders.find_one({"id": order_id})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    client = await db.clients.find_one({"id": order["client_id"]})
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Prepare data for PDF generation
    order_data = {
        "order_number": order["order_number"],
        "invoice_number": f"INV-{order['order_number']}",
        "due_date": order["due_date"].strftime("%d/%m/%Y") if isinstance(order["due_date"], datetime) else order["due_date"],
        "client_name": client["company_name"],
        "client_address": f"{client['address']}, {client['city']}, {client['state']} {client['postal_code']}",
        "client_email": client["email"],
        "client_phone": client["phone"],
        "client_payment_terms": client.get("payment_terms", "Net 30 days"),
        "client_lead_time_days": client.get("lead_time_days", 7),
        "delivery_instructions": order.get("delivery_instructions", "Standard delivery terms apply."),
        "items": order["items"],
        "subtotal": order["subtotal"],
        "gst": order["gst"],
        "total_amount": order["total_amount"],
        "bank_details": client.get("bank_details")
    }
    
    # Generate PDF
    pdf_content = doc_generator.generate_order_acknowledgment(order_data)
    
    return StreamingResponse(
        BytesIO(pdf_content),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=acknowledgment_{order['order_number']}.pdf"}
    )

@api_router.get("/documents/job-card/{order_id}")
async def generate_job_card(order_id: str, current_user: dict = Depends(require_production_access)):
    """Generate job card PDF"""
    order = await db.orders.find_one({"id": order_id})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Get job specifications if available
    job_spec = await db.job_specifications.find_one({"order_id": order_id})
    
    # Get product specifications
    specifications = None
    if order["items"] and len(order["items"]) > 0:
        product_id = order["items"][0].get("product_id")
        if product_id:
            product = await db.products.find_one({"id": product_id})
            if product:
                specifications = product.get("specifications")
    
    job_data = {
        "order_number": order["order_number"],
        "client_name": order["client_name"],
        "due_date": order["due_date"].strftime("%d/%m/%Y") if isinstance(order["due_date"], datetime) else order["due_date"],
        "current_stage": order.get("current_stage", "order_entered"),
        "specifications": specifications,
        "job_specification": job_spec
    }
    
    pdf_content = doc_generator.generate_job_card(job_data)
    
    return StreamingResponse(
        BytesIO(pdf_content),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=job_card_{order['order_number']}.pdf"}
    )

@api_router.get("/documents/packing-list/{order_id}")
async def generate_packing_list(order_id: str, token: str = None, current_user: dict = Depends(require_production_access)):
    """Generate packing list PDF"""
    order = await db.orders.find_one({"id": order_id})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    order_data = {
        "order_number": order["order_number"],
        "client_name": order["client_name"],
        "delivery_address": order.get("delivery_address", "N/A"),
        "delivery_instructions": order.get("delivery_instructions"),
        "items": order["items"]
    }
    
    pdf_content = doc_generator.generate_packing_list(order_data)
    
    return StreamingResponse(
        BytesIO(pdf_content),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=packing_list_{order['order_number']}.pdf"}
    )

async def optional_auth_dependency(token: str = None, authorization: str = Header(None)):
    """Handle authentication via token parameter or Authorization header"""
    from auth import SECRET_KEY, ALGORITHM
    from jose import jwt, JWTError
    
    try:
        # Try token from query parameter first
        if token:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id = payload.get("user_id") or payload.get("sub")
            if not user_id:
                raise HTTPException(status_code=401, detail="Invalid token")
            
            # Get user details
            user = await db.users.find_one({"user_id": user_id})
            if not user:
                raise HTTPException(status_code=401, detail="User not found")
            
            return user
            
        # Fallback to Authorization header
        elif authorization and authorization.startswith("Bearer "):
            token_header = authorization.split(" ")[1]
            payload = jwt.decode(token_header, SECRET_KEY, algorithms=[ALGORITHM])
            user_id = payload.get("user_id") or payload.get("sub")
            if not user_id:
                raise HTTPException(status_code=401, detail="Invalid token")
            
            user = await db.users.find_one({"user_id": user_id})
            if not user:
                raise HTTPException(status_code=401, detail="User not found")
            
            return user
        else:
            raise HTTPException(status_code=401, detail="Authentication required")
            
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

@api_router.get("/documents/invoice/{order_id}")
async def generate_invoice_pdf(order_id: str, token: str = None, current_user: dict = Depends(optional_auth_dependency)):
    """Generate invoice PDF"""
    order = await db.orders.find_one({"id": order_id})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    client = await db.clients.find_one({"id": order["client_id"]})
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    invoice_data = {
        "invoice_number": f"INV-{order['order_number']}",
        "order_number": order["order_number"],
        "payment_due_date": (datetime.utcnow() + timedelta(days=30)).strftime("%d/%m/%Y"),
        "client_name": client["company_name"],
        "client_address": f"{client['address']}, {client['city']}, {client['state']} {client['postal_code']}",
        "client_abn": client.get("abn", "N/A"),
        "items": order["items"],
        "subtotal": order["subtotal"],
        "gst": order["gst"],
        "total_amount": order["total_amount"]
    }
    
    pdf_content = doc_generator.generate_invoice(invoice_data)
    
    return StreamingResponse(
        BytesIO(pdf_content),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=invoice_{order['order_number']}.pdf"}
    )

# ============= XERO INTEGRATION ENDPOINTS =============

# Xero credentials (provided by user)
XERO_CLIENT_ID = "0C765F92708046D5B625162E5D42C5FB"
XERO_CLIENT_SECRET = "nOLpzNnYonx6SCW6SKw-SINB8cSX2wMIL0OWbsvXeXkj4P--"
XERO_CALLBACK_URL = "http://localhost:3000/api/xero/callback"
XERO_SCOPES = "accounting.transactions accounting.contacts.read accounting.invoices.read accounting.settings.read"

# Debug endpoint for testing
@api_router.get("/xero/debug")
async def debug_xero_config():
    """Debug endpoint to check Xero configuration"""
    return {
        "client_id": XERO_CLIENT_ID,
        "callback_url": XERO_CALLBACK_URL,
        "scopes": XERO_SCOPES,
        "expected_auth_url_start": "https://login.xero.com/identity/connect/authorize"
    }

@api_router.get("/debug/test-pdf")
async def test_pdf_download():
    """Simple test PDF for debugging download issues"""
    from reportlab.pdfgen import canvas
    from io import BytesIO
    
    buffer = BytesIO()
    c = canvas.Canvas(buffer)
    c.drawString(100, 750, "Test PDF Download")
    c.drawString(100, 730, "If you can see this, PDF downloads are working!")
    c.save()
    
    buffer.seek(0)
    
    return StreamingResponse(
        BytesIO(buffer.read()),
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=test.pdf"}
    )

import secrets
import requests
import base64
from urllib.parse import urlencode

@api_router.get("/xero/status")
async def check_xero_connection_status(current_user: dict = Depends(require_admin_or_production_manager)):
    """Check if user has active Xero connection"""
    # Check if user has stored Xero tokens
    user_tokens = await db.xero_tokens.find_one({"user_id": current_user["user_id"]})
    
    if user_tokens and user_tokens.get("access_token"):
        # TODO: Validate token is still active with Xero API
        return {"connected": True, "message": "Xero connection active"}
    else:
        return {"connected": False, "message": "No Xero connection found"}

@api_router.get("/xero/auth/url")
async def get_xero_auth_url(current_user: dict = Depends(require_admin_or_production_manager)):
    """Get Xero OAuth authorization URL"""
    # Generate secure state parameter
    state = secrets.token_urlsafe(32)
    
    # Store state for validation
    await db.xero_auth_states.insert_one({
        "state": state,
        "user_id": current_user["user_id"],
        "created_at": datetime.utcnow()
    })
    
    # Build authorization URL
    auth_params = {
        "response_type": "code",
        "client_id": XERO_CLIENT_ID,
        "redirect_uri": XERO_CALLBACK_URL,
        "scope": XERO_SCOPES,
        "state": state
    }
    
    auth_url = f"https://login.xero.com/identity/connect/authorize?{urlencode(auth_params)}"
    
    # Debug logging
    logger.info(f"Generated Xero OAuth URL: {auth_url}")
    logger.info(f"Client ID: {XERO_CLIENT_ID}")
    logger.info(f"Callback URL: {XERO_CALLBACK_URL}")
    logger.info(f"Scopes: {XERO_SCOPES}")
    
    return {"auth_url": auth_url, "state": state, "debug_info": {
        "client_id": XERO_CLIENT_ID,
        "callback_url": XERO_CALLBACK_URL,
        "scopes": XERO_SCOPES
    }}

@api_router.get("/xero/callback")
async def handle_xero_oauth_redirect(code: str = None, state: str = None, error: str = None):
    """Handle Xero OAuth redirect - redirect to frontend callback handler"""
    if error:
        return f"<html><body><script>window.opener.postMessage({{ error: '{error}' }}, '*'); window.close();</script></body></html>"
    
    if code and state:
        # Redirect to frontend callback handler with parameters
        return f"<html><body><script>window.location.href='http://localhost:3000/xero/callback?code={code}&state={state}';</script></body></html>"
    
    return "<html><body><script>window.close();</script></body></html>"

@api_router.post("/xero/auth/callback")
async def handle_xero_callback(
    callback_data: dict,
    current_user: dict = Depends(require_admin_or_production_manager)
):
    """Handle Xero OAuth callback and exchange code for tokens"""
    auth_code = callback_data.get("code")
    state = callback_data.get("state")
    
    if not auth_code or not state:
        raise HTTPException(status_code=400, detail="Missing authorization code or state")
    
    # Validate state parameter
    stored_state = await db.xero_auth_states.find_one({
        "state": state,
        "user_id": current_user["user_id"]
    })
    
    if not stored_state:
        raise HTTPException(status_code=400, detail="Invalid state parameter")
    
    # Clean up used state
    await db.xero_auth_states.delete_one({"state": state})
    
    # Exchange code for tokens
    token_url = "https://identity.xero.com/connect/token"
    
    # Prepare authentication
    auth_string = f"{XERO_CLIENT_ID}:{XERO_CLIENT_SECRET}"
    auth_bytes = auth_string.encode('ascii')
    auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
    
    headers = {
        "Authorization": f"Basic {auth_b64}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    token_data = {
        "grant_type": "authorization_code",
        "code": auth_code,
        "redirect_uri": XERO_CALLBACK_URL
    }
    
    try:
        response = requests.post(token_url, headers=headers, data=token_data)
        response.raise_for_status()
        
        tokens = response.json()
        
        # Store tokens for user
        token_record = {
            "user_id": current_user["user_id"],
            "access_token": tokens["access_token"],
            "refresh_token": tokens["refresh_token"],
            "expires_at": datetime.utcnow() + timedelta(seconds=tokens.get("expires_in", 1800)),
            "created_at": datetime.utcnow(),
            "tenant_id": None  # Will be updated when we get tenant info
        }
        
        # Upsert token record
        await db.xero_tokens.replace_one(
            {"user_id": current_user["user_id"]},
            token_record,
            upsert=True
        )
        
        return {"message": "Xero connection successful", "access_token_expires_in": tokens.get("expires_in", 1800)}
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Xero token exchange failed: {str(e)}")
        raise HTTPException(status_code=400, detail="Failed to exchange authorization code")

@api_router.delete("/xero/disconnect")
async def disconnect_xero(current_user: dict = Depends(require_admin_or_production_manager)):
    """Disconnect from Xero"""
    # Remove stored tokens
    result = await db.xero_tokens.delete_one({"user_id": current_user["user_id"]})
    
    if result.deleted_count > 0:
        return {"message": "Xero disconnection successful"}
    else:
        return {"message": "No Xero connection found to disconnect"}

# ============= INVOICING ENDPOINTS =============

@api_router.get("/invoicing/live-jobs")
async def get_live_jobs(current_user: dict = Depends(require_admin_or_production_manager)):
    """Get all jobs ready for invoicing (completed production, not yet invoiced)"""
    live_jobs = await db.orders.find({
        "current_stage": "delivery", 
        "invoiced": {"$ne": True}
    }).to_list(length=None)
    
    # Convert ObjectId to string and enrich with client information
    for job in live_jobs:
        # Remove MongoDB ObjectId if present
        if "_id" in job:
            del job["_id"]
            
        client = await db.clients.find_one({"id": job["client_id"]})
        if client:
            job["client_name"] = client["company_name"]
            job["client_payment_terms"] = client.get("payment_terms", "Net 30 days")
        
    return {"data": live_jobs}

@api_router.post("/invoicing/generate/{job_id}")
async def generate_job_invoice(
    job_id: str,
    invoice_data: dict,
    current_user: dict = Depends(require_admin_or_production_manager)
):
    """Generate invoice for a completed job"""
    # Get job/order
    job = await db.orders.find_one({"id": job_id})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.get("invoiced"):
        raise HTTPException(status_code=400, detail="Job already invoiced")
    
    # Get client info
    client = await db.clients.find_one({"id": job["client_id"]})
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Generate invoice number (simple sequential for now)
    invoice_count = await db.invoices.count_documents({}) + 1
    invoice_number = f"INV-{invoice_count:04d}"
    
    # Prepare invoice data
    invoice_record = {
        "id": str(uuid.uuid4()),
        "invoice_number": invoice_number,
        "job_id": job_id,
        "client_id": job["client_id"],
        "invoice_type": invoice_data.get("invoice_type", "full"),  # "full" or "partial"
        "items": invoice_data.get("items", job["items"]),
        "subtotal": invoice_data.get("subtotal", job["subtotal"]),
        "gst": invoice_data.get("gst", job["gst"]),
        "total_amount": invoice_data.get("total_amount", job["total_amount"]),
        "payment_terms": client.get("payment_terms", "Net 30 days"),
        "due_date": invoice_data.get("due_date"),
        "created_by": current_user["user_id"],
        "created_at": datetime.utcnow(),
        "status": "draft"
    }
    
    # Insert invoice record
    await db.invoices.insert_one(invoice_record)
    
    # Update job status
    update_data = {
        "invoiced": True,
        "invoice_id": invoice_record["id"],
        "current_stage": "cleared",
        "updated_at": datetime.utcnow()
    }
    
    # If partial invoice, don't mark as fully invoiced
    if invoice_data.get("invoice_type") == "partial":
        update_data["invoiced"] = False
        update_data["partially_invoiced"] = True
        update_data["current_stage"] = "delivery"  # Keep in delivery stage for remaining items
    
    await db.orders.update_one(
        {"id": job_id},
        {"$set": update_data}
    )
    
    return {
        "message": "Invoice generated successfully",
        "invoice_id": invoice_record["id"],
        "invoice_number": invoice_number
    }

@api_router.get("/invoicing/archived-jobs")
async def get_archived_jobs(
    month: Optional[int] = None, 
    year: Optional[int] = None,
    current_user: dict = Depends(require_admin_or_production_manager)
):
    """Get archived jobs (completed and invoiced)"""
    # Build query filter
    query_filter = {"invoiced": True}
    
    if month and year:
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, month + 1, 1)
        
        query_filter["created_at"] = {
            "$gte": start_date,
            "$lt": end_date
        }
    
    archived_jobs = await db.orders.find(query_filter).to_list(length=None)
    
    # Enrich with client and invoice information
    for job in archived_jobs:
        # Remove MongoDB ObjectId if present
        if "_id" in job:
            del job["_id"]
            
        # Get client info
        client = await db.clients.find_one({"id": job["client_id"]})
        if client:
            job["client_name"] = client["company_name"]
        
        # Get invoice info
        if job.get("invoice_id"):
            invoice = await db.invoices.find_one({"id": job["invoice_id"]})
            if invoice:
                job["invoice_number"] = invoice["invoice_number"]
                job["invoice_date"] = invoice["created_at"]
    
    return {"data": archived_jobs}

@api_router.get("/invoicing/monthly-report")
async def get_monthly_invoicing_report(
    month: int,
    year: int,
    current_user: dict = Depends(require_admin_or_production_manager)
):
    """Generate monthly invoicing report"""
    start_date = datetime(year, month, 1)
    if month == 12:
        end_date = datetime(year + 1, 1, 1)
    else:
        end_date = datetime(year, month + 1, 1)
    
    # Get jobs completed this month
    completed_jobs = await db.orders.find({
        "updated_at": {"$gte": start_date, "$lt": end_date},
        "current_stage": "cleared"
    }).to_list(length=None)
    
    # Get jobs invoiced this month
    invoiced_jobs = await db.invoices.find({
        "created_at": {"$gte": start_date, "$lt": end_date}
    }).to_list(length=None)
    
    # Remove ObjectIds from results
    for job in completed_jobs:
        if "_id" in job:
            del job["_id"]
    
    for invoice in invoiced_jobs:
        if "_id" in invoice:
            del invoice["_id"]
    
    # Calculate totals
    total_jobs_completed = len(completed_jobs)
    total_jobs_invoiced = len(invoiced_jobs)
    total_invoice_amount = sum(inv.get("total_amount", 0) for inv in invoiced_jobs)
    
    return {
        "month": month,
        "year": year,
        "total_jobs_completed": total_jobs_completed,
        "total_jobs_invoiced": total_jobs_invoiced,
        "total_invoice_amount": total_invoice_amount,
        "completed_jobs": completed_jobs,
        "invoiced_jobs": invoiced_jobs
    }

# ============= FILE SERVING ENDPOINTS =============

@api_router.get("/uploads/{file_path:path}")
async def serve_uploaded_file(file_path: str):
    """Serve uploaded files"""
    full_path = f"/app/uploads/{file_path}"
    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(full_path)

# ============= SYSTEM ENDPOINTS =============

@api_router.get("/")
async def root():
    return {"message": "Misty Manufacturing Management System API"}

@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}

# Include the routers in the main app
app.include_router(api_router)
app.include_router(payroll_router)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for uploads
app.mount("/uploads", StaticFiles(directory="/app/uploads"), name="uploads")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_event():
    """Initialize system on startup"""
    logger.info("Starting Misty Manufacturing Management System...")
    
    # Create default admin user if not exists
    admin_user = await db.users.find_one({"username": "Callum"})
    if not admin_user:
        logger.info("Creating default admin user...")
        default_admin = User(
            username="Callum",
            email="admin@adelamerchants.com.au",
            hashed_password=get_password_hash("Peach7510"),
            role=UserRole.ADMIN,
            full_name="Callum - System Administrator"
        )
        await db.users.insert_one(default_admin.dict())
        logger.info("Default admin user created successfully")
    
    logger.info("Misty Manufacturing Management System started successfully!")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()