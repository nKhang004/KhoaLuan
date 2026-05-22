from sqlalchemy import Column, Integer, String, Text, Boolean, Float, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class NguoiDung(Base):
    __tablename__ = "nguoi_dung"
    id                = Column(Integer, primary_key=True, index=True)
    ten_dang_nhap     = Column(String(100), unique=True, nullable=False)
    mat_khau          = Column(String(255), nullable=False)
    ho_ten            = Column(String(150), nullable=False)

    vai_tro           = Column(Enum("admin", "giao_vien", "hoc_sinh"), nullable=False, default="hoc_sinh")
    kich_hoat         = Column(Boolean, default=True)
    phai_doi_mat_khau = Column(Boolean, default=True)
    ngay_tao          = Column(DateTime, server_default=func.now())

    cau_hoi      = relationship("CauHoi",      back_populates="nguoi_tao")
    de_thi       = relationship("DeThi",       back_populates="nguoi_tao")
    lan_thi      = relationship("LanThi",      back_populates="hoc_sinh")


class MonHoc(Base):
    __tablename__ = "mon_hoc"
    id       = Column(Integer, primary_key=True, index=True)
    ten_mon  = Column(String(150), nullable=False)
    ma_mon   = Column(String(20), unique=True, nullable=False)
    mo_ta    = Column(Text)
    an_hien  = Column(Boolean, default=True)
    ngay_tao = Column(DateTime, server_default=func.now())
    chu_de   = relationship("ChuDe", back_populates="mon_hoc")


class ChuDe(Base):
    __tablename__ = "chu_de"
    id         = Column(Integer, primary_key=True, index=True)
    ten_chu_de = Column(String(200), nullable=False)
    mo_ta      = Column(Text)
    mon_hoc_id = Column(Integer, ForeignKey("mon_hoc.id"), nullable=False)
    an_hien    = Column(Boolean, default=True)
    ngay_tao   = Column(DateTime, server_default=func.now())
    mon_hoc    = relationship("MonHoc", back_populates="chu_de")
    cau_hoi    = relationship("CauHoi", back_populates="chu_de")


class CauHoi(Base):
    __tablename__ = "cau_hoi"
    id            = Column(Integer, primary_key=True, index=True)
    noi_dung      = Column(Text, nullable=False)
    loai_cau_hoi  = Column(Enum("trac_nghiem_mot_dap_an","trac_nghiem_nhieu_dap_an","dung_sai"), nullable=False, default="trac_nghiem_mot_dap_an")
    do_kho        = Column(Enum("de","trung_binh","kho"), nullable=False, default="trung_binh")
    chu_de_id     = Column(Integer, ForeignKey("chu_de.id"), nullable=False)
    nguoi_tao_id  = Column(Integer, ForeignKey("nguoi_dung.id"), nullable=False)
    giai_thich    = Column(Text)
    an_hien       = Column(Boolean, default=True)
    ngay_tao      = Column(DateTime, server_default=func.now())
    ngay_cap_nhat = Column(DateTime, server_default=func.now(), onupdate=func.now())
    chu_de        = relationship("ChuDe",    back_populates="cau_hoi")
    nguoi_tao     = relationship("NguoiDung", back_populates="cau_hoi")
    lua_chon      = relationship("LuaChon",   back_populates="cau_hoi", cascade="all, delete-orphan")
    cau_hoi_de_thi = relationship("CauHoiDeThi", back_populates="cau_hoi")


class LuaChon(Base):
    __tablename__ = "lua_chon"
    id         = Column(Integer, primary_key=True, index=True)
    noi_dung   = Column(Text, nullable=False)
    la_dap_an  = Column(Boolean, default=False)
    cau_hoi_id = Column(Integer, ForeignKey("cau_hoi.id"), nullable=False)
    thu_tu     = Column(Integer, default=0)
    cau_hoi = relationship("CauHoi",  back_populates="lua_chon")
    tra_loi = relationship("TraLoi",  back_populates="lua_chon")


