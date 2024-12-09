from kivy.uix.floatlayout import FloatLayout
from kivymd.uix.screen import MDScreen
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRectangleFlatButton
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.scrollview import MDScrollView
from kivy.graphics import Color, Rectangle
from kivymd.app import MDApp
from firebase_admin import firestore

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

class ReviewScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = MDBoxLayout(orientation='vertical')

        layout.add_widget(self.create_title(size_hint_y=1/10))
        self.content_area = self.create_content(size_hint_y=8/10)
        layout.add_widget(self.content_area)
        layout.add_widget(self.create_back_button_area(size_hint_y=1/10))

        self.add_widget(layout)

        # Load reviews from Firestore
        self.load_reviews()

    def create_title(self, **kwargs):
        layout = ColoredBoxLayout(color=(1, 1, 0.7, 1), **kwargs)
        title_label = MDLabel(text="Lịch Sử Đánh Giá", halign="center",
                              font_style="H5",theme_text_color="Primary")
        layout.add_widget(title_label)
        return layout

    def create_content(self, **kwargs):
        layout = ColoredBoxLayout(color=(0.8, 0.8, 0.8, 1), **kwargs)  # Màu xám nhẹ

        # Create ScrollView
        scroll_view = MDScrollView()
        self.card_layout = MDBoxLayout(orientation='vertical', padding=10, spacing=10, size_hint_y=None)
        self.card_layout.bind(minimum_height=self.card_layout.setter('height'))  # Auto adjust height

        scroll_view.add_widget(self.card_layout)  # Add layout containing cards to ScrollView
        layout.add_widget(scroll_view)  # Add ScrollView to main layout
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
        # Go back to MainHomeScreen
        app = MDApp.get_running_app()
        app.root.current = 'main'  # Go back to the screen with id 'main'

    def load_reviews(self):
        try:
            reviews_ref = firestore.client().collection('Test')
            reviews = reviews_ref.get()

            if not reviews:
                no_data_label = MDLabel(text="Không có đánh giá nào!", halign="center")
                self.card_layout.add_widget(no_data_label)
                return

            for index, review in enumerate(reviews, start=1):
                self.add_review_card(index, review.id ,review.to_dict().get('id', ''), review.to_dict().get('summary_status', ''))

        except Exception as e:
            error_label = MDLabel(text=f"Lỗi khi tải dữ liệu: {e}", halign="center", theme_text_color="Error")
            self.card_layout.add_widget(error_label)

    def add_review_card(self, index,id_doc ,review_id, summary_status):
        card = MDCard(size_hint_y=None, height='120dp', padding=10)
        card_layout = MDBoxLayout(orientation='horizontal', padding=10, spacing=10)

        # Layout cho nội dung bên trái
        content_layout = MDBoxLayout(orientation='vertical', size_hint_x=0.8, padding=10,
                                     spacing=10)  # Thêm spacing ở đây

        # Hiển thị STT, ID, và summary status
        index_label = MDLabel(text=f"STT: {index}", halign="left")
        id_label = MDLabel(text=f"Ngày: {review_id}", halign="left")
        summary_label = MDLabel(text=f"Kết quả đánh giá: {summary_status}", halign="left")

        content_layout.add_widget(index_label)
        content_layout.add_widget(id_label)
        content_layout.add_widget(summary_label)

        # Nút "Xem" bên phải, căn giữa
        button_layout = MDBoxLayout(orientation='vertical', size_hint_x=None, size=(100, 120), padding=10)
        view_button = MDRectangleFlatButton(
            text="Xem",
            on_release=lambda x: self.view_review(id_doc),
            size_hint=(1, None),
            height='40dp'  # Chiều cao của nút
        )

        # Căn giữa nút trong layout
        button_layout.add_widget(view_button)
        button_layout.add_widget(MDLabel())  # Thêm thêm một label trống để căn giữa

        # Thêm layout nội dung và nút vào card
        card_layout.add_widget(content_layout)
        card_layout.add_widget(button_layout)

        card.add_widget(card_layout)
        self.card_layout.add_widget(card)

    def view_review(self, review_id):
        app = MDApp.get_running_app()
        app.root.current = 'review_detail'  # Chuyển đến màn hình chi tiết đánh giá
        app.root.get_screen('review_detail').load_review_details(review_id)  # Tải chi tiết đánh giá

# Main App Class
class MyApp(MDApp):
    def build(self):
        return ReviewScreen()  # Replace with your main screen setup

if __name__ == '__main__':
    MyApp().run()