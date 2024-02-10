from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio import join_room, leave_room, SocketIO, send
import random
from string import ascii_uppercase

rooms = {}

app = Flask(__name__)
app.config['SECRET_KEY'] = "tjmanojofficial"
socketio = SocketIO(app)


def generate_unique_id(length):
    while True:
        code = ""
        for _ in range(length):
            code += random.choice(ascii_uppercase)
        
        if code not in rooms:
            break 
    return code

@app.route("/", methods = ["POST", "GET"])
def home():
    session.clear()
    if request.method == "POST":
        name = request.form.get("name")
        code = request.form.get("code")
        join = request.form.get("join", False)
        create = request.form.get("create", False)

        if not name:
            return render_template("home.html", error = "Please enter the name!", code=code, name=name)
        
        if join != False and not code:
            return render_template("home.html", error = "Please enter the room code!", code=code, name=name)
            return render_template("home.html", error = "Please enter the room code!", code=code, name=name)

        room = code
        if create != False:
            room = generate_unique_id(4)
            rooms[room] = {"members": 0, "messages": []}
        
        elif code not in rooms:
            return render_template("home.html", error = "Room doesn't exist!", code=code, name=name)
        
        session["room"] = room
        session["name"] = name 
        return redirect(url_for("room"))
        
    return render_template("home.html")



@app.route("/room")
def room():
    room = session.get("room")
    if room is None or session.get("name") is None or room not in rooms:
        return redirect(url_for("home"))

    return render_template("room.html", code = room, messages = rooms[room]["messages"])


@socketio.on("connect")
def connect(auth):
    room = session.get("room")
    name = session.get("name")
    if not room and not name:
        return 
    if room not in rooms:
        leave_room(room)
        return

    join_room(room)
    send({"name":name, "message": "has joined"}, to=room)
    rooms[room]["members"] += 1
    print(f"{name} joined {room}")


@socketio.on("disconnect")
def disconnect():
    room = session.get("room")
    name = session.get("name")
    leave_room(room)

    if room in rooms:
        rooms[room]["members"] -= 1 
        if rooms[room]["members"] < 1:
            del rooms[room]
    send({"name":name, "message": "has left"}, to=room)
    print(f"{name} has left {room}")


@socketio.on("message")
def message(data):
    room = session.get("room")
    if room not in rooms:
        return 
    
    content = {
        "name": session.get("name"),
        "message": data["data"]
    }

    send(content, to=room)
    rooms[room]["messages"].append(content)
    print(f"{session.get('name')} said: {data['data']}")


if __name__ == "__main__":
    socketio.run(app, debug=True)
