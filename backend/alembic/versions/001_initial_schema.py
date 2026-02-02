"""Initial schema for Israeli CRE marketplace

Revision ID: 001
Revises:
Create Date: 2026-02-02
"""
from alembic import op
import sqlalchemy as sa

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Users table
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("full_name_he", sa.String(255), nullable=True),
        sa.Column("phone", sa.String(20), nullable=True),
        sa.Column("role", sa.Enum("landlord", "tenant", "broker", "admin", name="userrole"), nullable=False),
        sa.Column("company", sa.String(255), nullable=True),
        sa.Column("company_he", sa.String(255), nullable=True),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column("is_verified", sa.Boolean(), default=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_id", "users", ["id"])
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    # Properties table
    op.create_table(
        "properties",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("owner_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("name_he", sa.String(255), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("description_he", sa.Text(), nullable=True),
        sa.Column("property_type", sa.Enum("office", "retail", "industrial", "logistics", "coworking", "mixed_use", name="propertytype"), nullable=False),
        sa.Column("status", sa.Enum("active", "inactive", "under_renovation", name="propertystatus"), default="active"),
        sa.Column("city", sa.Enum("tel_aviv", "jerusalem", "haifa", "beer_sheva", "ramat_gan", "herzliya", "petah_tikva", "netanya", "rishon_lezion", "ashdod", "holon", "bnei_brak", "rehovot", "kfar_saba", "modiin", "raanana", "lod", "yokneam", "caesarea", "other", name="city"), nullable=False),
        sa.Column("neighborhood", sa.String(255), nullable=True),
        sa.Column("neighborhood_he", sa.String(255), nullable=True),
        sa.Column("street_address", sa.String(255), nullable=True),
        sa.Column("street_address_he", sa.String(255), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("total_area_sqm", sa.Float(), nullable=False),
        sa.Column("floor_count", sa.Integer(), nullable=True),
        sa.Column("year_built", sa.Integer(), nullable=True),
        sa.Column("parking_spots", sa.Integer(), default=0),
        sa.Column("has_elevator", sa.Boolean(), default=False),
        sa.Column("has_loading_dock", sa.Boolean(), default=False),
        sa.Column("has_generator", sa.Boolean(), default=False),
        sa.Column("accessibility", sa.Boolean(), default=False),
        sa.Column("building_class", sa.String(10), nullable=True),
        sa.Column("energy_rating", sa.String(10), nullable=True),
        sa.Column("arnona_zone", sa.String(50), nullable=True),
        sa.Column("images", sa.JSON(), default=[]),
        sa.Column("floor_plans", sa.JSON(), default=[]),
        sa.Column("virtual_tour_url", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"]),
    )
    op.create_index("ix_properties_id", "properties", ["id"])
    op.create_index("ix_properties_owner_id", "properties", ["owner_id"])
    op.create_index("ix_properties_city_type", "properties", ["city", "property_type"])
    op.create_index("ix_properties_area", "properties", ["total_area_sqm"])

    # Property Units table
    op.create_table(
        "property_units",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("property_id", sa.Integer(), nullable=False),
        sa.Column("unit_number", sa.String(50), nullable=False),
        sa.Column("floor", sa.Integer(), nullable=True),
        sa.Column("area_sqm", sa.Float(), nullable=False),
        sa.Column("is_available", sa.Boolean(), default=True),
        sa.Column("unit_type", sa.Enum("office", "retail", "industrial", "logistics", "coworking", "mixed_use", name="propertytype", create_type=False), nullable=True),
        sa.Column("rooms", sa.Integer(), nullable=True),
        sa.Column("has_balcony", sa.Boolean(), default=False),
        sa.Column("has_kitchenette", sa.Boolean(), default=False),
        sa.Column("has_server_room", sa.Boolean(), default=False),
        sa.Column("ceiling_height_m", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["property_id"], ["properties.id"]),
    )
    op.create_index("ix_property_units_id", "property_units", ["id"])
    op.create_index("ix_property_units_property_id", "property_units", ["property_id"])

    # Listings table
    op.create_table(
        "listings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("property_id", sa.Integer(), nullable=False),
        sa.Column("unit_id", sa.Integer(), nullable=True),
        sa.Column("broker_id", sa.Integer(), nullable=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("title_he", sa.String(255), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("description_he", sa.Text(), nullable=True),
        sa.Column("listing_type", sa.Enum("lease", "sublease", "sale", name="listingtype"), nullable=False),
        sa.Column("status", sa.Enum("active", "pending", "leased", "sold", "withdrawn", "expired", name="listingstatus"), default="active"),
        sa.Column("price", sa.Float(), nullable=False),
        sa.Column("price_period", sa.Enum("monthly", "annual", "per_sqm_monthly", "per_sqm_annual", "total", name="priceperiod"), default="monthly"),
        sa.Column("management_fee_monthly", sa.Float(), nullable=True),
        sa.Column("arnona_monthly", sa.Float(), nullable=True),
        sa.Column("negotiable", sa.Boolean(), default=True),
        sa.Column("available_area_sqm", sa.Float(), nullable=False),
        sa.Column("min_area_sqm", sa.Float(), nullable=True),
        sa.Column("min_lease_months", sa.Integer(), nullable=True),
        sa.Column("max_lease_months", sa.Integer(), nullable=True),
        sa.Column("available_from", sa.DateTime(timezone=True), nullable=True),
        sa.Column("furnished", sa.Boolean(), default=False),
        sa.Column("condition", sa.String(50), nullable=True),
        sa.Column("view_count", sa.Integer(), default=0),
        sa.Column("inquiry_count", sa.Integer(), default=0),
        sa.Column("tour_count", sa.Integer(), default=0),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["property_id"], ["properties.id"]),
        sa.ForeignKeyConstraint(["unit_id"], ["property_units.id"]),
        sa.ForeignKeyConstraint(["broker_id"], ["users.id"]),
    )
    op.create_index("ix_listings_id", "listings", ["id"])
    op.create_index("ix_listings_property_id", "listings", ["property_id"])
    op.create_index("ix_listings_status_type", "listings", ["status", "listing_type"])
    op.create_index("ix_listings_price", "listings", ["price"])
    op.create_index("ix_listings_area", "listings", ["available_area_sqm"])

    # Deals table
    op.create_table(
        "deals",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("listing_id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("broker_id", sa.Integer(), nullable=True),
        sa.Column("stage", sa.Enum("inquiry", "tour_scheduled", "tour_completed", "proposal", "negotiation", "loi_signed", "legal_review", "signed", "lost", "withdrawn", name="dealstage"), nullable=False),
        sa.Column("proposed_price", sa.Float(), nullable=True),
        sa.Column("final_price", sa.Float(), nullable=True),
        sa.Column("proposed_area_sqm", sa.Float(), nullable=True),
        sa.Column("lease_term_months", sa.Integer(), nullable=True),
        sa.Column("inquiry_date", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("tour_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("proposal_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("loi_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("signed_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("lost_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expected_move_in", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("lost_reason", sa.String(255), nullable=True),
        sa.Column("activity_log", sa.JSON(), default=[]),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["listing_id"], ["listings.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["broker_id"], ["users.id"]),
    )
    op.create_index("ix_deals_id", "deals", ["id"])
    op.create_index("ix_deals_listing_id", "deals", ["listing_id"])
    op.create_index("ix_deals_stage_date", "deals", ["stage", "inquiry_date"])

    # Tours table
    op.create_table(
        "tours",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("listing_id", sa.Integer(), nullable=False),
        sa.Column("contact_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.Enum("requested", "confirmed", "completed", "cancelled", "no_show", name="tourstatus"), default="requested"),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_minutes", sa.Integer(), default=30),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("rating", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["listing_id"], ["listings.id"]),
        sa.ForeignKeyConstraint(["contact_id"], ["users.id"]),
    )
    op.create_index("ix_tours_id", "tours", ["id"])
    op.create_index("ix_tours_listing_id", "tours", ["listing_id"])

    # Favorites table
    op.create_table(
        "favorites",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("listing_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["listing_id"], ["listings.id"]),
        sa.UniqueConstraint("user_id", "listing_id", name="uq_user_listing_favorite"),
    )
    op.create_index("ix_favorites_id", "favorites", ["id"])
    op.create_index("ix_favorites_user_id", "favorites", ["user_id"])

    # Market Snapshots table
    op.create_table(
        "market_snapshots",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("snapshot_date", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("city", sa.Enum("tel_aviv", "jerusalem", "haifa", "beer_sheva", "ramat_gan", "herzliya", "petah_tikva", "netanya", "rishon_lezion", "ashdod", "holon", "bnei_brak", "rehovot", "kfar_saba", "modiin", "raanana", "lod", "yokneam", "caesarea", "other", name="city", create_type=False), nullable=False),
        sa.Column("property_type", sa.Enum("office", "retail", "industrial", "logistics", "coworking", "mixed_use", name="propertytype", create_type=False), nullable=False),
        sa.Column("avg_price_per_sqm", sa.Float(), nullable=True),
        sa.Column("median_price_per_sqm", sa.Float(), nullable=True),
        sa.Column("min_price_per_sqm", sa.Float(), nullable=True),
        sa.Column("max_price_per_sqm", sa.Float(), nullable=True),
        sa.Column("total_listings", sa.Integer(), default=0),
        sa.Column("total_available_sqm", sa.Float(), default=0),
        sa.Column("new_listings_count", sa.Integer(), default=0),
        sa.Column("absorbed_listings_count", sa.Integer(), default=0),
        sa.Column("avg_days_on_market", sa.Float(), nullable=True),
        sa.Column("occupancy_rate", sa.Float(), nullable=True),
        sa.Column("deals_closed", sa.Integer(), default=0),
        sa.Column("avg_deal_price_per_sqm", sa.Float(), nullable=True),
        sa.Column("avg_lease_term_months", sa.Float(), nullable=True),
        sa.Column("details_json", sa.JSON(), default={}),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_market_snapshots_id", "market_snapshots", ["id"])
    op.create_index("ix_market_city_type_date", "market_snapshots", ["city", "property_type", "snapshot_date"])


def downgrade() -> None:
    op.drop_table("market_snapshots")
    op.drop_table("favorites")
    op.drop_table("tours")
    op.drop_table("deals")
    op.drop_table("listings")
    op.drop_table("property_units")
    op.drop_table("properties")
    op.drop_table("users")
