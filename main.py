#  _____
# |  ___|_ _ ___ _ __ ___    __ _  __ _
# | |_ / _` / __| '_ ` _ \  / _` |/ _` |
# |  _| (_| \__ \ | | | | || (_| | (_| |
# |_|  \__,_|___/_| |_| |_(_)__, |\__,_|
#                           |___/

# © 2020-today Fasm.ga
# Protected by MIT License.
# https://github.com/fasm-ga/fasmga

############################### Modules

from flask import Flask, make_response, redirect, render_template, request, send_from_directory
import hashlib, os, pymongo, random, requests, string, dotenv, ssl, json

############################### Setting up basic things

dotenv.load_dotenv()

app = Flask("fasmga", template_folder = os.path.abspath("pages"))

database = pymongo.MongoClient(os.getenv("MongoString"), ssl_cert_reqs=ssl.CERT_NONE)
db = database["fasmga"]
users = db["users"]
urls = db["urls"]
blacklist = db["blacklist"]


############################### Functions

def getLang():
    if request.cookies.get("lang"):
        import json
        try:
            with open(app.root_path + "/translations/" + request.cookies.get("lang") + ".json", "r") as file:
                translation = json.load(file)
                return translation
        except:
            with open(app.root_path + "/translations/en.json", "r") as file:
                translation = json.load(file)
                return translation
    else:
        import json
        with open(app.root_path + "/translations/en.json", "r") as file:
            translation = json.load(file)
            return translation

def getError(error):
    translations = getLang()
    return translations["errors"][str(error)]

def validLogin():
    if not request.cookies.get("login_token"):
        return False
    else:
        if not users.find_one({ "login_token": request.cookies.get("login_token") }):
            return False
        else:
            return True

def getUsername():
	user = users.find_one({ "login_token": request.cookies.get("login_token") })
	return user["username"]
			
def newToken():
    letters = string.ascii_letters
    result_str = "".join(random.choice(letters) for i in range(69))
    return result_str

def generateURLID(idtype):
	if idtype == "abcdefgh":
		urlid = "".join(random.choice(string.ascii_lowercase) for i in range(8))
		return urlid
	elif idtype == "abc12345":
		urlid = "".join(random.choice(string.ascii_lowercase) for i in range(3)) + str(random.randint(10000, 99999))
		return urlid
	elif idtype == "aBCde":
		urlid = "".join(random.choice(string.ascii_letters) for i in range(5))
		return urlid

def getDashboardTranslation(translation):
	lang = getLang()
	return lang["dashboard"][translation]

def getIndexTranslation(translation):
	lang = getLang()
	return lang["index"][translation]

