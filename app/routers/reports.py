from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import get_db
from app.core.security import require_teacher, get_current_user
from app.models.models import LanThi, TraLoi, DeThi, CauHoi
from app.schemas.schemas import ThongKeDeThi, ThongKeCauHoi

router = APIRouter(prefix="/reports", tags=["Thống kê & Báo cáo"])


@router.get("/exam/{exam_id}", response_model=ThongKeDeThi, summary="Thống kê kết quả một đề thi")
def thong_ke_de_thi(exam_id: int, db: Session = Depends(get_db), _=Depends(require_teacher)):
    de_thi = db.query(DeThi).filter(DeThi.id == exam_id).first()
    if not de_thi:
        raise HTTPException(status_code=404, detail="Không tìm thấy đề thi")

    # Chỉ tính những lần thi đã nộp bài
    lan_thi_list = db.query(LanThi).filter(LanThi.de_thi_id == exam_id, LanThi.nop_bai_luc.isnot(None)).all()
    tong_luot = len(lan_thi_list)

    diem_tb = None
    ty_le_dat = None
    if tong_luot > 0:
        diem_tb = round(sum(lt.tong_diem for lt in lan_thi_list if lt.tong_diem) / tong_luot, 2)
        so_dat = sum(1 for lt in lan_thi_list if lt.dat_yeu_cau)
        ty_le_dat = round((so_dat / tong_luot) * 100, 1)

    return {
        "de_thi_id": exam_id,
        "tieu_de": de_thi.tieu_de,
        "tong_luot_thi": tong_luot,
        "diem_trung_binh": diem_tb,
        "ty_le_dat": ty_le_dat,
    }


@router.get("/question/{question_id}", response_model=ThongKeCauHoi, summary="Thống kê tỷ lệ đúng/sai theo câu hỏi")
def thong_ke_cau_hoi(question_id: int, db: Session = Depends(get_db), _=Depends(require_teacher)):
    cau_hoi = db.query(CauHoi).filter(CauHoi.id == question_id).first()
    if not cau_hoi:
        raise HTTPException(status_code=404, detail="Không tìm thấy câu hỏi")

    tra_loi_list = db.query(TraLoi).filter(TraLoi.cau_hoi_id == question_id).all()
    so_tra_loi = len(tra_loi_list)
    so_dung = sum(1 for tl in tra_loi_list if tl.dung)
    ty_le = round((so_dung / so_tra_loi) * 100, 1) if so_tra_loi > 0 else 0.0

    return {
        "cau_hoi_id": question_id,
        "noi_dung": cau_hoi.noi_dung,
        "so_lan_tra_loi": so_tra_loi,
        "so_lan_dung": so_dung,
        "ty_le_dung": ty_le,
    }


@router.get("/my-history", summary="Lịch sử làm bài của học sinh đang đăng nhập")
def lich_su_ca_nhan(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    lan_thi_list = (
        db.query(LanThi)
        .filter(LanThi.hoc_sinh_id == current_user.id, LanThi.nop_bai_luc.isnot(None))
        .order_by(LanThi.bat_dau_luc.desc())
        .all()
    )
    ket_qua = []
    for lt in lan_thi_list:
        de_thi = db.query(DeThi).filter(DeThi.id == lt.de_thi_id).first()
        ket_qua.append({
            "lan_thi_id": lt.id,
            "ten_de_thi": de_thi.tieu_de if de_thi else "Không rõ",
            "ngay_thi": lt.bat_dau_luc,
            "diem_so": lt.tong_diem,
            "ket_qua": "Đạt" if lt.dat_yeu_cau else "Chưa đạt",
        })
    return ket_qua