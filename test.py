import requests

while True:
        print(requests.post("http://localhost:8000/chat", json={"message": input("Digite o prompt:")}).content)
