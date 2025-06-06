from fastapi import FastAPI, APIRouter, HTTPException, Depends, Body, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from fastapi.encoders import jsonable_encoder
from models import Room, RoomCreate, RoomUpdate, PositionUpdate
from db_config import ORMBaseModel, db_engine, get_db_session
from encoders import to_dict
from fastapi.responses import PlainTextResponse
import os
import json

DATABASE_URL = os.getenv("DATABASE_URL")

ORMBaseModel.metadata.create_all(bind=db_engine)
app = FastAPI()
router = APIRouter()

active_connections: list[WebSocket] = []

@app.get("/", response_class=PlainTextResponse)
def test():
    return (
        "Room database\n"
        "operations:\n"
        "   post/rooms\n"
        "   get/rooms\n"
        "   get/rooms/room_id\n"
        "   delete/rooms/room_id\n"
        "   put/room/room_id\n"
        "\n Jan Knyspel"
    )

@app.post("/rooms")
def create_room(room_create: RoomCreate, db_session: Session = Depends(get_db_session)):
    new_room = Room(
        room_number=room_create.room_number,
        room_category_id=room_create.room_category_id,
        floor_id=room_create.floor_id,
        latitude=room_create.latitude,         # Added
        longitude=room_create.longitude        # Added
    )

    db_session.add(new_room)
    db_session.commit()
    db_session.refresh(new_room)

    return jsonable_encoder({
        "id": new_room.id,
        "room_number": new_room.room_number,
        "room_category_id": new_room.room_category_id,
        "floor_id": new_room.floor_id,
        "latitude": new_room.latitude,         # Added
        "longitude": new_room.longitude        # Added
    })

@app.get("/rooms")
def get_all_rooms(db_session: Session = Depends(get_db_session)):
    rooms = db_session.query(Room).all()
    result = []
    for room in rooms:
        room_dict = to_dict(room)
        result.append(room_dict)
    return jsonable_encoder(result)

@app.get("/rooms/{room_id}")
def get_room(room_id: int, db_session: Session = Depends(get_db_session)):
    room = db_session.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    return jsonable_encoder(to_dict(room))

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
    if room_update.latitude is not None:           # Added
        room.latitude = room_update.latitude
    if room_update.longitude is not None:          # Added
        room.longitude = room_update.longitude

    db_session.commit()
    db_session.refresh(room)

    return jsonable_encoder({
        "id": room.id,
        "room_number": room.room_number,
        "room_category_id": room.room_category_id,
        "floor_id": room.floor_id,
        "latitude": room.latitude,                 # Added
        "longitude": room.longitude                # Added
    })

@app.put("/rooms/{room_id}/position")
async def update_position(
    room_id: int, 
    position: PositionUpdate = Body(...), 
    db_session: Session = Depends(get_db_session)
):
    room = db_session.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    room.latitude = position.latitude
    room.longitude = position.longitude
    db_session.commit()
    db_session.refresh(room)

    message = json.dumps({
        "id": room.id,
        "lat": room.latitude,
        "lon": room.longitude,
        "room_number": room.room_number,
        "room_category_id": room.room_category_id,
        "floor_id": room.floor_id
    })

    for connection in active_connections:
        await connection.send_text(message)

    return {"status": "position updated"}

@app.websocket("/ws/positions")
async def positions(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    try:
        while True:
            await websocket.receive_text()  # Utrzymanie połączenia
    except WebSocketDisconnect:
        active_connections.remove(websocket)

app.include_router(router)
