from json import JSONDecodeError, loads
from locale import LC_ALL, setlocale
from time import sleep
from requests import Session
import codecs

setlocale(LC_ALL, "en_US.UTF-8")
SESSION_ID = "REPLACE ME"          # Configure this with OWN session id

class Config:
    """
    Config class
    """
    def __init__(self):
        """
        Config init
        """
        self.fd = None
        self.num_followers = None
        self.num_following = None
        self.picture_headers = None
        self.session = None
        self.user = None
        self.user_id = None

def create_session(config):
    """
    Create a session
    """
    headers = {
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-GB,en;q=0.5",
        "Accept": "*/*",
        "Alt-Used": "i.instagram.com",
        "Connection": "keep-alive",
        "DNT": "1",
        "Host": "i.instagram.com",
        "Origin": "https://www.instagram.com",
        "Referer": "https://www.instagram.com/",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site",
        "TE": "trailers",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:101.0) Gecko/20100101 Firefox/101.0",
        "X-IG-App-ID": "936619743392459",
        "X-ASBD-ID": "198387",
    }

    config.session = Session()
    config.session.headers = headers
    config.session.cookies.update({"sessionid": SESSION_ID})
   
    config.picture_headers = config.session.headers.copy()
    config.picture_headers.update({
        "Host": "scontent-lcy1-1.cdninstagram.com",
        "Sec-Fetch-Dest": "image",
        "Sec-Fetch-Mode": "navigate"
    })


def get_input():
    """
    Get username input
    """
    username = input("Enter the username you wish to find out about: ")
    return username

def get_api_request(config, url):
    """
    Make an API request
    """
    resp = config.session.get(f"https://i.instagram.com/api/v1/{url}")
    return resp

def write_html_individuals(config, resp):
    """
    Write the inviduals from a response to HTML
    """
    if (resp.status_code == 200):
        config.fd.write("""
                            <td>
                                <table border='1' class='inner'>
                                    <thead>
                                        <tr>
                                            <th id="index">Index</th>
                                            <th id="username">Username</th>
                                            <th id="biography">Biography</th>
                                            <th id="pp">Profile picture</th>
                                        </tr>
                                    </thead>
                                    <tbody>
        """)
        followers = loads(resp.text)

        for i,user in enumerate(followers['users']):
            resp = get_api_request(config, f"users/web_profile_info/?username={user['username']}")
            timer = 60
            while resp.status_code == 429:
                sleep(timer)
                resp = get_api_request(config, f"users/web_profile_info/?username={user['username']}")
                timer += 30

            try:
                follower_data = loads(resp.text)
                if follower_data['status'] != "ok":
                    continue
                follower_data = follower_data["data"]["user"]
            except KeyError as exception:
                continue
            except JSONDecodeError as exception:
                continue
            
            if user['is_private']:
                color = 'red'
            else:
                color = 'green'
            
            config.fd.write(
                f"""
                                        <tr>
                                            <td style='background-color: {color};'>{i+1}</td>
                                            <td>{follower_data['username']}</td>
                                            <td>{follower_data['biography']}</td>
                                            <td><img src="{follower_data['profile_pic_url_hd']}" /></td>
                                        </tr>
                """
            )
            config.fd.flush()
        config.fd.write(
            """
                                    </tbody>
                                </table>
                            </td>
            """
        )
        config.fd.flush()
    else:
        print(
            f"""
            Error:
            Status code: {resp.status_code}
            Data: {resp.text}
            """
        )


def get_followers(config):
    """
    Get followers
    """
    resp = get_api_request(config, f"friendships/{config.user_id}/followers/?count={config.num_followers}&search_surface=follow_list_page")
    write_html_individuals(config, resp)
    print("Follower grab complete.")



def get_following(config):
    """
    Get following
    """
    resp = get_api_request(config, f"friendships/{config.user_id}/following/?count={config.num_following}&max_id=1")
    write_html_individuals(config, resp)
    print("Following grab complete.")

def get_user(config, user):
    """
    Get a user from API
    """
    resp = get_api_request(config, f"users/web_profile_info/?username={user}")
    if resp.status_code == 200:
        data = loads(resp.text)
        if "status" in data and data["status"] != "ok":
            print("Could not find profile.")
            exit(1)

        return data["data"]["user"]


def main():
    """
    main function
    """
    config = Config()

    username = get_input()
    create_session(config)

    config.user = get_user(config, username)
    config.user_id = config.user["id"]
    print(f"{username} has ID: {config.user_id}")

    try:
        config.num_followers = config.user["edge_followed_by"]["count"]
        print(f"{username} has {config.num_followers} followers.")
    except KeyError as exception:
        print(f"Could not identify number of people who follow {username}.")
        print(exception)
        exit(1)

    try:
        config.num_following = config.user["edge_follow"]["count"]
        print(f"{username} is following {config.num_following} people.")
    except KeyError as exception:
        print(f"Could not identify number of people who {username} follows.")
        print(exception)
        exit(1)

    config.fd = codecs.open("followers.html","w","utf-8")
    config.fd.write(
        f"""
        <!DOCTYPE html>
        <html>
            <head>
                <title>{username}'s follow details</title>
                <style>
                    * {{
                        text-align: center;
                    }}

                    .outer {{
                        width: 100%;
                    }}

                    .outer tbody {{
                        vertical-align: top;
                    }}

                    .outer th {{
                        width: 50%;
                    }}

                    .inner {{
                        border-collapse: collapse;
                    }}

                    img {{
                        width: 150px;
                        height: 150px;
                    }}

                    #index {{
                        width: 10%;
                    }}

                    #username {{
                        width: 40%;
                    }}

                    #pp {{
                        width: 40%;
                    }}
                </style>
            </head>
            <body>
                <table class='outer'>
                    <thead>
                        <tr>
                            <th class='outer'>Followers</th>
                            <th class='outer'>Following</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                                
        """
    )
    config.fd.flush()
    
    print("Grabbing followers")
    get_followers(config)
    print("Grabbing following")
    get_following(config)
    print("Finished grabbing")

    config.fd.write(
        """
                        </tr>
                    </tbody>
                </table>
            </body>
        </html>
        """
    )
    config.fd.close()

if __name__ == "__main__":
    main()
