import time
import base64

import requests as req

# The scopes that the access token should have
SCOPES = "user-read-playback-state,user-modify-playback-state,user-read-currently-playing,app-remote-control,streaming"
# URLs to connect to the Spotify WebAPI
BASE_URL = "https://api.spotify.com/v1/"
URL_LOGIN = 'https://accounts.spotify.com/api/token'
URL_USER_TOKEN = 'https://accounts.spotify.com/authorize?'

def query_string(d):
    return "&".join([f"{key}={val}" for key, val in d.items()])

class Track:
    def __init__(self):
        self.track = ""
        self.artist = ""
    
    def __str__(self):
        return f"{self.artist}: {self.track}"
    
    def set_track(self, track, artist):
        self.track = track
        self.artist = artist

class Client:
    def __init__(self):
        self.id = "" # The id of the registered application
        self.__secret = "" # The secret of the registered application
        self.token = "" # The access token received when logging in
        self.refresh_token = "" # The refresh toekn received when logging in
        self.token_type = "Bearer"
        self.device = ""
        self.volume = 50
        self.track = Track()

    # Login through browser and get auth code, put into getToken() reg.post as code value
    def printLoginUrl(self):
        query_p = {
            "response_type": 'code',
        "client_id": self.id,
        "scope": SCOPES,
        "redirect_uri": "https://google.se",
        }
        print(f"{URL_USER_TOKEN}{query_string(query_p)}")
    
    def getToken(self):
        client_stuff = f'{self.id}:{self.__secret}'
        b64str = base64.b64encode(client_stuff.encode("ascii")).decode("utf-8")
        resp = req.post(URL_LOGIN,
                   headers={'Authorization': f'Basic {b64str}',},
                   data = {"grant_type" : "authorization_code",
                           "code" : "",
                           "redirect_uri" : "https://google.se"
                           },
                   json=True).json()
        self.token = resp["access_token"]
        self.token_type = resp["token_type"]
        self.refresh_token = resp["refresh_token"]

    def refreshToken(self):
        client_stuff = f'{self.id}:{self.__secret}'
        b64str = base64.b64encode(client_stuff.encode("ascii")).decode("utf-8")
        resp = req.post(URL_LOGIN,
                   headers={'Authorization': f'Basic {b64str}',},
                   data = {"grant_type" : "refresh_token",
                           "refresh_token" : self.refresh_token,
                           "client_id" : self.id
                           },
                   json=True).json()
        self.token = resp["access_token"]
        self.token_type = resp["token_type"]
        self.refresh_token = resp["refresh_token"]

    def getDevice(self):
        resp = req.get(f"{BASE_URL}me/player/devices",
                       headers={"Authorization": f"{self.token_type} {self.token}"})
        if resp.status_code == 401:
            self.refreshToken()
            return
        resp = resp.json()
        self.device = ""
        for dev in resp["devices"]:
            if dev["is_active"]:
                self.device = dev["id"]
                self.volume = int(dev["volume_percent"])
        if self.device == "" and len(resp["devices"]) > 0:
            self.device = resp["devices"][0]["id"]
        self.volume = self.volume - self.volume % 5
        self.setVolume()

    def post_playback(self, method: str):
        resp = req.post(f"{BASE_URL}me/player/{method}",
                    headers={"Authorization": f"{self.token_type} {self.token}"},
                    data=f"device_id={self.device}")
        if resp.status_code == 401:
            self.refreshToken()

    def put_playback(self, method: str):
        resp = req.put(f"{BASE_URL}me/player/{method}",
                    headers={"Authorization": f"{self.token_type} {self.token}"},
                    data=f"device_id={self.device}")
        if resp.status_code == 401:
            self.refreshToken()
        return resp

    def setVolume(self):
        resp = self.put_playback(f"volume?volume_percent={self.volume}")
        print(resp.content)

    def increace_vol(self):
        self.volume = min(100, self.volume+5)
        self.setVolume()
    
    def decreace_vol(self):
        self.volume = max(0, self.volume-5)
        self.setVolume()

    def get_playstate(self):
        resp = req.get(f"{BASE_URL}me/player",
                    headers={"Authorization": f"{self.token_type} {self.token}"})
        if resp.status_code == 401:
            self.refreshToken()
            return
        if resp.status_code == 200:
            info = resp.json()
            return info
        return None

    def get_playing(self):
        info = self.get_playstate()
        if info != None:
            return int(info["progress_ms"]), info["is_playing"]
        return 0, False

    def pause(self):
        self.put_playback("pause")

    def play(self, ms: int):
        resp = req.put(f"{BASE_URL}me/player/play",
                    headers={"Authorization": f"{self.token_type} {self.token}"},
                    data="{\"position_ms\": "+str(ms)+"}",
                    json=True)
        if resp.status_code == 401:
            self.refreshToken()
            return

    def toggle(self):
        ms, is_playing = self.get_playing()
        if is_playing:
            self.pause()
        else:
            self.play(ms)

    def previous(self):
        self.post_playback("previous")

    def next(self):
        self.post_playback("next")

    def get_track(self):
        info = self.get_playstate()
        self.track.set_track(info["item"]["name"], info["item"]["artists"][0]["name"])
        print(self.track)

client = Client()

SETUP = False

def main():
    # client.printLoginUrl()
    # client.getToken()
    # client.pause()
    if not SETUP:
        client.getDevice()
        dontQuit = True
        while dontQuit:
            g = input()
            match g:
                case "g":
                    client.get_track()
                case "t":
                    client.toggle()
                case "n":
                    client.next()
                case "p":
                    client.previous()
                case "u":
                    client.increace_vol()
                case "d":
                    client.decreace_vol()
                case "dev":
                    print(client.device)
                case "q":
                    dontQuit = False
                case _:
                    print("I don't know what you did")
            client.getDevice()

if __name__ == "__main__":
    main()