from sqlalchemy import (
    Column, Integer, BigInteger, String, Boolean,
    Float, ForeignKey, DateTime, Text, Enum
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from db.base import Base

class NosologyEnum(str, enum.Enum):
    wheelchair = "wheelchair"
    blind = "blind"
    deaf = "deaf"

class CategoryEnum(str, enum.Enum):
    cafe = "cafe"
    pharmacy = "pharmacy"
    bank = "bank"
    clinic = "clinic"
    supermarket = "supermarket"
    mall = "mall"
    transport = "transport"
    government = "government"
    sport = "sport"
    hotel = "hotel"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)
    username = Column(String(100), nullable=True)
    nosology = Column(Enum(NosologyEnum), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<User tg_id={self.telegram_id} nosology={self.nosology}>"

class Chain(Base):
    __tablename__ = "chains"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    category = Column(Enum(CategoryEnum), nullable=False)
    description = Column(Text, nullable=True)

    places = relationship("Place", back_populates="chain")

    def __repr__(self):
        return f"<Chain {self.name}>"

class Place(Base):
    __tablename__ = "places"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    address = Column(String(300), nullable=False)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    phone = Column(String(50), nullable=True)
    website = Column(String(200), nullable=True)
    category = Column(Enum(CategoryEnum), nullable=False)

    chain_id = Column(Integer, ForeignKey("chains.id"), nullable=True)
    chain = relationship("Chain", back_populates="places")

    accessibility = relationship("Accessibility", back_populates="place", uselist=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<Place {self.name} @ {self.address}>"

class Accessibility(Base):
    __tablename__ = "accessibility"

    id = Column(Integer, primary_key=True, index=True)
    place_id = Column(Integer, ForeignKey("places.id"), unique=True, nullable=False)
    place = relationship("Place", back_populates="accessibility")

    wheelchair = Column(Boolean, default=False)
    accessible_entrance = Column(Boolean, default=False)
    accessible_toilet = Column(Boolean, default=False)
    elevator = Column(Boolean, default=False)

    blind = Column(Boolean, default=False)
    braille_signs = Column(Boolean, default=False)
    audio_guide = Column(Boolean, default=False)

    deaf = Column(Boolean, default=False)
    induction_loop = Column(Boolean, default=False)
    visual_alerts = Column(Boolean, default=False)

    notes = Column(Text, nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return (
            f"<Accessibility place_id={self.place_id} "
            f"wheelchair={self.wheelchair} blind={self.blind} deaf={self.deaf}>"
        )