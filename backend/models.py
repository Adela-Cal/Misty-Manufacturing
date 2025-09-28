from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
import uuid

# Enums for system constants
class UserRole(str, Enum):
    ADMIN = "admin"
    PRODUCTION_MANAGER = "production_manager"
    SALES = "sales"
    PRODUCTION_TEAM = "production_team"
    MANAGER = "manager"          # Department/Team managers
    EMPLOYEE = "employee"        # Regular employees

class ProductionStage(str, Enum):
    ORDER_ENTERED = "order_entered"
    PENDING_MATERIAL = "pending_material"
    PAPER_SLITTING = "paper_slitting"
    WINDING = "winding"
    FINISHING = "finishing"
    DELIVERY = "delivery"
    INVOICING = "invoicing"
    CLEARED = "cleared"

class OrderStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    OVERDUE = "overdue"

# User Models
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    email: EmailStr
    hashed_password: str
    role: UserRole
    full_name: str
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    role: UserRole
    full_name: str

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user: dict

# Client Models
class ClientContact(BaseModel):
    name: str
    position: str
    email: EmailStr
    phone: str
    is_primary: bool = False

class ClientBankDetails(BaseModel):
    bank_name: str
    account_name: str
    bsb: str
    account_number: str
    reference: Optional[str] = None

