from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timezone
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

class EmploymentType(str, Enum):
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CASUAL = "casual"

class ProductionStage(str, Enum):
    ORDER_ENTERED = "order_entered"
    PENDING_MATERIAL = "pending_material"
    PAPER_SLITTING = "paper_slitting"
    WINDING = "winding"
    FINISHING = "finishing"
    DELIVERY = "delivery"
    INVOICING = "invoicing"
    ACCOUNTING_TRANSACTION = "accounting_transaction"  # New stage for accounting processing
    CLEARED = "cleared"

class OrderStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    OVERDUE = "overdue"
    ACCOUNTING_DRAFT = "accounting_draft"  # New status for accounting transactions
    ARCHIVED = "archived"

class OrderPriority(str, Enum):
    ASAP = "ASAP"
    MUST_DELIVERY_ON_DATE = "Must Delivery On Date"
    NORMAL_LOW = "Normal/Low"

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
    full_name: str
    role: UserRole = UserRole.PRODUCTION_TEAM
    department: Optional[str] = None
    phone: Optional[str] = None
    employment_type: EmploymentType = EmploymentType.FULL_TIME

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
    purchase_order_number: Optional[str] = None  # Client's PO number
    items: List[OrderItem]
    subtotal: float
    discount_percentage: Optional[float] = None  # Discount percentage (0-100)
    discount_amount: Optional[float] = None  # Calculated discount amount
    discount_notes: Optional[str] = None  # Reason for discount
    discounted_subtotal: Optional[float] = None  # Subtotal after discount
    gst: float
    total_amount: float
    due_date: datetime
    priority: OrderPriority = OrderPriority.NORMAL_LOW
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
    purchase_order_number: Optional[str] = None  # Client's PO number
    items: List[OrderItem]
    discount_percentage: Optional[float] = None  # Discount percentage (0-100)
    discount_notes: Optional[str] = None  # Reason for discount
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

class StageJumpRequest(BaseModel):
    target_stage: str  # Direct stage to jump to
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

