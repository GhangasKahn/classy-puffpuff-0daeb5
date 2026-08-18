from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Household(Base):
    __tablename__ = "households"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(80), default="House")
    weekly_cap: Mapped[float] = mapped_column(Float, default=110.0)
    freezer_share: Mapped[str] = mapped_column(String(40), default="none")
    freezer_lb: Mapped[float] = mapped_column(Float, default=0.0)
    share_cost: Mapped[float] = mapped_column(Float, default=0.0)
    share_weeks: Mapped[int] = mapped_column(Integer, default=12)
    bulk_weeks: Mapped[int] = mapped_column(Integer, default=4)

    people: Mapped[list["Person"]] = relationship(back_populates="household")


class Person(Base):
    __tablename__ = "people"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    household_id: Mapped[int] = mapped_column(ForeignKey("households.id"), index=True)
    legal_name: Mapped[str] = mapped_column(String(80), default="")
    alias: Mapped[str] = mapped_column(String(80), default="")
    weight_kg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    cancer_track: Mapped[bool] = mapped_column(Boolean, default=False)
    soft_food: Mapped[bool] = mapped_column(Boolean, default=False)
    protein_target_g: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    kcal_target: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    household: Mapped[Household] = relationship(back_populates="people")


class CatalogItem(Base):
    __tablename__ = "catalog_items"
    __table_args__ = (UniqueConstraint("household_id", "key", name="uq_catalog_key"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    household_id: Mapped[int] = mapped_column(ForeignKey("households.id"), index=True)
    key: Mapped[str] = mapped_column(String(80))
    name: Mapped[str] = mapped_column(String(120))
    default_store: Mapped[str] = mapped_column(String(40))
    unit: Mapped[str] = mapped_column(String(40))
    typical_price: Mapped[float] = mapped_column(Float)
    protein_g: Mapped[float] = mapped_column(Float, default=0.0)
    kcal: Mapped[float] = mapped_column(Float, default=0.0)
    staple: Mapped[bool] = mapped_column(Boolean, default=True)
    sale_ends: Mapped[Optional[date]] = mapped_column(Date, nullable=True)


class Ad(Base):
    __tablename__ = "ads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    household_id: Mapped[int] = mapped_column(ForeignKey("households.id"), index=True)
    catalog_key: Mapped[str] = mapped_column(String(80), index=True)
    store: Mapped[str] = mapped_column(String(40))
    price: Mapped[float] = mapped_column(Float)
    sale_ends: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    source: Mapped[str] = mapped_column(String(40), default="manual")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class AdFetch(Base):
    __tablename__ = "ad_fetches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    store: Mapped[str] = mapped_column(String(40))
    fetched_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    url: Mapped[str] = mapped_column(String(400))
    ok: Mapped[bool] = mapped_column(Boolean, default=False)
    text_excerpt: Mapped[str] = mapped_column(Text, default="")


class MealPlan(Base):
    __tablename__ = "meal_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    household_id: Mapped[int] = mapped_column(ForeignKey("households.id"), index=True)
    week_start: Mapped[date] = mapped_column(Date, index=True)
    notes: Mapped[str] = mapped_column(Text, default="")

    meals: Mapped[list["Meal"]] = relationship(back_populates="plan", cascade="all, delete-orphan")
    items: Mapped[list["ShoppingItem"]] = relationship(back_populates="plan", cascade="all, delete-orphan")


class Meal(Base):
    __tablename__ = "meals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    meal_plan_id: Mapped[int] = mapped_column(ForeignKey("meal_plans.id"), index=True)
    day_index: Mapped[int] = mapped_column(Integer)
    day_name: Mapped[str] = mapped_column(String(16))
    slot: Mapped[str] = mapped_column(String(16))
    title: Mapped[str] = mapped_column(String(200))
    cook_notes: Mapped[str] = mapped_column(Text, default="")
    protein_g_est: Mapped[float] = mapped_column(Float, default=0.0)
    kcal_est: Mapped[float] = mapped_column(Float, default=0.0)

    plan: Mapped[MealPlan] = relationship(back_populates="meals")


class ShoppingItem(Base):
    __tablename__ = "shopping_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    meal_plan_id: Mapped[int] = mapped_column(ForeignKey("meal_plans.id"), index=True)
    catalog_key: Mapped[str] = mapped_column(String(80), default="")
    name: Mapped[str] = mapped_column(String(120))
    qty: Mapped[float] = mapped_column(Float, default=1.0)
    unit: Mapped[str] = mapped_column(String(40), default="")
    store: Mapped[str] = mapped_column(String(40), default="aldi")
    unit_price: Mapped[float] = mapped_column(Float, default=0.0)
    checked: Mapped[bool] = mapped_column(Boolean, default=False)
    source: Mapped[str] = mapped_column(String(20), default="week")
    note: Mapped[str] = mapped_column(String(80), default="")

    plan: Mapped[MealPlan] = relationship(back_populates="items")


class QuietNeed(Base):
    __tablename__ = "quiet_needs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    household_id: Mapped[int] = mapped_column(ForeignKey("households.id"), index=True)
    week_start: Mapped[date] = mapped_column(Date, index=True)
    person_id: Mapped[int] = mapped_column(Integer)
    catalog_key: Mapped[str] = mapped_column(String(80))
    qty: Mapped[float] = mapped_column(Float, default=1.0)
    public_ack: Mapped[str] = mapped_column(String(200), default="")


class VaultMessage(Base):
    __tablename__ = "vault_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    household_id: Mapped[int] = mapped_column(ForeignKey("households.id"), index=True)
    room: Mapped[str] = mapped_column(String(16), index=True)
    person_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    ciphertext: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    agent_name: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)


class Recipe(Base):
    __tablename__ = "recipes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    household_id: Mapped[int] = mapped_column(ForeignKey("households.id"), index=True)
    title: Mapped[str] = mapped_column(String(160))
    body: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Receipt(Base):
    __tablename__ = "receipts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    household_id: Mapped[int] = mapped_column(ForeignKey("households.id"), index=True)
    store: Mapped[str] = mapped_column(String(40))
    amount: Mapped[float] = mapped_column(Float)
    purchased_at: Mapped[date] = mapped_column(Date)
    notes: Mapped[str] = mapped_column(String(200), default="")
