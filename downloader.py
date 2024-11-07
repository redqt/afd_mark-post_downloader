from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.firefox.options import Options
import os
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pickle
import requests
from urllib.parse import unquote

def save_cookies(driver, path):
    """保存 cookies 到文件"""
    with open(path, 'wb') as file:
        pickle.dump(driver.get_cookies(), file)
    print("Cookies 已保存")

def load_cookies(driver, path):
    """从文件加载 cookies"""
    try:
        with open(path, 'rb') as file:
            cookies = pickle.load(file)
            for cookie in cookies:
                driver.add_cookie(cookie)
        print("Cookies 已加载")
        return True
    except Exception as e:
        print(f"加载 Cookies 失败: {e}")
        return False

# 设置 cookies 文件路径
cookies_file = "ifdian_cookies.pkl"

# 初始化浏览器配置
options = Options()
options.accept_insecure_certs = True
options.set_preference("browser.download.folderList", 2)
options.set_preference("browser.download.dir", r"D:\downloads")
options.set_preference("browser.helperApps.neverAsk.saveToDisk", 
    "application/zip,application/octet-stream,image/jpeg,application/vnd.ms-excel,application/pdf")

# 初始化浏览器
service = Service(GeckoDriverManager().install())
driver = webdriver.Firefox(service=service, options=options)

try:
    # 先访问网站主页（为了设置 cookies）
    driver.get("https://ifdian.net")
    
    # 检查是否存在已保存的 cookies
    if os.path.exists(cookies_file):
        # 加载 cookies
        load_cookies(driver, cookies_file)
        # 刷新页面
        driver.refresh()
        
        # 访问目标页面
        driver.get("https://ifdian.net/dashboard/mark-post")
        
        # 检查是否需要重新登录（可以通过检查页面标题或特定元素）
        if "登录" in driver.title:  # 根据实际登录页面特征修改
            print("Cookies 已过期，需要重新登录")
            # 等待手动登录
            input("请手动登录，完成后按回车继续...")
            # 保存新的 cookies
            save_cookies(driver, cookies_file)
    else:
        print("未找到已保存的 Cookies，请登录")
        # 等待手动登录
        input("请手动登录，完成后按回车继续...")
        # 保存 cookies
        save_cookies(driver, cookies_file)
    
    # 访问目标页面
    driver.get("https://ifdian.net/dashboard/mark-post")
    driver.implicitly_wait(10)
    
    # 等待页面加载
    wait = WebDriverWait(driver, 20)
    
    # 创建下载目录
    download_dir = "downloaded_videos"
    if not os.path.exists(download_dir):
        os.makedirs(download_dir)
    
    # 找到所有视频容器
    video_containers = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "vm-video-player")))
    print(f"\n找到 {len(video_containers)} 个视频")
    
    # 遍历每个视频容器
    for index, container in enumerate(video_containers, 1):
        try:
            # 在容器中找到视频元素
            video_element = container.find_element(By.TAG_NAME, "video")
            
            # 获取视频源地址
            video_src = video_element.get_attribute('src')
            
            # 获取视频标题
            try:
                title_element = container.find_element(By.XPATH, "../..//div[contains(@class, 'title')]")
                video_title = title_element.text.strip()
                # 清理文件名中的非法字符
                video_title = "".join(c for c in video_title if c.isalnum() or c in (' ', '-', '_'))
            except:
                video_title = f"video_{index}"
            
            print(f"\n视频 {index}:")
            print(f"标题: {video_title}")
            print(f"下载链接: {video_src}")
            
            # 下载视频
            if video_src:
                try:
                    print(f"正在下载: {video_title}")
                    response = requests.get(video_src, stream=True)
                    file_path = os.path.join(download_dir, f"{video_title}.mp4")
                    
                    # 获取文件大小
                    total_size = int(response.headers.get('content-length', 0))
                    
                    # 下载文件并显示进度
                    with open(file_path, 'wb') as f:
                        if total_size == 0:
                            f.write(response.content)
                        else:
                            downloaded = 0
                            for data in response.iter_content(chunk_size=4096):
                                downloaded += len(data)
                                f.write(data)
                                # 计算下载进度
                                progress = int(50 * downloaded / total_size)
                                print(f"\r下载进度: [{'=' * progress}{' ' * (50-progress)}] {downloaded}/{total_size} bytes", end='')
                    print(f"\n{video_title} 下载完成!")
                    
                except Exception as e:
                    print(f"下载视频时出错: {e}")
            
        except Exception as e:
            print(f"\n处理第 {index} 个视频时出错: {e}")
    
    print("\n所有视频下载完成!")
    input("按回车键退出...")
    
except Exception as e:
    print(f"发生错误: {e}")
    
finally:
    driver.quit()