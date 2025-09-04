# 定时同步前置操作
```
mkdir - p /root/image_syncer
# 复制image-syncer 到image_syncer目录
cp image-syncer /root/image_syncer
cp image_sync.sh /root/image_syncer
cd /root/image_syncer
```
新建auth.json，内容参考
```
{
  "swr.cn-north-4.myhuaweicloud.com": {
    "username": "长期登录指令-u后面的一串内容",
    "password": "长期登录指令-p后面的一串内容"
  },
  "swr.cn-south-4.myhuaweicloud.com": {
    "username": "长期登录指令-u后面的一串内容",
    "password": "长期登录指令-p后面的一串内容"
  }
}
```
新建images.json，里面是指定镜像同步的路径，必须到镜像级别，参考：
```
{
    "swr.cn-north-4.myhuaweicloud.com/xyr-test/nginx": "swr.cn-south-4.myhuaweicloud.com/xyr-test/nginx"
}
```
配置crontab
```
echo "0 * * * * * root /bin/bash /root/image_syncer/image_sync.sh" >> /etc/crontab
```

---配置完成---