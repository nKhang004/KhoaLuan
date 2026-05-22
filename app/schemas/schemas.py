from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

# ─── Enums ────────────────────────────────────────────────────────────────────

class VaiTro(str, Enum):
    admin     = "admin"
    giao_vien = "giao_vien"
    hoc_sinh  = "hoc_sinh"

class LoaiCauHoi(str, Enum):
    trac_nghiem_mot_dap_an   = "trac_nghiem_mot_dap_an"
    trac_nghiem_nhieu_dap_an = "trac_nghiem_nhieu_dap_an"
    dung_sai = "dung_sai"

class DoKho(str, Enum):
    de         = "de"
    trung_binh = "trung_binh"
    kho        = "kho"

# ─── Auth ─────────────────────────────────────────────────────────────────────

class TokenResponse(BaseModel):
    access_token: str
    token_type:   str = "bearer"

class DoiMatKhauLanDauRequest(BaseModel):
    ten_dang_nhap: str = Field(..., min_length=4)
    mat_khau_cu:   str = Field(..., min_length=1)
    mat_khau_moi:  str = Field(..., min_length=6)

class DoiMatKhauRequest(BaseModel):
    mat_khau_cu:  str = Field(..., min_length=1)
    mat_khau_moi: str = Field(..., min_length=6)

class CapNhatVaiTroRequest(BaseModel):
    vai_tro: VaiTro

# ─── Người dùng ───────────────────────────────────────────────────────────────

class NguoiDungResponse(BaseModel):
    id:           int
    ten_dang_nhap: str
    ho_ten:       str
    vai_tro:      str
    kich_hoat:    bool
    phai_doi_mat_khau: bool = True
    ngay_tao:     Optional[datetime]

    class Config:
        from_attributes = True

# ─── Môn học ──────────────────────────────────────────────────────────────────

class MonHocCreate(BaseModel):
    ten_mon: str = Field(..., min_length=2, max_length=150)
    ma_mon:  str = Field(..., min_length=2, max_length=20)
    mo_ta:   Optional[str] = None

class MonHocResponse(BaseModel):
    id:      int
    ten_mon: str
    ma_mon:  str
    mo_ta:   Optional[str]
    an_hien: bool
    ngay_tao: Optional[datetime]

    class Config:
        from_attributes = True

# ─── Chủ đề ───────────────────────────────────────────────────────────────────

class ChuDeCreate(BaseModel):
    ten_chu_de: str = Field(..., min_length=2)
    mo_ta:      Optional[str] = None
    mon_hoc_id: int

class ChuDeResponse(BaseModel):
    id:         int
    ten_chu_de: str
    mo_ta:      Optional[str]
    mon_hoc_id: int
    an_hien:    bool

    class Config:
        from_attributes = True

# ─── Lựa chọn ─────────────────────────────────────────────────────────────────

class LuaChonCreate(BaseModel):
    noi_dung:  str
    la_dap_an: bool = False
    thu_tu:    int  = 0

class LuaChonResponse(BaseModel):
    id:        int
    noi_dung:  str
    la_dap_an: bool
    thu_tu:    int

    class Config:
        from_attributes = True

# ─── Câu hỏi ──────────────────────────────────────────────────────────────────

class CauHoiCreate(BaseModel):
    noi_dung:    str  = Field(..., min_length=5)
    loai_cau_hoi: LoaiCauHoi = LoaiCauHoi.trac_nghiem_mot_dap_an
    do_kho:      DoKho = DoKho.trung_binh
    chu_de_id:   int
    giai_thich:  Optional[str] = None
    lua_chon:    List[LuaChonCreate] = Field(..., min_length=2, max_length=6)

class CauHoiUpdate(BaseModel):
    noi_dung:    Optional[str] = None
    loai_cau_hoi: Optional[LoaiCauHoi] = None
    do_kho:      Optional[DoKho] = None
    giai_thich:  Optional[str] = None

class CauHoiResponse(BaseModel):
    id:          int
    noi_dung:    str
    loai_cau_hoi: str
    do_kho:      str
    chu_de_id:   int
    giai_thich:  Optional[str]
    an_hien:     bool
    ngay_tao:    Optional[datetime]
    lua_chon:    List[LuaChonResponse] = []

    class Config:
        from_attributes = True

# ─── Đề thi ───────────────────────────────────────────────────────────────────

class CauHoiDeThiCreate(BaseModel):
    cau_hoi_id: int
    thu_tu:     int   = 1
    diem_so:    float = 1.0

class DeThiCreate(BaseModel):
    tieu_de:          str  = Field(..., min_length=3)
    mo_ta:            Optional[str] = None
    thoi_gian_lam_bai: int = Field(..., gt=0)
    diem_dat:         float = Field(default=5.0, ge=0, le=10)
    danh_sach_cau_hoi: List[CauHoiDeThiCreate] = []

class DeThiAutoCreate(BaseModel):
    tieu_de:           str
    mo_ta:             Optional[str] = None
    thoi_gian_lam_bai: int
    diem_dat:          float = 5.0
    chu_de_id:         int
    do_kho:            Optional[DoKho] = None
    so_luong_cau_hoi:  int   = Field(default=10, ge=1, le=100)
    diem_moi_cau:      float = 1.0

class DeThiResponse(BaseModel):
    id:               int
    tieu_de:          str
    mo_ta:            Optional[str]
    thoi_gian_lam_bai: int
    diem_dat:         float
    cong_bo:          bool
    nguoi_tao_id:     int
    ngay_tao:         Optional[datetime]

    class Config:
        from_attributes = True

# ─── Lần thi & Trả lời ────────────────────────────────────────────────────────

class TraLoiRequest(BaseModel):
    cau_hoi_id:  int
    lua_chon_id: int

class NopBaiRequest(BaseModel):
    danh_sach_tra_loi: List[TraLoiRequest]
    nop_tu_dong: bool = False

class LanThiResponse(BaseModel):
    id:               int
    de_thi_id:        int
    bat_dau_luc:      Optional[datetime]
    nop_bai_luc:      Optional[datetime]
    tong_diem:        Optional[float]
    dat_yeu_cau:      Optional[bool]
    so_lan_thoat_tab: Optional[int] = 0
    bi_nop_tu_dong:   Optional[bool] = False

    class Config:
        from_attributes = True

# ─── Báo cáo ──────────────────────────────────────────────────────────────────

class ThongKeDeThi(BaseModel):
    de_thi_id:       int
    tieu_de:         str
    tong_luot_thi:   int
    diem_trung_binh: Optional[float]
    ty_le_dat:       Optional[float]

class ThongKeCauHoi(BaseModel):
    cau_hoi_id:    int
    noi_dung:      str
    so_lan_tra_loi: int
    so_lan_dung:   int
    ty_le_dung:    float