class DeThi(Base):
    __tablename__ = "de_thi"
    id                = Column(Integer, primary_key=True, index=True)
    tieu_de           = Column(String(255), nullable=False)
    mo_ta             = Column(Text)
    thoi_gian_lam_bai = Column(Integer, nullable=False)
    diem_dat          = Column(Float, default=5.0)
    cong_bo           = Column(Boolean, default=False)
    nguoi_tao_id      = Column(Integer, ForeignKey("nguoi_dung.id"), nullable=False)
    ngay_tao          = Column(DateTime, server_default=func.now())
    ngay_cap_nhat     = Column(DateTime, server_default=func.now(), onupdate=func.now())
    nguoi_tao      = relationship("NguoiDung",    back_populates="de_thi")
    cau_hoi_de_thi = relationship("CauHoiDeThi",  back_populates="de_thi", cascade="all, delete-orphan")
    lan_thi        = relationship("LanThi",        back_populates="de_thi")


class CauHoiDeThi(Base):
    __tablename__ = "cau_hoi_de_thi"
    id         = Column(Integer, primary_key=True, index=True)
    de_thi_id  = Column(Integer, ForeignKey("de_thi.id"), nullable=False)
    cau_hoi_id = Column(Integer, ForeignKey("cau_hoi.id"), nullable=False)
    thu_tu     = Column(Integer, default=1)
    diem_so    = Column(Float, default=1.0)
    de_thi  = relationship("DeThi",   back_populates="cau_hoi_de_thi")
    cau_hoi = relationship("CauHoi",  back_populates="cau_hoi_de_thi")


class LanThi(Base):
    __tablename__ = "lan_thi"
    id               = Column(Integer, primary_key=True, index=True)
    hoc_sinh_id      = Column(Integer, ForeignKey("nguoi_dung.id"), nullable=False)
    de_thi_id        = Column(Integer, ForeignKey("de_thi.id"), nullable=False)
    bat_dau_luc      = Column(DateTime, server_default=func.now())
    nop_bai_luc      = Column(DateTime, nullable=True)
    tong_diem        = Column(Float, nullable=True)
    dat_yeu_cau      = Column(Boolean, nullable=True)
    so_lan_thoat_tab = Column(Integer, default=0)
    bi_nop_tu_dong   = Column(Boolean, default=False)
    hoc_sinh   = relationship("NguoiDung",  back_populates="lan_thi")
    de_thi     = relationship("DeThi",      back_populates="lan_thi")
    tra_loi    = relationship("TraLoi",     back_populates="lan_thi", cascade="all, delete-orphan")
    giam_sat   = relationship("GiamSatThi", back_populates="lan_thi", cascade="all, delete-orphan")


class TraLoi(Base):
    __tablename__ = "tra_loi"
    id          = Column(Integer, primary_key=True, index=True)
    lan_thi_id  = Column(Integer, ForeignKey("lan_thi.id"), nullable=False)
    cau_hoi_id  = Column(Integer, ForeignKey("cau_hoi.id"), nullable=False)
    lua_chon_id = Column(Integer, ForeignKey("lua_chon.id"), nullable=True)
    dung        = Column(Boolean, nullable=True)
    lan_thi  = relationship("LanThi",  back_populates="tra_loi")
    lua_chon = relationship("LuaChon", back_populates="tra_loi")


class GiamSatThi(Base):
    __tablename__ = "giam_sat_thi"
    id           = Column(Integer, primary_key=True, index=True)
    lan_thi_id   = Column(Integer, ForeignKey("lan_thi.id"), nullable=False)
    loai_su_kien = Column(Enum("thoat_tab", "quay_lai", "nop_tu_dong", "canh_bao"), nullable=False)
    thoi_diem    = Column(DateTime, server_default=func.now())
    mo_ta        = Column(String(255))
    lan_thi = relationship("LanThi", back_populates="giam_sat")