def compileDashboard(username):
	global urls
	userURLs = urls.find({ "owner": username })
	dashboard = ""
	for url in userURLs:
		dashboard += "<div><div class=\"uk-card uk-card-default uk-card-body\"><h3 class=\"uk-card-title\" style=\"width: 100%; text-overflow: ellipsis; white-space: nowrap; overflow: hidden;\"><abbr title=\"/" + url["ID"] + "\">" + url["ID"] + "</abbr></h3><p style=\"width: 100%; text-overflow: ellipsis; white-space: nowrap; overflow: hidden;\"><abbr title=\"" + url["redirect_url"] + "\">" + url["redirect_url"] + "</abbr></p><p style=\"width: 100%; text-overflow: ellipsis; white-space: nowrap; overflow: hidden;\"><abbr title=\"" + str(url["clicks"]) + "\">↗ " + str(url["clicks"]) + "</abbr></p><a href=\"#delete-" + url["ID"] + "\" style=\"color: #666666;\" uk-toggle><i class=\"material-icons\">delete</i></a> <a href=\"#edit-" + url["ID"] + "\" style=\"color: #666666;\" uk-toggle><i class=\"material-icons\">edit</i></a><div id=\"edit-" + url["ID"] + "\" uk-modal><div class=\"uk-modal-dialog uk-modal-body\"><h2 class=\"uk-modal-title\">" + getDashboardTranslation("edit") + " /" + url["ID"] + "</h2><form action=\"https://www.fasmga.org/edit\" method=\"POST\"><label for=\"id\">ID...</label><br><input class=\"uk-input\" value=\"" + url["ID"] + "\" readonly id=\"id\" name=\"id\"><br><br><label for=\"url\">URL...</label><br><input class=\"uk-input\" value=\"" + url["redirect_url"] + "\" id=\"url\" name=\"url\" required><br><br><label for=\"password\">" + getIndexTranslation("password") + "</label><br><input class=\"uk-input\" id=\"password\" name=\"password\" type=\"password\" placeholder=\"" + getDashboardTranslation("pass_hint") + "\"><br><br><label for=\"nsfw\">NSFW?</label><br><select class=\"uk-select\" id=\"nsfw\" name=\"nsfw\" required><option value=\"false\"" + str(url["nsfw"]).replace("True", " selected").replace("False", "") + ">" + getIndexTranslation("nsfw_false") + "</option><option value=\"true\"" + str(url["nsfw"]).replace("True", " selected").replace("False", "") + ">" + getIndexTranslation("nsfw_true") + "</option></select><p class=\"uk-text-right\"><button class=\"uk-button uk-button-default uk-modal-close\" type=\"button\">" + getDashboardTranslation("cancel") + "</button> <input type=\"submit\" class=\"uk-button uk-button-primary\" value=\"" + getDashboardTranslation("save") + "\"></p></form></div></div><div id=\"delete-" + url["ID"] + "\" uk-modal><div class=\"uk-modal-dialog uk-modal-body\"><h2 class=\"uk-modal-title\">" + getDashboardTranslation("delete") + " /" + url["ID"] + "</h2><form action=\"https://www.fasmga.org/delete\" method=\"POST\"><label for=\"id\">ID...</label><br><input class=\"uk-input\" value=\"" + url["ID"] + "\" readonly id=\"id\" name=\"id\"><p class=\"uk-text-right\"><button class=\"uk-button uk-button-default uk-modal-close\" type=\"button\">" + getDashboardTranslation("no") + "</button> <input type=\"submit\" class=\"uk-button uk-button-danger\" value=\"" + getDashboardTranslation("yes") + "\"></p></form></div></div></div></div>"
	return dashboard

############################### Site pages

@app.route("/", strict_slashes = False)
def main():
	if not request.cookies.get("cookie_consent"): return render_template("updating.html", cookie_consent = "1")
	return render_template("updating.html")

############################### Cookie consent

@app.route("/cookie_consent", strict_slashes = False)
def cookie_consent():
	resp = make_response(redirect("/"))
	resp.set_cookie("cookie_consent", "1", 15780000)
	return resp

############################### Internal APIs

@app.route("/new", methods = ["POST", "GET"], strict_slashes = False)
def index():
	if request.method == "GET":
		if not request.cookies.get("cookie_consent"): return render_template("index.html", cookie_consent = "1", lang = getLang())
		return render_template("index.html", lang = getLang())
	elif request.method == "POST":
		try:
			if validLogin() == False:
				if request.form["password"]:
					if request.form["id"]:
						req = requests.post("http://127.0.0.1:2002/internal/create", { "login": False, "url": request.form["url"], "nsfw": request.form["nsfw"], "password": request.form["password"], "idtype": request.form["idtype"], "id": request.form["id"], "token": os.getenv("anonymousToken") })
						response = req.json()
					else:
						req = requests.post("http://127.0.0.1:2002/internal/create", { "login": False, "url": request.form["url"], "nsfw": request.form["nsfw"], "password": request.form["password"], "idtype": request.form["idtype"], "token": os.getenv("anonymousToken") })
						response = req.json()
				else:
					if request.form["id"]:
						req = requests.post("http://127.0.0.1:2002/internal/create", { "login": False, "url": request.form["url"], "nsfw": request.form["nsfw"], "idtype": request.form["idtype"], "id": request.form["id"], "token": os.getenv("anonymousToken") })
						response = req.json()
					else:
						req = requests.post("http://127.0.0.1:2002/internal/create", { "login": False, "url": request.form["url"], "nsfw": request.form["nsfw"], "idtype": request.form["idtype"], "token": os.getenv("anonymousToken") })
						response = req.json()
			else:
				api_token = users.find_one({ "login_token": request.cookies.get("login_token") })["api_token"]
				
				if request.form["password"]:
					if request.form["id"]:
						req = requests.post("http://127.0.0.1:2002/internal/create", { "login": True, "url": request.form["url"], "nsfw": request.form["nsfw"], "idtype": request.form["idtype"], "token": api_token, "id": request.form["id"] })
						response = req.json()
					else:
						req = requests.post("http://127.0.0.1:2002/internal/create", { "login": True, "url": request.form["url"], "nsfw": request.form["nsfw"], "password": request.form["password"], "idtype": request.form["idtype"], "token": api_token })
						response = req.json()
				else:
					if request.form["id"]:
						req = requests.post("http://127.0.0.1:2002/internal/create", { "login": True, "url": request.form["url"], "nsfw": request.form["nsfw"], "idtype": request.form["idtype"], "token": api_token, "id": request.form["id"] })
						response = req.json()
					else:
						req = requests.post("http://127.0.0.1:2002/internal/create", { "login": True, "url": request.form["url"], "nsfw": request.form["nsfw"], "idtype": request.form["idtype"], "token": api_token })
						response = req.json()
			return render_template("index.html", url = "https://fasm.ga" + response["success"], lang = getLang())
		except:
			try:
				if response["error"] == "blacklisted":
					return render_template("index.html", error = getError(987), lang = getLang())
				elif response["error"] == "exists":
					return render_template("index.html", error = getError(989), lang = getLang())
				else:
					return render_template("index.html", error = getError(988), lang = getLang())
			except:
				return render_template("index.html", error = getError(988), lang = getLang())