class Client(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    company_name: str
    abn: Optional[str] = None
    address: str
    city: str
    state: str
    postal_code: str
    country: str = "Australia"
    phone: str
    email: EmailStr
    website: Optional[str] = None
    logo_path: Optional[str] = None
    contacts: List[ClientContact] = []
    bank_details: Optional[ClientBankDetails] = None
    payment_terms: str = "Net 30 days"  # Default payment terms
    lead_time_days: int = 7  # Default lead time in days
    notes: Optional[str] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

class ClientCreate(BaseModel):
    company_name: str
    abn: Optional[str] = None
    address: str
    city: str
    state: str
    postal_code: str
    country: str = "Australia"
    phone: str
    email: EmailStr
    website: Optional[str] = None
    contacts: List[ClientContact] = []
    bank_details: Optional[ClientBankDetails] = None
    payment_terms: str = "Net 30 days"
    lead_time_days: int = 7
    notes: Optional[str] = None

# Product Models
class ProductSpecification(BaseModel):
    material_type: str
    dimensions: str
    weight: Optional[str] = None
    color: Optional[str] = None
    finishing_requirements: Optional[str] = None
    quality_standards: Optional[str] = None
    special_instructions: Optional[str] = None

class Product(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_id: str
    product_name: str
    product_code: Optional[str] = None
    description: str
    unit_price: float
    unit_of_measure: str
    specifications: ProductSpecification
    delivery_requirements: Optional[str] = None
    lead_time_days: int = 7
    point_of_contact: Optional[str] = None
    notes: Optional[str] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

class ProductCreate(BaseModel):
    client_id: str
    product_name: str
    product_code: Optional[str] = None
    description: str
    unit_price: float
    unit_of_measure: str
    specifications: ProductSpecification
    delivery_requirements: Optional[str] = None
    lead_time_days: int = 7
    point_of_contact: Optional[str] = None
    notes: Optional[str] = None

# Order Models
class OrderItem(BaseModel):
    product_id: str
    product_name: str
    quantity: int
    unit_price: float
    total_price: float
    specifications: Optional[ProductSpecification] = None
    is_completed: bool = False  # Track if this item is completed

class Order(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    order_number: str
    client_id: str
    client_name: str
    items: List[OrderItem]
    subtotal: float
    gst: float
    total_amount: float
    due_date: datetime
    delivery_address: Optional[str] = None
    delivery_instructions: Optional[str] = None
    status: OrderStatus = OrderStatus.ACTIVE
    current_stage: ProductionStage = ProductionStage.ORDER_ENTERED
    runtime_estimate: Optional[str] = None  # e.g., "2-3 days", "1 week"
    notes: Optional[str] = None
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

class OrderCreate(BaseModel):
    client_id: str
    items: List[OrderItem]
    due_date: datetime
    delivery_address: Optional[str] = None
    delivery_instructions: Optional[str] = None
    runtime_estimate: Optional[str] = None
    notes: Optional[str] = None

# Production Stage Tracking
class ProductionStageUpdate(BaseModel):
    order_id: str
    from_stage: ProductionStage
    to_stage: ProductionStage
    updated_by: str
    notes: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ProductionLog(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    order_id: str
    stage: ProductionStage
    updated_by: str
    notes: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

# Materials Status Tracking
class MaterialsStatus(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    order_id: str
    materials_ready: bool = False
    materials_checklist: List[Dict[str, Any]] = []  # List of materials with ready status
    updated_by: str
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class MaterialsStatusUpdate(BaseModel):
    materials_ready: bool
    materials_checklist: List[Dict[str, Any]] = []

# Order Item Status Updates
class OrderItemStatusUpdate(BaseModel):
    item_index: int
    is_completed: bool

# Stage Movement Request
class StageMovementRequest(BaseModel):
    direction: str  # "forward" or "backward"
    notes: Optional[str] = None

# Job Specification Models
class JobSpecification(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    order_id: str
    product_id: str
    client_requirements: str
    delivery_timeline: str
    point_of_contact: str
    contact_email: EmailStr
    contact_phone: str
    special_instructions: Optional[str] = None
    quality_checkpoints: List[str] = []
    materials_required: List[str] = []
    estimated_completion: datetime
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

class JobSpecificationCreate(BaseModel):
    order_id: str
    product_id: str
    client_requirements: str
    delivery_timeline: str
    point_of_contact: str
    contact_email: EmailStr
    contact_phone: str
    special_instructions: Optional[str] = None
    quality_checkpoints: List[str] = []
    materials_required: List[str] = []
    estimated_completion: datetime

# Report Models
class OutstandingJobsReport(BaseModel):
    total_jobs: int
    jobs_by_stage: Dict[str, int]
    overdue_jobs: int
    jobs_due_today: int
    jobs_due_this_week: int
    report_generated_at: datetime = Field(default_factory=datetime.utcnow)

class LateDeliveryReport(BaseModel):
    total_late_deliveries: int
    average_delay_days: float
    late_deliveries_by_client: Dict[str, int]
    late_deliveries_by_month: Dict[str, int]
    report_generated_at: datetime = Field(default_factory=datetime.utcnow)

class CustomerAnnualReport(BaseModel):
    client_id: str
    client_name: str
    year: int
    total_orders: int
    total_revenue: float
    average_order_value: float
    orders_by_month: Dict[str, int]
    revenue_by_month: Dict[str, float]
    top_products: List[Dict[str, Any]]
    on_time_delivery_rate: float
    report_generated_at: datetime = Field(default_factory=datetime.utcnow)

# Document Models
class DocumentTemplate(BaseModel):
    type: str  # acknowledgment, job_card, packing_list, invoice
    template_data: Dict[str, Any]
    generated_at: datetime = Field(default_factory=datetime.utcnow)

# Materials & Products Models
class Material(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    supplier: str
    product_code: str
    order_to_delivery_time: str
    price: float
    unit: str  # m2, By the Box, Single Unit
    raw_substrate: bool = False
    # Raw substrate fields (only if raw_substrate is True)
    gsm: Optional[str] = None
    thickness_mm: Optional[float] = None
    burst_strength_kpa: Optional[float] = None
    ply_bonding_jm2: Optional[float] = None
    moisture_percent: Optional[float] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

class MaterialCreate(BaseModel):
    supplier: str
    product_code: str
    order_to_delivery_time: str
    price: float
    unit: str
    raw_substrate: bool = False
    gsm: Optional[str] = None
    thickness_mm: Optional[float] = None
    burst_strength_kpa: Optional[float] = None
    ply_bonding_jm2: Optional[float] = None
    moisture_percent: Optional[float] = None

# Client Product Types
class ClientProductType(str, Enum):
    FINISHED_GOODS = "finished_goods"
    PAPER_CORES = "paper_cores"

class ClientProduct(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_id: str
    product_type: ClientProductType
    product_code: str
    product_description: str
    price_ex_gst: float
    minimum_order_quantity: int
    consignment: bool = False
    
    # Paper Cores specific fields
    material_used: Optional[List[str]] = []  # List of material IDs
    core_id: Optional[str] = None
    core_width: Optional[str] = None
    core_thickness: Optional[str] = None
    strength_quality_important: Optional[bool] = False
    delivery_included: Optional[bool] = False
    
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

class ClientProductCreate(BaseModel):
    client_id: Optional[str] = None  # Will be set from URL path
    product_type: ClientProductType
    product_code: str
    product_description: str
    price_ex_gst: float
    minimum_order_quantity: int
    consignment: bool = False
    material_used: Optional[List[str]] = []
    core_id: Optional[str] = None
    core_width: Optional[str] = None
    core_thickness: Optional[str] = None
    strength_quality_important: Optional[bool] = False
    delivery_included: Optional[bool] = False

# Response Models
class StandardResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Any] = None

class PaginatedResponse(BaseModel):
    success: bool
    data: List[Any]
    total: int
    page: int
    per_page: int
    total_pages: int