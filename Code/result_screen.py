from kivy.uix.floatlayout import FloatLayout
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRectangleFlatButton
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.gridlayout import MDGridLayout
from kivy.graphics import Color, Rectangle
from kivy.uix.image import Image
import os

from kivymd.uix.scrollview import MDScrollView


class ColoredBoxLayout(MDBoxLayout):
    def __init__(self, color, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(*color)
            self.rect = Rectangle(pos=(0, 0), size=self.size)
        self.bind(size=self._update_rect, pos=self._update_rect)

    def _update_rect(self, instance, value):
        self.rect.pos = self.pos
        self.rect.size = self.size


class ResultScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = MDBoxLayout(orientation='vertical')

        layout.add_widget(self.create_title(size_hint_y=1 / 10))
        self.image_area = self.create_image_area(size_hint_y=5 / 10)
        layout.add_widget(self.image_area)
        self.detail_area = self.create_detail_area(size_hint_y=2 / 10)
        layout.add_widget(self.detail_area)
        self.result_area = self.create_result_area(size_hint_y=1 / 10)
        layout.add_widget(self.result_area)
        layout.add_widget(self.create_back_button_area(size_hint_y=1 / 10))

        self.add_widget(layout)

    def create_title(self, **kwargs):
        layout = ColoredBoxLayout(color=(1, 1, 0.7, 1), **kwargs)
        title_label = MDLabel(text="Kết Đánh Giá Chi Tiết", halign="center",font_style="H4", theme_text_color="Primary")
        layout.add_widget(title_label)
        return layout

    def create_image_area(self, **kwargs):
        layout = ColoredBoxLayout(color=(0.8, 0.8, 0.8, 1), **kwargs)

        # Tạo ScrollView
        scroll_view = MDScrollView()

        # Tạo GridLayout để chứa các card hình ảnh
        self.grid_layout = MDGridLayout(cols=2, spacing=10, padding=10, size_hint_y=None)
        self.grid_layout.bind(minimum_height=self.grid_layout.setter('height'))  # Để tự động điều chỉnh chiều cao

        scroll_view.add_widget(self.grid_layout)  # Thêm GridLayout vào ScrollView
        layout.add_widget(scroll_view)  # Thêm ScrollView vào layout chính

        return layout

    def create_detail_area(self, **kwargs):
        layout = ColoredBoxLayout(color=(0.68, 0.85, 0.90, 1),padding=(40,0), **kwargs)
        self.detail_label = MDLabel(text="", halign="left", theme_text_color="Primary")
        self.detail_label2 = MDLabel(text="", halign="left", theme_text_color="Primary")
        layout.add_widget(self.detail_label)
        layout.add_widget(self.detail_label2)
        return layout

    def create_result_area(self, **kwargs):
        layout = ColoredBoxLayout(color=(1.0, 1.0, 0.8, 1), **kwargs)
        self.result_label = MDLabel(text="", halign="center", font_style="H6",theme_text_color="Primary")
        layout.add_widget(self.result_label)
        return layout

    def create_back_button_area(self, **kwargs):
        layout = ColoredBoxLayout(color=(1, 1, 1, 1), **kwargs)

        # Tạo FloatLayout để căn giữa nút
        float_layout = FloatLayout()

        back_button = MDRectangleFlatButton(
            text="Quay lại",
            on_release=self.go_back,
            size_hint=(None, None),  # Đặt size_hint thành None để chỉ định kích thước
            size=(200, 50)  # Kích thước cụ thể cho nút
        )

        # Căn giữa nút
        back_button.pos_hint = {'center_x': 0.5, 'center_y': 0.5}

        float_layout.add_widget(back_button)
        layout.add_widget(float_layout)

        return layout

    def go_back(self, instance):
        app = MDApp.get_running_app()
        app.root.current = 'main'  # Quay lại trang có id 'main'

    def update_results(self, original_images, processed_images, object_counts, object_areas, summary_status):
        # Xóa các card hình ảnh cũ trước khi cập nhật
        self.grid_layout.clear_widgets()

        # Cập nhật hình ảnh gốc
        for img_path in original_images:
            self.add_image_card(img_path, "Hình ảnh gốc")

        # Cập nhật hình ảnh đã xử lý
        for img_path in processed_images:
            self.add_image_card(img_path, "Hình ảnh đã xử lý")

        # Cập nhật thông tin chi tiết
        details = "\n".join([f"{obj}: {count}" for obj, count in object_counts.items()])
        self.detail_label.text = f"Số lượng:\n{details}"
        details2 = "\n".join([f"{obj}: {count}%" for obj, count in object_areas.items()])
        self.detail_label2.text = f"Tỷ lệ phần trăm:\n{details2}"

        # Cập nhật trạng thái tổng hợp
        self.result_label.text = f"Kết quả: {summary_status}"

    def add_image_card(self, image_path, title):
        if not isinstance(image_path, str):
            print(f"Đường dẫn hình ảnh không hợp lệ: {image_path}")
            return

        if not os.path.exists(image_path):
            print(f"Tệp hình ảnh không tồn tại: {image_path}")
            return

        card = MDCard(size_hint_y=None, height='200dp', padding=10)
        card_layout = MDBoxLayout(orientation='vertical')

        # Thêm tiêu đề cho card
        title_label = MDLabel(text=title, halign="center", theme_text_color="Primary")
        card_layout.add_widget(title_label)

        # Thêm hình ảnh
        img = Image(source=image_path, allow_stretch=True, keep_ratio=True)
        card_layout.add_widget(img)

        card.add_widget(card_layout)
        self.grid_layout.add_widget(card)  # Thêm card vào GridLayout


# Chạy ứng dụng (nếu cần thiết)
if __name__ == "__main__":
    class TestApp(MDApp):
        def build(self):
            return ResultScreen()


    TestApp().run()