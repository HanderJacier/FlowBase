from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.orm import declarative_base

# 1. Khởi tạo Base để các class khác kế thừa
Base = declarative_base()

# 2. Định nghĩa bảng Product
class Product(Base):
    __tablename__ = 'products'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    sku = Column(String, unique=True, nullable=False)
    quantity = Column(Integer, default=0)
    price = Column(Integer, default=0)

# 3. Kết nối Database và tạo bảng
if __name__ == "__main__":
    # Tạo engine (file stash_forge.db sẽ xuất hiện trong thư mục bạn đứng chạy code)
    engine = create_engine("sqlite:///stash_forge.db")
    
    Base.metadata.create_all(engine)
    print("Đã tạo Database và bảng Product thành công!")