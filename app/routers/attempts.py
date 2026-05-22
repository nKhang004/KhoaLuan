import random
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from datetime import datetime, timezone
from typing import List
from pydantic import BaseModel
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.models import LanThi, TraLoi, DeThi, CauHoiDeThi, LuaChon, CauHoi, GiamSatThi
from app.schemas.schemas import LanThiResponse, NopBaiRequest

router = APIRouter(tags=["Làm bài & Chấm điểm"])

GIOI_HAN_THOAT_TAB  = 3    # Số lần thoát tab → nộp tự động
THOI_GIAN_TOI_THIEU = 0.5  # Phải làm ít nhất 50% thời gian (phút)


class GiamSatRequest(BaseModel):
    loai_su_kien: str
    mo_ta: str = None


# ── Bắt đầu làm bài ───────────────────────────────────────────────────────────
@router.post("/exams/{exam_id}/start", response_model=LanThiResponse, status_code=201,
             summary="Bắt đầu làm bài thi")
def bat_dau_lam_bai(exam_id: int, db: Session = Depends(get_db),
                    current_user=Depends(get_current_user)):
    de_thi = db.query(DeThi).filter(DeThi.id == exam_id, DeThi.cong_bo == True).first()
    if not de_thi:
        raise HTTPException(status_code=404, detail="Đề thi không tồn tại hoặc chưa được công bố")
    lan_thi = LanThi(hoc_sinh_id=current_user.id, de_thi_id=exam_id,
                     so_lan_thoat_tab=0, bi_nop_tu_dong=False)
    db.add(lan_thi)
    db.commit()
    db.refresh(lan_thi)
    return lan_thi


# ── Lấy câu hỏi đã xáo trộn ──────────────────────────────────────────────────
@router.get("/exams/{exam_id}/questions", summary="Lấy câu hỏi đề thi (đã xáo trộn)")
def lay_cau_hoi_de_thi(exam_id: int, db: Session = Depends(get_db),
                       current_user=Depends(get_current_user)):
    de_thi = db.query(DeThi).filter(DeThi.id == exam_id, DeThi.cong_bo == True).first()
    if not de_thi:
        raise HTTPException(status_code=404, detail="Đề thi không tồn tại hoặc chưa công bố")

    items = db.query(CauHoiDeThi).filter(CauHoiDeThi.de_thi_id == exam_id).order_by(CauHoiDeThi.thu_tu).all()
    ket_qua = []
    for item in items:
        cq = db.query(CauHoi).options(joinedload(CauHoi.lua_chon)).filter(CauHoi.id == item.cau_hoi_id).first()
        if not cq:
            continue
        lua_chon = list(cq.lua_chon)
        random.shuffle(lua_chon)
        ket_qua.append({
            "cau_hoi_id": cq.id,
            "noi_dung": cq.noi_dung,
            "loai_cau_hoi": cq.loai_cau_hoi,
            "do_kho": cq.do_kho,
            "thu_tu": item.thu_tu,
            "diem_so": item.diem_so,
            "lua_chon": [{"id": lc.id, "noi_dung": lc.noi_dung} for lc in lua_chon],
        })
    random.shuffle(ket_qua)
    return {
        "de_thi_id": exam_id,
        "tieu_de": de_thi.tieu_de,
        "thoi_gian_lam_bai": de_thi.thoi_gian_lam_bai,
        "tong_so_cau": len(ket_qua),
        "danh_sach_cau_hoi": ket_qua,
    }


