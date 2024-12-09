
from datetime import time, datetime

# main.py
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.metrics import dp
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget
from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.progressbar import MDProgressBar
from kivymd.uix.screen import MDScreen
from kivy.uix.screenmanager import ScreenManager
from kivymd.uix.card import MDCard
from kivymd.uix.button import MDRectangleFlatButton
from kivymd.uix.gridlayout import MDGridLayout
import os

from networkx.algorithms.bipartite import color
from ultralytics import YOLO
import cv2

from kivymd.uix.dialog import MDDialog
from kivy.clock import Clock
from threading import Thread
from kivymd.uix.spinner import MDSpinner


import firebase_admin
from firebase_admin import credentials, storage, firestore


from WallDetect.result_screen import ResultScreen
from WallDetect.review_detail import ReviewDetailScreen
from WallDetect.review_screen import ReviewScreen

# Khởi tạo Firebase
cred = credentials.Certificate('serviceKey.json') #người dùng tự khởi tạo cơ sở dữ liệu. Project sử dụng firebase (storage,firestore)
firebase_admin.initialize_app(cred, {
    'storageBucket': 'xxxxxxxxxxxxx' #NGười dùng lấy key của mình
})

# Khởi tạo Firestore và Storage
db = firestore.client()
bucket = storage.bucket()


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

