playwright 使用cdp查找 close shadow dom 思路

目前方案

1.逆向直接过，每次代码算法变动，需要大量时间处理js环境、逆向数据。

2.浏览器方案，使用浏览器点击通过。
2.1 需要 IP UA cookie一致才能通过，一些打码平台就是通过浏览器方案，让用户传递代理 返回UA 和cookie通过。
2.2 目前浏览器方案主要问题 1、无法点击 close shadow dom （需要多思考一下方案和框架很多）2、点击后无法通过指纹识别 （stealth.min.js）3、框架被识别（更换新写的自动化框架）主要是对cdp包的比较好的。没被搜集特征的。
2.3 目前我用了3个服务、 服务1请求 创建任务 返回唯一任务ID，存入待处理信息到redis 服务2 不断从redis中获取处理任务，并标记完成。 服务3 通过唯一ID查询，返回cookie/ua 删除reids key。

3.我们还可以想一下为什么要过cf, 是因为网站设置了cf，如果我们知道源站IP的话 那么就不需要考虑这些问题了。
