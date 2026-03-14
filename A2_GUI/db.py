# db.py

from sqlalchemy import (
    create_engine, Column, Integer, String,
    DateTime, Float, ForeignKey, func
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from config import DB_URL

# -----------------------------------------------------------------------------
# Engine & Session setup
# -----------------------------------------------------------------------------
# Connects to your Neon Postgres via DB_URL from config.py
engine = create_engine(DB_URL, echo=False, future=True)
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    future=True
)

# Base class for ORM models
Base = declarative_base()


# -----------------------------------------------------------------------------
# ORM Models
# -----------------------------------------------------------------------------

class User(Base):
    """
    Represents a farmer in the system.
    """
    __tablename__ = "users"

    id            = Column(Integer, primary_key=True, index=True)
    username      = Column(String, unique=True, nullable=False, index=True)
    email         = Column(String, unique=True, nullable=False, index=True)
    region        = Column(String, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at    = Column(DateTime(timezone=True), server_default=func.now())

    # One-to-many: a user can have multiple predictions
    predictions = relationship(
        "Prediction",
        back_populates="user",
        cascade="all, delete-orphan"
    )


class Prediction(Base):
    """
    Stores the results of running the three CNNs on an uploaded image.
    """
    __tablename__ = "predictions"

    id             = Column(Integer, primary_key=True, index=True)
    user_id        = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    image_path     = Column(String, nullable=False)
    predicted_age  = Column(Float, nullable=False)
    predicted_var  = Column(String, nullable=False)
    disease_label  = Column(String, nullable=False)
    timestamp      = Column(DateTime(timezone=True), server_default=func.now())

    # Back-ref to the owning user
    user = relationship("User", back_populates="predictions")

    # One-to-many: a prediction can generate multiple chat logs
    chats = relationship(
        "ChatLog",
        back_populates="prediction",
        cascade="all, delete-orphan"
    )


class ChatLog(Base):
    """
    Records each question/response turn for a given prediction.
    """
    __tablename__ = "chat_logs"

    id             = Column(Integer, primary_key=True, index=True)
    prediction_id  = Column(Integer, ForeignKey("predictions.id"), nullable=False, index=True)
    user_question  = Column(String, nullable=False)
    ai_response    = Column(String, nullable=False)
    timestamp      = Column(DateTime(timezone=True), server_default=func.now())

    # Back-ref to the parent prediction
    prediction = relationship("Prediction", back_populates="chats")


# -----------------------------------------------------------------------------
# Create tables in the database (if they don't exist)
# -----------------------------------------------------------------------------
def init_db():
    """
    Call this once at startup to ensure all tables are created.
    """
    Base.metadata.create_all(bind=engine)


# If you want to auto-initialize on import, uncomment:
# init_db()