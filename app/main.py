from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.base import Base, Product

# 1. Kết nối DB
engine = create_engine("sqlite:///stash_forge.db")
Base.metadata.create_all(engine) # Đảm bảo bảng đã được tạo

# 2. Tạo Session để làm việc với DB
Session = sessionmaker(bind=engine)
session = Session()

def run_app():
    print("--- CHƯƠNG TRÌNH QUẢN LÝ KHO FLOWBASE ---")
    while True:
        print("\n1. Thêm sản phẩm")
        print("2. Xem danh sách kho")
        print("3. Thoát")
        choice = input("Chọn chức năng (1-3): ")

        if choice == '1':
            name = input("Tên sản phẩm: ")
            sku = input("Mã SKU: ")
            qty = int(input("Số lượng: "))
            
            new_item = Product(name=name, sku=sku, quantity=qty)
            session.add(new_item)
            session.commit()
            print("Đã thêm thành công!")

        elif choice == '2':
            products = session.query(Product).all()
            print("\nDANH SÁCH TRONG KHO:")
            for p in products:
                print(f"ID: {p.id} | Tên: {p.name} | SKU: {p.sku} | SL: {p.quantity}")

        elif choice == '3':
            break

if __name__ == "__main__":
    run_app()