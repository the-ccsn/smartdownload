import json
import os
import requests
import datetime
import time
import random
import base64
import cv2
import pytesseract
import tkinter as tk
from tkinter import simpledialog

def login():
    # 获取验证码
    response = requests.get("https://buct.smartclass.cn/Login.aspx", headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36"})
    cookies = response.cookies.get_dict()
    verifycode_json = json.loads(response.text)

    # 显示验证码图片
    verifyimg = base64.b64decode(verifycode_json["Value"]["img"])
    with open("verifyimg.png", "wb") as f:
        f.write(verifyimg)
    image = cv2.imread("verifyimg.png")
    cv2.imshow("Verification Code", image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    # 输入验证码
    verifycode = pytesseract.image_to_string(image).strip()
    if not verifycode:
        verifycode = simpledialog.askstring("Input Code", "Please enter the verification code:")

    # 登录
    login_data = {
        "UserName": "",
        "PassWord": "",
        "isRember": "false",
        "VerifyCode": verifycode,
        "VerifyCodeId": verifycode_json["Value"]["Code"],
        "redirectUri": ""
    }
    response = requests.post("https://buct.smartclass.cn/Home/Login", data=login_data, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36"}, cookies=cookies)
    cookies.update(response.cookies.get_dict())
    return cookies

def get_csrf_token(cookies):
    # 获取 CSRF 令牌
    response = requests.get("https://buct.smartclass.cn/wechat.json?r=2021-01-29", headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36"}, cookies=cookies)
    csrkKey = json.loads(response.text)["csrkKey"]
    token = "".join(csrkKey[int((time.time() - time.time() % (10 ** i)) / (10 ** i))] for i in range(10, 0, -1))
    return token

def download_videos(cookies, token):
    # 获取课程列表
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    fromday = (datetime.datetime.now() - datetime.timedelta(days=36)).strftime("%Y-%m-%d")
    response = requests.get(f"https://buct.smartclass.cn/Webapi/V1/Video/GetMyVideoList?csrkToken={token}&TeacherName=&Sort=StartTime&TagID=&SyCommonKey=&StartDate={fromday}&EndDate={today}&Order=1&PageSize=100&PageNumber=1&attribute=&IncludePublic=", headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36"}, cookies=cookies)
    video_data = json.loads(response.text)

    # 下载视频
    total_count = video_data["TotalCount"]
    for i in range(total_count):
        cover = video_data["Data"][i]["Cover"]
        start_time = video_data["Data"][i]["StartTime"]
        course_name = video_data["Data"][i]["CourseName"]
        start_time_formatted = start_time.replace(":", "_")

        # 下载 VGA 视频
        vga_url = cover.replace("/1/", "/0/").replace("000.jpg", "VGA.mp4")
        if not os.path.exists(f"D:\\OvlerDrive\\OneDrive\\downloads\\{course_name}\\{start_time_formatted}_VGA.mp4"):
            response = requests.get(vga_url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36"}, cookies=cookies)
            with open(f"D:\\OvlerDrive\\OneDrive\\downloads\\{course_name}\\{start_time_formatted}_VGA.mp4", "wb") as f:
                f.write(response.content)

        # 下载 Video1 视频
        video1_url = cover.replace("/1/", "/0/").replace("000.jpg", "Video1.mp4")
        if not os.path.exists(f"D:\\OvlerDrive\\OneDrive\\downloads\\{course_name}\\Video1\\{start_time_formatted}_Video1.mp4"):
            response = requests.get(video1_url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36"}, cookies=cookies)
            if not os.path.exists(f"D:\\OvlerDrive\\OneDrive\\downloads\\{course_name}\\Video1"):
                os.makedirs(f"D:\\OvlerDrive\\OneDrive\\downloads\\{course_name}\\Video1")
            with open(f"D:\\OvlerDrive\\OneDrive\\downloads\\{course_name}\\Video1\\{start_time_formatted}_Video1.mp4", "wb") as f:
                f.write(response.content)
        time.sleep(0.1)

def get_live_streams(cookies, token):
    # 获取直播列表
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    fromday = (datetime.datetime.now() + datetime.timedelta(days=7)).strftime("%Y-%m-%d")
    response = requests.get(f"https://buct.smartclass.cn/Webapi/V1/Live/GetMyLiveList?csrkToken={token}&MajorUserID=&ClassroomID=&Sort=IsLiving%20desc%2CIsCompleted%2CStartTime&StartDate={today}&EndDate={fromday}&PageSize=50&PageNumber=1&attribute=&IncludePublic=true", headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36"}, cookies=cookies)
    live_data = json.loads(response.text)

    # 获取直播流信息
    total_count = live_data["TotalCount"]
    page2read = int(total_count * 0.02 + 1)
    vga_output = ["#EXTM3U"]
    for page in range(1, page2read + 1):
        response = requests.get(f"https://buct.smartclass.cn/Webapi/V1/Live/GetMyLiveList?csrkToken={token}&MajorUserID=&ClassroomID=&Sort=IsLiving%20desc%2CIsCompleted%2CStartTime&StartDate={today}&EndDate={fromday}&PageSize=50&PageNumber={page}&attribute=&IncludePublic=true", headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36"}, cookies=cookies)
        live_data = json.loads(response.text)
        for i in range(live_data["TotalCount"]):
            schedule_id = live_data["Data"][i]["ScheduleID"]
            title = live_data["Data"][i]["Title"]
            response = requests.post("https://buct.smartclass.cn/Live/GetLiveStreamInfo", data={"ScheduleId": schedule_id}, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36"}, cookies=cookies)
            stream_data = json.loads(response.text)
            vga = stream_data["Value"]["LanLiveMainRtmpSourceStreamNames"][0]
            video1 = stream_data["Value"]["LanLiveMainRtmpSourceStreamNames"][1]
            if vga and vga not in vga_output:
                vga_output.append(f"#EXTINF:-1,{title}_vga")
                vga_output.append(vga)
            if video1 and video1 not in vga_output:
                vga_output.append(f"#EXTINF:-1,{title}_video1")
                vga_output.append(video1)
        time.sleep(0.1)

    with open("vga.m3u", "w", encoding="utf-8") as f:
        f.write("\n".join(vga_output))

def main():
    cookies = login()
    token = get_csrf_token(cookies)
    download_videos(cookies, token)
    get_live_streams(cookies, token)

if __name__ == "__main__":
    main()
