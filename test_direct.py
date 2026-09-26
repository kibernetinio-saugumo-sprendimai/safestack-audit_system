import requests
import json

def test():
    url = "http://localhost:11434/api/generate"
    data = {
        "model": "phi3",
        "prompt": "Labas, ar girdi mane?",
        "stream": False
    }
    try:
        print("Siunčiama tiesioginė užklausa į Ollama...")
        response = requests.post(url, json=data, timeout=10)
        print("Atsakymas gautas:", response.json().get("response"))
    except Exception as e:
        print("Klaida:", e)

if __name__ == "__main__":
    test()
