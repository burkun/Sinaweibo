# Sinaweibo
新浪微博模拟登录 和 自动发 微博，带图片微博 的python脚本，使用opencv实现读取摄像头上传图片到微博。

    weibo = Weibo('burkun', '******')
    print weibo.uploadJpegImg("../test.JPG")
    weibo.postTextWithImage("机器发的第一个带图片的微博!!!很兴奋呐!!!", "../test.JPG")
    weibo.decide_post_comment();
    weibo.get_comment('3856489792158325')
