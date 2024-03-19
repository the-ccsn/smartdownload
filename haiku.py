import requests
import os
import datetime
import time

# Login
url = "https://buct.smartclass.cn/Login.aspx"
response = requests.get(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36"})
resp_cookies = response.cookies

# Get verification code
random_num = int(str(int(time.time() * 1000000000)) * 0.0000001)
verify_code_url = f"https://buct.smartclass.cn/home/VerifyImage2?{random_num}"
response = requests.get(verify_code_url, cookies=resp_cookies, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36"})
verify_code_json = response.text
verify_code_img = response.content.decode("base64")
verify_code = input("Input verification code: ")

# Login
login_url = "https://buct.smartclass.cn/Home/Login"
login_data = {
    "UserName": "",
    "PassWord": "",
    "isRember": "false",
    "VerifyCode": verify_code,
    "VerifyCodeId": verify_code_json["Code"],
    "redirectUri": ""
}
response = requests.post(login_url, data=login_data, cookies=resp_cookies, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36"})
login_return = response.text

# Get CSRF token
wechat_url = "https://buct.smartclass.cn/wechat.json?r=2021-01-29"
response = requests.get(wechat_url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36"})
wechat_json = response.text
csrf_key = wechat_json["csrkKey"]
token = "".join([csrf_key[int((time.time() - time.time() % i) / i)] for i in [1000000000000, 100000000000, 10000000000, 1000000000, 100000000, 10000000, 1000000, 100000, 10000, 1000, 100, 10]])

# Get video list
today = (datetime.datetime.now() - datetime.timedelta(days=36)).strftime("%Y-%m-%d")
from_day = (datetime.datetime.now() - datetime.timedelta(days=14)).strftime("%Y-%m-%d")
video_list_url = f"https://buct.smartclass.cn/Webapi/V1/Video/GetMyVideoList?csrkToken={token}&TeacherName=&Sort=StartTime&TagID=&SyCommonKey=&StartDate={from_day}&EndDate={today}&Order=1&PageSize=100&PageNumber=1&attribute=&IncludePublic="
response = requests.get(video_list_url, cookies=resp_cookies, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36"})
video_list = response.text
covers = [item.split("?")[0] for item in response.json()["Data"]["Cover"]]
start_times = response.json()["Data"]["StartTime"]
total_count = response.json()["TotalCount"]
course_names = response.json()["Data"]["CourseName"]

# Process video list
output_vga = ["#EXTM3U"]
output_video1 = ["#EXTM3U"]
for i in range(total_count):
    cover = covers[i]
    start_time = start_times[i].replace(":", "_")
    course_name = course_names[i]

    vga_path = f"D:\\OvlerDrive\\OneDrive\\downloads\\{course_name}\\{start_time}_VGA.mp4"
    if not os.path.exists(vga_path):
        response = requests.post("http://localhost:16800/jsonrpc", json={
            "jsonrpc": "2.0",
            "method": "aria2.addUri",
            "id": "QXJpYU5nXzE2NDY4MzM4NDJfMC4zNDc3MTcxOTgzNTA1NDQ1",
            "params": [[cover.replace("000.jpg", "VGA.mp4")], {"out": f"{course_name}/{start_time}_VGA.mp4"}]
        })

    video1_path = f"D:\\OvlerDrive\\OneDrive\\downloads\\{course_name}\\Video1\\{start_time}_Video1.mp4"
    if not os.path.exists(video1_path):
        response = requests.post("http://localhost:16800/jsonrpc", json={
            "jsonrpc": "2.0",
            "method": "aria2.addUri",
            "id": "QXJpYU5nXzE2NDY4MzM4NDJfMC4zNDc3MTcxOTgzNTA1NDQ1",
            "params": [[cover.replace("000.jpg", "Video1.mp4")], {"out": f"{course_name}/Video1/{start_time}_Video1.mp4"}]
        })

    if cover.replace("000.jpg", "VGA.mp4") not in output_vga:
        output_vga.append(f"#EXTINF:-1,{course_name}_vga")
        output_vga.append(cover.replace("000.jpg", "VGA.mp4"))
    if cover.replace("000.jpg", "Video1.mp4") not in output_video1:
        output_video1.append(f"#EXTINF:-1,{course_name}_video1")
        output_video1.append(cover.replace("000.jpg", "Video1.mp4"))
    time.sleep(0.1)

# Save playlists
with open("E:\\Video\\smartclass\\vga.m3u", "w", encoding="utf-8") as f:
    f.write("\n".join(output_vga))

with open("E:\\Video\\smartclass\\video1.m3u", "w", encoding="utf-8") as f:
    f.write("\n".join(output_video1))