@app.route("/delete", methods = ["POST"], strict_slashes = False)
def delete_url():
	if not request.form["id"]:
		return "Hm, don't try to break Fasm.ga."
	if validLogin() == False:
		return redirect("https://www.fasmga.org/dashboard")
	else:
		api_token = users.find_one({ "login_token": request.cookies.get("login_token") })["api_token"]
		req = requests.post("http://127.0.0.1:2002/internal/delete", { "login": "true", "id": request.form["id"], "token": api_token })
		response = req.json()
		try:
			undefined = response["success"]
			return redirect("https://www.fasmga.org/dashboard")
		except:
			return render_template("error.html", code = "401", error = getError(988), lang = getLang())

@app.route("/edit", methods = ["POST"], strict_slashes = False)
def edit_url():
	if not request.form["id"]:
		return "Hm, don't try to break Fasm.ga."
	if validLogin() == False:
		return redirect("https://www.fasmga.org/dashboard")
	else:
		api_token = users.find_one({ "login_token": request.cookies.get("login_token") })["api_token"]
		req = requests.post("http://127.0.0.1:2002/internal/edit", { "login": "true", "id": request.form["id"], "token": api_token, "password": request.form["password"], "nsfw": request.form["nsfw"], "url": request.form["url"] })
		response = req.json()
		try:
			undefined = response["success"]
			return redirect("https://www.fasmga.org/dashboard")
		except:
			return render_template("error.html", code = "401", error = getError(989), lang = getLang())

############################### Settings

@app.route("/settings", methods = ["POST", "GET"], strict_slashes = False)
def settings():
	if request.method == "GET":
		return render_template("settings.html", lang = getLang())
	elif request.method == "POST":
		if not request.form["language"]: return "nope"
		if not request.form["language"] in ["en", "it", "pl"]: return "nope"
		response = make_response(redirect("/settings"))
		response.set_cookie("lang", request.form["language"], 15780000)
		return response

############################### Dashboard

@app.route("/dashboard", strict_slashes = False)
def dashboard():
	if validLogin() == False:
		return redirect("/login")
	else:
		return render_template("dashboard.html", lang = getLang(), urls = compileDashboard(getUsername()))

############################### For developers

@app.route("/developers", methods = ["GET", "POST"], strict_slashes = False)
def developers():
	if validLogin() == False:
		return redirect("/login")
	else:
		return "WIP ;)"

############################### Login system

@app.route("/login", strict_slashes = False)
def login():
	if validLogin() == True: return redirect("/")
	return redirect("https://account.fasmga.org/login?service=fasmga")

