#include <stdio.h>
#include <stdlib.h>
#include <windows.h>

static int is_vk_pressed(int vk_code) {
  return (GetAsyncKeyState(vk_code) & 0x8000) != 0;
}

static void enable_high_dpi_awareness(void) { SetProcessDPIAware(); }

static void get_cursor_position(LONG *x, LONG *y) {
  POINT point;

  if (GetPhysicalCursorPos(&point) || GetCursorPos(&point)) {
    *x = point.x;
    *y = point.y;
    return;
  }

  *x = 0;
  *y = 0;
}

static void wait_space(const char *record_prompt, LONG *x, LONG *y) {
  int was_pressed;
  int is_pressed;

  printf("%s\n", record_prompt);
  was_pressed = is_vk_pressed(VK_SPACE);

  for (;;) {
    get_cursor_position(x, y);
    printf("\r当前坐标: X=%8ld, Y=%8ld", *x, *y);
    fflush(stdout);

    is_pressed = is_vk_pressed(VK_SPACE);
    if (is_pressed && !was_pressed) {
      printf("\r已记录坐标: X=%ld, Y=%ld                \n", *x, *y);
      return;
    }

    was_pressed = is_pressed;
    Sleep(30);
  }
}

int main(void) {
  LONG left_top_x, left_top_y;
  LONG right_bottom_x, right_bottom_y;
  LONG left, top, width, height;

  enable_high_dpi_awareness();
  SetConsoleOutputCP(CP_UTF8);
  SetConsoleCP(CP_UTF8);

  printf("GTAOL Dre Helper - 识别区域定位工具\n");
  printf("--------------------------------\n");

  wait_space("请将鼠标移动到矩形识别区域左上角后按空格...", &left_top_x,
             &left_top_y);
  wait_space("\n请将鼠标移动到矩形识别区域右下角后按空格...", &right_bottom_x,
             &right_bottom_y);

  left = (left_top_x < right_bottom_x) ? left_top_x : right_bottom_x;
  top = (left_top_y < right_bottom_y) ? left_top_y : right_bottom_y;
  width = labs(right_bottom_x - left_top_x);
  height = labs(right_bottom_y - left_top_y);

  printf("--------------------------------\n");
  printf("识别区域左上角坐标: X=%ld, Y=%ld\n", left, top);
  printf("识别区域长宽: Width=%ld, Height=%ld\n", width, height);
  printf("--------------------------------\n");
  printf("x: %ld\ny: %ld\nwidth: %ld\nheight: %ld\n", left, top, width, height);
  printf("--------------------------------\n");
  printf("请将以上值填入 config.yaml\n");
  printf("\n按回车键退出...");
  fflush(stdout);
  getchar();

  return 0;
}
