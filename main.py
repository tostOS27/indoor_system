from fastapi import FastAPI, HTTPException, Depends, Body
from sqlalchemy.orm import Session
from fastapi.encoders import jsonable_encoder
from models import Room, RoomCreate, RoomUpdate
from db_config import ORMBaseModel, db_engine, get_db_session
from encoders import to_dict
import os

DATABASE_URL = os.getenv("DATABASE_URL")

ORMBaseModel.metadata.create_all(bind=db_engine)
app = FastAPI()

@app.get("/")
def test():
    return {"message": "Hello world!"}

@app.post("/rooms")
def create_room(room_create: RoomCreate, db_session: Session = Depends(get_db_session)):
    new_room = Room(
        room_number=room_create.room_number,
        room_category_id=room_create.room_category_id,
        floor_id=room_create.floor_id
    )

    db_session.add(new_room)
    db_session.commit()
    db_session.refresh(new_room)

    return jsonable_encoder({
        "id": new_room.room_id,
        "room_number": new_room.room_number,
        "room_category_id": new_room.room_category_id,
        "floor_id": new_room.floor_id,
    })

@app.get("/rooms")
def get_all_rooms(db_session: Session = Depends(get_db_session)):
    rooms = db_session.query(Room).all()
    result = []
    for room in rooms:
        room_dict = to_dict(room)
        result.append(room_dict)
    return jsonable_encoder(result)

@app.delete("/rooms/{room_id}")
def delete_room(room_id: int, db_session: Session = Depends(get_db_session)):
    room = db_session.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    db_session.delete(room)
    db_session.commit()
    return {"message": "Room deleted successfully"}

@app.put("/rooms/{room_id}")
def update_room(
    room_id: int,
    room_update: RoomUpdate = Body(...),
    db_session: Session = Depends(get_db_session)
):
    room = db_session.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    if room_update.room_number is not None:
        room.room_number = room_update.room_number
    if room_update.room_category_id is not None:
        room.room_category_id = room_update.room_category_id
    if room_update.floor_id is not None:
        room.floor_id = room_update.floor_id

    db_session.commit()
    db_session.refresh(room)

    return jsonable_encoder({
        "id": room.id,
        "room_number": room.room_number,
        "room_category_id": room.room_category_id,
        "floor_id": room.floor_id,
    })