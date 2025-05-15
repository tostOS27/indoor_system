from sqlalchemy import Column, Integer, String
from db_config import ORMBaseModel
from pydantic import BaseModel
from typing import Optional

# TODO Wzorując się na poniższych przykładach, zdefiniuj odpowienie modele w swojej aplikacji.

class Room(ORMBaseModel):
    __tablename__ = 'Room'
    id = Column(Integer, primary_key=True, index=True)
    room_number = Column(String, nullable=False)
    room_category_id = Column(Integer, nullable=False)
    floor_id = Column(Integer, index=True, nullable=False)

class RoomCreate(BaseModel):
    room_number: str
    room_category_id: int
    floor_id: int

class RoomUpdate(BaseModel):
    room_number: Optional[str] = None
    room_category_id: Optional[int] = None
    floor_id: Optional[int] = None