# Supplier Models
class Supplier(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    supplier_name: str
    contact_person: Optional[str] = None
    phone_number: str
    email: EmailStr
    physical_address: str
    post_code: str
    currency_accepted: str = "AUD"
    # Bank details
    bank_name: str
    bank_address: str
    account_name: str  # New field
    bank_account_number: str
    swift_code: Optional[str] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

class SupplierCreate(BaseModel):
    supplier_name: str
    contact_person: Optional[str] = None
    phone_number: str
    email: EmailStr
    physical_address: str
    post_code: str
    currency_accepted: str = "AUD"
    bank_name: str
    bank_address: str
    account_name: str  # New field
    bank_account_number: str
    swift_code: Optional[str] = None

# Product Specifications Models
# Enhanced Material Layer Assignment Model
class MaterialLayerAssignment(BaseModel):
    material_id: str
    material_name: str
    layer_type: str  # "Outer Most Layer", "Central Layer", "Inner Most Layer"
    width: Optional[float] = None  # mm for Outer/Inner layers
    width_range: Optional[str] = None  # e.g., "61-68" for Central layers
    thickness: float  # mm - thickness of this material
    quantity: Optional[float] = None  # quantity/percentage if applicable
    notes: Optional[str] = None

# Machinery Models for Product Specifications
class MachineryRate(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    function: str  # "Slitting", "winding", "Cutting/Indexing", "splitting", "Packing", "Delivery Time"
    rate_per_hour: float  # Default $ rate per hour for this function
    description: Optional[str] = None  # Optional description for the rate
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

class MachineryRateCreate(BaseModel):
    function: str
    rate_per_hour: float
    description: Optional[str] = None

class MachineryRateUpdate(BaseModel):
    function: Optional[str] = None
    rate_per_hour: Optional[float] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

class MachineryFunction(BaseModel):
    function: str  # "Slitting", "winding", "Cutting/Indexing", "splitting", "Packing", "Delivery Time"
    rate_per_hour: Optional[float] = None  # $ rate per hour for this function

class MachinerySpec(BaseModel):
    machine_name: str
    running_speed: Optional[float] = None  # Meters Per Minute
    setup_time: Optional[str] = None  # Time in HH:MM format
    pack_up_time: Optional[str] = None  # Time in HH:MM format
    functions: List[MachineryFunction] = []  # Available functions for this machine

class ProductSpecification(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    product_name: str
    product_type: str  # e.g., "Paper Core", "Spiral Paper Core"
    specifications: Dict[str, Any]  # Flexible spec storage
    materials_composition: List[Dict[str, Any]] = []  # Legacy materials (for backward compatibility)
    material_layers: List[MaterialLayerAssignment] = []  # New enhanced material layers
    machinery: List[MachinerySpec] = []  # Machinery specifications for job card/run sheet
    manufacturing_notes: Optional[str] = None
    calculated_total_thickness: Optional[float] = None  # Auto-calculated from material layers
    selected_thickness: Optional[float] = None  # User-selected thickness from calculated options
    thickness_options: List[float] = []  # Available thickness options
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

class ProductSpecificationCreate(BaseModel):
    product_name: str
    product_type: str
    specifications: Dict[str, Any]
    materials_composition: List[Dict[str, Any]] = []
    material_layers: List[MaterialLayerAssignment] = []
    machinery: List[MachinerySpec] = []
    manufacturing_notes: Optional[str] = None
    selected_thickness: Optional[float] = None

# Calculator Models
class MaterialConsumptionByClientRequest(BaseModel):
    client_id: str
    material_id: str
    start_date: date
    end_date: date

class MaterialPermutationRequest(BaseModel):
    core_ids: List[str]
    sizes_to_manufacture: List[Dict[str, Any]]  # [{width: float, priority: int}]
    master_deckle_width: float
    acceptable_waste_percentage: float

class SpiralCoreConsumptionRequest(BaseModel):
    product_specification_id: str
    core_internal_diameter: float  # mm
    core_length: float  # mm
    quantity: int

class CalculationResult(BaseModel):
    calculation_type: str
    input_parameters: Dict[str, Any]
    results: Dict[str, Any]
    calculated_at: datetime = Field(default_factory=datetime.utcnow)
    calculated_by: str

# Stocktake Models
class StocktakeEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    stocktake_id: str
    material_id: str
    material_name: str
    current_quantity: float  # Up to 2 decimal places
    unit: str
    counted_by: str
    counted_at: datetime = Field(default_factory=datetime.utcnow)

class Stocktake(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    stocktake_date: date
    month: str  # "2025-09"
    status: str = "in_progress"  # in_progress, completed
    entries: List[StocktakeEntry] = []
    completed_by: Optional[str] = None
    completed_at: Optional[datetime] = None
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class StocktakeCreate(BaseModel):
    stocktake_date: date
    
class StocktakeEntryUpdate(BaseModel):
    material_id: str
    current_quantity: float

# User Management Models (Enhanced)
# UserRole enum is defined earlier in the file - removed duplicate

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    role: Optional[UserRole] = None
    department: Optional[str] = None
    phone: Optional[str] = None
    employment_type: Optional[EmploymentType] = None
    is_active: Optional[bool] = None

class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str

# Materials & Products Models
class Material(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    supplier: str
    product_code: str
    order_to_delivery_time: str
    material_description: Optional[str] = None  # Made optional for backward compatibility
    price: float
    currency: str = "AUD"  # New field with default
    unit: str  # m2, By the Box, Single Unit
    raw_substrate: bool = False
    # Raw substrate fields (only if raw_substrate is True)
    gsm: Optional[str] = None
    thickness_mm: Optional[float] = None
    burst_strength_kpa: Optional[float] = None
    ply_bonding_jm2: Optional[float] = None
    moisture_percent: Optional[float] = None
    supplied_roll_weight: Optional[float] = None  # New field
    master_deckle_width_mm: Optional[float] = None  # New field
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

class MaterialCreate(BaseModel):
    supplier: str
    product_code: str
    order_to_delivery_time: str
    material_description: str  # New field
    price: float
    currency: str = "AUD"  # New field with default
    unit: str
    raw_substrate: bool = False
    gsm: Optional[str] = None
    thickness_mm: Optional[float] = None
    burst_strength_kpa: Optional[float] = None
    ply_bonding_jm2: Optional[float] = None
    moisture_percent: Optional[float] = None
    supplied_roll_weight: Optional[float] = None  # New field
    master_deckle_width_mm: Optional[float] = None  # New field

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
    
    # Common fields for database management
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None

# Archived Orders
class ArchivedOrder(BaseModel):
    """Complete order data preserved when archived"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    original_order_id: str
    order_number: str
    client_id: str
    client_name: str
    purchase_order_number: Optional[str] = None
    items: List[OrderItem]
    subtotal: float
    gst: float
    total_amount: float
    due_date: datetime
    delivery_address: Optional[str] = None
    delivery_instructions: Optional[str] = None
    status: OrderStatus = OrderStatus.ARCHIVED
    final_stage: ProductionStage = ProductionStage.CLEARED
    runtime_estimate: Optional[str] = None
    notes: Optional[str] = None
    created_by: str
    created_at: datetime
    completed_at: datetime
    archived_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    archived_by: str

class ArchivedOrderFilter(BaseModel):
    """Filters for archived orders search"""
    client_id: Optional[str] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    search_query: Optional[str] = None  # Search in order number, client name, product names
    
class ReportField(str, Enum):
    """Available fields for Fast Report"""
    ORDER_NUMBER = "order_number"
    CLIENT_NAME = "client_name"
    PURCHASE_ORDER_NUMBER = "purchase_order_number"
    ORDER_DATE = "created_at"
    COMPLETION_DATE = "completed_at"
    DUE_DATE = "due_date"
    SUBTOTAL = "subtotal"
    GST = "gst" 
    TOTAL_AMOUNT = "total_amount"
    DELIVERY_ADDRESS = "delivery_address"
    PRODUCT_NAMES = "product_names"
    PRODUCT_QUANTITIES = "product_quantities"
    NOTES = "notes"
    RUNTIME_ESTIMATE = "runtime_estimate"

class ReportTimePeriod(str, Enum):
    """Time period filters for reports"""
    CURRENT_MONTH = "current_month"
    LAST_MONTH = "last_month"
    LAST_3_MONTHS = "last_3_months"
    LAST_6_MONTHS = "last_6_months"
    LAST_9_MONTHS = "last_9_months"
    LAST_YEAR = "last_year"
    CURRENT_QUARTER = "current_quarter"
    LAST_QUARTER = "last_quarter"
    CURRENT_FINANCIAL_YEAR = "current_financial_year"
    LAST_FINANCIAL_YEAR = "last_financial_year"
    YEAR_TO_DATE = "year_to_date"
    CUSTOM_RANGE = "custom_range"

class FastReportRequest(BaseModel):
    """Request for generating Fast Report"""
    client_id: str
    time_period: ReportTimePeriod
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    selected_fields: List[ReportField]
    product_filter: Optional[str] = None  # Filter by specific product names
    report_title: Optional[str] = None
    
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