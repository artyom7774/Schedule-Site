import traceback
import requests
import time

URL = "https://ge3.pythonanywhere.com/api/ai/"


def requestAI(message):
    data = {"message": message, "model": "gemini-3.5-flash-lite"}

    response = requests.post(f"{URL}/request", json=data)

    ids = response.json()["ids"]

    answer = None

    while True:
        try:
            status = requests.get(f"{URL}/status/{ids}").json()

        except requests.exceptions.RequestException as e:
            answer = (1, traceback.format_exc())

            break

        except requests.exceptions.ConnectTimeout as e:
            answer = (1, traceback.format_exc())

            break

        except Exception as e:
            answer = (1, traceback.format_exc())

            break

        if status["status"] == "completed":
            answer = (0, status["response"])

            break

        if status["status"] == "error":
            answer = (1, status["error"])

            break

        time.sleep(5)

    if "503" in answer[1]:
        return requestAI(message)

    return answer