class CustomFileChooser(MDBoxLayout):
    def __init__(self, popup, main_screen, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.popup = popup
        self.main_screen = main_screen

        self.filechooser = FileChooserListView(multiselect=True)
        self.add_widget(self.filechooser)

        button_layout = MDBoxLayout(size_hint_y=None, height='50dp')
        button_layout.add_widget(MDRectangleFlatButton(text='Cancel', on_release=self.dismiss))
        button_layout.add_widget(MDRectangleFlatButton(text='Select', on_release=self.select_file))
        self.add_widget(button_layout)

    def select_file(self, instance):
        selected = self.filechooser.selection
        if selected:
            print(f'Selected files: {selected}')
            self.dismiss()
            self.main_screen.load_image(selected)

    def dismiss(self, *args):
        self.popup.dismiss()

class MainHomeScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.image_paths = []
        self.processed_image_paths = []
        self.model = self.load_yolo_model("E:\\KivyMD\\KivyT\\wall.pt")
        self.object_counts = { "dirty": 0, "crack": 0, "air bubbles": 0, "not uniform": 0, "peeling paint": 0 }
        self.object_areas = { "dirty": 0, "crack": 0, "air bubbles": 0, "not uniform": 0, "peeling paint": 0 }
        self.total_area = 0
        self.summary_status = None

        # Khởi tạo result_area
        self.result_area = self.create_result_area(size_hint_y=0.1)
        self.result_area.opacity = 0  # Ẩn result_area ban đầu

        # Các phần khác không thay đổi
        background_layout = ColoredBoxLayout(color=(1.0, 0.8, 0.9, 0.3))  # Màu xám nhẹ
        main_layout = MDBoxLayout(orientation='vertical', spacing=0)
        main_layout.add_widget(self.create_title(size_hint_y=0.1))
        main_layout.add_widget(self.create_note(size_hint_y=0.1))
        main_layout.add_widget(self.create_image_area(size_hint_y=0.475))
        main_layout.add_widget(self.create_upload_button(size_hint_y=0.075))
        main_layout.add_widget(self.result_area)  # Thêm result_area vào layout
        main_layout.add_widget(self.create_evaluate_area(size_hint_y=0.075))
        main_layout.add_widget(self.create_review_evaluate_area(size_hint_y=0.075))

        # Thêm main_layout vào layout chính
        # self.add_widget(main_layout)

        background_layout.add_widget(main_layout)
        self.add_widget(background_layout)

    def create_title(self, **kwargs):
        layout = ColoredBoxLayout(color=(0.678, 0.847, 0.902, 1), **kwargs)
        layout.add_widget(MDLabel(text="Đánh Giá Các Vấn Đề Của Tường",
                                  halign="center",
                                  theme_text_color="Primary",
                                  font_style='H5'
                                             ))
        return layout

    def create_note(self, **kwargs):
        # Tạo layout ColoredBox với nền trắng và padding bên trái và phải là 10dp
        layout = ColoredBoxLayout(color=(1, 1, 1, 1), padding=(10, 0), **kwargs)

        # Tạo nhãn với nội dung ghi chú
        note_label = MDLabel(
            text="Lưu ý: Áp dụng cho loại tường trơn. Ảnh nên chụp góc rộng để có đánh giá tổng quan",
            halign="left",  # Căn trái
            theme_text_color="Custom",  # Sử dụng tùy chỉnh
            text_color=(1, 0, 0, 1)  # Màu đỏ

        )

        # Thêm nhãn vào layout
        layout.add_widget(note_label)

        return layout

    def create_image_area(self, **kwargs):
        # Tạo ColoredBoxLayout với màu nền xám nhẹ
        background_layout = ColoredBoxLayout(color=(0.9, 0.9, 0.9, 0.7), **kwargs)  # Màu xám nhẹ

        self.image_area = MDGridLayout(cols=3, spacing=10, padding=10, size_hint_y=None)
        self.image_area.bind(minimum_height=self.image_area.setter('height'))

        # Thêm image_area vào background_layout
        scroll_view = ScrollView()
        scroll_view.add_widget(self.image_area)

        # Thêm ScrollView vào ColoredBoxLayout
        background_layout.add_widget(scroll_view)

        return background_layout


    def create_upload_button(self, **kwargs):
        layout = ColoredBoxLayout(color=(0.9, 0.9, 0.9, 0.4), padding=(20,0), **kwargs)
        upload_button = MDRectangleFlatButton(text="Chọn ảnh", on_release=self.open_filechooser)
        layout.add_widget(upload_button)
        return layout

    def create_result_area(self, **kwargs):
        layout = ColoredBoxLayout(color=(1.0, 1.0, 0.8, 0.8), padding=(60, 0), **kwargs)

        # Sử dụng FloatLayout để căn giữa
        float_layout = FloatLayout()

        horizontal_layout = MDBoxLayout(orientation='horizontal', spacing=10, size_hint_y=None, height='50dp')

        self.result_label = MDLabel(text="Kết quả đánh giá", halign="left", size_hint_x=0.5,
                                    theme_text_color="Custom",  # Sử dụng tùy chỉnh
                                    text_color=(1, 0, 0, 1),
                                    font_style='H6'
                                    # Màu đỏ
                                    )
        view_result_button = MDRectangleFlatButton(text="Xem kết quả chi tiết", on_release=self.go_to_results, size_hint_x=0.5
                                                   # md_bg_color=(1, 0, 0, 0),  # Màu nền đỏ
                                                   # text_color=(1, 0, 0, 1),  # Màu chữ trắng
                                                   # line_color=(1, 0, 0, 1),  # Màu viền đỏ
                                                   )

        horizontal_layout.add_widget(self.result_label)
        horizontal_layout.add_widget(view_result_button)

        # Căn giữa horizontal_layout trong FloatLayout
        horizontal_layout.pos_hint = {'center_x': 0.5, 'center_y': 0.5}

        float_layout.add_widget(horizontal_layout)
        layout.add_widget(float_layout)

        return layout

    def create_evaluate_area(self, **kwargs):
        # Thêm padding cho layout
        layout = ColoredBoxLayout(color=(0.9, 0.9, 0.9, 0.3), padding=(20, 20), **kwargs)

        # Tạo một FloatLayout để căn giữa
        center_layout = FloatLayout()

        # Tạo nút với viền và chữ xanh lá cây
        evaluate_button = MDRectangleFlatButton(
            text="Đánh giá",
            on_release=self.go_to_evaluate,
            size_hint=(None, None),
            size=(200, 50),
            md_bg_color=(1, 1, 1, 0),  # Nền trắng
            text_color=(0, 0.7, 0.3, 1),  # Màu chữ xanh lá cây
            line_color=(0, 0.7, 0.3, 1),  # Màu viền xanh lá cây
        )

        # Căn giữa nút và điều chỉnh vị trí
        evaluate_button.pos_hint = {'center_x': 0.06, 'center_y': 0.5}
        center_layout.add_widget(evaluate_button)
        layout.add_widget(center_layout)

        return layout

    def determine_summary_status(self):
        counts = self.object_counts
        if all(count == 0 for count in counts.values()):
            self.summary_status = "Cấp độ 1 (Tốt)"
        elif (counts["crack"] <= 10 and counts["dirty"] <= 10 and
              counts["air bubbles"] == 0 and counts["not uniform"] == 0):
            self.summary_status = "Cấp độ 2 (Khá)"
        elif (counts["crack"] <= 50 or counts["dirty"] <= 50 or
              counts["air bubbles"] > 0):
            self.summary_status = "Cấp độ 3 (Trung bình)"
        elif (counts["crack"] > 50 or counts["dirty"] > 50 or
              counts["air bubbles"] > 10 or counts["peeling paint"] > 10):
            self.summary_status = "Cấp độ 4 (Kém)"
        else:
            self.summary_status = "Cấp độ 5 (Rất kém)"

    def load_yolo_model(self, model_path):
        return YOLO(model_path)

    def go_to_evaluate(self, instance):
        self.show_progress_dialog()  # Hiển thị dialog

        # Tạo và chạy một luồng cho xử lý
        thread = Thread(target=self.evaluate_images)
        thread.start()

    def evaluate_images(self):
        self.process_images_with_yolo(self.image_paths)
        self.display_processed_images()
        self.display_object_counts_and_percentages()
        self.determine_summary_status()
        print(f"Trạng thái tổng hợp: {self.summary_status}")
        self.upload_and_save_images(self.image_paths, self.processed_image_paths)

        # Hiện result_area và cập nhật văn bản
        Clock.schedule_once(lambda dt: self.update_result_area())

        # Đóng dialog sau khi hoàn tất trong luồng chính
        Clock.schedule_once(lambda dt: self.dismiss_progress_dialog())

    def update_result_area(self):
        self.result_label.text += f" - {self.summary_status}"  # Cập nhật văn bản

        # Hiện result_area nếu chưa có
        if self.result_area.parent is None:
            self.add_widget(self.result_area)  # Thêm vào layout nếu chưa có

        self.result_area.opacity = 1  # Hiện result_area

    def show_progress_dialog(self):
        # Tạo dialog với layout tùy chỉnh
        self.dialog = MDDialog(
            type="custom",
            content_cls=MDBoxLayout(
                orientation='vertical',
                padding=[20, 20, 20, 20],
                spacing=10,
                md_bg_color=(0.1, 0.1, 0.1, 1)  # Nền tối
            )
        )

        # Tạo một layout mới để căn chỉnh spinner và tiêu đề
        layout = MDBoxLayout(orientation='horizontal', spacing=10, size_hint_y=None, height=dp(48), padding=(0, dp(10)))

        # Thêm MDSpinner
        spinner = MDSpinner(size_hint=(None, None), size=(dp(48), dp(48)))
        layout.add_widget(spinner)

        # Thêm một label để hiển thị tiêu đề
        title_label = MDLabel(
            text="Processing...",
            halign="center",
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1)  # Màu trắng
        )
        layout.add_widget(title_label)

        # Thêm layout vào dialog
        self.dialog.content_cls.add_widget(layout)

        # Thêm MDProgressBar vào dialog
        progress_bar = MDProgressBar()
        progress_bar.size_hint_y = None
        progress_bar.height = dp(10)
        progress_bar.md_bg_color = (0, 0.7, 0.3, 1)  # Màu xanh lá cây
        self.dialog.content_cls.add_widget(progress_bar)

        self.dialog.open()

    def dismiss_progress_dialog(self, *args):
        self.dialog.dismiss()

    def upload_and_save_images(self, original_image_paths, processed_image_paths):
        """Tải ảnh gốc và đã xử lý lên Firebase và lưu liên kết vào Firestore."""
        image_links = []  # Danh sách lưu trữ URL

        for image_path in original_image_paths:
            original_image_url = self.upload_image_to_firebase(image_path)
            image_links.append(original_image_url)

        for processed_image_path in processed_image_paths:
            processed_image_url = self.upload_image_to_firebase(processed_image_path)
            image_links.append(processed_image_url)

        self.save_image_links_to_firestore(image_links)

    def upload_image_to_firebase(self, image_path):
        """Tải ảnh lên Firebase Storage và trả về URL."""
        image_name = os.path.basename(image_path)
        blob = bucket.blob(f'images/{image_name}')
        blob.upload_from_filename(image_path)
        return blob.public_url

    def save_image_links_to_firestore(self, image_links):
        """Lưu danh sách liên kết ảnh vào Firestore cùng với các thông tin khác."""
        # Tạo ID với định dạng dd:mm:yyyy
        timestamp = datetime.now().strftime('%d:%m:%Y')  # Định dạng ngày
        session_data = {
            'id': timestamp,
            's_imgLink': image_links,
            'object_counts': self.object_counts,
            'object_percentages': self.calculate_area_percentages(),  # Tính phần trăm
            'summary_status': self.summary_status  # Trạng thái tổng hợp
        }

        # Lưu vào Firestore
        db.collection('Test').add(session_data)  # Thêm vào Firestore
        print("Save Success:", session_data)  # In ra thông tin đã lưu

    def process_images_with_yolo(self, image_paths):
        threshold = 0.1
        for image_path in image_paths:
            processed_image_path = self.yolo_process_image(image_path, threshold)
            self.processed_image_paths.append(processed_image_path)

    # def yolo_process_image(self, image_path, threshold):
    #     frame = cv2.imread(image_path)
    #     if frame is None:
    #         print(f"Không thể đọc ảnh: {image_path}")
    #         return None
    #
    #     height, width = frame.shape[:2]
    #     self.total_area += height * width
    #
    #     results = self.model(frame)[0]
    #
    #     for result in results.boxes.data.tolist():
    #         x1, y1, x2, y2, score, class_id = result
    #         if score > threshold:
    #             class_name = results.names[int(class_id)].lower()
    #
    #             if class_name in self.object_counts:
    #                 self.object_counts[class_name] += 1
    #                 bbox_area = (x2 - x1) * (y2 - y1)
    #                 self.object_areas[class_name] += bbox_area
    #
    #             cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 4)
    #             cv2.putText(frame, f"{class_name} {score:.2f}",
    #                         (int(x1), int(y1 - 10)),
    #                         cv2.FONT_HERSHEY_SIMPLEX, 1.3, (0, 255, 0), 3, cv2.LINE_AA)
    #
    #     output_image_path = os.path.join(os.path.dirname(image_path), f"processed_{os.path.basename(image_path)}")
    #     cv2.imwrite(output_image_path, frame)
    #     print(f"Đã lưu ảnh đã xử lý tại: {output_image_path}")
    #     return output_image_path
    #
    # def calculate_area_percentages(self):
    #     percentages = {}
    #     for object_type in self.object_areas:
    #         if self.total_area > 0:
    #             percentages[object_type] = (self.object_areas[object_type] / self.total_area) * 100
    #         else:
    #             percentages[object_type] = 0
    #     return percentages

    def yolo_process_image(self, image_path, threshold):
        frame = cv2.imread(image_path)
        if frame is None:
            print(f"Không thể đọc ảnh: {image_path}")
            return None

        height, width = frame.shape[:2]
        self.total_area += height * width

        results = self.model(frame)[0]

        for result in results.boxes.data.tolist():
            x1, y1, x2, y2, score, class_id = result
            if score > threshold:
                class_name = results.names[int(class_id)].lower()

                if class_name in self.object_counts:
                    self.object_counts[class_name] += 1
                    bbox_area = (x2 - x1) * (y2 - y1)


                cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 4)
                cv2.putText(frame, f"{class_name} {score:.2f}",
                            (int(x1), int(y1 - 10)),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.3, (0, 255, 0), 3, cv2.LINE_AA)

        output_image_path = os.path.join(os.path.dirname(image_path), f"processed_{os.path.basename(image_path)}")
        cv2.imwrite(output_image_path, frame)
        print(f"Đã lưu ảnh đã xử lý tại: {output_image_path}")
        return output_image_path

    def calculate_area_percentages(self):
        total_counts = sum(self.object_counts.values())
        percentages = {}

        for object_type in self.object_counts:
            if total_counts > 0:
                percentages[object_type] = (self.object_counts[object_type] / total_counts) * 100
            else:
                percentages[object_type] = 0

        return percentages

    def display_object_counts_and_percentages(self):
        percentages = self.calculate_area_percentages()
        for object_type, count in self.object_counts.items():
            self.object_areas[object_type] = percentages[object_type]#
            print(f"{object_type}: {count} - Diện tích chiếm: {percentages[object_type]:.2f}%")

    def create_review_evaluate_area(self, **kwargs):
        layout = ColoredBoxLayout(color=(0.9, 0.9, 0.9, 0.4), padding=(20, 0), **kwargs)

        # Tạo một FloatLayout để căn nút ở bên phải
        button_layout = FloatLayout(size_hint=(1, None), height='50dp')

        review_button = MDRectangleFlatButton(
            text="Xem lại các phiên trước",
            on_release=self.go_to_review,
            size_hint=(None, None),  # Đặt kích thước cụ thể cho nút
            size=(200, 50),  # Kích thước của nút
            md_bg_color=(1, 0.75, 0.8, 0),  # Màu nền hồng
            text_color=(1, 0, 0.5, 1),  # Màu chữ hồng đậm
            line_color=(1, 0, 0.5, 1),  # Màu viền hồng
        )

        # Căn giữa nút bên phải
        review_button.pos_hint = {'center_x': 0.115, 'center_y': 0.5}

        button_layout.add_widget(review_button)
        layout.add_widget(button_layout)

        return layout

    def go_to_review(self, instance):
        app = MDApp.get_running_app()
        app.root.current = 'review'

    def go_to_results(self, instance):
        app = MDApp.get_running_app()

        # Truyền dữ liệu đến ResultScreen
        result_screen = app.root.get_screen('result')  # Giả sử bạn đã thêm ResultScreen vào App
        result_screen.update_results(
            original_images=self.image_paths,  # Đường dẫn ảnh gốc
            processed_images=self.processed_image_paths,  # Đường dẫn ảnh đã xử lý
            object_counts=self.object_counts,  # Số lượng các đối tượng
            object_areas = self.object_areas, #% diện tích các đôối tượng
            summary_status=self.summary_status  # Trạng thái tổng hợp
        )


        app.root.current = 'result'

    def open_filechooser(self, instance):
        content = CustomFileChooser(popup=None, main_screen=self)
        popup = Popup(title="Choose Images", content=content, size_hint=(0.9, 0.9))
        content.popup = popup
        popup.open()

    def load_image(self, selection):
        if selection:
            for path in selection:
                try:
                    self.image_paths.append(path)
                    self.display_image(path)
                except Exception as e:
                    print(f"Error loading image: {e}")

    def display_image(self, path):
        card = MDCard(size_hint_y=None, height=200, orientation='vertical', elevation=8)
        img = Image(source=path, allow_stretch=True, keep_ratio=True)
        card.add_widget(img)
        self.image_area.add_widget(card)

    def display_processed_images(self):
        # Đảm bảo rằng việc cập nhật giao diện diễn ra trong luồng chính
        Clock.schedule_once(self._display_processed_images)

    def _display_processed_images(self, dt):
        self.image_area.clear_widgets()  # Xóa tất cả widget trong image_area
        for image_path in self.processed_image_paths:
            if image_path:
                self.display_image(image_path)
            # Gọi phương thức để hiển thị ảnh

class MyApp(MDApp):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(MainHomeScreen(name='main'))
        sm.add_widget(ResultScreen(name='result'))
        sm.add_widget(ReviewScreen(name='review'))
        sm.add_widget(ReviewDetailScreen(name='review_detail'))
        return sm

if __name__ == "__main__":
    MyApp().run()