@app.route("/login/confirm", strict_slashes = False)
def login_confirm():
	if not request.args.get("user_token"): return redirect("/")
	if not users.find_one({ "login_token": request.args.get("user_token") }): return redirect("/")
	resp = make_response(redirect("/"))
	resp.set_cookie("login_token", request.args.get("user_token"), 15780000)
	return resp

@app.route("/logout", strict_slashes = False)
def logout():
	if not request.cookies.get("login_token"):
		return redirect("/")
	else:
		resp = make_response(redirect("/"))
		resp.set_cookie("login_token", "", 0)
		requests.post("https://account.fasmga.org/logout?auth=" + os.getenv("LOGOUT_TOKEN"))
		return resp

############################### that FU***NG ToS

@app.route("/tos")
def tos():
	return render_template("tos.html", lang = getLang())

############################### Redirects

@app.route('/<id>', strict_slashes = False)
def redirectURL(id):
	try:
		url = urls.find_one({ "ID": id })
		redirectURL = url["redirect_url"]
		password = url["password"]
		nsfw = url["nsfw"]
		clicks = url["clicks"]
		if redirectURL:
			if password != "":
				return render_template("password.html", id = id, lang = getLang())
			else:
				if request.args.get("nsfwConsent"):
					if request.args.get("nsfwConsent") == "yes":
						urls.find_one_and_update({ "ID": id }, { "$set": { "clicks": clicks + 1 }})
						return redirect(redirectURL, 302)
					else:
						if nsfw == False:
							urls.find_one_and_update({ "ID": id }, { "$set": { "clicks": clicks + 1 }})
							return redirect(redirectURL, 302)
						else:
							return render_template("nsfw.html", lang = getLang(), url = id)
				else:
					if nsfw == False:
						urls.find_one_and_update({ "ID": id }, { "$set": { "clicks": clicks + 1 }})
						return redirect(redirectURL, 302)
					else:
						return render_template("nsfw.html", lang = getLang(), url = id)
		else:
			return render_template("error.html", lang = getLang(), code = "404", error = getError(800))
	except:
		return render_template("error.html", lang = getLang(), code = "404", error = getError(800))

@app.route("/check_password", methods = ["POST"], strict_slashes = False)
def check_password():
	if not request.form["id"]: return redirect("/")
	if not request.form["password"]: return redirect("/")
	url = urls.find_one({ "ID": request.form["id"] })
	if not url: return redirect("/")
	if not hashlib.sha512(request.form["password"].encode()).hexdigest() == url["password"]: return render_template("error.html", lang = getLang(), code = "401", error = getError(801))
	urls.find_one_and_update({ "ID": request.form["id"] }, { "$set": { "clicks": url["clicks"] + 1 }})
	if url["nsfw"] == False:
		return redirect(url["redirect_url"])
	else:
		return render_template("nsfw_password.html", lang = getLang(), url = url["redirect_url"])

@app.route("/staff", strict_slashes = False)
def staff_redirect():
	return redirect("https://6n7ynae1dxz.typeform.com/to/qBkQ03cz")

@app.route("/discord", strict_slashes = False)
def discord_redirect():
	return redirect("https://discord.com/invite/MgQhdSZSsp")

############################### Assets

@app.route("/embed-image.png", strict_slashes = False)
def embed_image():
	return send_from_directory(app.root_path + "/assets", "embed-image.png")

@app.route("/favicon.ico", strict_slashes = False)
def favicon():
	return send_from_directory(app.root_path + "/assets", "favicon.ico")

@app.route("/robots.txt", strict_slashes = False)
def robots():
	return send_from_directory(app.root_path + "/assets", "robots.txt")

@app.route("/sitemap.xml", strict_slashes = False)
def sitemap():
	return send_from_directory(app.root_path + "/assets", "sitemap.xml")

############################### Errors

@app.errorhandler(404)
def error_404(error):
	return render_template("error.html", lang = getLang(), code = "404", error = getError(404))

@app.errorhandler(405)
def error_405(error):
	return render_template("error.html", lang = getLang(), code = "405", error = getError(405))

@app.errorhandler(500)
def error_500(error):
	return render_template("error.html", lang = getLang(), code = "500", error = getError(500))

app.run(host = "0.0.0.0", port = 2000)