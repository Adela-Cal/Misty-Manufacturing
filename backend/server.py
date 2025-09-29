from fastapi import FastAPI, APIRouter, HTTPException, Depends, UploadFile, File, status, Header
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from datetime import datetime, date, timedelta
from typing import List, Optional, Dict, Any
import uuid
from io import BytesIO
import secrets
import requests
import base64
from urllib.parse import urlencode
import asyncio

# Xero SDK imports
from xero_python.api_client import ApiClient, Configuration
from xero_python.api_client.oauth2 import OAuth2Token
from xero_python.accounting import AccountingApi
from xero_python.accounting.models import Invoice, Contact, LineItem, Contacts, Invoices

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

@api_router.get("/products", response_model=List[Product])
async def get_all_products(current_user: dict = Depends(require_any_role)):
    """Get all products"""
    products = await db.products.find({"is_active": True}).to_list(1000)
    return [Product(**product) for product in products]

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

# ============= MATERIALS MANAGEMENT ENDPOINTS =============

@api_router.get("/materials", response_model=List[Material])
async def get_materials(current_user: dict = Depends(require_any_role)):
    """Get all materials"""
    materials = await db.materials.find({"is_active": True}).to_list(1000)
    return [Material(**material) for material in materials]

@api_router.post("/materials", response_model=StandardResponse)
async def create_material(material_data: MaterialCreate, current_user: dict = Depends(require_admin_or_manager)):
    """Create new material"""
    new_material = Material(**material_data.dict())
    await db.materials.insert_one(new_material.dict())
    
    return StandardResponse(success=True, message="Material created successfully", data={"id": new_material.id})

@api_router.get("/materials/{material_id}", response_model=Material)
async def get_material(material_id: str, current_user: dict = Depends(require_any_role)):
    """Get specific material"""
    material = await db.materials.find_one({"id": material_id, "is_active": True})
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    
    return Material(**material)

