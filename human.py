# %%
import json
import yaml
import os
import requests
import time
import base64
import cv2
import aria2p
import tkinter as tk
from tkinter import simpledialog
import concurrent.futures

# %%
# 读取配置文件
with open('config.yaml', 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

# 从配置文件中获取Aria2设置
aria2_host = config.get('aria2_host', 'http://localhost')
aria2_port = config.get('aria2_port', 6800)
aria2_secret = config.get('aria2_secret', '')
aria2 = aria2p.API(aria2p.Client(host=aria2_host, port=aria2_port, secret=aria2_secret))

# 从配置文件中获取base_dir
base_dir = config.get('base_dir')

# 从配置文件中获取PowerCreatorCMSAuthenticationID和platform_token
PowerCreatorCMSAuthenticationID = config.get('PowerCreatorCMSAuthenticationID')
platform_token = config.get('platform_token')

base_urls = {
    "in": config.get('base_urls_in'),
    "out": config.get('base_urls_out')
}

website = config.get('website_url')

# 如果PowerCreatorCMSAuthenticationID或platform_token未设置,则提示用户输入
if not PowerCreatorCMSAuthenticationID:
    PowerCreatorCMSAuthenticationID = input("请输入PowerCreatorCMSAuthenticationID: ")

if not platform_token:
    platform_token = input("请输入platform_token: ")

# 保存到cookies.txt
cookies = {
    "PowerCreatorCMSAuthenticationID": PowerCreatorCMSAuthenticationID,
    "platform_token": platform_token
}
with open("cookies.txt", "w") as f:
    json.dump(cookies, f)


def load_cookies():
    if os.path.exists("cookies.txt"):
        with open("cookies.txt", "r") as f:
            cookies = json.load(f)
        return cookies
    else:
        return None

# %%
def get_csrf_token():
    url = "https://buct.smartclass.cn/wechat.json?r=2021-01-29"
    response = requests.get(url)
    wechat_json = response.content.decode('utf-8-sig') 
    csrkKey = json.loads(wechat_json)["csrkKey"]

    t = int(time.time() * 1000)
    token = ""
    j = 1000000000000
    while j != 0:
        k = (t - t % j) // j
        token += csrkKey[k]
        t -= k * j
        j = j // 10
    return token

get_csrf_token()
def load_cookies():
    if os.path.exists("cookies.txt"):
        with open("cookies.txt", "r") as f:
            cookies = json.load(f)
        return cookies
    else:
        return None

def check_login(session):
    url = "https://buct.smartclass.cn/Permission/DataBoardPageList?csrkToken=" + get_csrf_token()
    response = session.get(url)
    if response.status_code == 200 and "登录" not in response.text:
        print("Login successful using saved cookies.")
        return True
    else:
        print("Login failed using saved cookies.")
        print(response.text)
        print(response.status_code)
        return False

def login():
    session = requests.Session()
    cookies = load_cookies()
    if cookies:
        session.cookies.update(cookies)
        if check_login(session):
            print("Login successful using saved cookies.")
            return session

    url = "https://buct.smartclass.cn/Login.aspx"
    response = session.get(url)
    verfycodejson = response.text
    random = str(int(time.time() * 1000000))
    random = str(float(random) * 0.0000001)
    url = f"https://buct.smartclass.cn/home/VerifyImage2?{random}"
    response = session.get(url)
    verfycodejson = response.text
    verfyimg = json.loads(verfycodejson)["Value"]["img"]
    verfycode = json.loads(verfycodejson)["Value"]["Code"]
    verfyimg = "data:image/png;base64," + verfyimg
    with open("verifyimg.png", "wb") as f:
        f.write(base64.b64decode(verfyimg.split(",")[1]))
    image = cv2.imread("verifyimg.png")
    cv2.imshow("Verification Code", image)
    root = tk.Tk()
    root.withdraw()
    code = simpledialog.askstring("Input Code", "Please enter the verification code:")
    cv2.destroyAllWindows()
    os.remove("verifyimg.png")

    url = "https://buct.smartclass.cn/Home/Login"
    data = {
        "UserName": "",
        "PassWord": "",
        "isRember": "true",
        "VerifyCode": code,
        "VerifyCodeId": verfycode,
        "redirectUri": ""
    }
    response = session.post(url, data=data)
    print(response.text)
    print(response.cookies.get_dict())
    if check_login(session):
        print(session.cookies.get_dict())
        print("Login successful.")
        cookies = response.cookies.get_dict()
        with open("cookies.txt", "w") as f:
            json.dump(cookies, f)
        # save to yaml
        config["PowerCreatorCMSAuthenticationID"] = cookies["PowerCreatorCMSAuthenticationID"]
        config["platform_token"] = cookies["platform_token"]
        with open('config.yaml', 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
        return session
    else:
        print("Login failed.")
        return None

def get_course_list():
    token = get_csrf_token()
    url = f"https://buct.smartclass.cn/WebApi/V1/video/GetCourseLists?csrkToken={token}&schoolId=289&order=&sort=StartTime&Source=&IsDeleted=false&IsProcessSuccess=&IsProcessing=&IsNeedLive=&CollectorID=&ViewerID=&IsPublic=&IsPublish=true&stopDate=&startDate=&ClassroomID=&CourseID=&organizationID=&StudentID=13248246&TeacherID=&NodeID=&titleKey=&pageNumber=1&pageSize=100&GradeID=&attribute=&type=0&ActivityID="
    response = session.get(url)
    course_list = json.loads(response.text)
    return course_list

def get_course_videos(course_info):
    token = get_csrf_token()
    # get needed information
    teacher_id = course_info["TeacherID"]
    course_id = course_info["CourseID"]
    user_id = course_info["UserID"]
    class_id = course_info["ClassID"]
    # get course video
    url = "https://buct.smartclass.cn/WebApi/V1/video/GetCourseVideos"
    data = {
        "ClassRoomId": "",
        "csrkToken": token,
        "pageSize": 100,
        "pageNumber": 1,
        "Sort": "StartTime",
        "order": 1,
        "IsDeleted": False,
        "ChapterTreeIDs": "",
        "TeacherID": teacher_id,
        "courseID": course_id,
        "userID": user_id,
        "classId": class_id,
        "type": 0,
        "IsPublish": True
    }
    response = session.post(url, data=data)
    video_list = json.loads(response.text)
    return video_list

def get_valid_url(base_url, replacements):
    """
    根据给定的 base_url 和替换规则,获取有效的视频 URL。

    Args:
        base_url (str): 基础 URL。
        replacements (list): 替换规则列表,每个元素都是一个元组,包含要替换的字符串和替换后的字符串。

    Returns:
        str: 有效的视频 URL,如果没有找到有效的 URL,则返回 None。
    """
    session = requests.Session()
    valid_urls = []

    for replacement in replacements:
        url_0 = base_url.replace(*replacement)
        url_1 = base_url.replace(*replacement[::-1])

        response_0 = session.head(url_0)
        response_1 = session.head(url_1)

        if (
            response_0.status_code == 200
            and response_0.headers.get("Content-Type") == "video/mp4"
            and "Content-Length" in response_0.headers
        ):
            valid_urls.append((url_0, int(response_0.headers["Content-Length"])))

        if (
            response_1.status_code == 200
            and response_1.headers.get("Content-Type") == "video/mp4"
            and "Content-Length" in response_1.headers
        ):
            valid_urls.append((url_1, int(response_1.headers["Content-Length"])))

    if valid_urls:
        return min(valid_urls, key=lambda x: x[1])[0]

    return None

def download_video(video_info):
    pic_url = video_info["PicUrl"]
    title = video_info["Title"]
    start_time = video_info["StartTime"]
    start_time = start_time.replace(":", "-").replace(" ", "_")[:-3][2:]
    # 实际上的下载路径是title第一个空格前的部分-第二个空格前的部分
    download_path = os.path.join(base_dir, title.split(" ")[0] + "-" + title.split(" ")[1])
    if not os.path.exists(download_path):
        os.makedirs(download_path)
   
    vga_file = os.path.join(download_path, start_time + ".VGA.mp4")
    video1_file = os.path.join(download_path, start_time + ".Video1.mp4")
    vga_aria2_file = os.path.join(download_path, start_time + ".VGA.mp4.aria2")
    video1_aria2_file = os.path.join(download_path, start_time + ".Video1.mp4.aria2")
    
    if (os.path.exists(vga_aria2_file)) or (os.path.exists(video1_aria2_file)):
        print(f"{title} already downloaded but not finished.")
        os.remove(vga_file)
        os.remove(vga_aria2_file)
        os.remove(video1_file)
        os.remove(video1_aria2_file)
    if os.path.exists(os.path.join(download_path, start_time + ".VGA.mp4")) and os.path.exists(os.path.join(download_path, start_time + ".Video1.mp4")):
        print(f"{title} already downloaded.")
        return
    vga_url = get_valid_url(pic_url.replace("000.jpg", "VGA.mp4"), [("/1/", "/0/")])
    video1_url = get_valid_url(pic_url.replace("000.jpg", "video1.mp4"), [("/1/", "/0/")])
    if vga_url:
        # download video
        print(f"Downloading {title}...")
        aria2.add_uris([vga_url], options={"dir": download_path, "out": start_time + ".VGA.mp4"})
    if video1_url:
        # download video
        print(f"Downloading {title}...")
        aria2.add_uris([video1_url], options={"dir": download_path, "out": start_time + ".Video1.mp4"})

def write_watch_list(video_infos):
    title = video_infos[0]["Title"]
    path = title.split(" ")[0] + "-" + title.split(" ")[1]
    with open(os.path.join(base_dir, path, title.split(" ")[0] + ".md"), "w", encoding="utf-8") as f:
        f.write("| StartTime | Video1 | VGA | Video1 | VGA |\n")
        f.write("| --- | --- | --- | --- | --- |\n")
        for video_info in video_infos:
            start_time = video_info["StartTime"]
            start_time = start_time.replace(":", "-").replace(" ", "_")[:-3][2:]
            vga_in_url = f"{base_urls['in']}/{path}/{start_time}_VGA.mp4"
            video1_in_url = f"{base_urls['in']}/{path}/{start_time}.Video1.mp4"
            vga_out_url = f"{base_urls['out']}/{path}/{start_time}_VGA.mp4"
            video1_out_url = f"{base_urls['out']}/{path}/{start_time}.Video1.mp4"
            subtitle_in_url = f"{base_urls['in']}/{path}/{start_time}.Video1.json"
            subtitle_out_url = f"{base_urls['out']}/{path}/{start_time}.Video1.json"
            base_url = website
            f.write(f"| {start_time} | [Video1]({base_url}?video={video1_in_url}&subtitle={subtitle_in_url}) | [VGA]({base_url}?video={vga_in_url}&subtitle={subtitle_in_url}) | [Video1]({base_url}?video={video1_out_url}&subtitle={subtitle_out_url}) | [VGA]({base_url}?video={vga_out_url}&subtitle={subtitle_out_url}) |\n")

    with open(os.path.join(base_dir, path, "index.html"), "w", encoding="utf-8") as f:
        f.write("<html><head><title>Watch List</title></head><body>")
        f.write("<table>")
        f.write("<tr><th>StartTime</th><th>Video1</th><th>VGA</th><th>Video1</th><th>VGA</th></tr>")
        for video_info in video_infos:
            start_time = video_info["StartTime"]
            start_time = start_time.replace(":", "-").replace(" ", "_")[:-3][2:]
            vga_in_url = f"{base_urls['in']}/{path}/{start_time}_VGA.mp4"
            video1_in_url = f"{base_urls['in']}/{path}/{start_time}.Video1.mp4"
            vga_out_url = f"{base_urls['out']}/{path}/{start_time}_VGA.mp4"
            video1_out_url = f"{base_urls['out']}/{path}/{start_time}.Video1.mp4"
            subtitle_in_url = f"{base_urls['in']}/{path}/{start_time}.Video1.json"
            subtitle_out_url = f"{base_urls['out']}/{path}/{start_time}.Video1.json"
            base_url = website
            f.write(f"<tr><td>{start_time}</td><td><a href='{base_url}?video={video1_in_url}&subtitle={subtitle_in_url}' target='_blank'>Video1</a></td><td><a href='{base_url}?video={vga_in_url}&subtitle={subtitle_in_url}' target='_blank'>VGA</a></td><td><a href='{base_url}?video={video1_out_url}&subtitle={subtitle_out_url}' target='_blank'>Video1</a></td><td><a href='{base_url}?video={vga_out_url}&subtitle={subtitle_out_url}' target='_blank'>VGA</a></td></tr>")
        f.write("</table>")
        f.write("</body></html>")


# %%
session = login()
course_list = get_course_list()
futures = []
for course_info in course_list["Value"]["Data"]:
    video_list = get_course_videos(course_info)
    write_watch_list(video_list["Value"]["Data"])

with concurrent.futures.ThreadPoolExecutor(max_workers=16) as executor:
    for course_info in course_list["Value"]["Data"]:
        video_list = get_course_videos(course_info)
        write_watch_list(video_list["Value"]["Data"])
        for video_info in video_list["Value"]["Data"]:
            future = executor.submit(download_video, video_info)
            futures.append(future)


