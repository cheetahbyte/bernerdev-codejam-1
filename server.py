from http.server import HTTPServer, BaseHTTPRequestHandler
from http.cookies import SimpleCookie
from manager import Fail2Ban, Session, User
from template import TemplateEngine
from urllib.parse import parse_qs
import datetime
templater: TemplateEngine = TemplateEngine("templates")


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        count = Fail2Ban.fails(self.client_address[0]) if Fail2Ban.fails(
            self.client_address[0]) else 0
        if self.path == "/register":
            cookies = SimpleCookie(self.headers.get("Cookie"))
            isLoggedin: bool = Session.check(cookies)
            if isLoggedin is True:
                self.send_response(302)
                self.send_header("Location", "/dashboard")
                self.end_headers()
            if count >= 3:
                self.send_response(302)
                self.send_header("Location", "/access-denied")
                self.end_headers()
            content = templater.render("register.html")
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        elif self.path == "/login":
            # sessions
            cookies = SimpleCookie(self.headers.get("Cookie"))
            isLoggedin: bool = Session.check(cookies)
            if isLoggedin is True:
                self.send_response(302)
                self.send_header("Location", "/dashboard")
                self.end_headers()
            # fail2ban check
            if count >= 3:
                self.send_response(302)
                self.send_header("Location", "/access-denied")
                self.end_headers()
            # send html
            content = templater.render("login.html")
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        elif self.path == "/access-denied":
            error = templater.render("error.html")
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(error)))
            self.end_headers()
            self.wfile.write(error)
        elif self.path == "/dashboard":
            cookies = SimpleCookie(self.headers.get("Cookie"))
            isLoggedin: bool = Session.check(cookies)
            if isLoggedin is not True:
                self.send_response(302)
                self.send_header("Location", "/login")
                self.end_headers()
            session = Session.find(cookies["sessionId"].value)
            timedelta = datetime.datetime.fromisoformat(
                session["validUntil"]) - datetime.datetime.now()
            content: bytes = templater.render(
                "dashboard.html", sessionId=session["uuid"], username=session["username"], expiresIn="{} minutes".format(round(timedelta.seconds / 60)))
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        elif self.path == "/error":
            error = templater.render("login.error.html", tries=str(3-count))
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(error)))
            self.end_headers()
            self.wfile.write(error)
        elif self.path == "/logout":
            try:
                cookie = SimpleCookie(self.headers.get("Cookie"))
                sessionId = cookie["sessionId"].value
                session = Session.find(sessionId)
                Session.remove(session["index"], session["username"])
                self.send_response(302)
                self.send_header("Location", "/login")
                self.end_headers()
            except KeyError:
                self.send_response(302)
                self.send_header("Location", "/login")
                self.end_headers()
        elif self.path == "/" or self.path == "":
            content = templater.render("index.html")
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        else:
            self.send_response(302)
            self.send_header("Location", "/")
            self.end_headers()


    def do_POST(self):
        if self.path == "/register":
            content_length = int(self.headers['Content-Length'])
            data = self.rfile.read(content_length).decode()
            params = parse_qs(data)
            if not User.exists(params.get("username")[0]):
                user = User.create(params.get("username")[
                                   0], params.get("pwd")[0])
                sessionId = Session.create(user[0], params.get("username")[0])
                self.send_response(302)
                self.send_header("Location", "/dashboard")
                cookie = SimpleCookie()
                cookie["sessionId"] = sessionId
                for morsel in cookie.values():
                    self.send_header("Set-Cookie", morsel.OutputString())
                self.end_headers()
            else:
                self.wfile.write(bytes("Username already claimed", "utf-8"))
        if self.path == "/login":
            content_length = int(self.headers['Content-Length'])
            data = self.rfile.read(content_length).decode()
            params = parse_qs(data)
            loggedin: bool = User.check(params.get(
                "username")[0], params.get("pwd")[0])
            user = User.get_user(params.get("username")[0])
            if (loggedin is True):
                Fail2Ban.remove(self.client_address[0])
                sessionId = Session.create(user[0], params.get("username")[0])
                self.send_response(302)
                self.send_header("Location", "/dashboard")
                cookie = SimpleCookie()
                cookie["sessionId"] = sessionId
                for morsel in cookie.values():
                    self.send_header("Set-Cookie", morsel.OutputString())
                self.end_headers()
            else:
                Fail2Ban.increase(self.client_address[0])
                self.send_response(302)
                self.send_header("Location", "/error")
                self.end_headers()


httpd = HTTPServer(("0.0.0.0", 8080), Handler)
httpd.serve_forever()
