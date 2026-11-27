# Search Studio

Ứng dụng trực quan hóa thuật toán tìm kiếm (**BFS**, **DFS**, **UCS**) cho **8 Puzzle** và **Máy hút bụi**.

## Chạy ứng dụng

```powershell
python -m pip install pygame
python src/main.py
```

## Tính năng & Điều khiển

- **8 Puzzle:** nhấn 2 ô để đổi chỗ; tự động kiểm tra tính giải được (trọng số UCS: `UP`/`DOWN` = 1, `LEFT`/`RIGHT` = 2).
- **Máy hút bụi:** tùy chỉnh 2–10 phòng, nhấn phòng để đổi Sạch/Bẩn và chọn vị trí bắt đầu của robot (trọng số UCS: `LEFT`/`RIGHT` = 1, `SUCK` = 2).
- **Lộ trình & Giao diện:** nhấn trực tiếp từng bước trên thanh lộ trình để xem; hỗ trợ chế độ Sáng/Tối.
- **Phím tắt:** `Space` phát/dừng · `←`/`→` lùi/tiến bước · `R` xáo trộn · `1`/`2` đổi trò chơi · `Esc` thoát.

Thuật toán nằm tại `algorithms/search.py` và đăng ký ở `algorithms/registry.py`. Luật trò chơi nằm trong `games/`.
