import requests

API_URL = "http://localhost:8000/api/ask"


def ask(prompt):

    res = requests.post(API_URL, json={"prompt": prompt})

    print(res.json())


if __name__ == "__main__":

    while True:
        prompt = input("syntra > ")

        ask(prompt)
