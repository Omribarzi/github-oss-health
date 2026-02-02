from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, JSON, ForeignKey
from sqlalchemy import Enum as SQLEnum, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum


class PropertyType(str, enum.Enum):
    OFFICE = "office"           # משרד
    RETAIL = "retail"           # מסחרי
    INDUSTRIAL = "industrial"   # תעשייה
    LOGISTICS = "logistics"     # לוגיסטיקה
    COWORKING = "coworking"     # חלל עבודה משותף
    MIXED_USE = "mixed_use"     # שימוש מעורב


class PropertyStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    UNDER_RENOVATION = "under_renovation"


class City(str, enum.Enum):
    TEL_AVIV = "tel_aviv"
    JERUSALEM = "jerusalem"
    HAIFA = "haifa"
    BEER_SHEVA = "beer_sheva"
    RAMAT_GAN = "ramat_gan"
    HERZLIYA = "herzliya"
    PETAH_TIKVA = "petah_tikva"
    NETANYA = "netanya"
    RISHON_LEZION = "rishon_lezion"
    ASHDOD = "ashdod"
    HOLON = "holon"
    BNEI_BRAK = "bnei_brak"
    REHOVOT = "rehovot"
    KFAR_SABA = "kfar_saba"
    MODIIN = "modiin"
    RAANANA = "raanana"
    LOD = "lod"
    YOKNEAM = "yokneam"
    CAESAREA = "caesarea"
    OTHER = "other"


# Hebrew city name mapping
CITY_NAMES_HE = {
    City.TEL_AVIV: "תל אביב-יפו",
    City.JERUSALEM: "ירושלים",
    City.HAIFA: "חיפה",
    City.BEER_SHEVA: "באר שבע",
    City.RAMAT_GAN: "רמת גן",
    City.HERZLIYA: "הרצליה",
    City.PETAH_TIKVA: "פתח תקווה",
    City.NETANYA: "נתניה",
    City.RISHON_LEZION: "ראשון לציון",
    City.ASHDOD: "אשדוד",
    City.HOLON: "חולון",
    City.BNEI_BRAK: "בני ברק",
    City.REHOVOT: "רחובות",
    City.KFAR_SABA: "כפר סבא",
    City.MODIIN: "מודיעין",
    City.RAANANA: "רעננה",
    City.LOD: "לוד",
    City.YOKNEAM: "יקנעם",
    City.CAESAREA: "קיסריה",
    City.OTHER: "אחר",
}

PROPERTY_TYPE_NAMES_HE = {
    PropertyType.OFFICE: "משרד",
    PropertyType.RETAIL: "מסחרי",
    PropertyType.INDUSTRIAL: "תעשייה",
    PropertyType.LOGISTICS: "לוגיסטיקה",
    PropertyType.COWORKING: "חלל עבודה משותף",
    PropertyType.MIXED_USE: "שימוש מעורב",
}


class Property(Base):
    __tablename__ = "properties"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Basic info
    name = Column(String(255), nullable=False)
    name_he = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    description_he = Column(Text, nullable=True)
    property_type = Column(SQLEnum(PropertyType), nullable=False, index=True)
    status = Column(SQLEnum(PropertyStatus), default=PropertyStatus.ACTIVE)

    # Location
    city = Column(SQLEnum(City), nullable=False, index=True)
    neighborhood = Column(String(255), nullable=True)
    neighborhood_he = Column(String(255), nullable=True)
    street_address = Column(String(255), nullable=True)
    street_address_he = Column(String(255), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    # Building details
    total_area_sqm = Column(Float, nullable=False)
    floor_count = Column(Integer, nullable=True)
    year_built = Column(Integer, nullable=True)
    parking_spots = Column(Integer, default=0)
    has_elevator = Column(Boolean, default=False)
    has_loading_dock = Column(Boolean, default=False)
    has_generator = Column(Boolean, default=False)
    accessibility = Column(Boolean, default=False)

    # Classification (Israeli standards)
    building_class = Column(String(10), nullable=True)  # A, B, C
    energy_rating = Column(String(10), nullable=True)
    arnona_zone = Column(String(50), nullable=True)  # ארנונה zone

    # Media
    images = Column(JSON, default=list)  # List of image URLs
    floor_plans = Column(JSON, default=list)
    virtual_tour_url = Column(String(500), nullable=True)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    owner = relationship("User", back_populates="properties")
    units = relationship("PropertyUnit", back_populates="property", cascade="all, delete-orphan")
    listings = relationship("Listing", back_populates="property")

    __table_args__ = (
        Index("ix_properties_city_type", "city", "property_type"),
        Index("ix_properties_area", "total_area_sqm"),
    )


class PropertyUnit(Base):
    __tablename__ = "property_units"

    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=False, index=True)

    unit_number = Column(String(50), nullable=False)
    floor = Column(Integer, nullable=True)
    area_sqm = Column(Float, nullable=False)
    is_available = Column(Boolean, default=True)
    unit_type = Column(SQLEnum(PropertyType), nullable=True)

    # Unit features
    rooms = Column(Integer, nullable=True)
    has_balcony = Column(Boolean, default=False)
    has_kitchenette = Column(Boolean, default=False)
    has_server_room = Column(Boolean, default=False)
    ceiling_height_m = Column(Float, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    property = relationship("Property", back_populates="units")
    listings = relationship("Listing", back_populates="unit")
