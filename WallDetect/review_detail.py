import urllib

from kivy.graphics import Color, Rectangle
from kivy.uix.floatlayout import FloatLayout
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRectangleFlatButton
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.scrollview import MDScrollView
from kivy.uix.image import Image, AsyncImage
from firebase_admin import firestore


class ColoredBoxLayout(MDBoxLayout):
    def __init__(self, color, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(*color)
            self.rect = Rectangle(size=self.size, pos=self.pos)

        self.bind(size=self._update_rect, pos=self._update_rect)

    def _update_rect(self, instance, value):
        self.rect.pos = self.pos
        self.rect.size = self.size


class ReviewDetailScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = MDBoxLayout(orientation='vertical')

        layout.add_widget(self.create_title(size_hint_y=1 / 10))
        self.image_area = self.create_image_area(size_hint_y=4.5 / 10)
        layout.add_widget(self.image_area)
        self.detail_area = self.create_detail_area(size_hint_y=2.5 / 10)
        layout.add_widget(self.detail_area)
        self.result_area = self.create_result_area(size_hint_y=1 / 10)
        layout.add_widget(self.result_area)
        layout.add_widget(self.create_back_button_area(size_hint_y=1 / 10))

        self.add_widget(layout)

    def create_title(self, **kwargs):
        layout = ColoredBoxLayout(color=(1, 1, 1, 1), **kwargs)
        self.title_label = MDLabel(text="Lịch Sử Kết Quả Đánh Giá Chi Tiết",
        font_style="H5",halign="center", theme_text_color="Primary")
        layout.add_widget(self.title_label)
        return layout

    def create_image_area(self, **kwargs):
        layout = ColoredBoxLayout(color=(0.8, 0.8, 0.8, 1), **kwargs)  # Màu xám nhẹ

        # Tạo ScrollView
        scroll_view = MDScrollView()

        # Tạo GridLayout để chứa các card hình ảnh
        self.grid_layout = MDGridLayout(cols=2, spacing=10, padding=10, size_hint_y=None)
        self.grid_layout.bind(minimum_height=self.grid_layout.setter('height'))  # Để tự động điều chỉnh chiều cao

        scroll_view.add_widget(self.grid_layout)  # Thêm GridLayout vào ScrollView
        layout.add_widget(scroll_view)  # Thêm ScrollView vào layout chính

        return layout

    def create_detail_area(self, **kwargs):
        layout = ColoredBoxLayout(color=(0.68, 0.85, 0.90, 1),padding=(30,0), **kwargs)
        self.detail_label = MDLabel(text="", halign="left", theme_text_color="Primary")
        self.detail_label2 = MDLabel(text="", halign="left", theme_text_color="Primary")
        layout.add_widget(self.detail_label)
        layout.add_widget(self.detail_label2)
        return layout

    def create_result_area(self, **kwargs):
        layout = ColoredBoxLayout(color=(1.0, 1.0, 0.8, 1), **kwargs)  # Màu vàng nhạt
        self.result_label = MDLabel(text="", halign="center", font_style="H6" ,theme_text_color="Primary")
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
        app.root.current = 'review'  # Quay lại màn hình đánh giá

    def normalize_url(self, original_url):
        if not isinstance(original_url, str):
            return ''  # Trả về chuỗi rỗng nếu không phải là chuỗi

        # Tách thành phần của URL
        parts = original_url.split('/')

        # Lấy tên bucket
        bucket_name = parts[2]  # lemond-5d8af.appspot.com

        # Lấy đường dẫn tệp
        file_path = '/'.join(parts[4:])  # imgBadLemon/screenshot_bad_4150.png

        # Mã hóa đường dẫn tệp
        encoded_file_path = urllib.parse.quote(file_path, safe='')  # Mã hóa tất cả, không giữ lại ký tự an toàn

        # Thay thế ký tự '/' bằng '%2F'
        encoded_file_path = encoded_file_path.replace('/', '%2F')

        # Tạo URL chuẩn hóa
        normalized_url = f"https://firebasestorage.googleapis.com/v0/b/lemonde-5d8af.appspot.com/o/{encoded_file_path}?alt=media"

        return normalized_url

    def load_review_details(self, review_id):
        # Tải chi tiết đánh giá từ Firestore
        try:
            review_ref = firestore.client().collection('Test').document(review_id)
            review = review_ref.get()
            if review.exists:
                review_data = review.to_dict()
                self.title_label.text += f" - {review_data.get('id', 'Không có trạng thái.')}"

                # Lấy object_counts và object_percentages
                object_counts = review_data.get('object_counts', {})
                object_percentages = review_data.get('object_percentages', {})

                # Tạo chuỗi mô tả cho object_counts
                counts_details = "\n".join([f"{obj}: {count}" for obj, count in object_counts.items()])
                percentages_details = "\n".join([f"{obj}: {percentage}%" for obj, percentage in object_percentages.items()])

                # Cập nhật label với thông tin chi tiết
                self.detail_label.text = f"Số lượng:\n{counts_details}\n"
                self.detail_label2.text = f"Tỷ lệ phần trăm:\n{percentages_details}\n"

                # Lấy hình ảnh từ trường s_linkImg
                s_link_img = review_data.get('s_imgLink', None)

                # Kiểm tra kiểu dữ liệu của s_link_img
                if isinstance(s_link_img, str) and s_link_img:  # Nếu là chuỗi và không rỗng
                    image_paths = s_link_img.split(',')
                    normalized_paths = [self.normalize_url(img_path.strip()) for img_path in image_paths]
                    self.update_images(normalized_paths)
                elif isinstance(s_link_img, list):  # Nếu là danh sách
                    normalized_paths = [self.normalize_url(img_path) for img_path in s_link_img]
                    self.update_images(normalized_paths)
                else:
                    self.detail_label.text += "\nKhông có hình ảnh để hiển thị."

                # Cập nhật trạng thái tổng hợp
                summary_status = review_data.get('summary_status', 'Không có trạng thái.')
                self.result_label.text = f"Kết quả: {summary_status}"
            else:
                self.detail_label.text = "Không tìm thấy đánh giá!"
                self.result_label.text = ""
        except Exception as e:
            self.detail_label.text = "Lỗi khi tải chi tiết đánh giá!"
            self.result_label.text = str(e)

    def update_images(self, image_paths):
        self.grid_layout.clear_widgets()  # Xóa các hình ảnh hiện tại
        for img_path in image_paths:
            img = AsyncImage(source=img_path, allow_stretch=True, size_hint=(1, None), height='200dp')
            self.grid_layout.add_widget(img)  # Thêm AsyncImage vào GridLayout