@api_router.put("/materials/{material_id}", response_model=StandardResponse)
async def update_material(material_id: str, material_data: MaterialCreate, current_user: dict = Depends(require_admin_or_manager)):
    """Update material"""
    update_data = material_data.dict()
    update_data["updated_at"] = datetime.utcnow()
    
    result = await db.materials.update_one(
        {"id": material_id, "is_active": True},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Material not found")
    
    return StandardResponse(success=True, message="Material updated successfully")

@api_router.delete("/materials/{material_id}", response_model=StandardResponse)
async def delete_material(material_id: str, current_user: dict = Depends(require_admin_or_manager)):
    """Delete material (soft delete)"""
    result = await db.materials.update_one(
        {"id": material_id, "is_active": True},
        {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Material not found")
    
    return StandardResponse(success=True, message="Material deleted successfully")

# ============= SUPPLIERS ENDPOINTS =============

@api_router.get("/suppliers", response_model=List[Supplier])
async def get_suppliers(current_user: dict = Depends(require_any_role)):
    """Get all active suppliers"""
    suppliers = await db.suppliers.find({"is_active": True}).sort("supplier_name", 1).to_list(1000)
    return [Supplier(**supplier) for supplier in suppliers]

@api_router.post("/suppliers", response_model=StandardResponse)
async def create_supplier(supplier_data: SupplierCreate, current_user: dict = Depends(require_admin_or_manager)):
    """Create new supplier"""
    new_supplier = Supplier(**supplier_data.dict())
    
    await db.suppliers.insert_one(new_supplier.dict())
    
    return StandardResponse(success=True, message="Supplier created successfully", data={"id": new_supplier.id})

@api_router.get("/suppliers/{supplier_id}", response_model=Supplier)
async def get_supplier(supplier_id: str, current_user: dict = Depends(require_any_role)):
    """Get specific supplier by ID"""
    supplier = await db.suppliers.find_one({"id": supplier_id, "is_active": True})
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    
    return Supplier(**supplier)

@api_router.put("/suppliers/{supplier_id}", response_model=StandardResponse)
async def update_supplier(supplier_id: str, supplier_data: SupplierCreate, current_user: dict = Depends(require_admin_or_manager)):
    """Update supplier"""
    update_data = supplier_data.dict()
    update_data["updated_at"] = datetime.utcnow()
    
    result = await db.suppliers.update_one(
        {"id": supplier_id, "is_active": True},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Supplier not found")
    
    return StandardResponse(success=True, message="Supplier updated successfully")

@api_router.delete("/suppliers/{supplier_id}", response_model=StandardResponse)
async def delete_supplier(supplier_id: str, current_user: dict = Depends(require_admin_or_manager)):
    """Soft delete supplier"""
    result = await db.suppliers.update_one(
        {"id": supplier_id, "is_active": True},
        {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Supplier not found")
    
    return StandardResponse(success=True, message="Supplier deleted successfully")

# ============= PRODUCT SPECIFICATIONS ENDPOINTS =============

@api_router.get("/product-specifications", response_model=List[ProductSpecification])
async def get_product_specifications(current_user: dict = Depends(require_any_role)):
    """Get all product specifications"""
    specs = await db.product_specifications.find({"is_active": True}).sort("product_name", 1).to_list(1000)
    return [ProductSpecification(**spec) for spec in specs]

@api_router.post("/product-specifications", response_model=StandardResponse)
async def create_product_specification(spec_data: ProductSpecificationCreate, current_user: dict = Depends(require_admin_or_manager)):
    """Create new product specification with automatic thickness calculation"""
    # Calculate total thickness from material layers (thickness * quantity for each layer)
    calculated_thickness = sum(layer.thickness * (layer.quantity or 1.0) for layer in spec_data.material_layers)
    
    # Generate thickness options (±5%, ±10%, exact)
    thickness_options = []
    if calculated_thickness > 0:
        thickness_options = [
            round(calculated_thickness * 0.90, 3),  # -10%
            round(calculated_thickness * 0.95, 3),  # -5%
            round(calculated_thickness, 3),         # Exact
            round(calculated_thickness * 1.05, 3),  # +5%
            round(calculated_thickness * 1.10, 3),  # +10%
        ]
        # Remove duplicates and sort
        thickness_options = sorted(list(set(thickness_options)))
    
    # Create new specification with calculated values
    new_spec = ProductSpecification(
        **spec_data.dict(),
        calculated_total_thickness=calculated_thickness if calculated_thickness > 0 else None,
        thickness_options=thickness_options
    )
    
    await db.product_specifications.insert_one(new_spec.dict())
    
    return StandardResponse(success=True, message="Product specification created successfully", data={
        "id": new_spec.id, 
        "calculated_thickness": calculated_thickness,
        "thickness_options": thickness_options
    })

@api_router.get("/product-specifications/{spec_id}", response_model=ProductSpecification)
async def get_product_specification(spec_id: str, current_user: dict = Depends(require_any_role)):
    """Get specific product specification by ID"""
    spec = await db.product_specifications.find_one({"id": spec_id, "is_active": True})
    if not spec:
        raise HTTPException(status_code=404, detail="Product specification not found")
    
    return ProductSpecification(**spec)

@api_router.put("/product-specifications/{spec_id}", response_model=StandardResponse)
async def update_product_specification(spec_id: str, spec_data: ProductSpecificationCreate, current_user: dict = Depends(require_admin_or_manager)):
    """Update product specification with automatic thickness calculation"""
    # Calculate total thickness from material layers (thickness * quantity for each layer)
    calculated_thickness = sum(layer.thickness * (layer.quantity or 1.0) for layer in spec_data.material_layers)
    
    # Generate thickness options (±5%, ±10%, exact)
    thickness_options = []
    if calculated_thickness > 0:
        thickness_options = [
            round(calculated_thickness * 0.90, 3),  # -10%
            round(calculated_thickness * 0.95, 3),  # -5%
            round(calculated_thickness, 3),         # Exact
            round(calculated_thickness * 1.05, 3),  # +5%
            round(calculated_thickness * 1.10, 3),  # +10%
        ]
        # Remove duplicates and sort
        thickness_options = sorted(list(set(thickness_options)))
    
    # Prepare update data
    update_data = spec_data.dict()
    update_data.update({
        "calculated_total_thickness": calculated_thickness if calculated_thickness > 0 else None,
        "thickness_options": thickness_options,
        "updated_at": datetime.utcnow()
    })
    
    result = await db.product_specifications.update_one(
        {"id": spec_id, "is_active": True},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Product specification not found")
    
    return StandardResponse(success=True, message="Product specification updated successfully", data={
        "calculated_thickness": calculated_thickness,
        "thickness_options": thickness_options
    })

@api_router.delete("/product-specifications/{spec_id}", response_model=StandardResponse)
async def delete_product_specification(spec_id: str, current_user: dict = Depends(require_admin_or_manager)):
    """Soft delete product specification"""
    result = await db.product_specifications.update_one(
        {"id": spec_id, "is_active": True},
        {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Product specification not found")
    
    return StandardResponse(success=True, message="Product specification deleted successfully")

# ============= CALCULATORS ENDPOINTS =============

@api_router.post("/calculators/material-consumption-by-client", response_model=StandardResponse)
async def calculate_material_consumption_by_client(
    request: MaterialConsumptionByClientRequest, 
    current_user: dict = Depends(require_any_role)
):
    """Calculate material consumption for a client within date range"""
    try:
        # Get orders for client within date range
        orders = await db.orders.find({
            "client_id": request.client_id,
            "created_at": {
                "$gte": datetime.combine(request.start_date, datetime.min.time()),
                "$lte": datetime.combine(request.end_date, datetime.max.time())
            },
            "status": {"$ne": "cancelled"}
        }).to_list(1000)
        
        # Get material info
        material = await db.materials.find_one({"id": request.material_id})
        if not material:
            raise HTTPException(status_code=404, detail="Material not found")
        
        total_consumption = 0
        order_breakdown = []
        
        for order in orders:
            # Calculate material usage based on order items and product specifications
            order_consumption = 0
            for item in order["items"]:
                # This is a simplified calculation - you may need to enhance based on your business logic
                order_consumption += item["quantity"] * 1.0  # Placeholder calculation
            
            total_consumption += order_consumption
            order_breakdown.append({
                "order_number": order["order_number"],
                "order_date": order["created_at"],
                "consumption": order_consumption
            })
        
        result = CalculationResult(
            calculation_type="material_consumption_by_client",
            input_parameters={
                "client_id": request.client_id,
                "material_id": request.material_id,
                "start_date": request.start_date.isoformat(),
                "end_date": request.end_date.isoformat()
            },
            results={
                "total_consumption": total_consumption,
                "material_name": material["product_code"],
                "unit": material["unit"],
                "order_count": len(orders),
                "order_breakdown": order_breakdown
            },
            calculated_by=current_user["sub"]
        )
        
        return StandardResponse(success=True, message="Calculation completed", data=result.dict())
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Calculation failed: {str(e)}")

@api_router.post("/calculators/material-permutation", response_model=StandardResponse)
async def calculate_material_permutation(
    request: MaterialPermutationRequest,
    current_user: dict = Depends(require_any_role)
):
    """Calculate optimal material permutation for core IDs"""
    try:
        # Get product specifications for the core IDs
        core_specs = await db.product_specifications.find({
            "specifications.core_id": {"$in": request.core_ids},
            "is_active": True
        }).to_list(1000)
        
        # Calculate permutation options
        permutation_options = []
        for arrangement in _generate_permutations(request.sizes_to_manufacture, request.master_deckle_width):
            waste_percentage = _calculate_waste(arrangement, request.master_deckle_width)
            if waste_percentage <= request.acceptable_waste_percentage:
                permutation_options.append({
                    "arrangement": arrangement,
                    "waste_percentage": waste_percentage,
                    "efficiency": 100 - waste_percentage
                })
        
        # Sort by efficiency
        permutation_options.sort(key=lambda x: x["efficiency"], reverse=True)
        
        result = CalculationResult(
            calculation_type="material_permutation",
            input_parameters=request.dict(),
            results={
                "permutation_options": permutation_options[:10],  # Top 10 options
                "total_options_found": len(permutation_options)
            },
            calculated_by=current_user["sub"]
        )
        
        return StandardResponse(success=True, message="Permutation calculation completed", data=result.dict())
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Permutation calculation failed: {str(e)}")

@api_router.post("/calculators/spiral-core-consumption", response_model=StandardResponse)
async def calculate_spiral_core_consumption(
    request: SpiralCoreConsumptionRequest,
    current_user: dict = Depends(require_any_role)
):
    """Calculate material consumption for Spiral Paper Cores"""
    try:
        # Get product specification
        spec = await db.product_specifications.find_one({"id": request.product_specification_id})
        if not spec:
            raise HTTPException(status_code=404, detail="Product specification not found")
        
        if spec["product_type"] != "Spiral Paper Core":
            raise HTTPException(status_code=400, detail="Specification is not for Spiral Paper Cores")
        
        specifications = spec["specifications"]
        
        # Get material information
        material_id = specifications.get("selected_material_id")
        if not material_id:
            raise HTTPException(status_code=400, detail="No material selected in specification")
            
        material = await db.materials.find_one({"id": material_id})
        if not material:
            raise HTTPException(status_code=404, detail="Material not found")
        
        # Calculate consumption
        internal_diameter = float(specifications.get("internal_diameter", 0))
        wall_thickness = float(specifications.get("wall_thickness_required", 0))
        gsm = float(material.get("gsm", 0))
        material_thickness = float(material.get("thickness_mm", 1))
        
        # Calculate surface area per core
        outer_diameter = internal_diameter + (2 * wall_thickness)
        circumference = 3.14159 * outer_diameter
        surface_area = circumference * request.core_length  # mm²
        surface_area_m2 = surface_area / 1000000  # Convert to m²
        
        # Calculate material weight per core
        layers_required = max(1, round(wall_thickness / material_thickness))
        material_weight_per_core = surface_area_m2 * gsm * layers_required / 1000  # kg
        
        # Total consumption
        total_weight = material_weight_per_core * request.quantity
        
        result = CalculationResult(
            calculation_type="spiral_core_consumption",
            input_parameters=request.dict(),
            results={
                "material_name": material["product_code"],
                "gsm": gsm,
                "material_thickness_mm": material_thickness,
                "layers_required": layers_required,
                "internal_diameter_mm": internal_diameter,
                "outer_diameter_mm": outer_diameter,
                "wall_thickness_mm": wall_thickness,
                "core_length_mm": request.core_length,
                "surface_area_m2_per_core": round(surface_area_m2, 4),
                "material_weight_per_core_kg": round(material_weight_per_core, 4),
                "quantity": request.quantity,
                "total_material_weight_kg": round(total_weight, 2),
                "unit": material["unit"]
            },
            calculated_by=current_user["sub"]
        )
        
        return StandardResponse(success=True, message="Spiral core consumption calculated", data=result.dict())
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Spiral core calculation failed: {str(e)}")

# Helper functions for calculations
def _generate_permutations(sizes, master_width):
    """Generate possible arrangements of sizes within master width"""
    # Simplified permutation logic - you can enhance this
    arrangements = []
    for size_combo in _get_size_combinations(sizes, master_width):
        arrangements.append(size_combo)
    return arrangements

def _get_size_combinations(sizes, master_width):
    """Get combinations of sizes that fit within master width"""
    combinations = []
    # This is a simplified algorithm - implement more sophisticated logic as needed
    for size in sizes:
        width = size.get("width", 0)
        if width <= master_width:
            combinations.append([size])
    return combinations

def _calculate_waste(arrangement, master_width):
    """Calculate waste percentage for an arrangement"""
    used_width = sum(item.get("width", 0) for item in arrangement)
    waste = master_width - used_width
    return (waste / master_width) * 100 if master_width > 0 else 100

# ============= STOCKTAKE ENDPOINTS =============

@api_router.get("/stocktake/current", response_model=StandardResponse)
async def get_current_stocktake(current_user: dict = Depends(require_manager_or_admin)):
    """Get current month's stocktake or check if one is needed"""
    current_date = date.today()
    current_month = current_date.strftime("%Y-%m")
    
    # Check if stocktake exists for current month
    stocktake = await db.stocktakes.find_one({"month": current_month})
    
    # Check if it's first business day and stocktake is needed
    is_first_business_day = _is_first_business_day(current_date)
    
    if not stocktake and is_first_business_day:
        return StandardResponse(
            success=True, 
            message="Stocktake required", 
            data={
                "stocktake_required": True,
                "month": current_month,
                "first_business_day": True
            }
        )
    
    # Convert ObjectId to string if stocktake exists
    if stocktake:
        stocktake["id"] = str(stocktake["_id"])
        del stocktake["_id"]
    
    return StandardResponse(
        success=True, 
        message="Stocktake status retrieved", 
        data={
            "stocktake": stocktake,
            "stocktake_required": not bool(stocktake),
            "first_business_day": is_first_business_day
        }
    )

@api_router.post("/stocktake", response_model=StandardResponse)
async def create_stocktake(
    stocktake_data: StocktakeCreate,
    current_user: dict = Depends(require_manager_or_admin)
):
    """Create new stocktake with all materials"""
    current_month = stocktake_data.stocktake_date.strftime("%Y-%m")
    
    # Check if stocktake already exists for this month
    existing = await db.stocktakes.find_one({"month": current_month})
    if existing:
        raise HTTPException(status_code=400, detail="Stocktake already exists for this month")
    
    # Get all active materials
    materials = await db.materials.find({"is_active": True}).to_list(1000)
    
    new_stocktake = Stocktake(
        stocktake_date=stocktake_data.stocktake_date,
        month=current_month,
        created_by=current_user["sub"]
    )
    
    # Convert the stocktake to dict and handle date serialization
    stocktake_dict = new_stocktake.dict()
    stocktake_dict["stocktake_date"] = datetime.combine(stocktake_data.stocktake_date, datetime.min.time())
    
    await db.stocktakes.insert_one(stocktake_dict)
    
    return StandardResponse(
        success=True, 
        message="Stocktake created", 
        data={
            "stocktake_id": new_stocktake.id,
            "materials_count": len(materials),
            "materials": [{"id": m["id"], "name": f"{m['supplier']} - {m['product_code']}", "unit": m["unit"]} for m in materials]
        }
    )

@api_router.put("/stocktake/{stocktake_id}/entry", response_model=StandardResponse)
async def update_stocktake_entry(
    stocktake_id: str,
    entry_data: StocktakeEntryUpdate,
    current_user: dict = Depends(require_manager_or_admin)
):
    """Update stocktake entry for a material"""
    stocktake = await db.stocktakes.find_one({"id": stocktake_id})
    if not stocktake:
        raise HTTPException(status_code=404, detail="Stocktake not found")
    
    material = await db.materials.find_one({"id": entry_data.material_id})
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    
    # Create or update entry
    entry = StocktakeEntry(
        stocktake_id=stocktake_id,
        material_id=entry_data.material_id,
        material_name=f"{material['supplier']} - {material['product_code']}",
        current_quantity=entry_data.current_quantity,
        unit=material["unit"],
        counted_by=current_user["sub"]
    )
    
    # Update stocktake entries
    await db.stocktake_entries.replace_one(
        {"stocktake_id": stocktake_id, "material_id": entry_data.material_id},
        entry.dict(),
        upsert=True
    )
    
    return StandardResponse(success=True, message="Stocktake entry updated")

@api_router.post("/stocktake/{stocktake_id}/complete", response_model=StandardResponse)
async def complete_stocktake(
    stocktake_id: str,
    current_user: dict = Depends(require_manager_or_admin)
):
    """Complete stocktake"""
    result = await db.stocktakes.update_one(
        {"id": stocktake_id},
        {
            "$set": {
                "status": "completed",
                "completed_by": current_user["sub"],
                "completed_at": datetime.utcnow()
            }
        }
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Stocktake not found")
    
    return StandardResponse(success=True, message="Stocktake completed")

def _is_first_business_day(check_date):
    """Check if given date is first business day of month"""
    first_day = check_date.replace(day=1)
    # Skip weekends
    while first_day.weekday() >= 5:  # 5=Saturday, 6=Sunday
        first_day += timedelta(days=1)
    return check_date == first_day

# ============= USER MANAGEMENT ENDPOINTS =============

@api_router.get("/users", response_model=List[dict])
async def get_users(current_user: dict = Depends(require_admin)):
    """Get all users (Admin only)"""
    users = await db.users.find({}).sort("full_name", 1).to_list(1000)
    
    # Remove password hashes and convert ObjectId to string
    for user in users:
        if "password_hash" in user:
            del user["password_hash"]
        if "_id" in user:
            del user["_id"]  # Remove MongoDB ObjectId
    
    return users

@api_router.post("/users", response_model=StandardResponse)
async def create_user(user_data: UserCreate, current_user: dict = Depends(require_admin)):
    """Create new user account (Admin only)"""
    # Check if username or email already exists
    existing_user = await db.users.find_one({
        "$or": [
            {"username": user_data.username},
            {"email": user_data.email}
        ]
    })
    
    if existing_user:
        if existing_user["username"] == user_data.username:
            raise HTTPException(status_code=400, detail="Username already exists")
        if existing_user["email"] == user_data.email:
            raise HTTPException(status_code=400, detail="Email already exists")
    
    # Hash the password
    password_hash = hash_password(user_data.password)
    
    # Create user document
    new_user = {
        "id": str(uuid.uuid4()),
        "username": user_data.username,
        "email": user_data.email,
        "password_hash": password_hash,
        "full_name": user_data.full_name,
        "role": user_data.role,
        "department": user_data.department,
        "phone": user_data.phone,
        "employment_type": user_data.employment_type.value,
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": None,
        "created_by": current_user["sub"]
    }
    
    await db.users.insert_one(new_user)
    
    return StandardResponse(success=True, message="User created successfully", data={"id": new_user["id"]})

@api_router.get("/users/{user_id}", response_model=dict)
async def get_user(user_id: str, current_user: dict = Depends(require_admin)):
    """Get specific user by ID (Admin only)"""
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Remove password hash and ObjectId from response
    if "password_hash" in user:
        del user["password_hash"]
    if "_id" in user:
        del user["_id"]  # Remove MongoDB ObjectId
    
    return user

@api_router.put("/users/{user_id}", response_model=StandardResponse)
async def update_user(user_id: str, user_data: UserUpdate, current_user: dict = Depends(require_admin)):
    """Update user account (Admin only)"""
    # Check if user exists
    existing_user = await db.users.find_one({"id": user_id})
    if not existing_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Prepare update data
    update_data = {}
    if user_data.username is not None:
        # Check if username is already used by another user
        username_user = await db.users.find_one({"username": user_data.username, "id": {"$ne": user_id}})
        if username_user:
            raise HTTPException(status_code=400, detail="Username already exists")
        update_data["username"] = user_data.username
    
    if user_data.email is not None:
        # Check if email is already used by another user
        email_user = await db.users.find_one({"email": user_data.email, "id": {"$ne": user_id}})
        if email_user:
            raise HTTPException(status_code=400, detail="Email already exists")
        update_data["email"] = user_data.email
    
    if user_data.full_name is not None:
        update_data["full_name"] = user_data.full_name
    if user_data.role is not None:
        update_data["role"] = user_data.role
    if user_data.department is not None:
        update_data["department"] = user_data.department
    if user_data.phone is not None:
        update_data["phone"] = user_data.phone
    if user_data.employment_type is not None:
        update_data["employment_type"] = user_data.employment_type.value
    if user_data.is_active is not None:
        update_data["is_active"] = user_data.is_active
    
    update_data["updated_at"] = datetime.utcnow()
    
    await db.users.update_one(
        {"id": user_id},
        {"$set": update_data}
    )
    
    return StandardResponse(success=True, message="User updated successfully")

@api_router.delete("/users/{user_id}", response_model=StandardResponse)
async def delete_user(user_id: str, current_user: dict = Depends(require_admin)):
    """Delete user permanently (Admin only)"""
    # Check if user exists before deletion
    existing_user = await db.users.find_one({"id": user_id})
    if not existing_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Prevent admin from deleting themselves
    if user_id == current_user.get("user_id") or user_id == current_user.get("sub"):
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    
    # Permanently delete the user
    result = await db.users.delete_one({"id": user_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    return StandardResponse(success=True, message="User deleted successfully")

@api_router.post("/users/change-password", response_model=StandardResponse)
async def change_user_password(password_data: PasswordChangeRequest, current_user: dict = Depends(get_current_user)):
    """Change user's own password"""
    # Get current user from database using user_id from JWT token
    user_id = current_user.get("user_id")
    if not user_id:
        raise HTTPException(status_code=404, detail="User ID not found in token")
    
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Verify current password (check both possible field names for compatibility)
    password_field = "password_hash" if "password_hash" in user else "hashed_password"
    if not verify_password(password_data.current_password, user[password_field]):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    
    # Hash new password
    new_password_hash = hash_password(password_data.new_password)
    
    # Update password (use the same field name that exists)
    await db.users.update_one(
        {"id": user_id},
        {"$set": {
            password_field: new_password_hash,
            "updated_at": datetime.utcnow()
        }}
    )
    
    return StandardResponse(success=True, message="Password changed successfully")

# Helper functions for user management
def _generate_permissions(role: UserRole) -> List[str]:
    """Generate permissions based on role"""
    base_permissions = []
    
    if role == UserRole.ADMIN:
        return ["all"]  # Admin has all permissions
    
    elif role == UserRole.MANAGER:
        return [
            "manage_clients", "create_orders", "update_production", 
            "view_reports", "manage_payroll", "manage_materials",
            "manage_suppliers", "manage_specifications", "use_calculators"
        ]
    
    elif role == UserRole.MANAGER:
        return [
            "create_orders", "update_production", "use_calculators", 
            "view_own_payroll", "submit_timesheets", "request_leave"
        ]
    
    elif role == UserRole.PRODUCTION_TEAM:
        return [
            "update_production", "view_own_payroll", "submit_timesheets", "request_leave"
        ]
    
    elif role == UserRole.SALES:
        return [
            "manage_clients", "create_orders", "view_reports"
        ]
    
    return base_permissions

# ============= CLIENT PRODUCT CATALOG ENDPOINTS =============

@api_router.get("/clients/{client_id}/catalog", response_model=List[ClientProduct])
async def get_client_product_catalog(client_id: str, current_user: dict = Depends(require_any_role)):
    """Get product catalog for specific client"""
    products = await db.client_products.find({"client_id": client_id, "is_active": True}).to_list(1000)
    return [ClientProduct(**product) for product in products]

@api_router.post("/clients/{client_id}/catalog", response_model=StandardResponse)
async def create_client_product(client_id: str, product_data: ClientProductCreate, current_user: dict = Depends(require_admin_or_sales)):
    """Create new product for client catalog"""
    # Verify client exists
    client = await db.clients.find_one({"id": client_id, "is_active": True})
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Set client_id from URL
    product_data.client_id = client_id
    new_product = ClientProduct(**product_data.dict())
    await db.client_products.insert_one(new_product.dict())
    
    return StandardResponse(success=True, message="Client product created successfully", data={"id": new_product.id})

@api_router.get("/clients/{client_id}/catalog/{product_id}", response_model=ClientProduct)
async def get_client_product(client_id: str, product_id: str, current_user: dict = Depends(require_any_role)):
    """Get specific client product"""
    product = await db.client_products.find_one({
        "id": product_id, 
        "client_id": client_id,
        "is_active": True
    })
    if not product:
        raise HTTPException(status_code=404, detail="Client product not found")
    
    return ClientProduct(**product)

@api_router.put("/clients/{client_id}/catalog/{product_id}", response_model=StandardResponse)
async def update_client_product(client_id: str, product_id: str, product_data: ClientProductCreate, current_user: dict = Depends(require_admin_or_sales)):
    """Update client product"""
    # Verify client exists
    client = await db.clients.find_one({"id": client_id, "is_active": True})
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    update_data = product_data.dict()
    update_data["client_id"] = client_id  # Ensure client_id is correct
    update_data["updated_at"] = datetime.now(timezone.utc)
    
    result = await db.client_products.update_one(
        {"id": product_id, "client_id": client_id, "is_active": True},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Client product not found")
    
    return StandardResponse(success=True, message="Client product updated successfully")

@api_router.delete("/clients/{client_id}/catalog/{product_id}", response_model=StandardResponse)
async def delete_client_product(client_id: str, product_id: str, current_user: dict = Depends(require_admin_or_sales)):
    """Delete client product (soft delete)"""
    result = await db.client_products.update_one(
        {"id": product_id, "client_id": client_id, "is_active": True},
        {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Client product not found")
    
    return StandardResponse(success=True, message="Client product deleted successfully")

@api_router.post("/clients/{client_id}/catalog/{product_id}/copy-to/{target_client_id}", response_model=StandardResponse)
async def copy_client_product(client_id: str, product_id: str, target_client_id: str, current_user: dict = Depends(require_admin_or_sales)):
    """Copy product to another client catalog"""
    # Verify both clients exist
    source_client = await db.clients.find_one({"id": client_id, "is_active": True})
    target_client = await db.clients.find_one({"id": target_client_id, "is_active": True})
    
    if not source_client:
        raise HTTPException(status_code=404, detail="Source client not found")
    if not target_client:
        raise HTTPException(status_code=404, detail="Target client not found")
    
    # Get source product
    source_product = await db.client_products.find_one({
        "id": product_id,
        "client_id": client_id,
        "is_active": True
    })
    
    if not source_product:
        raise HTTPException(status_code=404, detail="Source product not found")
    
    # Create copy for target client
    copied_product = ClientProduct(**source_product)
    copied_product.id = str(uuid.uuid4())  # Generate new ID
    copied_product.client_id = target_client_id
    copied_product.created_at = datetime.utcnow()
    copied_product.updated_at = None
    
    await db.client_products.insert_one(copied_product.dict())
    
    return StandardResponse(
        success=True, 
        message=f"Product copied successfully to {target_client['company_name']}", 
        data={"id": copied_product.id}
    )

@api_router.delete("/clients/{client_id}", response_model=StandardResponse)
async def delete_client(client_id: str, current_user: dict = Depends(require_admin)):
    """Delete client (soft delete - Admin only)"""
    # Check if client exists
    existing_client = await db.clients.find_one({"id": client_id, "is_active": True})
    if not existing_client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Check if client has active orders
    active_orders = await db.orders.find_one({"client_id": client_id, "status": {"$nin": ["completed", "cancelled"]}})
    if active_orders:
        raise HTTPException(status_code=400, detail="Cannot delete client with active orders")
    
    # Perform soft delete
    result = await db.clients.update_one(
        {"id": client_id},
        {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Client not found")
    
    return StandardResponse(success=True, message="Client deleted successfully")

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
async def create_order(order_data: OrderCreate, current_user: dict = Depends(require_admin_or_manager)):
    """Create new order"""
    # Get client details
    client = await db.clients.find_one({"id": order_data.client_id, "is_active": True})
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Generate order number
    order_count = await db.orders.count_documents({})
    order_number = f"ADM-{datetime.now().year}-{order_count + 1:04d}"
    
    # Calculate totals with discount applied before GST
    subtotal = sum(item.total_price for item in order_data.items)
    
    # Apply discount if provided
    discount_percentage = order_data.discount_percentage or 0
    discount_amount = 0
    discounted_subtotal = subtotal
    
    if discount_percentage > 0:
        discount_amount = subtotal * (discount_percentage / 100)
        discounted_subtotal = subtotal - discount_amount
    
    # Calculate GST on discounted amount
    gst = discounted_subtotal * 0.1
    total_amount = discounted_subtotal + gst
    
    new_order = Order(
        order_number=order_number,
        client_id=order_data.client_id,
        client_name=client["company_name"],
        purchase_order_number=order_data.purchase_order_number,
        items=order_data.items,
        subtotal=subtotal,
        discount_percentage=discount_percentage if discount_percentage > 0 else None,
        discount_amount=discount_amount if discount_amount > 0 else None,
        discount_notes=order_data.discount_notes if order_data.discount_notes else None,
        discounted_subtotal=discounted_subtotal,
        gst=gst,
        total_amount=total_amount,
        due_date=order_data.due_date,
        delivery_address=order_data.delivery_address,
        delivery_instructions=order_data.delivery_instructions,
        runtime_estimate=order_data.runtime_estimate,
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
    
    # If moving to completed, set completion date and archive the order
    if stage_update.to_stage == ProductionStage.CLEARED:
        update_data["completed_at"] = datetime.utcnow()
        update_data["status"] = OrderStatus.COMPLETED
        
        # Get the complete order data for archiving
        order = await db.orders.find_one({"id": order_id})
        if order:
            # Create archived order
            archived_order = ArchivedOrder(
                original_order_id=order["id"],
                order_number=order["order_number"],
                client_id=order["client_id"],
                client_name=order["client_name"],
                purchase_order_number=order.get("purchase_order_number"),
                items=order["items"],
                subtotal=order["subtotal"],
                gst=order["gst"],
                total_amount=order["total_amount"],
                due_date=order["due_date"],
                delivery_address=order.get("delivery_address"),
                delivery_instructions=order.get("delivery_instructions"),
                runtime_estimate=order.get("runtime_estimate"),
                notes=order.get("notes"),
                created_by=order["created_by"],
                created_at=order["created_at"],
                completed_at=datetime.utcnow(),
                archived_by=current_user["user_id"]
            )
            
            # Insert into archived orders collection
            await db.archived_orders.insert_one(archived_order.dict())
            
            # Update order status to archived and keep in main collection for now
            # This allows for transition period and potential rollback
            update_data["status"] = OrderStatus.ARCHIVED
    
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
async def create_job_specification(spec_data: JobSpecificationCreate, current_user: dict = Depends(require_admin_or_manager)):
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

@api_router.delete("/orders/{order_id}", response_model=StandardResponse)
async def delete_order(order_id: str, current_user: dict = Depends(require_admin)):
    """Delete order permanently (Admin only)"""
    # Check if order exists
    existing_order = await db.orders.find_one({"id": order_id})
    if not existing_order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Check if order is in production (not safe to delete if in progress)
    unsafe_stages = ["paper_slitting", "winding", "finishing"]
    current_stage = existing_order.get("current_stage", "order_entered")
    if current_stage in unsafe_stages:
        raise HTTPException(status_code=400, detail="Cannot delete order in production. Contact manager to halt production first.")
    
    # Clean up related data first
    # Remove job specifications
    await db.job_specifications.delete_many({"order_id": order_id})
    
    # Remove materials status
    await db.materials_status.delete_many({"order_id": order_id})
    
    # Remove order items status
    await db.order_items_status.delete_many({"order_id": order_id})
    
    # Perform hard delete - completely remove the order
    result = await db.orders.delete_one({"id": order_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Order not found")
    
    return StandardResponse(success=True, message="Order deleted successfully")

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
            
            # Get materials status
            materials_status = await db.materials_status.find_one({"order_id": order["id"]})
            materials_ready = materials_status.get("materials_ready", False) if materials_status else False
            
            order_info = {
                "id": order["id"],
                "order_number": order["order_number"],
                "client_name": order["client_name"],
                "client_logo": get_file_url(client.get("logo_path", "")) if client else None,
                "due_date": order["due_date"],
                "total_amount": order["total_amount"],
                "runtime": order.get("runtime_estimate", "2-3 days"),
                "materials_ready": materials_ready,
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

@api_router.post("/production/move-stage/{order_id}")
async def move_order_stage(
    order_id: str, 
    request: StageMovementRequest, 
    current_user: dict = Depends(require_admin_or_manager)
):
    """Move order to next or previous production stage"""
    # Get current order
    order = await db.orders.find_one({"id": order_id})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Define stage progression
    stage_order = [
        ProductionStage.ORDER_ENTERED,
        ProductionStage.PENDING_MATERIAL,
        ProductionStage.PAPER_SLITTING,
        ProductionStage.WINDING,
        ProductionStage.FINISHING,
        ProductionStage.DELIVERY,
        ProductionStage.INVOICING,
        ProductionStage.CLEARED
    ]
    
    current_stage = ProductionStage(order["current_stage"])
    current_index = stage_order.index(current_stage)
    
    # Calculate new stage
    if request.direction == "forward":
        new_index = min(current_index + 1, len(stage_order) - 1)
    elif request.direction == "backward":
        new_index = max(current_index - 1, 0)
    else:
        raise HTTPException(status_code=400, detail="Direction must be 'forward' or 'backward'")
    
    if new_index == current_index:
        raise HTTPException(status_code=400, detail="Order is already at the first/last stage")
    
    new_stage = stage_order[new_index]
    
    # Update order stage
    await db.orders.update_one(
        {"id": order_id},
        {
            "$set": {
                "current_stage": new_stage.value,
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    # Log stage change
    stage_log = ProductionLog(
        order_id=order_id,
        stage=new_stage,
        updated_by=current_user["sub"],
        notes=request.notes
    )
    await db.production_logs.insert_one(stage_log.dict())
    
    return {"success": True, "message": f"Order moved to {new_stage.value}", "new_stage": new_stage.value}

@api_router.get("/production/materials-status/{order_id}")
async def get_materials_status(order_id: str, current_user: dict = Depends(require_any_role)):
    """Get materials status for order"""
    # Check if order exists first
    order = await db.orders.find_one({"id": order_id})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    status = await db.materials_status.find_one({"order_id": order_id})
    if not status:
        # Create default status if not exists
        default_status = MaterialsStatus(
            order_id=order_id,
            materials_ready=False,
            materials_checklist=[],
            updated_by=current_user["sub"]
        )
        await db.materials_status.insert_one(default_status.dict())
        return {"success": True, "data": default_status.dict()}
    
    # Remove MongoDB _id field to avoid serialization issues
    if "_id" in status:
        del status["_id"]
    
    return {"success": True, "data": status}

@api_router.put("/production/materials-status/{order_id}")
async def update_materials_status(
    order_id: str, 
    status_update: MaterialsStatusUpdate,
    current_user: dict = Depends(require_admin_or_manager)
):
    """Update materials status for order"""
    # Check if order exists
    order = await db.orders.find_one({"id": order_id})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Update or create materials status
    update_data = {
        "materials_ready": status_update.materials_ready,
        "materials_checklist": status_update.materials_checklist,
        "updated_by": current_user["sub"],
        "updated_at": datetime.utcnow()
    }
    
    result = await db.materials_status.update_one(
        {"order_id": order_id},
        {"$set": update_data},
        upsert=True
    )
    
    return {"success": True, "message": "Materials status updated"}

@api_router.put("/production/order-item-status/{order_id}")
async def update_order_item_status(
    order_id: str,
    item_update: OrderItemStatusUpdate,
    current_user: dict = Depends(require_admin_or_manager)
):
    """Update completion status of specific order item"""
    # Get the order
    order = await db.orders.find_one({"id": order_id})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Validate item index
    if item_update.item_index >= len(order["items"]) or item_update.item_index < 0:
        raise HTTPException(status_code=400, detail="Invalid item index")
    
    # Update the specific item's completion status
    update_query = {
        f"items.{item_update.item_index}.is_completed": item_update.is_completed,
        "updated_at": datetime.utcnow()
    }
    
    await db.orders.update_one(
        {"id": order_id},
        {"$set": update_query}
    )
    
    return {"success": True, "message": f"Item {item_update.item_index} marked as {'completed' if item_update.is_completed else 'pending'}"}


# ============= REPORTS ENDPOINTS =============

@api_router.get("/reports/outstanding-jobs")
async def get_outstanding_jobs_report(current_user: dict = Depends(require_admin_or_manager)):
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
async def get_late_deliveries_report(current_user: dict = Depends(require_admin_or_manager)):
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
async def get_customer_annual_report(client_id: str, year: int, current_user: dict = Depends(require_admin_or_manager)):
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

# Simplified authentication for PDF documents - allow open access for testing
async def simple_pdf_auth(token: str = None):
    """Simplified authentication for PDF downloads"""
    # For now, let's make PDFs accessible without strict authentication for testing
    # In production, you'd want proper authentication
    return {"user_id": "test-user", "role": "admin"}

@api_router.get("/documents/acknowledgment/{order_id}")
async def generate_acknowledgment(order_id: str):
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
async def generate_job_card(order_id: str):
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
async def generate_packing_list(order_id: str):
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

# Moved this function above document endpoints

@api_router.get("/documents/invoice/{order_id}")
async def generate_invoice_pdf(order_id: str):
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

# Xero Integration Configuration
XERO_CLIENT_ID = os.getenv("XERO_CLIENT_ID")
XERO_CLIENT_SECRET = os.getenv("XERO_CLIENT_SECRET")  
XERO_CALLBACK_URL = os.getenv("XERO_REDIRECT_URI", "https://app.emergent.sh/api/xero/callback")
XERO_SCOPES = "openid profile email accounting.transactions accounting.contacts accounting.settings offline_access"

# Xero Account Configuration
XERO_DEFAULT_SALES_ACCOUNT_CODE = "200"  # Sales account code
XERO_DEFAULT_TAX_TYPE = "OUTPUT"  # Default GST/tax type

# Debug endpoint for testing
@api_router.get("/xero/debug")
async def debug_xero_config():
    """Debug endpoint to check Xero configuration"""
    return {
        "client_id": XERO_CLIENT_ID,
        "callback_url": XERO_CALLBACK_URL,
        "scopes": XERO_SCOPES,
        "expected_auth_url_start": "https://login.xero.com/identity/connect/authorize",
        "frontend_url": os.getenv("FRONTEND_URL", "https://app.emergent.sh"),
        "environment_check": {
            "client_id_set": bool(XERO_CLIENT_ID),
            "client_secret_set": bool(XERO_CLIENT_SECRET),
            "redirect_uri": XERO_CALLBACK_URL
        }
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

@api_router.get("/xero/status")
async def check_xero_connection_status(current_user: dict = Depends(require_admin_or_manager)):
    """Check if user has active Xero connection"""
    # Check if user has stored Xero tokens
    user_tokens = await db.xero_tokens.find_one({"user_id": current_user["user_id"]})
    
    if user_tokens and user_tokens.get("access_token"):
        # TODO: Validate token is still active with Xero API
        return {"connected": True, "message": "Xero connection active", "tenant_id": user_tokens.get("tenant_id")}
    else:
        return {"connected": False, "message": "No Xero connection found"}

# Helper function to get authenticated Xero API client
async def get_xero_api_client(user_id: str):
    """Get authenticated Xero API client for user"""
    user_tokens = await db.xero_tokens.find_one({"user_id": user_id})
    if not user_tokens or not user_tokens.get("access_token"):
        raise HTTPException(status_code=401, detail="No Xero connection found")
    
    # Check if token is expired
    if user_tokens.get("expires_at") and user_tokens["expires_at"] < datetime.utcnow():
        # Try to refresh token
        try:
            refreshed_tokens = await refresh_xero_token(user_id, user_tokens["refresh_token"])
            user_tokens = refreshed_tokens
        except Exception as e:
            raise HTTPException(status_code=401, detail="Xero token expired and refresh failed")
    
    # Create OAuth2 token object
    oauth2_token = OAuth2Token(
        client_id=XERO_CLIENT_ID,
        client_secret=XERO_CLIENT_SECRET
    )
    oauth2_token.access_token = user_tokens["access_token"]
    oauth2_token.refresh_token = user_tokens.get("refresh_token")
    oauth2_token.expires_at = user_tokens.get("expires_at")
    
    # Create API client
    configuration = Configuration(oauth2_token=oauth2_token)
    api_client = ApiClient(configuration, pool_threads=1)
    
    return api_client, user_tokens.get("tenant_id")

async def refresh_xero_token(user_id: str, refresh_token: str):
    """Refresh expired Xero access token"""
    token_url = "https://identity.xero.com/connect/token"
    
    auth_string = f"{XERO_CLIENT_ID}:{XERO_CLIENT_SECRET}"
    auth_bytes = auth_string.encode('ascii')
    auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
    
    headers = {
        "Authorization": f"Basic {auth_b64}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    token_data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token
    }
    
    response = requests.post(token_url, headers=headers, data=token_data)
    response.raise_for_status()
    
    tokens = response.json()
    
    # Update stored tokens
    token_record = {
        "user_id": user_id,
        "access_token": tokens["access_token"],
        "refresh_token": tokens.get("refresh_token", refresh_token),
        "expires_at": datetime.utcnow() + timedelta(seconds=tokens.get("expires_in", 1800)),
        "updated_at": datetime.utcnow()
    }
    
    await db.xero_tokens.update_one(
        {"user_id": user_id},
        {"$set": token_record}
    )
    
    return token_record

@api_router.get("/xero/auth/url")
async def get_xero_auth_url(current_user: dict = Depends(require_admin_or_manager)):
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
        frontend_callback_url = os.getenv("FRONTEND_URL", "https://app.emergent.sh") + f"/xero/callback?code={code}&state={state}"
        return f"<html><body><script>window.location.href='{frontend_callback_url}';</script></body></html>"
    
    return "<html><body><script>window.close();</script></body></html>"

@api_router.post("/xero/auth/callback")
async def handle_xero_callback(
    callback_data: dict,
    current_user: dict = Depends(require_admin_or_manager)
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
async def disconnect_xero(current_user: dict = Depends(require_admin_or_manager)):
    """Disconnect from Xero"""
    # Remove stored tokens
    result = await db.xero_tokens.delete_one({"user_id": current_user["user_id"]})
    
    if result.deleted_count > 0:
        return {"message": "Xero disconnection successful"}
    else:
        return {"message": "No Xero connection found to disconnect"}

@api_router.get("/xero/next-invoice-number")
async def get_next_xero_invoice_number(current_user: dict = Depends(require_admin_or_manager)):
    """Get the next available invoice number from Xero"""
    try:
        api_client, tenant_id = await get_xero_api_client(current_user["user_id"])
        
        if not tenant_id:
            # Get tenant info if not stored
            from xero_python.identity import IdentityApi
            identity_api = IdentityApi(api_client)
            connections = identity_api.get_connections()
            
            if not connections or not connections[0]:
                raise HTTPException(status_code=400, detail="No Xero organization connected")
            
            tenant_id = connections[0].tenant_id
            
            # Update stored token record with tenant_id
            await db.xero_tokens.update_one(
                {"user_id": current_user["user_id"]},
                {"$set": {"tenant_id": tenant_id}}
            )
        
        # Get invoices to determine next number
        accounting_api = AccountingApi(api_client)
        
        # Get recent invoices ordered by invoice number descending
        invoices_response = accounting_api.get_invoices(
            xero_tenant_id=tenant_id,
            order="InvoiceNumber DESC",
            page=1
        )
        
        next_number = 1
        if invoices_response.invoices and len(invoices_response.invoices) > 0:
            # Extract numeric part from the last invoice number
            last_invoice = invoices_response.invoices[0]
            if last_invoice.invoice_number:
                # Try to extract number from invoice number (handle different formats)
                import re
                numbers = re.findall(r'\d+', last_invoice.invoice_number)
                if numbers:
                    next_number = int(numbers[-1]) + 1
        
        # Format as INV-XXXXXX
        formatted_number = f"INV-{next_number:06d}"
        
        return {
            "next_number": next_number,
            "formatted_number": formatted_number,
            "tenant_id": tenant_id
        }
        
    except Exception as e:
        logger.error(f"Failed to get next invoice number from Xero: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get next invoice number: {str(e)}")

@api_router.get("/xero/account-codes")
async def get_xero_account_codes(current_user: dict = Depends(require_admin_or_manager)):
    """Get available account codes from Xero for setup verification"""
    try:
        api_client, tenant_id = await get_xero_api_client(current_user["user_id"])
        
        if not tenant_id:
            raise HTTPException(status_code=400, detail="No Xero tenant ID found")
        
        accounting_api = AccountingApi(api_client)
        
        # Get all revenue accounts
        accounts_response = accounting_api.get_accounts(
            xero_tenant_id=tenant_id,
            where='Type=="REVENUE" AND Status=="ACTIVE"'
        )
        
        revenue_accounts = []
        if accounts_response.accounts:
            for account in accounts_response.accounts:
                revenue_accounts.append({
                    "code": account.code,
                    "name": account.name,
                    "description": account.description,
                    "type": account.type
                })
        
        return {
            "success": True,
            "revenue_accounts": revenue_accounts,
            "recommended_setup": {
                "message": "For best results, ensure you have a revenue account with code '200' or update Misty to use one of your existing codes",
                "current_default": "200"
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get Xero account codes: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get account codes: {str(e)}")

@api_router.get("/xero/tax-rates")
async def get_xero_tax_rates(current_user: dict = Depends(require_admin_or_manager)):
    """Get available tax rates from Xero"""
    try:
        api_client, tenant_id = await get_xero_api_client(current_user["user_id"])
        
        if not tenant_id:
            raise HTTPException(status_code=400, detail="No Xero tenant ID found")
        
        accounting_api = AccountingApi(api_client)
        
        # Get all tax rates
        tax_rates_response = accounting_api.get_tax_rates(xero_tenant_id=tenant_id)
        
        tax_rates = []
        if tax_rates_response.tax_rates:
            for tax_rate in tax_rates_response.tax_rates:
                tax_rates.append({
                    "name": tax_rate.name,
                    "tax_type": tax_rate.tax_type,
                    "rate": str(tax_rate.effective_rate) if tax_rate.effective_rate else "0",
                    "status": tax_rate.status
                })
        
        return {
            "success": True,
            "tax_rates": tax_rates,
            "current_default": "OUTPUT"
        }
        
    except Exception as e:
        logger.error(f"Failed to get Xero tax rates: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get tax rates: {str(e)}")

async def validate_sales_account(accounting_api, tenant_id: str) -> str:
    """Validate that Sales account with code 200 exists, or find suitable alternative"""
    try:
        # First, try to find account with code "200"
        accounts_response = accounting_api.get_accounts(
            xero_tenant_id=tenant_id,
            where=f'Code="{XERO_DEFAULT_SALES_ACCOUNT_CODE}" AND Status=="ACTIVE"'
        )
        
        if accounts_response.accounts and len(accounts_response.accounts) > 0:
            account = accounts_response.accounts[0]
            logger.info(f"Found Sales account: {account.name} (Code: {account.code})")
            return account.code
        
        # If code "200" doesn't exist, look for any Sales or Revenue account
        logger.warning(f"Sales account with code {XERO_DEFAULT_SALES_ACCOUNT_CODE} not found. Looking for alternatives...")
        
        # Try to find Sales or Revenue accounts
        sales_accounts = accounting_api.get_accounts(
            xero_tenant_id=tenant_id,
            where='(Type=="REVENUE" OR Type=="SALES") AND Status=="ACTIVE"'
        )
        
        if sales_accounts.accounts and len(sales_accounts.accounts) > 0:
            # Use the first available sales/revenue account
            account = sales_accounts.accounts[0]
            logger.info(f"Using alternative Sales account: {account.name} (Code: {account.code})")
            return account.code
        
        # Last resort: look for any income account
        income_accounts = accounting_api.get_accounts(
            xero_tenant_id=tenant_id,
            where='Type=="REVENUE" AND Status=="ACTIVE"'
        )
        
        if income_accounts.accounts and len(income_accounts.accounts) > 0:
            account = income_accounts.accounts[0]
            logger.info(f"Using fallback Revenue account: {account.name} (Code: {account.code})")
            return account.code
        
        # If nothing found, return the default and let Xero handle the error
        logger.error("No suitable Sales or Revenue accounts found in Xero")
        return XERO_DEFAULT_SALES_ACCOUNT_CODE
        
    except Exception as e:
        logger.error(f"Error validating sales account: {str(e)}")
        return XERO_DEFAULT_SALES_ACCOUNT_CODE

@api_router.post("/xero/create-draft-invoice")
async def create_xero_draft_invoice(
    invoice_data: dict,
    current_user: dict = Depends(require_admin_or_manager)
):
    """Create a draft invoice in Xero"""
    try:
        api_client, tenant_id = await get_xero_api_client(current_user["user_id"])
        
        if not tenant_id:
            raise HTTPException(status_code=400, detail="No Xero tenant ID found")
        
        accounting_api = AccountingApi(api_client)
        
        # Get or create contact in Xero
        contact_name = invoice_data.get("client_name", "Unknown Client")
        contact_email = invoice_data.get("client_email")
        
        # Search for existing contact
        contact_id = None
        if contact_email:
            try:
                contacts_response = accounting_api.get_contacts(
                    xero_tenant_id=tenant_id,
                    where=f'EmailAddress="{contact_email}"'
                )
                if contacts_response.contacts and len(contacts_response.contacts) > 0:
                    contact_id = contacts_response.contacts[0].contact_id
            except:
                pass
        
        # Create contact if not found
        if not contact_id:
            try:
                new_contact = Contact(
                    name=contact_name,
                    email_address=contact_email if contact_email else None
                )
                contacts_request = Contacts(contacts=[new_contact])
                contacts_response = accounting_api.create_contacts(
                    xero_tenant_id=tenant_id,
                    contacts=contacts_request
                )
                if contacts_response.contacts and len(contacts_response.contacts) > 0:
                    contact_id = contacts_response.contacts[0].contact_id
                else:
                    raise Exception("Failed to create contact")
            except Exception as e:
                logger.error(f"Failed to create contact in Xero: {str(e)}")
                # Use default contact or create a simple one
                contact_id = None
        
        # Prepare line items with Sales account
        line_items = []
        items = invoice_data.get("items", [])
        
        # Validate that Sales account code "200" exists
        sales_account_code = await validate_sales_account(accounting_api, tenant_id)
        
        for item in items:
            line_item = LineItem(
                description=item.get("description", "Product/Service"),
                quantity=float(item.get("quantity", 1)),
                unit_amount=float(item.get("unit_price", 0)),
                account_code=sales_account_code,
                tax_type=XERO_DEFAULT_TAX_TYPE
            )
            line_items.append(line_item)
        
        # If no items provided, create a default line item
        if not line_items:
            total_amount = float(invoice_data.get("total_amount", 0))
            line_item = LineItem(
                description=f"Services for {contact_name}",
                quantity=1,
                unit_amount=total_amount,
                account_code=sales_account_code,
                tax_type=XERO_DEFAULT_TAX_TYPE
            )
            line_items.append(line_item)
        
        # Create invoice object
        invoice = Invoice(
            type="ACCREC",  # Accounts Receivable
            contact=Contact(contact_id=contact_id) if contact_id else Contact(name=contact_name),
            line_items=line_items,
            date=datetime.now().date(),
            due_date=invoice_data.get("due_date"),
            invoice_number=invoice_data.get("invoice_number"),
            reference=invoice_data.get("reference", invoice_data.get("order_number")),
            status="DRAFT"
        )
        
        # Create invoice in Xero
        invoices_request = Invoices(invoices=[invoice])
        invoices_response = accounting_api.create_invoices(
            xero_tenant_id=tenant_id,
            invoices=invoices_request
        )
        
        if not invoices_response.invoices or len(invoices_response.invoices) == 0:
            raise Exception("No invoice returned from Xero API")
        
        created_invoice = invoices_response.invoices[0]
        
        # Check for validation errors
        if hasattr(created_invoice, 'validation_errors') and created_invoice.validation_errors:
            error_messages = [error.message for error in created_invoice.validation_errors]
            raise Exception(f"Invoice validation failed: {', '.join(error_messages)}")
        
        return {
            "success": True,
            "message": "Draft invoice created in Xero",
            "invoice_id": created_invoice.invoice_id,
            "invoice_number": created_invoice.invoice_number,
            "status": created_invoice.status,
            "total": str(created_invoice.total) if created_invoice.total else "0",
            "xero_url": f"https://go.xero.com/AccountsReceivable/View.aspx?InvoiceID={created_invoice.invoice_id}"
        }
        
    except Exception as e:
        logger.error(f"Failed to create draft invoice in Xero: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create draft invoice: {str(e)}")

# ============= INVOICING ENDPOINTS =============

@api_router.get("/invoicing/live-jobs")
async def get_live_jobs(current_user: dict = Depends(require_admin_or_manager)):
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
    current_user: dict = Depends(require_admin_or_manager)
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
    current_user: dict = Depends(require_admin_or_manager)
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
    current_user: dict = Depends(require_admin_or_manager)
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

# ============= ARCHIVED ORDERS ENDPOINTS =============

@api_router.get("/clients/{client_id}/archived-orders")
async def get_client_archived_orders(
    client_id: str,
    filters: ArchivedOrderFilter = Depends(),
    current_user: dict = Depends(require_any_role)
):
    """Get archived orders for a specific client with filtering"""
    query = {"client_id": client_id}
    
    # Apply date filters
    if filters.date_from or filters.date_to:
        date_filter = {}
        if filters.date_from:
            date_filter["$gte"] = datetime.combine(filters.date_from, datetime.min.time())
        if filters.date_to:
            date_filter["$lte"] = datetime.combine(filters.date_to, datetime.max.time())
        query["archived_at"] = date_filter
    
    # Apply search query
    if filters.search_query:
        query["$or"] = [
            {"order_number": {"$regex": filters.search_query, "$options": "i"}},
            {"client_name": {"$regex": filters.search_query, "$options": "i"}},
            {"purchase_order_number": {"$regex": filters.search_query, "$options": "i"}},
            {"items.product_name": {"$regex": filters.search_query, "$options": "i"}}
        ]
    
    archived_orders = await db.archived_orders.find(query).sort("archived_at", -1).to_list(length=None)
    
    # Remove MongoDB ObjectIds
    for order in archived_orders:
        if "_id" in order:
            del order["_id"]
    
    return StandardResponse(success=True, message="Archived orders retrieved", data=archived_orders)

@api_router.post("/clients/{client_id}/archived-orders/fast-report")
async def generate_fast_report(
    client_id: str,
    report_request: FastReportRequest,
    current_user: dict = Depends(require_any_role)
):
    """Generate Excel fast report for client archived orders"""
    from openpyxl import Workbook
    from openpyxl.styles import Font, Alignment, Border, Side
    from openpyxl.utils.dataframe import dataframe_to_rows
    from io import BytesIO
    import pandas as pd
    from fastapi.responses import StreamingResponse
    
    # Calculate date range based on time period
    today = date.today()
    
    if report_request.time_period == ReportTimePeriod.CURRENT_MONTH:
        date_from = today.replace(day=1)
        date_to = today
    elif report_request.time_period == ReportTimePeriod.LAST_MONTH:
        first_day_current = today.replace(day=1)
        date_to = first_day_current - timedelta(days=1)
        date_from = date_to.replace(day=1)
    elif report_request.time_period == ReportTimePeriod.LAST_3_MONTHS:
        date_to = today
        date_from = today - timedelta(days=90)
    elif report_request.time_period == ReportTimePeriod.LAST_6_MONTHS:
        date_to = today
        date_from = today - timedelta(days=180)
    elif report_request.time_period == ReportTimePeriod.LAST_9_MONTHS:
        date_to = today
        date_from = today - timedelta(days=270)
    elif report_request.time_period == ReportTimePeriod.LAST_YEAR:
        date_to = today
        date_from = today - timedelta(days=365)
    elif report_request.time_period == ReportTimePeriod.CURRENT_QUARTER:
        quarter_start_month = (today.month - 1) // 3 * 3 + 1
        date_from = today.replace(month=quarter_start_month, day=1)
        date_to = today
    elif report_request.time_period == ReportTimePeriod.YEAR_TO_DATE:
        date_from = today.replace(month=1, day=1)
        date_to = today
    elif report_request.time_period == ReportTimePeriod.CURRENT_FINANCIAL_YEAR:
        # Australian financial year: July 1 - June 30
        if today.month >= 7:
            date_from = today.replace(month=7, day=1)
            date_to = today
        else:
            date_from = today.replace(year=today.year-1, month=7, day=1)
            date_to = today
    elif report_request.time_period == ReportTimePeriod.CUSTOM_RANGE:
        date_from = report_request.date_from
        date_to = report_request.date_to
    else:
        date_from = today - timedelta(days=30)
        date_to = today
    
    # Build query
    query = {"client_id": client_id}
    
    if date_from and date_to:
        query["archived_at"] = {
            "$gte": datetime.combine(date_from, datetime.min.time()),
            "$lte": datetime.combine(date_to, datetime.max.time())
        }
    
    # Apply product filter if specified
    if report_request.product_filter:
        query["items.product_name"] = {"$regex": report_request.product_filter, "$options": "i"}
    
    # Get archived orders
    archived_orders = await db.archived_orders.find(query).sort("archived_at", -1).to_list(length=None)
    
    if not archived_orders:
        raise HTTPException(status_code=404, detail="No archived orders found for the specified criteria")
    
    # Prepare data for Excel
    excel_data = []
    
    for order in archived_orders:
        row_data = {}
        
        # Map selected fields to Excel columns
        for field in report_request.selected_fields:
            if field == ReportField.ORDER_NUMBER:
                row_data["Order Number"] = order.get("order_number", "")
            elif field == ReportField.CLIENT_NAME:
                row_data["Client Name"] = order.get("client_name", "")
            elif field == ReportField.PURCHASE_ORDER_NUMBER:
                row_data["Purchase Order Number"] = order.get("purchase_order_number", "")
            elif field == ReportField.ORDER_DATE:
                row_data["Order Date"] = order.get("created_at", "").strftime("%Y-%m-%d") if order.get("created_at") else ""
            elif field == ReportField.COMPLETION_DATE:
                row_data["Completion Date"] = order.get("completed_at", "").strftime("%Y-%m-%d") if order.get("completed_at") else ""
            elif field == ReportField.DUE_DATE:
                row_data["Due Date"] = order.get("due_date", "").strftime("%Y-%m-%d") if order.get("due_date") else ""
            elif field == ReportField.SUBTOTAL:
                row_data["Subtotal"] = f"${order.get('subtotal', 0):.2f}"
            elif field == ReportField.GST:
                row_data["GST"] = f"${order.get('gst', 0):.2f}"
            elif field == ReportField.TOTAL_AMOUNT:
                row_data["Total Amount"] = f"${order.get('total_amount', 0):.2f}"
            elif field == ReportField.DELIVERY_ADDRESS:
                row_data["Delivery Address"] = order.get("delivery_address", "")
            elif field == ReportField.PRODUCT_NAMES:
                products = [item.get("product_name", "") for item in order.get("items", [])]
                row_data["Products"] = ", ".join(products)
            elif field == ReportField.PRODUCT_QUANTITIES:
                quantities = [f"{item.get('product_name', '')}: {item.get('quantity', 0)}" for item in order.get("items", [])]
                row_data["Product Quantities"] = ", ".join(quantities)
            elif field == ReportField.NOTES:
                row_data["Notes"] = order.get("notes", "")
            elif field == ReportField.RUNTIME_ESTIMATE:
                row_data["Runtime Estimate"] = order.get("runtime_estimate", "")
        
        excel_data.append(row_data)
    
    # Create Excel workbook
    df = pd.DataFrame(excel_data)
    wb = Workbook()
    ws = wb.active
    
    # Set title
    title = report_request.report_title or f"Archived Orders Report - {report_request.time_period.value.replace('_', ' ').title()}"
    ws.title = "Archived Orders Report"
    
    # Add header
    ws.merge_cells("A1:{}1".format(chr(65 + len(df.columns) - 1)))
    ws["A1"] = title
    ws["A1"].font = Font(bold=True, size=16)
    ws["A1"].alignment = Alignment(horizontal="center")
    
    # Add date range info
    ws.merge_cells("A2:{}2".format(chr(65 + len(df.columns) - 1)))
    ws["A2"] = f"Report Period: {date_from.strftime('%Y-%m-%d')} to {date_to.strftime('%Y-%m-%d')}"
    ws["A2"].alignment = Alignment(horizontal="center")
    
    # Add column headers
    for col, column_name in enumerate(df.columns, 1):
        cell = ws.cell(row=4, column=col, value=column_name)
        cell.font = Font(bold=True)
        cell.alignment = Alignment(horizontal="center")
    
    # Add data
    for row_idx, row_data in enumerate(excel_data, 5):
        for col_idx, (column_name, value) in enumerate(row_data.items(), 1):
            ws.cell(row=row_idx, column=col_idx, value=value)
    
    # Auto-adjust column widths
    from openpyxl.utils import get_column_letter
    for col_idx in range(1, len(df.columns) + 1):
        max_length = 0
        column_letter = get_column_letter(col_idx)
        
        # Check all cells in this column
        for row_idx in range(4, ws.max_row + 1):  # Start from row 4 (after headers)
            cell = ws.cell(row=row_idx, column=col_idx)
            try:
                if cell.value is not None:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
            except:
                pass
        
        # Also check header length
        header_cell = ws.cell(row=4, column=col_idx)
        if header_cell.value is not None:
            header_length = len(str(header_cell.value))
            if header_length > max_length:
                max_length = header_length
        
        adjusted_width = min(max_length + 2, 50)  # Cap at 50 characters
        ws.column_dimensions[column_letter].width = adjusted_width
    
    # Save to BytesIO
    excel_file = BytesIO()
    wb.save(excel_file)
    excel_file.seek(0)
    
    # Get client name for filename
    client = await db.clients.find_one({"id": client_id})
    client_name = client.get("company_name", "Client") if client else "Client"
    safe_client_name = "".join(c for c in client_name if c.isalnum() or c in (' ', '-', '_')).strip()
    
    filename = f"{safe_client_name}_Archived_Orders_{date_from.strftime('%Y%m%d')}-{date_to.strftime('%Y%m%d')}.xlsx"
    
    return StreamingResponse(
        BytesIO(excel_file.read()),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

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

# Add CORS middleware with debug logging
cors_origins_str = os.environ.get('CORS_ORIGINS', '*')
print(f"CORS Origins string from env: '{cors_origins_str}'")
cors_origins = cors_origins_str.split(',') if cors_origins_str != '*' else ["*"]
print(f"CORS Origins configured: {cors_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],  # Temporarily allow all origins for testing
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