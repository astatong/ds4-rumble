# ds4-rumble
有注释版
## 依赖于ds4drv请按下列步骤安装
```console
$ git clone https://github.com/naoki-mizuno/ds4drv --branch devel
$ cd ds4drv
$ mkdir -p ~/.local/lib/python3.8/site-packages
$ python3 setup.py install --prefix ~/.local
$ sudo cp udev/50-ds4drv.rules /etc/udev/rules.d/
$ sudo udevadm control --reload-rules
$ sudo udevadm trigger
```
## 安装后按照下列步骤编译
```console
$ git clone git@github.com:astatong/ds4-rumble.git
$ cd ds4-rumble
$ git checkout working 
$ mkdir -p ../ds4_ws/src && cp -r ds4_rumble ../ds4_ws/src && cd ../ds4_ws 
$ catkin_make && source devel/setup.bash
```
## 启动方式为
```console
$ roslaunch ds4_driver ds4_driver.launch
```
## 主要修改文件
src/controller_ros.py
## 新增配置文件
config/rumble_params.yaml
## 控制震动灯管话题
/set_feedback
### 消息类型为
```console
ds4_driver/Feedback
bool set_led #是否控制灯光
float32 led_r #红色亮度
float32 led_g #绿色亮度
float32 led_b #蓝色亮度
bool set_led_flash #是否闪烁
float32 led_flash_on #闪烁开
float32 led_flash_off #闪烁关
bool set_rumble #是否震动
float32 rumble_duration #震动时长
float32 rumble_small #触控板下方振动器强度
float32 rumble_big #手柄握持部分震动强度
```
### 测试话题发送指令(-r 为频率参数，1为1HZ。发送时注意震动时长与频率不要冲突)

```console
$ rostopic pub -r 1 /set_feedback ds4_driver/Feedback "{set_led: false, led_r: 0.0, led_g: 0.0, led_b: 0.0, set_led_flash: false, led_flash_on: 0.0,led_flash_off: 0.0, set_rumble: false, rumble_duration: 0.0, rumble_small: 0.0,rumble_big: 0.0}"
```
