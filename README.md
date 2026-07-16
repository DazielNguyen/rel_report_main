# Springer Nature LaTeX manuscript

Đây là repository chứa bản thảo LaTeX sử dụng template Springer Nature phiên
bản 3.1 (tháng 12/2024). Tài liệu này hướng dẫn collaborator cài môi trường,
clone project và compile trên Windows.

## 1. Phần mềm cần cài trên Windows

### Bắt buộc

1. **Git for Windows**: tải tại <https://git-scm.com/download/win>.
2. **Một bộ TeX**, khuyến nghị **TeX Live**:
   <https://tug.org/texlive/windows.html>.

TeX Live đã cung cấp các công cụ project cần dùng: `pdflatex`, `bibtex` và
`latexmk`. Khi cài, nên chọn cài đầy đủ để tránh thiếu package LaTeX.

Có thể dùng **MiKTeX** thay cho TeX Live
(<https://miktex.org/download>), nhưng cần:

- bật tùy chọn tự động cài package còn thiếu trong MiKTeX Console;
- kiểm tra package `latexmk` đã được cài;
- cài Perl, ví dụ Strawberry Perl (<https://strawberryperl.com/>), nếu chạy
  `latexmk` và nhận lỗi không tìm thấy Perl.

Không nên cài đồng thời TeX Live và MiKTeX, vì Windows có thể gọi nhầm chương
trình do thứ tự trong biến môi trường `PATH`.

### Khuyến nghị để soạn thảo

- Visual Studio Code: <https://code.visualstudio.com/>.
- Extension **LaTeX Workshop** của James Yu trong VS Code.

Sau khi cài, đóng và mở lại PowerShell/VS Code, rồi kiểm tra:

```powershell
git --version
pdflatex --version
bibtex --version
latexmk -v
```

Nếu một lệnh không được nhận diện, hãy khởi động lại Windows. Nếu vẫn lỗi,
kiểm tra thư mục `bin` của Git hoặc bộ TeX đã được thêm vào `PATH`.

## 2. Clone repository

Mở PowerShell tại thư mục muốn lưu project và chạy:

```powershell
git clone https://github.com/DazielNguyen/rel_report_main.git
cd rel_report_main
```

Nếu repository đang ở chế độ private, tài khoản GitHub của bạn phải được chủ
repository thêm làm collaborator. Git có thể yêu cầu đăng nhập qua trình duyệt
ở lần clone hoặc push đầu tiên.

## 3. Compile trên Windows

Tại thư mục gốc của project, chạy:

```powershell
latexmk -pdf -interaction=nonstopmode -halt-on-error sn-article.tex
```

File kết quả là `sn-article.pdf`. `latexmk` sẽ tự chạy `pdflatex` và BibTeX đủ
số lần cần thiết để cập nhật citation, bibliography và cross-reference.

Project có file `.latexmkrc` để BibTeX tự tìm thấy các style Springer Nature
trong thư mục `bst/`; collaborator không cần copy các file `.bst` vào hệ thống.

### Compile trong VS Code

1. Mở cả thư mục `rel_report_main` bằng **File > Open Folder**.
2. Mở `sn-article.tex`.
3. Nhấn `Ctrl+Alt+B`, hoặc mở bảng lệnh bằng `Ctrl+Shift+P` và chọn
   **LaTeX Workshop: Build LaTeX project**.
4. Mở PDF bằng nút **View LaTeX PDF** của LaTeX Workshop.

LaTeX Workshop thường tự nhận `latexmk` và file `.latexmkrc`. Nếu extension
hiển thị nhiều recipe, chọn recipe dùng `latexmk` và `pdfLaTeX`.

### Dọn file trung gian

Giữ lại PDF và xóa các file build trung gian:

```powershell
latexmk -c sn-article.tex
```

Xóa cả file trung gian và PDF được tạo:

```powershell
latexmk -C sn-article.tex
```

Trên macOS/Linux có thể dùng các lệnh tương đương `make`, `make clean` và
`make distclean` được định nghĩa trong `Makefile`. Windows không cần cài `make`.

## 4. Các file và thư mục chính

- `sn-article.tex`: nội dung bản thảo chính.
- `sn-bibliography.bib`: cơ sở dữ liệu tài liệu tham khảo.
- `sn-article.pdf`: PDF được tạo sau khi compile.
- `sn-jnl.cls`: document class của Springer Nature.
- `bst/`: các bibliography style của Springer Nature.
- `.latexmkrc`: cấu hình build dùng chung cho Windows, macOS và Linux.
- `user-manual.pdf`: hướng dẫn chính thức đi kèm template.

Thông thường collaborator chỉ cần sửa `sn-article.tex`,
`sn-bibliography.bib` và các file hình ảnh. Không sửa `sn-jnl.cls` hoặc các
file trong `bst/` trừ khi cả nhóm đã thống nhất.

## 5. Quy trình làm việc cho collaborator

Luôn lấy thay đổi mới nhất trước khi bắt đầu:

```powershell
git switch main
git pull
git switch -c ten-cua-ban/noi-dung-thay-doi
```

Sau khi sửa, compile thành công rồi commit:

```powershell
git status
git add sn-article.tex sn-bibliography.bib sn-article.pdf
git commit -m "Mô tả ngắn thay đổi"
git push -u origin ten-cua-ban/noi-dung-thay-doi
```

Chỉ thêm những file thực sự đã sửa; ví dụ trên giả định cả ba file đều thay
đổi. Sau đó tạo Pull Request trên GitHub để người khác review trước khi merge
vào `main`.

Không commit các file trung gian như `.aux`, `.log`, `.bbl`, `.blg` hoặc
`.fdb_latexmk`; chúng đã được loại trừ trong `.gitignore`. Nếu xảy ra conflict
ở `sn-article.pdf`, hãy giải quyết source `.tex`/`.bib` trước rồi compile lại
PDF, thay vì cố merge nội dung file PDF.

## 6. Lỗi thường gặp

### `latexmk` hoặc `pdflatex` is not recognized

Bộ TeX chưa được thêm vào `PATH`, hoặc terminal được mở trước khi cài. Mở lại
PowerShell/VS Code, khởi động lại Windows và kiểm tra lại các lệnh ở mục 1.

### `I couldn't open style file sn-mathphys-num.bst`

Đảm bảo chạy lệnh compile từ thư mục gốc của repository và file `.latexmkrc`
vẫn tồn tại. Không chạy trực tiếp từ một thư mục con.

### MiKTeX báo thiếu package

Mở MiKTeX Console, cập nhật package database, bật tự động cài package còn thiếu
rồi build lại. Nếu `latexmk` báo thiếu Perl, cài Strawberry Perl và mở lại
terminal.

### Citation hoặc reference hiển thị `?`

Dùng lệnh `latexmk` ở mục 3 thay vì chỉ chạy `pdflatex` một lần. Nếu vẫn còn,
kiểm tra citation key trong `sn-article.tex` có tồn tại chính xác trong
`sn-bibliography.bib` hay không.
