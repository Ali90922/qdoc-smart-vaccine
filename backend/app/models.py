from sqlalchemy import Column, Integer, String, Boolean, Date, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime


class User(Base):
    __tablename__ = "users"

    id            = Column(Integer, primary_key=True, index=True)
    email         = Column(String(150), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at    = Column(DateTime, default=datetime.utcnow)

    patient = relationship("Patient", back_populates="user", uselist=False)


class Patient(Base):
    __tablename__ = "patients"

    id                   = Column(Integer, primary_key=True, index=True)
    user_id              = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    name                 = Column(String(100), nullable=False)
    dob                  = Column(Date, nullable=False)
    gender               = Column(String(20))
    birth_year           = Column(Integer)

    # Risk factors
    is_pregnant          = Column(Boolean, default=False)
    is_immunocompromised = Column(Boolean, default=False)
    has_diabetes         = Column(Boolean, default=False)
    has_chronic_lung     = Column(Boolean, default=False)
    has_heart_disease    = Column(Boolean, default=False)
    has_chronic_kidney   = Column(Boolean, default=False)
    has_chronic_liver    = Column(Boolean, default=False)
    has_asplenia         = Column(Boolean, default=False)
    has_hiv              = Column(Boolean, default=False)

    user    = relationship("User", back_populates="patient")
    records = relationship("VaccinationRecord", back_populates="patient", cascade="all, delete-orphan")
    reminders = relationship("Reminder", back_populates="patient", cascade="all, delete-orphan")


class Vaccine(Base):
    __tablename__ = "vaccines"

    id                   = Column(Integer, primary_key=True, index=True)
    vaccine_key          = Column(String(50), unique=True, nullable=False)
    name                 = Column(String(150), nullable=False)
    description          = Column(Text)
    min_age_months       = Column(Integer)
    max_age_months       = Column(Integer)
    doses_required       = Column(Integer, nullable=False)
    dose_interval_days   = Column(Integer)
    repeat_interval_days = Column(Integer)

    records   = relationship("VaccinationRecord", back_populates="vaccine")
    reminders = relationship("Reminder", back_populates="vaccine")


class VaccinationRecord(Base):
    __tablename__ = "vaccination_records"

    id          = Column(Integer, primary_key=True, index=True)
    patient_id  = Column(Integer, ForeignKey("patients.id"), nullable=False)
    vaccine_id  = Column(Integer, ForeignKey("vaccines.id"), nullable=False)
    dose_number = Column(Integer, nullable=False)
    date_given  = Column(Date, nullable=False)
    notes       = Column(Text)

    patient = relationship("Patient", back_populates="records")
    vaccine = relationship("Vaccine", back_populates="records")


class Reminder(Base):
    __tablename__ = "reminders"

    id            = Column(Integer, primary_key=True, index=True)
    patient_id    = Column(Integer, ForeignKey("patients.id"), nullable=False)
    vaccine_id    = Column(Integer, ForeignKey("vaccines.id"), nullable=False)
    reminder_type = Column(String(20))   # 'email' | 'sms' | 'in_app'
    sent_at       = Column(DateTime, default=datetime.utcnow)

    patient = relationship("Patient", back_populates="reminders")
    vaccine = relationship("Vaccine", back_populates="reminders")
