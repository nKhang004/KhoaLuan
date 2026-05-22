import random
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import List
from app.core.database import get_db
from app.core.security import get_current_user, require_teacher
from app.models.models import DeThi, CauHoiDeThi, CauHoi, LanThi
from app.schemas.schemas import DeThiCreate, DeThiAutoCreate, DeThiResponse

router = APIRouter(prefix="/exams", tags=["Đề thi"])


@router.get("", response_model=List[DeThiResponse], summary="Lấy danh sách đề thi")
def lay_danh_sach_de_thi(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    query = db.query(DeThi)
    if current_user.vai_tro == "hoc_sinh":
        query = query.filter(DeThi.cong_bo == True)
    return query.all()


@router.post("", response_model=DeThiResponse, status_code=201, summary="Tạo đề thi thủ công")
def tao_de_thi(payload: DeThiCreate, db: Session = Depends(get_db), current_user=Depends(require_teacher)):
    de_thi = DeThi(
        tieu_de=payload.tieu_de,
        mo_ta=payload.mo_ta,
        thoi_gian_lam_bai=payload.thoi_gian_lam_bai,
        diem_dat=payload.diem_dat,
        nguoi_tao_id=current_user.id,
    )
    db.add(de_thi)
    db.flush()

    for item in payload.danh_sach_cau_hoi:
        cau_hoi = db.query(CauHoi).filter(CauHoi.id == item.cau_hoi_id, CauHoi.an_hien == True).first()
        if not cau_hoi:
            raise HTTPException(status_code=404, detail=f"Câu hỏi ID={item.cau_hoi_id} không tồn tại")
        lien_ket = CauHoiDeThi(
            de_thi_id=de_thi.id,
            cau_hoi_id=item.cau_hoi_id,
            thu_tu=item.thu_tu,
            diem_so=item.diem_so,
        )
        db.add(lien_ket)

    db.commit()
    db.refresh(de_thi)
    return de_thi


@router.post("/auto-generate", response_model=DeThiResponse, status_code=201, summary="Tự động sinh đề thi")
def tu_dong_sinh_de_thi(payload: DeThiAutoCreate, db: Session = Depends(get_db), current_user=Depends(require_teacher)):
    query = db.query(CauHoi).filter(CauHoi.chu_de_id == payload.chu_de_id, CauHoi.an_hien == True)
    if payload.do_kho:
        query = query.filter(CauHoi.do_kho == payload.do_kho)

    tat_ca_cau_hoi = query.all()
    if len(tat_ca_cau_hoi) < payload.so_luong_cau_hoi:
        raise HTTPException(
            status_code=400,
            detail=f"Ngân hàng chỉ có {len(tat_ca_cau_hoi)} câu hỏi, không đủ để tạo đề {payload.so_luong_cau_hoi} câu"
        )

    cau_hoi_chon = random.sample(tat_ca_cau_hoi, payload.so_luong_cau_hoi)

    de_thi = DeThi(
        tieu_de=payload.tieu_de,
        mo_ta=payload.mo_ta,
        thoi_gian_lam_bai=payload.thoi_gian_lam_bai,
        diem_dat=payload.diem_dat,
        nguoi_tao_id=current_user.id,
    )
    db.add(de_thi)
    db.flush()

    for idx, cau_hoi in enumerate(cau_hoi_chon, start=1):
        lien_ket = CauHoiDeThi(
            de_thi_id=de_thi.id,
            cau_hoi_id=cau_hoi.id,
            thu_tu=idx,
            diem_so=payload.diem_moi_cau,
        )
        db.add(lien_ket)

    db.commit()
    db.refresh(de_thi)
    return de_thi


@router.get("/{exam_id}", response_model=DeThiResponse, summary="Xem chi tiết đề thi")
def xem_de_thi(exam_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    de_thi = db.query(DeThi).filter(DeThi.id == exam_id).first()
    if not de_thi:
        raise HTTPException(status_code=404, detail="Không tìm thấy đề thi")
    if current_user.vai_tro == "hoc_sinh" and not de_thi.cong_bo:
        raise HTTPException(status_code=403, detail="Đề thi chưa được công bố")
    return de_thi


@router.post("/{exam_id}/publish", response_model=DeThiResponse, summary="Công bố / Gỡ công bố đề thi")
def cong_bo_de_thi(exam_id: int, db: Session = Depends(get_db), current_user=Depends(require_teacher)):
    de_thi = db.query(DeThi).filter(DeThi.id == exam_id).first()
    if not de_thi:
        raise HTTPException(status_code=404, detail="Không tìm thấy đề thi")
    if de_thi.nguoi_tao_id != current_user.id and current_user.vai_tro != "admin":
        raise HTTPException(status_code=403, detail="Bạn không có quyền công bố đề thi này")
    de_thi.cong_bo = not de_thi.cong_bo
    db.commit()
    db.refresh(de_thi)
    return de_thi


@router.delete("/{exam_id}", status_code=204, summary="Xóa đề thi")
def xoa_de_thi(exam_id: int, db: Session = Depends(get_db), current_user=Depends(require_teacher)):
    de_thi = db.query(DeThi).filter(DeThi.id == exam_id).first()
    if not de_thi:
        raise HTTPException(status_code=404, detail="Không tìm thấy đề thi")
    if de_thi.nguoi_tao_id != current_user.id and current_user.vai_tro != "admin":
        raise HTTPException(status_code=403, detail="Không có quyền xóa đề thi này")
    
    # Xóa các lần thi liên quan (foreign key constraint)
    db.query(LanThi).filter(LanThi.de_thi_id == exam_id).delete()
    # Xóa các câu hỏi trong đề thi
    db.query(CauHoiDeThi).filter(CauHoiDeThi.de_thi_id == exam_id).delete()
    # Xóa đề thi
    db.delete(de_thi)
    db.commit()