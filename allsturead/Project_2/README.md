
## 项目说明
项目来源：https://github.com/vldbss-2021/vldb-2021-labs


## 项目实验内容和要求
可参考项目地址下的说明。


## 项目目录结构
```
   |-- tinykv

   |-- tinysql

```

#### 运行环境
go >= 13.3
安装并可使用 make

#### 开发工具
GoLand  (建议使用)
VSCode + go插件


#### 编译与执行
#### 编译
cd tinykv
make
或者 make kv 

cd tinysql
make
或者 make server 

以上两个步骤，编译产生的可执行文件都在对应文件夹的 bin 目录下.



#### 启动
mkdir -p data

./tinyscheduler-server

./tinykv-server -path=data

./tinysql-server --store=tikv --path="127.0.0.1:2379"



## 项目测评
提交内容：项目代码（git(建议git 将提交时的版本打成 tag) or 压缩包）+ 实验报告（pdf 格式文件）
评分主要依据：test 测试案例通过情况（40%）+ 实验代码（30%） + 实验报告（30%）


实验报告撰写要求：描述实验 Lab 的实现过程（可以粘贴核心代码辅助阐述）。
实验报告内容可以重点关注以下三方面，已有代码结构的理解和阅读，功能的实现过程，遇到了问题及其解决的过程。

本次实验项目的提交时间：2024年6月7日23时 前提交。


## 参考资料
项目中有较多的项目说明和相关资料：https://github.com/vldbss-2021/vldb-2021-labs.
视频学习资料：https://learn.pingcap.cn/learner/course/750001.

