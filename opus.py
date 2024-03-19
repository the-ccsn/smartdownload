import requests
import json
import time
import os
import re

def main():
    # Login
    session = requests.Session()
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

    # TODO: Display the verification image and get user input for verfycode_ocr

    url = "https://buct.smartclass.cn/Home/Login"
    data = {
        "UserName": "",
        "PassWord": "",
        "isRember": "false",
        "VerifyCode": verfycode_ocr,
        "VerifyCodeId": verfycode,
        "redirectUri": ""
    }
    response = session.post(url, data=data)
    LOGINRETURN = response.text

    # CSRF token
    url = "https://buct.smartclass.cn/wechat.json?r=2021-01-29"
    response = session.get(url)
    wechat_json = response.text

    csrkKey = json.loads(wechat_json)["csrkKey"]

    t = int(time.time() * 1000)
    token = ""
    j = 1000000000000
    while j != 0:
        k = (t - t % j) // j
        token += csrkKey[k]
        t -= k * j
        j = j // 10

    # Get course information
    today = time.strftime("%Y-%m-%d")
    fromday = time.strftime("%Y-%m-%d", time.localtime(time.time() - 36 * 24 * 60 * 60))

    url = f"https://buct.smartclass.cn/Webapi/V1/Video/GetMyVideoList?csrkToken={token}&TeacherName=&Sort=StartTime&TagID=&SyCommonKey=&StartDate={fromday}&EndDate={today}&Order=1&PageSize=100&PageNumber=1&attribute=&IncludePublic="
    response = session.get(url)
    videolist = response.text

    Covers = json.loads(videolist)["Value"]["Data"]
    StartTimes = [item["StartTime"] for item in Covers]
    TotalCount = json.loads(videolist)["Value"]["TotalCount"]
    CourseName_list = [item["CourseName"] for item in Covers]

    for n in range(TotalCount):
        Cover = Covers[n]["Cover"].split("?")[0]
        VGA = Cover.replace("000.jpg", "VGA.mp4")
        Video1 = Cover.replace("000.jpg", "Video1.mp4")
        CourseName = CourseName_list[n]
        StartTime = StartTimes[n].replace(":", "_")

        if not os.path.exists(f"D:\\OvlerDrive\\OneDrive\\downloads\\{CourseName}\\{StartTime}_VGA.mp4"):
            url = "http://localhost:16800/jsonrpc"
            data = {
                "jsonrpc": "2.0",
                "method": "aria2.addUri",
                "id": "QXJpYU5nXzE2NDY4MzM4NDJfMC4zNDc3MTcxOTgzNTA1NDQ1",
                "params": [[VGA], {"out": f"{CourseName}/{StartTime}_VGA.mp4"}]
            }
            response = session.post(url, json=data, verify=False)

        if not os.path.exists(f"D:\\OvlerDrive\\OneDrive\\downloads\\{CourseName}\\Video1\\{StartTime}_Video1.mp4"):
            url = "http://localhost:16800/jsonrpc"
            data = {
                "jsonrpc": "2.0",
                "method": "aria2.addUri",
                "id": "QXJpYU5nXzE2NDY4MzM4NDJfMC4zNDc3MTcxOTgzNTA1NDQ1",
                "params": [[Video1], {"out": f"{CourseName}/Video1/{StartTime}_Video1.mp4"}]
            }
            response = session.post(url, json=data, verify=False)

        time.sleep(0.1)

if __name__ == "__main__":
    main()
