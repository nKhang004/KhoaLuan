from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.security import get_current_user, require_teacher
from app.models.models import MonHoc, ChuDe
from app.schemas.schemas import MonHocCreate, MonHocResponse, ChuDeCreate, ChuDeResponse

router = APIRouter(tags=["Môn học & Chủ đề"])


# ─── Môn học ──────────────────────────────────────────────────────────────────

@router.get("/subjects", response_model=List[MonHocResponse], summary="Lấy danh sách môn học")
def lay_danh_sach_mon_hoc(db: Session = Depends(get_db), _=Depends(get_current_user)):
    return db.query(MonHoc).filter(MonHoc.an_hien == True).all()


@router.post("/subjects", response_model=MonHocResponse, status_code=201, summary="Tạo môn học mới")
def tao_mon_hoc(payload: MonHocCreate, db: Session = Depends(get_db), _=Depends(require_teacher)):
    ton_tai = db.query(MonHoc).filter(MonHoc.ma_mon == payload.ma_mon).first()
    if ton_tai:
        raise HTTPException(status_code=400, detail=f"Mã môn '{payload.ma_mon}' đã tồn tại")
    mon = MonHoc(**payload.model_dump())
    db.add(mon)
    db.commit()
    db.refresh(mon)
    return mon


@router.get("/subjects/{subject_id}", response_model=MonHocResponse, summary="Xem chi tiết môn học")
def xem_mon_hoc(subject_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    mon = db.query(MonHoc).filter(MonHoc.id == subject_id).first()
    if not mon:
        raise HTTPException(status_code=404, detail="Không tìm thấy môn học")
    return mon


@router.put("/subjects/{subject_id}", response_model=MonHocResponse, summary="Cập nhật môn học")
def cap_nhat_mon_hoc(subject_id: int, payload: MonHocCreate, db: Session = Depends(get_db), _=Depends(require_teacher)):
    mon = db.query(MonHoc).filter(MonHoc.id == subject_id).first()
    if not mon:
        raise HTTPException(status_code=404, detail="Không tìm thấy môn học")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(mon, field, value)
    db.commit()
    db.refresh(mon)
    return mon


@router.delete("/subjects/{subject_id}", status_code=204, summary="Ẩn môn học")
def an_mon_hoc(subject_id: int, db: Session = Depends(get_db), _=Depends(require_teacher)):
    mon = db.query(MonHoc).filter(MonHoc.id == subject_id).first()
    if not mon:
        raise HTTPException(status_code=404, detail="Không tìm thấy môn học")
    mon.an_hien = False
    db.commit()


# ─── Chủ đề ───────────────────────────────────────────────────────────────────

@router.get("/topics", response_model=List[ChuDeResponse], summary="Lấy danh sách chủ đề")
def lay_danh_sach_chu_de(mon_hoc_id: int = None, db: Session = Depends(get_db), _=Depends(get_current_user)):
    query = db.query(ChuDe).filter(ChuDe.an_hien == True)
    if mon_hoc_id:
        query = query.filter(ChuDe.mon_hoc_id == mon_hoc_id)
    return query.all()


@router.post("/topics", response_model=ChuDeResponse, status_code=201, summary="Tạo chủ đề mới")
def tao_chu_de(payload: ChuDeCreate, db: Session = Depends(get_db), _=Depends(require_teacher)):
    mon = db.query(MonHoc).filter(MonHoc.id == payload.mon_hoc_id).first()
    if not mon:
        raise HTTPException(status_code=404, detail="Môn học không tồn tại")
    chu_de = ChuDe(**payload.model_dump())
    db.add(chu_de)
    db.commit()
    db.refresh(chu_de)
    return chu_de


@router.put("/topics/{topic_id}", response_model=ChuDeResponse, summary="Cập nhật chủ đề")
def cap_nhat_chu_de(topic_id: int, payload: ChuDeCreate, db: Session = Depends(get_db), _=Depends(require_teacher)):
    chu_de = db.query(ChuDe).filter(ChuDe.id == topic_id).first()
    if not chu_de:
        raise HTTPException(status_code=404, detail="Không tìm thấy chủ đề")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(chu_de, field, value)
    db.commit()
    db.refresh(chu_de)
    return chu_de


@router.delete("/topics/{topic_id}", status_code=204, summary="Ẩn chủ đề")
def an_chu_de(topic_id: int, db: Session = Depends(get_db), _=Depends(require_teacher)):
    chu_de = db.query(ChuDe).filter(ChuDe.id == topic_id).first()
    if not chu_de:
        raise HTTPException(status_code=404, detail="Không tìm thấy chủ đề")
    chu_de.an_hien = False
    db.commit()