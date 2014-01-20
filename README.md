mp3_zing_downloader
===================

A Tool for batch download on mp3.zing.vn

Tính năng
---------

* Tự động download các bài hát từ 1 link bất kỳ của mp3.zing.vn
* Tự động tổ chức file trên ổ cứng, cấu trúc xem phần Sử dụng
* Tự động thiết lập meta data cho file mp3:
    * Title
    * Album
    * Artist

Cài đặt
-------

### Dùng pip:
> Đang cập nhật

### clone hoặc download source code về máy, 1 thưc mục bất kỳ. Tạm gọi là src

    cd src
    python setup.py install

Sử dụng
-------

Để download tất cả các bài hát trong 1 url:

    ${python_dir}/bin/mp3_zing_downloader {url} --dir={DIR}

Trong đó DIR là thư mục sẽ lưu các bài hát download về, nếu không chỉ định thì là thư mục hiện tại.

Cách lưu bài hát sẽ như sau:

    DIR/Tên ca sỹ/Tên album/Tên bài hát.mp3