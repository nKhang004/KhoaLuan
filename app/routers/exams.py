import random
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from app.core.database import get_db
from app.core.security import get_current_user, require_teacher
from app.models.models import DeThi, CauHoiDeThi, CauHoi, LuaChon, LanThi
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
    # Lấy danh sách câu hỏi theo chủ đề và độ khó
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


@router.get("/{exam_id}/details", summary="Lấy chi tiết đề thi kèm danh sách câu hỏi và đáp án")
def chi_tiet_de_thi(exam_id: int, db: Session = Depends(get_db), current_user=Depends(require_teacher)):
    de_thi = db.query(DeThi).filter(DeThi.id == exam_id).first()
    if not de_thi:
        raise HTTPException(status_code=404, detail="Không tìm thấy đề thi")
    
    cau_hoi_list = (
        db.query(CauHoiDeThi)
        .filter(CauHoiDeThi.de_thi_id == exam_id)
        .order_by(CauHoiDeThi.thu_tu)
        .all()
    )
    result = {
        "id": de_thi.id,
        "tieu_de": de_thi.tieu_de,
        "mo_ta": de_thi.mo_ta,
        "thoi_gian_lam_bai": de_thi.thoi_gian_lam_bai,
        "diem_dat": de_thi.diem_dat,
        "cong_bo": de_thi.cong_bo,
        "cau_hoi": []
    }
    for item in cau_hoi_list:
        cau_hoi = db.query(CauHoi).options(joinedload(CauHoi.lua_chon)).filter(CauHoi.id == item.cau_hoi_id).first()
        if cau_hoi:
            result["cau_hoi"].append({
                "id": cau_hoi.id,
                "noi_dung": cau_hoi.noi_dung,
                "loai_cau_hoi": cau_hoi.loai_cau_hoi,
                "do_kho": cau_hoi.do_kho,
                "thu_tu": item.thu_tu,
                "diem_so": item.diem_so,
                "lua_chon": [{"id": lc.id, "noi_dung": lc.noi_dung, "la_dap_an": lc.la_dap_an} for lc in cau_hoi.lua_chon]
            })
    return result


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
    # Xóa các lần thi liên quan
    db.query(LanThi).filter(LanThi.de_thi_id == exam_id).delete()
    db.query(CauHoiDeThi).filter(CauHoiDeThi.de_thi_id == exam_id).delete()
    db.delete(de_thi)
    db.commit()