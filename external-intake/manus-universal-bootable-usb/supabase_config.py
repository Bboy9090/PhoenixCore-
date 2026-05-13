"""
Supabase Configuration for Bobby's PhoenixDrive
Handles PostgreSQL database connection and real-time features
"""

import os
import logging
from typing import Optional
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool

logger = logging.getLogger(__name__)


class SupabaseConfig:
    """Supabase configuration and connection management."""
    
    def __init__(self):
        """Initialize Supabase configuration."""
        self.url = os.getenv("SUPABASE_URL", "")
        self.key = os.getenv("SUPABASE_KEY", "")
        self.db_url = os.getenv("DATABASE_URL", "")
        self.jwt_secret = os.getenv("JWT_SECRET", "")
        
        # Parse database URL
        if self.db_url:
            self.engine = create_engine(
                self.db_url,
                poolclass=NullPool,  # Vercel serverless compatibility
                echo=False,
            )
        else:
            self.engine = None
        
        self.SessionLocal = sessionmaker(bind=self.engine) if self.engine else None
    
    def get_session(self) -> Optional[Session]:
        """Get database session."""
        if self.SessionLocal:
            return self.SessionLocal()
        return None
    
    def test_connection(self) -> bool:
        """Test database connection."""
        try:
            if self.engine:
                with self.engine.connect() as conn:
                    result = conn.execute(text("SELECT 1"))
                    logger.info("✓ Supabase database connection successful")
                    return True
            else:
                logger.warning("Database engine not configured")
                return False
        except Exception as e:
            logger.error(f"✗ Supabase database connection failed: {e}")
            return False


# Global Supabase instance
supabase_config = SupabaseConfig()


# Database Schema SQL
SCHEMA_SQL = """
-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Builds table
CREATE TABLE IF NOT EXISTS builds (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    build_id VARCHAR(255) UNIQUE NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'idle',
    overall_progress FLOAT DEFAULT 0,
    current_stage VARCHAR(255),
    stage_progress FLOAT DEFAULT 0,
    current_component VARCHAR(255),
    components_completed INT DEFAULT 0,
    total_components INT DEFAULT 0,
    speed_mbps FLOAT DEFAULT 0,
    eta_seconds INT DEFAULT 0,
    data_written_mb FLOAT DEFAULT 0,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);

-- Recipes table
CREATE TABLE IF NOT EXISTS recipes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    recipe_id VARCHAR(255) UNIQUE NOT NULL,
    recipe_name VARCHAR(255) NOT NULL,
    os_type VARCHAR(100) NOT NULL,
    os_version VARCHAR(100),
    tools JSONB DEFAULT '[]'::jsonb,
    checksum VARCHAR(255),
    timestamp TIMESTAMP DEFAULT NOW(),
    version VARCHAR(20) DEFAULT '1.0',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Hardware profiles table
CREATE TABLE IF NOT EXISTS hardware_profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    device_name VARCHAR(255) NOT NULL,
    device_type VARCHAR(100) NOT NULL,
    cpu_brand VARCHAR(100),
    gpu_model VARCHAR(255),
    ram_gb INT,
    storage_gb INT,
    os_type VARCHAR(100),
    bootcamp_compatible BOOLEAN DEFAULT FALSE,
    detected_at TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Build history table
CREATE TABLE IF NOT EXISTS build_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    build_id VARCHAR(255) NOT NULL,
    recipe_id VARCHAR(255),
    status VARCHAR(50) NOT NULL,
    duration_seconds INT,
    data_written_mb FLOAT,
    error_message TEXT,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Admin notifications table
CREATE TABLE IF NOT EXISTS admin_notifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    notification_type VARCHAR(100) NOT NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT,
    severity VARCHAR(50) DEFAULT 'info',
    read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Admin notification preferences table
CREATE TABLE IF NOT EXISTS admin_notification_preferences (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    admin_id VARCHAR(255) NOT NULL UNIQUE,
    email_addresses JSONB DEFAULT '[]'::jsonb,
    notification_types JSONB DEFAULT '{}'::jsonb,
    alert_thresholds JSONB DEFAULT '{}'::jsonb,
    quiet_hours_enabled BOOLEAN DEFAULT FALSE,
    quiet_hours_start VARCHAR(5),
    quiet_hours_end VARCHAR(5),
    timezone VARCHAR(100) DEFAULT 'UTC',
    digest_enabled BOOLEAN DEFAULT FALSE,
    digest_frequency VARCHAR(50),
    digest_time VARCHAR(5),
    notification_channels JSONB DEFAULT '["email"]'::jsonb,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Boot Camp installations table
CREATE TABLE IF NOT EXISTS bootcamp_installations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    installation_id VARCHAR(255) UNIQUE NOT NULL,
    mac_model VARCHAR(255) NOT NULL,
    driver_package_id VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    progress FLOAT DEFAULT 0,
    error_message TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_builds_build_id ON builds(build_id);
CREATE INDEX IF NOT EXISTS idx_builds_status ON builds(status);
CREATE INDEX IF NOT EXISTS idx_recipes_recipe_id ON recipes(recipe_id);
CREATE INDEX IF NOT EXISTS idx_hardware_device_type ON hardware_profiles(device_type);
CREATE INDEX IF NOT EXISTS idx_build_history_build_id ON build_history(build_id);
CREATE INDEX IF NOT EXISTS idx_bootcamp_mac_model ON bootcamp_installations(mac_model);

-- Enable row-level security
ALTER TABLE builds ENABLE ROW LEVEL SECURITY;
ALTER TABLE recipes ENABLE ROW LEVEL SECURITY;
ALTER TABLE hardware_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE build_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE admin_notifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE bootcamp_installations ENABLE ROW LEVEL SECURITY;

-- Create RLS policies (allow all for now, restrict in production)
CREATE POLICY "Allow all access" ON builds FOR ALL USING (true);
CREATE POLICY "Allow all access" ON recipes FOR ALL USING (true);
CREATE POLICY "Allow all access" ON hardware_profiles FOR ALL USING (true);
CREATE POLICY "Allow all access" ON build_history FOR ALL USING (true);
CREATE POLICY "Allow all access" ON admin_notifications FOR ALL USING (true);
CREATE POLICY "Allow all access" ON bootcamp_installations FOR ALL USING (true);
"""


def init_database():
    """Initialize database schema."""
    try:
        if supabase_config.engine:
            with supabase_config.engine.connect() as conn:
                # Split SQL into individual statements
                statements = SCHEMA_SQL.split(';')
                for statement in statements:
                    if statement.strip():
                        conn.execute(text(statement))
                conn.commit()
                logger.info("✓ Database schema initialized successfully")
                return True
        else:
            logger.warning("Database engine not configured")
            return False
    except Exception as e:
        logger.error(f"✗ Failed to initialize database schema: {e}")
        return False


def get_db() -> Optional[Session]:
    """Get database session for dependency injection."""
    session = supabase_config.get_session()
    try:
        yield session
    finally:
        if session:
            session.close()
