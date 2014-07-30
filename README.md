mp3_zing_downloader
===================

A tool for batch download on mp3.zing.vn

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

    pip install mp3_zing_downloader

Sử dụng
-------

Để download tất cả các bài hát trong 1 url:

    $mp3zingdownload {url} --dir={DIR}

Trong đó DIR là thư mục sẽ lưu các bài hát download về, nếu không chỉ định thì là thư mục hiện tại.

Cách lưu bài hát sẽ như sau:

    DIR/Tên ca sỹ/Tên album/Tên bài hát.mp3