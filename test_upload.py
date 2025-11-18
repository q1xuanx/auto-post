import unittest
from appium import webdriver
from appium.options.android import UiAutomator2Options
from appium.webdriver.common.appiumby import AppiumBy

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import json
import os
import time

capabilities = dict(
    platformName="Android",
    automationName="uiautomator2",
    deviceName="Android",
    appPackage="com.google.android.apps.nexuslauncher",
    appActivity="com.google.android.apps.nexuslauncher.NexusLauncherActivity",
    noReset=True,
    language="en",
    locale="US",
)

appium_server_url = "http://localhost:4723"


def load_json_data(filename):
    # Lấy đường dẫn tuyệt đối của file JSON
    # Giả sử file JSON nằm cùng thư mục với file script Python
    base_dir = os.path.dirname(os.path.abspath(__file__))
    filepath = os.path.join(base_dir, filename)

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        print(f"Lỗi: KHÔNG TÌM THẤY file {filename}. Vui lòng kiểm tra đường dẫn.")
        return None
    except json.JSONDecodeError:
        print(f"Lỗi: File {filename} không phải là JSON hợp lệ.")
        return None


class TestAppium(unittest.TestCase):
    def setUp(self) -> None:
        self.driver = webdriver.Remote(
            appium_server_url,
            options=UiAutomator2Options().load_capabilities(capabilities),
        )

    def logout_and_cleanup(self) -> None:
        """
        Thực hiện luồng Logout và dọn dẹp tài khoản khỏi thiết bị.
        Các bước này được đặt trong try...except để đảm bảo luồng tiếp tục
        ngay cả khi một bước nào đó fail (vì đây là cleanup).
        """
        driver = self.driver
        print("\n--- BẮT ĐẦU LUỒNG LOGOUT VÀ CLEANUP ---")
        time.sleep(5)
        # 1. Click Menu Tab
        xpath_menu_tab = '//android.view.View[@content-desc="Menu, tab 6 of 6"]'
        try:
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((AppiumBy.XPATH, xpath_menu_tab))
            ).click()
            print("1. ✅ Click Menu tab.")
        except Exception:
            print("1. ⚠️ Không tìm thấy hoặc click được Menu tab. Tiếp tục...")

        # 2. CUỘN VÀ CLICK NÚT LOG OUT (Sử dụng SWIPE dự phòng)
        xpath_log_out_button = '//android.widget.Button[@content-desc="Log out"]'
        print("2. Đang tìm nút Log out bằng cách cuộn thủ công...")

        max_scrolls = 5  # Giới hạn số lần cuộn để tránh lặp vô hạn
        found = False

        try:
            for i in range(max_scrolls):
                try:
                    # 1. Cố gắng tìm nút Log out (Nút Log out có thể đã nằm sẵn trên màn hình)
                    log_out_element = driver.find_element(
                        AppiumBy.XPATH, xpath_log_out_button
                    )
                    found = True
                    break
                except Exception:
                    # 2. Nếu chưa tìm thấy: Thực hiện Swipe (Cuộn lên, từ dưới lên)

                    # Lấy kích thước màn hình
                    size = driver.get_window_size()
                    start_x = size["width"] * 0.5
                    start_y = size["height"] * 0.8  # Bắt đầu từ 80% chiều cao
                    end_y = size["height"] * 0.2  # Vuốt tới 20% chiều cao

                    # Thực hiện vuốt (cuộn)
                    driver.swipe(
                        start_x, start_y, start_x, end_y, 800
                    )  # 800ms duration
                    print(f"2a. Đã cuộn lần {i + 1}...")

                    time.sleep(1)  # Chờ 1 giây để nội dung mới tải

            if found:
                # 3. CLICK NÚT LOG OUT (Sau khi đã cuộn và tìm thấy)
                log_out_element = WebDriverWait(driver, 20).until(
                    EC.element_to_be_clickable((AppiumBy.XPATH, xpath_log_out_button))
                )
                log_out_element.click()
                print("2b. ✅ Đã cuộn và click nút Log out lần 1.")
            else:
                # Nếu cuộn 5 lần vẫn không thấy
                raise Exception("Nút Log out không hiển thị sau 5 lần cuộn.")

        except Exception as e:
            print(f"2. ⚠️ Lỗi khi cuộn hoặc click nút Log out: {e}. Tiếp tục...")

        # 3. Xử lý pop-up NOT NOW
        xpath_not_now = '//android.widget.Button[@resource-id="com.facebook.katana:id/(name removed)" and @text="NOT NOW"]'
        try:
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((AppiumBy.XPATH, xpath_not_now))
            ).click()
            print("3. ✅ Xử lý pop-up NOT NOW.")
        except TimeoutException:
            print("3. ⏭️ Không thấy pop-up NOT NOW. Bỏ qua.")
        except Exception:
            print("3. ⚠️ Lỗi khi click NOT NOW. Bỏ qua.")

        # 4. Nhấn Log out lần 2
        xpath_log_out_final = '//android.widget.Button[@resource-id="com.facebook.katana:id/(name removed)" and @text="LOG OUT"]'
        try:
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((AppiumBy.XPATH, xpath_log_out_final))
            ).click()
            print("4. ✅ Click nút LOG OUT lần 2.")
        except Exception:
            print("4. ⚠️ Không thể thực hiện Log out lần 2. Tiếp tục Cleanup...")

        # --- BẮT ĐẦU LUỒNG DỌN DẸP PROFILE (Sau khi Logout) ---

        # 5. Chờ và click Settings (sau khi logout thành công)
        xpath_settings = '//android.widget.Button[@content-desc="Settings"]/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.widget.ImageView'
        try:
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((AppiumBy.XPATH, xpath_settings))
            ).click()
            print("5. ✅ Click nút Settings.")
        except Exception:
            print("5. ⚠️ Không tìm thấy nút Settings. Tiếp tục...")

        # 6. Click "Remove profiles from this device"
        xpath_remove_profiles = (
            '//android.view.ViewGroup[@content-desc="Remove profiles from this device"]'
        )
        try:
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((AppiumBy.XPATH, xpath_remove_profiles))
            ).click()
            print("6. ✅ Click 'Remove profiles from this device'.")
        except Exception:
            print("6. ⚠️ Không tìm thấy 'Remove profiles'. Tiếp tục...")

        # 7. Click nút Remove profile
        xpath_remove_profile_btn = '//android.widget.Button[@content-desc="Remove Nhân Nhân, Remove"]/android.view.ViewGroup'
        try:
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located(
                    (AppiumBy.XPATH, xpath_remove_profile_btn)
                )
            ).click()
            print("7. ✅ Click nút Remove Profile cụ thể.")
        except Exception:
            print("7. ⚠️ Không tìm thấy nút Remove Profile cụ thể. Tiếp tục...")

        # 8. Click Remove (xác nhận)
        xpath_remove_confirm = (
            '//android.widget.Button[@content-desc="Remove"]/android.view.ViewGroup'
        )
        try:
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((AppiumBy.XPATH, xpath_remove_confirm))
            ).click()
            print("8. ✅ Click Remove (xác nhận).")
        except Exception:
            print("8. ⚠️ Không thấy nút xác nhận Remove. Kết thúc luồng Cleanup.")

        print("--- KẾT THÚC LUỒNG LOGOUT VÀ CLEANUP ---")

    def tearDown(self) -> None:
        if self.driver:
            # self.logout_and_cleanup()
            self.driver.quit()

    def test_find_apps(self) -> None:
        el = self.driver.find_element(
            AppiumBy.ACCESSIBILITY_ID,
            "Facebook",
        )
        el.click()
        have_account_button = '//android.widget.Button[@content-desc="I already have an account"]/android.view.ViewGroup'

        try:
            acc_button = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((AppiumBy.XPATH, have_account_button))
            )
            acc_button.click()
        except TimeoutException:
            pass

        account_data = load_json_data("accounts.json")
        groups_data = load_json_data("groups.json")

        for acc_index, account in enumerate(account_data):
            username = account["username"]
            password = account["password"]

            print(
                f"\n--- BẮT ĐẦU TEST VỚI TÀI KHOẢN: {username} ({acc_index + 1}/{len(account_data)}) ---"
            )

            # Định nghĩa XPath cho các trường nhập liệu và nút Đăng nhập
            xpath_username = (
                '//android.widget.EditText[@content-desc="Mobile number or email,"]'
            )
            xpath_password = '//android.widget.EditText[@content-desc="Password,"]'
            # Sửa lại XPath để đảm bảo click vào phần tử bên trong (ViewGroup)
            xpath_login_button = (
                '//android.widget.Button[@content-desc="Log in"]/android.view.ViewGroup'
            )

            try:
                # Nhập Tài khoản (chờ 10s)
                username_field = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((AppiumBy.XPATH, xpath_username))
                )
                username_field.send_keys(username)

                # Nhập Mật khẩu
                self.driver.find_element(AppiumBy.XPATH, xpath_password).send_keys(
                    password
                )

                # Click Đăng nhập
                self.driver.find_element(AppiumBy.XPATH, xpath_login_button).click()
                print("✅ Đã nhập thông tin và click nút Đăng nhập.")

            except TimeoutException:
                self.fail(
                    "Lỗi: Không tìm thấy các trường nhập liệu Đăng nhập (Timeout)."
                )
            except Exception as e:
                self.fail(f"Lỗi khi nhập/click Đăng nhập: {e}")

            # 4. Chờ màn hình chính xuất hiện (Điều kiện chờ đăng nhập thành công)
            # Đây là bước quan trọng để đảm bảo bạn đã thoát khỏi màn hình đăng nhập.

            for group_index, group in enumerate(groups_data):
                print(f"===> Test voi group thu: {group_index}")

                xpath_homepage = '(//android.widget.FrameLayout[@resource-id="android:id/content"])[1]'
                print("Đang chờ màn hình chính xuất hiện (sau đăng nhập)...")

                try:
                    WebDriverWait(self.driver, 40).until(
                        EC.presence_of_element_located((AppiumBy.XPATH, xpath_homepage))
                    )
                    print("✅ Màn hình chính đã tải xong.")
                except TimeoutException:
                    self.fail(
                        "Lỗi: Màn hình chính không tải kịp sau 40 giây (Đăng nhập thất bại?)."
                    )

                # 5. Click vào nút Tìm kiếm (Search Facebook)
                xpath_search_button = '//android.widget.Button[@content-desc="Search"]'
                print("Đang tìm nút Tìm kiếm...")

                try:
                    # THÊM EXPLICIT WAIT CHO NÚT TÌM KIẾM
                    search_button = WebDriverWait(self.driver, 20).until(
                        EC.presence_of_element_located(
                            (AppiumBy.XPATH, xpath_search_button)
                        )
                    )
                    search_button.click()
                    print("✅ Đã click vào nút Tìm kiếm.")
                except TimeoutException:
                    # Sẽ báo lỗi nếu không tìm thấy trong 15s
                    self.fail("Lỗi: Không tìm thấy nút 'Search Facebook' sau 15 giây.")

                # 6. Chọn vào thanh tìm kiếm và nhập liệu
                xpath_search_input = '//android.widget.EditText[@resource-id="com.facebook.katana:id/(name removed)"]'
                text_to_search = group

                try:
                    # Nên chờ một chút vì đôi khi thanh tìm kiếm cần thời gian để hiển thị
                    search_input = WebDriverWait(self.driver, 40).until(
                        EC.presence_of_element_located(
                            (AppiumBy.XPATH, xpath_search_input)
                        )
                    )
                    search_input.send_keys(text_to_search)
                    print(f"✅ Đã nhập nội dung tìm kiếm: '{text_to_search}'")

                    # 3. NHẤN PHÍM ENTER để thực hiện tìm kiếm
                    self.driver.press_keycode(66)
                    print("✅ Đã nhấn Keycode 66 (Enter/Search) để bắt đầu tìm kiếm.")

                except TimeoutException:
                    self.fail(
                        "Lỗi: Không tìm thấy thanh nhập liệu tìm kiếm (EditText)."
                    )

                    # 6. Chờ màn hình kết quả tìm kiếm tải xong
                # Bạn muốn chờ phần tử gốc này, nhưng ta nên chờ phần tử cụ thể hơn trên trang kết quả.
                # Tuy nhiên, nếu bạn tin tưởng vào XPath này, ta sẽ dùng nó:
                xpath_search_result_page = (
                    '//android.widget.FrameLayout[@resource-id="android:id/content"]'
                )
                print("6. Đang chờ trang kết quả tìm kiếm...")
                try:
                    WebDriverWait(self.driver, 40).until(
                        EC.presence_of_element_located(
                            (AppiumBy.XPATH, xpath_search_result_page)
                        )
                    )
                    print("✅ Trang kết quả tìm kiếm đã tải xong.")
                except TimeoutException:
                    self.fail("Lỗi: Trang kết quả tìm kiếm không tải kịp.")

                # 7. Nhấn vào kết quả nhóm "Day la nhom de test"
                xpath_group_result = '//android.widget.Button[@content-desc="Day la nhom de test,Public · 2 members"]/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup/android.view.ViewGroup[1]'
                try:
                    group_link = WebDriverWait(self.driver, 20).until(
                        EC.presence_of_element_located(
                            (AppiumBy.XPATH, xpath_group_result)
                        )
                    )
                    group_link.click()
                    print("7. ✅ Đã nhấn vào nhóm 'Day la nhom de test'.")
                except TimeoutException:
                    self.fail("Lỗi: Không tìm thấy kết quả nhóm cần thiết.")

                # 8. Chọn "Write something..." để tạo bài viết
                xpath_write_something = (
                    '//android.view.ViewGroup[@content-desc="Write something..."]'
                )
                try:
                    write_box = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located(
                            (AppiumBy.XPATH, xpath_write_something)
                        )
                    )
                    write_box.click()
                    print("8. ✅ Đã nhấn vào 'Write something...'")
                except TimeoutException:
                    self.fail("Lỗi: Không tìm thấy ô 'Write something...'.")

                # 9. Nhập nội dung bài viết
                xpath_post_title = (
                    '//android.widget.EditText[@content-desc="Post Title"]'
                )
                post_content = "test test test 8888888"
                try:
                    post_input = WebDriverWait(self.driver, 20).until(
                        EC.presence_of_element_located(
                            (AppiumBy.XPATH, xpath_post_title)
                        )
                    )
                    post_input.send_keys(post_content)
                    print(f"9. ✅ Đã nhập nội dung bài viết: '{post_content}'.")
                except TimeoutException:
                    self.fail("Lỗi: Không tìm thấy trường nhập liệu bài viết.")

                # 10. Chọn ảnh (Photo/video)
                xpath_photo_button = (
                    '//android.widget.Button[@content-desc="Photo/video"]'
                )
                try:
                    self.driver.find_element(AppiumBy.XPATH, xpath_photo_button).click()
                    print("10. ✅ Đã nhấn nút 'Photo/video'.")
                except Exception:
                    self.fail("Lỗi: Không tìm thấy nút 'Photo/video'.")

                # 11. Chọn ảnh đầu tiên
                # LƯU Ý: XPath này rất dễ thay đổi (ngày/giờ chụp). Nếu thất bại, cần XPath chung hơn.
                xpath_first_photo = '//android.view.ViewGroup[@content-desc="Photo taken on Nov 16, 2025 13:57"]'
                try:
                    photo = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located(
                            (AppiumBy.XPATH, xpath_first_photo)
                        )
                    )
                    photo.click()
                    print("11. ✅ Đã chọn ảnh đầu tiên.")
                except TimeoutException:
                    self.fail("Lỗi: Không tìm thấy ảnh đầu tiên để chọn.")

                # 12. Nhấn nút POST
                xpath_post_final = '//android.widget.Button[@content-desc="POST"]'
                try:
                    WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located(
                            (AppiumBy.XPATH, xpath_post_final)
                        )
                    ).click()
                    print("12. ✅ Đã nhấn nút POST.")
                except TimeoutException:
                    self.fail("Lỗi: Không tìm thấy nút POST cuối cùng.")

                print("\n--- BẮT ĐẦU QUAY LẠI MÀN HÌNH CHÍNH ---")

                # 13. Quay lại màn hình chính bằng cách nhấn nút Back liên tục
                xpath_facebook_home_menu = (
                    '//android.view.View[@content-desc="Menu, tab 6 of 6"]'
                )
                max_back_presses = 5
                for i in range(max_back_presses):
                    try:
                        # Kiểm tra xem nút Menu Tab (trên News Feed) đã xuất hiện chưa
                        self.driver.find_element(
                            AppiumBy.XPATH, xpath_facebook_home_menu
                        )
                        print(f"13. ✅ Đã quay lại News Feed sau {i} lần nhấn Back.")
                        break  # Thoát khỏi vòng lặp nếu tìm thấy

                    except Exception:
                        # Nếu chưa thấy (vẫn đang ở màn hình con), nhấn nút Back
                        self.driver.back()

                        # Thêm độ trễ ngắn để đợi màn hình chuyển cảnh

                        time.sleep(1)
                        print(f"13. Đã nhấn Back lần {i + 1}...")

                    except Exception as e:
                        # Bắt các lỗi khác (ví dụ: session disconnect)
                        print(f"13. ⚠️ Lỗi không mong muốn trong khi nhấn Back: {e}")
                        break

                    if i == max_back_presses - 1:
                        print(
                            f"13. ⚠️ Đã vượt quá {max_back_presses} lần nhấn Back, không thể về News Feed."
                        )
            print("\n--- KỊCH BẢN TEST HOÀN THÀNH. BẮT ĐẦU LOGOUT TRONG tearDown ---")
            self.logout_and_cleanup()


if __name__ == "__main__":
    unittest.main()
