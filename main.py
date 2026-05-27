from wpp_api import WppApi

api = WppApi()
app = api.app

if __name__ == '__main__':
    api.run()