# ── Ghi nhận sự kiện giám sát ─────────────────────────────────────────────────
@router.post("/attempts/{attempt_id}/monitor", summary="Ghi nhận sự kiện thoát tab")
def ghi_su_kien(attempt_id: int, payload: GiamSatRequest,
                db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    lan_thi = db.query(LanThi).filter(
        LanThi.id == attempt_id, LanThi.hoc_sinh_id == current_user.id
    ).first()
    if not lan_thi or lan_thi.nop_bai_luc:
        raise HTTPException(status_code=404, detail="Không tìm thấy lần thi")

    db.add(GiamSatThi(
        lan_thi_id=lan_thi.id,
        loai_su_kien=payload.loai_su_kien,
        mo_ta=payload.mo_ta,
    ))

    nop_tu_dong = False
    if payload.loai_su_kien == "thoat_tab":
        lan_thi.so_lan_thoat_tab += 1
        if lan_thi.so_lan_thoat_tab >= GIOI_HAN_THOAT_TAB:
            nop_tu_dong = True

    db.commit()

    if nop_tu_dong:
        return {"canh_bao": True, "nop_tu_dong": True,
                "thong_bao": f"Bạn đã thoát tab {GIOI_HAN_THOAT_TAB} lần. Bài thi sẽ bị nộp tự động!"}

    con_lai = max(0, GIOI_HAN_THOAT_TAB - lan_thi.so_lan_thoat_tab)
    return {"canh_bao": lan_thi.so_lan_thoat_tab > 0, "nop_tu_dong": False,
            "thong_bao": f"Cảnh báo! Bạn còn {con_lai} lần trước khi bị nộp bài tự động.",
            "so_lan_thoat_tab": lan_thi.so_lan_thoat_tab}


# ── Nộp bài ───────────────────────────────────────────────────────────────────
@router.post("/attempts/{attempt_id}/submit", response_model=LanThiResponse,
             summary="Nộp bài và chấm điểm tự động")
def nop_bai(attempt_id: int, payload: NopBaiRequest,
            db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    lan_thi = db.query(LanThi).filter(
        LanThi.id == attempt_id, LanThi.hoc_sinh_id == current_user.id
    ).first()
    if not lan_thi:
        raise HTTPException(status_code=404, detail="Không tìm thấy lần thi")
    if lan_thi.nop_bai_luc:
        raise HTTPException(status_code=400, detail="Bạn đã nộp bài trước đó rồi")

    de_thi = db.query(DeThi).filter(DeThi.id == lan_thi.de_thi_id).first()

    # Kiểm tra thời gian tối thiểu (50% thời gian cho phép)
    thoi_gian_da_lam = (
        datetime.now(timezone.utc) - lan_thi.bat_dau_luc.replace(tzinfo=timezone.utc)
    ).total_seconds() / 60
    thoi_gian_toi_thieu = de_thi.thoi_gian_lam_bai * 0.5
    if thoi_gian_da_lam < thoi_gian_toi_thieu and not payload.nop_tu_dong:
        raise HTTPException(
            status_code=400,
            detail=f"Bạn cần làm bài ít nhất {int(thoi_gian_toi_thieu)} phút trước khi nộp. "
                   f"Hiện tại mới được {int(thoi_gian_da_lam)} phút."
        )

    # Kiểm tra hết giờ server
    if thoi_gian_da_lam > de_thi.thoi_gian_lam_bai + 2 and not payload.nop_tu_dong:
        raise HTTPException(status_code=400, detail="Đã hết thời gian làm bài")

    # Kiểm tra phải trả lời tất cả câu hỏi
    items = db.query(CauHoiDeThi).filter(CauHoiDeThi.de_thi_id == de_thi.id).all()
    tong_so_cau = len(items)
    so_cau_da_tra_loi = len(payload.danh_sach_tra_loi)

    if so_cau_da_tra_loi < tong_so_cau and not payload.nop_tu_dong:
        raise HTTPException(
            status_code=400,
            detail=f"Bạn còn {tong_so_cau - so_cau_da_tra_loi} câu chưa trả lời. "
                   f"Phải hoàn thành tất cả {tong_so_cau} câu trước khi nộp bài."
        )

    bang_diem = {item.cau_hoi_id: item.diem_so for item in items}
    tong_diem = 0.0
    so_dung   = 0

    for tra_loi_data in payload.danh_sach_tra_loi:
        lc = db.query(LuaChon).filter(
            LuaChon.id == tra_loi_data.lua_chon_id,
            LuaChon.cau_hoi_id == tra_loi_data.cau_hoi_id
        ).first()
        if not lc:
            continue
        if lc.la_dap_an:
            so_dung += 1
            tong_diem += bang_diem.get(tra_loi_data.cau_hoi_id, 0)
        db.add(TraLoi(
            lan_thi_id=lan_thi.id,
            cau_hoi_id=tra_loi_data.cau_hoi_id,
            lua_chon_id=tra_loi_data.lua_chon_id,
            dung=lc.la_dap_an,
        ))

    tong_diem_de  = sum(bang_diem.values()) or 1
    diem_thang_10 = round((tong_diem / tong_diem_de) * 10, 2)

    lan_thi.nop_bai_luc     = datetime.utcnow()
    lan_thi.tong_diem       = diem_thang_10
    lan_thi.dat_yeu_cau     = diem_thang_10 >= de_thi.diem_dat
    if payload.nop_tu_dong:
        lan_thi.bi_nop_tu_dong = True
    db.commit()
    db.refresh(lan_thi)
    return lan_thi

# ── Xem kết quả ───────────────────────────────────────────────────────────────
@router.get("/attempts/{attempt_id}/result", summary="Xem kết quả chi tiết")
def xem_ket_qua(attempt_id: int, db: Session = Depends(get_db),
                current_user=Depends(get_current_user)):
    lan_thi = db.query(LanThi).filter(
        LanThi.id == attempt_id, LanThi.hoc_sinh_id == current_user.id
    ).first()
    if not lan_thi:
        raise HTTPException(status_code=404, detail="Không tìm thấy lần thi")
    if not lan_thi.nop_bai_luc:
        raise HTTPException(status_code=400, detail="Bạn chưa nộp bài")

    tra_loi_list = db.query(TraLoi).options(joinedload(TraLoi.lua_chon)).filter(
        TraLoi.lan_thi_id == attempt_id
    ).all()

    chi_tiet = []
    for tl in tra_loi_list:
        cq = db.query(CauHoi).options(joinedload(CauHoi.lua_chon)).filter(CauHoi.id == tl.cau_hoi_id).first()
        dap_an_dung = next((lc.noi_dung for lc in cq.lua_chon if lc.la_dap_an), None) if cq else None
        chi_tiet.append({
            "cau_hoi_id":       tl.cau_hoi_id,
            "noi_dung_cau_hoi": cq.noi_dung if cq else "",
            "lua_chon_da_chon": tl.lua_chon.noi_dung if tl.lua_chon else None,
            "dap_an_dung":      dap_an_dung,
            "dung":             tl.dung,
            "giai_thich":       cq.giai_thich if cq else None,
        })

    return {
        "lan_thi_id":    lan_thi.id,
        "de_thi_id":     lan_thi.de_thi_id,
        "tong_diem":     lan_thi.tong_diem,
        "dat_yeu_cau":   lan_thi.dat_yeu_cau,
        "bat_dau_luc":   lan_thi.bat_dau_luc,
        "nop_bai_luc":   lan_thi.nop_bai_luc,
        "so_lan_thoat_tab": lan_thi.so_lan_thoat_tab,
        "bi_nop_tu_dong": lan_thi.bi_nop_tu_dong,
        "chi_tiet_tung_cau": chi_tiet,
    }


@router.get("/my-attempts", response_model=List[LanThiResponse], summary="Lịch sử làm bài")
def lich_su(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return db.query(LanThi).filter(LanThi.hoc_sinh_id == current_user.id).order_by(
        LanThi.bat_dau_luc.desc()
    ).all()