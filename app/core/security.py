from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token không hợp lệ hoặc đã hết hạn")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    from app.models.models import NguoiDung
    payload = decode_token(token)
    username = payload.get("sub")
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Không xác định được người dùng")
    user = db.query(NguoiDung).filter(NguoiDung.ten_dang_nhap == username).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Tài khoản không tồn tại")
    if not user.kich_hoat:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tài khoản đã bị khóa")
    return user

def require_admin(current_user=Depends(get_current_user)):
    if current_user.vai_tro != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Chỉ Admin mới có quyền thực hiện thao tác này")
    return current_user

def require_teacher(current_user=Depends(get_current_user)):
    if current_user.vai_tro not in ("admin", "giao_vien"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Chỉ Giáo viên hoặc Admin mới có quyền thực hiện thao tác này")
    return current_user

def require_change_password(current_user=Depends(get_current_user)):
    """Kiểm tra xem tài khoản có cần đổi mật khẩu lần đầu không"""
    if current_user.phai_doi_mat_khau:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn cần đổi mật khẩu lần đầu trước khi sử dụng hệ thống"
        )
    return current_user