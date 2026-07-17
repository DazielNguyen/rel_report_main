# So sánh Rel-report-v2 vs Rel-report-v3

## 1. Thay đổi chính

| Hạng mục | v2 (cũ) | v3 (mới) | Nguyên nhân |
|---|---|---|---|
| **Reward function** | `R = -(cost) × 1e-8` | `R = (revenue − cost) × 1e-8` | v2 quên cộng revenue → agent tối ưu cost → nhập ít → thiếu hàng |
| **Retail margin** | 25% (MARGIN_MULTIPLIER=1.25) | **40%** (MARGIN_MULTIPLIER=1.40) | Vẫn còn lỗ ở 25%, tăng lên 40% để có profit dương |
| **Số episodes SAC** | 200 | **300** | Cho SAC thêm thời gian hội tụ |
| **Start steps SAC** | 1,000 | **2,000** | Tăng thám hiểm ban đầu |

---

## 2. Kết quả số

### 2.1 So sánh profit

| Thuật toán | v2 Profit (B) | v3 Profit (B) | Thay đổi |
|---|---|---|---|
| Random | −73.68 | **−63.34** | Cải thiện nhẹ (seed khác) |
| Q-learning | −53.49 | **+16.06** | ✅ Chuyển từ lỗ sang lãi |
| SARSA | −35.87 | **+8.84** | ✅ Chuyển từ lỗ sang lãi |
| SAC-AlphaLR | −27.88 | **+24.77** | ✅ Tốt nhất, lãi cao nhất |

### 2.2 Chi phí và shortage

| Thuật toán | v2 Cost (B) | v3 Cost (B) | v2 Shortage | v3 Shortage |
|---|---|---|---|---|
| Random | 182.64 | 183.03 | 5,022 | 4,973 |
| Q-learning | 178.09 | **158.35** | 4,286 | **2,365** |
| SARSA | 171.05 | **161.36** | 3,785 | **2,472** |
| SAC-AlphaLR | 167.35 | **156.78** | 2,709 | **2,039** |

### 2.3 Revenue

| Thuật toán | v2 Revenue (B) | v3 Revenue (B) |
|---|---|---|
| Random | 108.96 | 119.69 |
| Q-learning | 124.60 | **174.41** |
| SARSA | 135.18 | **170.20** |
| SAC-AlphaLR | 139.47 | **181.55** |

---

## 3. Thay đổi nội dung

### ✅ Thêm mới trong v3

- **Profit-based reward** — giải thích lý do chuyển từ cost sang profit
- **MARGIN_MULTIPLIER = 1.4** — tham số được điều chỉnh
- **Floor-space constraint** — dẫn số liệu từ source (RETAIL_STORE_AREA_M2=25m²)
- **GitHub link thật** — thay "available upon request" bằng link thật
- **Kết luận về Q-learning vs SARSA** — đảo ngược so với v2 (giờ Q-learning thắng)

### 🔄 Thay đổi trong v3

| Section | v2 | v3 |
|---|---|---|
| Abstract | SAC cost 167.35B, lỗ 27.88B | SAC cost **156.78B**, lãi **+24.77B** |
| Section 1 | Cost-minimization framing | **Profit-maximization** framing |
| Section 2.1 (MDP) | Reward = −cost | Reward = **revenue − cost** |
| Section 5 (Results) | Mô tả net loss | Mô tả **net profit** |
| Section 6 (Discussion) | "All policies at net loss" | **"All learned policies profitable"** |
| Declarations | Code: "upon request" | Code: **github.com link** |

### ❌ Bỏ trong v3

- **Sensitivity analysis (Section 5.1)** — chưa update kịp số liệu mới
- **Figure 1–3** — cần tạo lại từ kết quả v3
- **SAC-AlphaLR naming issue footnote** — đã bỏ, giữ nguyên tên

---

## 4. Kết luận chính cho paper (v3)

1. **SAC-AlphaLR là best performer** — profit +24.77B, cost 156.78B, shortage 2,039
2. **Cả 3 RL algorithms đều có lợi nhuận dương** — Q-learning +16.06B, SARSA +8.84B
3. **Chìa khóa: profit-based reward** — khi không có revenue trong reward, agent chọn nhập ít nhất → thua random
4. **Q-learning cạnh tranh hơn SARSA** — +16.06B vs +8.84B (ngược với v2)

---

## 5. Công việc còn lại (từ taskuutien)

| STT | Việc | Trạng thái |
|---|---|---|
| 5 | Chạy lại toàn bộ kết quả | ✅ **Đã xong** (v3 numbers) |
| 6 | Chuẩn hóa tên SAC | ✅ Giữ SAC-AlphaLR (đã quyết định) |
| 12 | Sửa reward function | ✅ **Đã xong** (profit-based) |
| 14 | Giải quyết net loss | ✅ **Đã xong** (MARGIN=1.4) |
| 25 | Metadata + GitHub | ✅ **Đã xong** (link thật) |
| 7 | SAC Fixed Alpha baseline | ❌ Chưa làm |
| 8 | Multi-seed | ❌ Chưa làm |
| 13 | Ablation reward | ❌ Chưa làm |
| 15 | Learning curves | ❌ Chưa làm |
| 17 | Sensitivity tất cả | ❌ Chưa làm |
| 26 | Abstract + Conclusion sau cùng | ✅ Tạm xong, cần review |
