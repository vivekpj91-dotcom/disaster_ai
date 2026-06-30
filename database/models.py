import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database.db_connection import Base

class User(Base):
    """User Model representing anonymous sessions and authenticated users."""
    __tablename__ = "users"

    session_id = Column(String(255), primary_key=True, index=True)
    auth_provider = Column(String(50), default="anonymous")
    email = Column(String(255), unique=True, index=True, nullable=True)
    last_latitude = Column(Float, nullable=True)
    last_longitude = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Relationships
    emergency_requests = relationship("EmergencyRequest", back_populates="user", cascade="all, delete-orphan")
    disaster_reports = relationship("DisasterReport", back_populates="user", cascade="all, delete-orphan")
    uploaded_images = relationship("UploadedImage", back_populates="user", cascade="all, delete-orphan")
    conversations = relationship("ConversationHistory", back_populates="user", cascade="all, delete-orphan")


class EmergencyRequest(Base):
    """Emergency Requests Model representing direct calls for life safety rescue."""
    __tablename__ = "emergency_requests"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(String(255), ForeignKey("users.session_id", ondelete="SET NULL"), nullable=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    details = Column(Text, nullable=False)
    contact_phone = Column(String(50), nullable=True)
    priority = Column(String(50), default="NORMAL")  # CRITICAL, HIGH, NORMAL
    status = Column(String(50), default="PENDING")    # PENDING, DISPATCHED, RESOLVED
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="emergency_requests")
    images = relationship("UploadedImage", back_populates="emergency_request")


class Shelter(Base):
    """Shelter Model representing physical safety zones and capacities."""
    __tablename__ = "shelters"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    latitude = Column(Float, nullable=False, index=True)
    longitude = Column(Float, nullable=False, index=True)
    capacity = Column(Integer, nullable=False)
    occupancy = Column(Integer, default=0)
    status = Column(String(50), default="OPEN")  # OPEN, FULL, CLOSED
    address = Column(Text, nullable=True)
    contact_info = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


class Hospital(Base):
    """Hospital Model representing emergency medical facilities."""
    __tablename__ = "hospitals"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    latitude = Column(Float, nullable=False, index=True)
    longitude = Column(Float, nullable=False, index=True)
    status = Column(String(50), default="OPERATIONAL")  # OPERATIONAL, OVERLOADED, INOPERATIVE
    emergency_services = Column(Boolean, default=True)
    contact_info = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


class DisasterReport(Base):
    """Disaster Reports Model representing community-generated structural hazard updates."""
    __tablename__ = "disaster_reports"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(String(255), ForeignKey("users.session_id", ondelete="SET NULL"), nullable=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    disaster_type = Column(String(100), nullable=False)  # flood, earthquake, wildfire, etc.
    description = Column(Text, nullable=False)
    severity = Column(String(50), default="MEDIUM")       # LOW, MEDIUM, HIGH, CRITICAL
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="disaster_reports")
    images = relationship("UploadedImage", back_populates="disaster_report")


class UploadedImage(Base):
    """Uploaded Images Model tracking multimodal vision analysis payloads."""
    __tablename__ = "uploaded_images"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(String(255), ForeignKey("users.session_id", ondelete="CASCADE"))
    report_id = Column(Integer, ForeignKey("disaster_reports.id", ondelete="SET NULL"), nullable=True)
    request_id = Column(Integer, ForeignKey("emergency_requests.id", ondelete="SET NULL"), nullable=True)
    storage_path = Column(String(500), nullable=False)  # Local file system relative path or GCS URL
    analyzed_severity = Column(String(50), nullable=True) # MINOR, MODERATE, CRITICAL
    analysis_summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="uploaded_images")
    disaster_report = relationship("DisasterReport", back_populates="images")
    emergency_request = relationship("EmergencyRequest", back_populates="images")


class ConversationHistory(Base):
    """Conversation History Model logging chat dialogue messages in the session."""
    __tablename__ = "conversation_history"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    session_id = Column(String(255), ForeignKey("users.session_id", ondelete="CASCADE"), nullable=False)
    sender = Column(String(50), nullable=False)  # user, coordinator, sub_agent, system
    message = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="conversations")


class Alert(Base):
    """Alert Model defining geo-fenced weather and evacuation warnings."""
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    severity = Column(String(50), default="WATCH")  # ADVISORY, WATCH, WARNING
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    radius_km = Column(Float, default=10.0)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
