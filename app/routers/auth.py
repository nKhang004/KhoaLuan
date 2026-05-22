from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.core.security import hash_password, verify_password, create_access_token, get_current_user, require_admin
from app.models.models import NguoiDung
from app.schemas.schemas import (
    TokenResponse, NguoiDungResponse,
    DoiMatKhauLanDauRequest,
    DoiMatKhauRequest, CapNhatVaiTroRequest
)

router = APIRouter(prefix="/auth", tags=["Xác thực"])


@router.post("/login", response_model=TokenResponse, summary="Đăng nhập")
def dang_nhap(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    nd = db.query(NguoiDung).filter(NguoiDung.ten_dang_nhap == form_data.username).first()
    if not nd or not verify_password(form_data.password, nd.mat_khau):
        raise HTTPException(status_code=401, detail="Tên đăng nhập hoặc mật khẩu không đúng")
    if not nd.kich_hoat:
        raise HTTPException(status_code=403, detail="Tài khoản đã bị vô hiệu hóa bởi quản trị viên")
    
    # ✅ CHỦ ĐÍCH: Chỉ sinh viên mới bị kiểm tra phai_doi_mat_khau
    if nd.vai_tro == "hoc_sinh" and nd.phai_doi_mat_khau:
        raise HTTPException(
            status_code=403,
            detail="Bạn cần đổi mật khẩu lần đầu trước khi sử dụng hệ thống. Vui lòng sử dụng API đổi mật khẩu lần đầu."
        )

    token = create_access_token(data={"sub": nd.ten_dang_nhap, "vai_tro": nd.vai_tro})
    return {"access_token": token, "token_type": "bearer"}


@router.post("/change-first-password", summary="Đổi mật khẩu lần đầu (chỉ dành cho sinh viên)")
def doi_mat_khau_lan_dau(payload: DoiMatKhauLanDauRequest, db: Session = Depends(get_db)):
    nd = db.query(NguoiDung).filter(NguoiDung.ten_dang_nhap == payload.ten_dang_nhap).first()
    if not nd:
        raise HTTPException(status_code=404, detail="Tên đăng nhập không tồn tại")
    
    # ✅ Chỉ sinh viên mới được đổi mật khẩu lần đầu
    if nd.vai_tro != "hoc_sinh":
        raise HTTPException(status_code=403, detail="Chức năng này chỉ dành cho sinh viên")
    
    if not nd.phai_doi_mat_khau:
        raise HTTPException(status_code=400, detail="Tài khoản này không yêu cầu đổi mật khẩu lần đầu")
    if not verify_password(payload.mat_khau_cu, nd.mat_khau):
        raise HTTPException(status_code=400, detail="Mật khẩu cũ không đúng")
    
    nd.mat_khau = hash_password(payload.mat_khau_moi)
    nd.phai_doi_mat_khau = False
    db.commit()
    
    return {"thong_bao": "Đổi mật khẩu thành công. Vui lòng đăng nhập lại với mật khẩu mới."}


@router.get("/me", response_model=NguoiDungResponse, summary="Thông tin tài khoản hiện tại")
def thong_tin_ca_nhan(current_user=Depends(get_current_user)):
    return current_user


@router.get("/users", response_model=List[NguoiDungResponse], summary="Danh sách người dùng (Admin)")
def lay_danh_sach(db: Session = Depends(get_db), current_user=Depends(require_admin)):
    return db.query(NguoiDung).order_by(NguoiDung.id).all()


@router.put("/users/{user_id}/toggle-active", response_model=NguoiDungResponse,
            summary="Khóa / Mở khóa tài khoản (Admin)")
def khoa_mo(user_id: int, db: Session = Depends(get_db), current_user=Depends(require_admin)):
    nd = db.query(NguoiDung).filter(NguoiDung.id == user_id).first()
    if not nd:
        raise HTTPException(status_code=404, detail="Không tìm thấy người dùng")
    if nd.id == current_user.id:
        raise HTTPException(status_code=400, detail="Không thể tự khóa tài khoản của chính mình")
    nd.kich_hoat = not nd.kich_hoat
    db.commit()
    db.refresh(nd)
    return nd


@router.put("/users/{user_id}/role", response_model=NguoiDungResponse,
            summary="Thay đổi vai trò (Admin)")
def doi_vai_tro(user_id: int, payload: CapNhatVaiTroRequest,
                db: Session = Depends(get_db), current_user=Depends(require_admin)):
    nd = db.query(NguoiDung).filter(NguoiDung.id == user_id).first()
    if not nd:
        raise HTTPException(status_code=404, detail="Không tìm thấy người dùng")
    if nd.id == current_user.id:
        raise HTTPException(status_code=400, detail="Không thể tự thay đổi vai trò")
    nd.vai_tro = payload.vai_tro
    db.commit()
    db.refresh(nd)
    return nd


@router.delete("/users/{user_id}", status_code=204, summary="Xóa tài khoản (Admin)")
def xoa_tai_khoan(user_id: int, db: Session = Depends(get_db),
                  current_user=Depends(require_admin)):
    nd = db.query(NguoiDung).filter(NguoiDung.id == user_id).first()
    if not nd:
        raise HTTPException(status_code=404, detail="Không tìm thấy người dùng")
    if nd.id == current_user.id:
        raise HTTPException(status_code=400, detail="Không thể tự xóa tài khoản của chính mình")
    db.delete(nd)
    db.commit()


@router.put("/change-password", summary="Đổi mật khẩu (dành cho tất cả người dùng đã đăng nhập)")
def doi_mat_khau(payload: DoiMatKhauRequest, db: Session = Depends(get_db),
                 current_user=Depends(get_current_user)):
    if not verify_password(payload.mat_khau_cu, current_user.mat_khau):
        raise HTTPException(status_code=400, detail="Mật khẩu cũ không đúng")
    current_user.mat_khau = hash_password(payload.mat_khau_moi)
    # Nếu là sinh viên và đang đổi mật khẩu bình thường, đảm bảo phai_doi_mat_khau = False
    if current_user.vai_tro == "hoc_sinh":
        current_user.phai_doi_mat_khau = False
    db.commit()
    return {"thong_bao": "Đổi mật khẩu thành công"}