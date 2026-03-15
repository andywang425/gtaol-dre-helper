# GTAOL CEO Helper

这是一个帮助 GTA Online 玩家自动执行“卡CEO“操作的小工具。原理是通过 OCR 识别屏幕右下角的文字，当检测到已加入人数 >=2 时，自动执行预设的按键操作注册为 CEO。

> 此处的”卡CEO“指利用德瑞bot跳前置时的”卡CEO“，不是差传的”卡CEO“（这个用宏就能搞定）

## 安装

1. 前往 [Release 页面](https://github.com/andywang425/gtaol-ceo-helper/releases/latest)，下载 `gtaol-ceo-helper.zip`、`tesseract.zip` 和 `find_coords.exe`（可选）。
2. 解压 `gtaol-ceo-helper.zip` 到任意目录。
3. 把 `tesseract.zip` 解压到 `gtaol-ceo-helper` 目录下。
4. 编辑 `config.yaml` 配置文件。过程中可能会用到 `find_coords.exe` 辅助定位 OCR 区域。

## 配置项说明（`config.yaml`）

完整结构如下：

```yaml
# 屏幕监控配置
monitor:
  # 监控开关键，按一次开启，再按一次关闭
  # 支持的按键详见下文
  toggle_key: "f12"

  # OCR 识别区域
  # 单位：屏幕像素
  # 程序会截图这个矩形区域识别“已加入人数/人数上限”
  # x, y: 矩形左上角坐标
  # width, height: 矩形宽高
  #
  # 全屏游戏时各屏幕分辨率推荐设置：
  # 4k (3840x2160): x=3609, y=1974, width=172, height=55
  # 2k (2560x1440): x=2409, y=1314, width=105, height=37
  # 1080p (1920x1080): x=1807, y=986, width=78, height=27
  region:
    x: 3609
    y: 1974
    width: 172
    height: 55

# 执行动作
actions:
  # 动作序列
  # key: 按下的键。支持 'm', 'enter', 'up', 'down' 等（还支持很多其它的，但是卡CEO时用不到）
  # hold: 按下持续时长(秒)。默认0.1秒
  # delay: 每次按键后的延迟(秒)。默认0.05秒
  # times: 按键次数。默认1次
  sequence:
    - key: "m" # 打开菜单
      hold: 0.03
      delay: 0.18
    - key: "down" # 向下选择两次
      hold: 0.03
      delay: 0.06
      times: 2
    - key: "enter" # 连续确认三次
      hold: 0.03
      delay: 0.06
      times: 3
```

<details>
  <summary> toggle_key 支持的按键（点击展开）</summary>

- 功能键：`f1` ~ `f24`
- 单个字母或数字：`a`~`z`、`0`~`9`
- 特殊键：
  - `backspace`, `tab`, `enter`, `shift`, `ctrl`, `alt`, `pause`, `capslock`, `esc`, `space`
  - `pageup`, `pagedown`, `end`, `home`
  - `left`, `up`, `right`, `down`
  - `insert`, `delete`
- 小键盘：
  - 数字：`numpad0`~`numpad9` 或 `kp0`~`kp9`
  - 运算符：除号 `numpad_div`(`num_div`), 乘号 `numpad_mul`(`num_mul`), 减号 `numpad_sub`(`num_sub`), 加号 `numpad_add`(`num_add`), 小数点 `numpad_decimal`(`num_decimal`),

> 不区分大小写，例如 `F12` 和 `f12` 等价。

</details>

## 使用方法

1. 双击运行 `gtaol-ceo-helper.exe`。
2. 游戏中打开手机，选择快速加入，开始匹配差事。
3. 按你设置好的快捷键 (默认是`f12`) 开启监控。
4. 当匹配到差事并且已加入人数 >=2 时，程序会自动按键注册为 CEO。然后监控会停止，如需再次监控请按你设置好的快捷键重新开启。
5. 如果长时间匹配不到差事弹出了”注意“警告，或者匹配到差事之后秒进了，请手动退出来打开手机重新匹配。

## 定位 OCR 区域

如果需要定位 OCR 区域，可使用 `find_coords.exe` 辅助工具。

这是一个 [OCR 识别区域示例](assets/识别区域示例.png)，右下角的红色矩形是你需要手动定位的区域。

使用方法：首先进游戏匹配差事，像示例中那样匹配到差事后，全屏截图。运行 `find_coords.exe`，以全屏的方式打开这张截图，然后根据软件提示定位矩形识别区域区域。定位需要准确，不能太多（比如把左侧差事名称包含进去），也不能太少（注意”已加入人数”和“人数上限”这两个数都可能为两位数）。

## 注意

本程序会频繁获取屏幕截图，注册为 CEO 时会模拟键盘按键。这两个操作底层都是通过win32 API实现的。可能存在风险，介意勿用。

> 我个人认为风险不大，因为本程序没有任何直接读写游戏数据的操作（截图也是屏幕截图而不是获取游戏窗口画面）

## 相关推荐

### [QuellGTA](https://www.mageangela.cn/QuellGTA/)

建议搭配 QuellGTA（小红帽）一起用，用本程序卡完 CEO 进任务后利用小红帽一键卡单。
