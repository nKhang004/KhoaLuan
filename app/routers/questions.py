from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from app.core.database import get_db
from app.core.security import get_current_user, require_teacher
from app.models.models import CauHoi, LuaChon, ChuDe
from app.schemas.schemas import CauHoiCreate, CauHoiUpdate, CauHoiResponse

router = APIRouter(prefix="/questions", tags=["Ngân hàng câu hỏi"])


@router.get("", response_model=List[CauHoiResponse], summary="Tìm kiếm và lọc câu hỏi")
def lay_danh_sach_cau_hoi(
    mon_hoc_id: Optional[int] = Query(None, description="Lọc theo môn học"),
    chu_de_id: Optional[int] = Query(None, description="Lọc theo chủ đề"),
    do_kho: Optional[str] = Query(None, description="Lọc độ khó: de | trung_binh | kho"),
    loai_cau_hoi: Optional[str] = Query(None, description="Loại câu hỏi"),
    tu_khoa: Optional[str] = Query(None, description="Từ khóa tìm kiếm trong nội dung"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _=Depends(get_current_user)
):
    query = (
        db.query(CauHoi)
        .options(joinedload(CauHoi.lua_chon))
        .filter(CauHoi.an_hien == True)
    )
    if chu_de_id:
        query = query.filter(CauHoi.chu_de_id == chu_de_id)
    if do_kho:
        query = query.filter(CauHoi.do_kho == do_kho)
    if loai_cau_hoi:
        query = query.filter(CauHoi.loai_cau_hoi == loai_cau_hoi)
    if tu_khoa:
        query = query.filter(CauHoi.noi_dung.ilike(f"%{tu_khoa}%"))
    if mon_hoc_id:
        query = query.join(ChuDe).filter(ChuDe.mon_hoc_id == mon_hoc_id)

    return query.offset(skip).limit(limit).all()


@router.post("", response_model=CauHoiResponse, status_code=201, summary="Tạo câu hỏi mới kèm lựa chọn")
def tao_cau_hoi(payload: CauHoiCreate, db: Session = Depends(get_db), current_user=Depends(require_teacher)):
    chu_de = db.query(ChuDe).filter(ChuDe.id == payload.chu_de_id).first()
    if not chu_de:
        raise HTTPException(status_code=404, detail="Chủ đề không tồn tại")

    # Kiểm tra phải có ít nhất một đáp án đúng
    so_dap_an_dung = sum(1 for lc in payload.lua_chon if lc.la_dap_an)
    if so_dap_an_dung == 0:
        raise HTTPException(status_code=400, detail="Câu hỏi phải có ít nhất một đáp án đúng")

    cau_hoi = CauHoi(
        noi_dung=payload.noi_dung,
        loai_cau_hoi=payload.loai_cau_hoi,
        do_kho=payload.do_kho,
        chu_de_id=payload.chu_de_id,
        nguoi_tao_id=current_user.id,
        giai_thich=payload.giai_thich,
    )
    db.add(cau_hoi)
    db.flush()

    for lc_data in payload.lua_chon:
        lua_chon = LuaChon(cau_hoi_id=cau_hoi.id, **lc_data.model_dump())
        db.add(lua_chon)

    db.commit()
    db.refresh(cau_hoi)
    return cau_hoi


@router.get("/{question_id}", response_model=CauHoiResponse, summary="Xem chi tiết câu hỏi")
def xem_cau_hoi(question_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    cau_hoi = (
        db.query(CauHoi)
        .options(joinedload(CauHoi.lua_chon))
        .filter(CauHoi.id == question_id, CauHoi.an_hien == True)
        .first()
    )
    if not cau_hoi:
        raise HTTPException(status_code=404, detail="Không tìm thấy câu hỏi")
    return cau_hoi


@router.put("/{question_id}", response_model=CauHoiResponse, summary="Cập nhật nội dung câu hỏi")
def cap_nhat_cau_hoi(question_id: int, payload: CauHoiUpdate, db: Session = Depends(get_db), current_user=Depends(require_teacher)):
    cau_hoi = db.query(CauHoi).filter(CauHoi.id == question_id).first()
    if not cau_hoi:
        raise HTTPException(status_code=404, detail="Không tìm thấy câu hỏi")
    if cau_hoi.nguoi_tao_id != current_user.id and current_user.vai_tro != "admin":
        raise HTTPException(status_code=403, detail="Bạn không có quyền chỉnh sửa câu hỏi này")
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(cau_hoi, field, value)
    db.commit()
    db.refresh(cau_hoi)
    return cau_hoi


@router.delete("/{question_id}", status_code=204, summary="Xóa (ẩn) câu hỏi")
def xoa_cau_hoi(question_id: int, db: Session = Depends(get_db), current_user=Depends(require_teacher)):
    cau_hoi = db.query(CauHoi).filter(CauHoi.id == question_id).first()
    if not cau_hoi:
        raise HTTPException(status_code=404, detail="Không tìm thấy câu hỏi")
    if cau_hoi.nguoi_tao_id != current_user.id and current_user.vai_tro != "admin":
        raise HTTPException(status_code=403, detail="Bạn không có quyền xóa câu hỏi này")
    cau_hoi.an_hien = False
    db.commit()