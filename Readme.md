# First bernerdev.de codejam

This is the code for the first minicodejam organized by bernerdev. All participants had the same task, and could complete it in the language of their choice.

### What was the goal?
---

The goal was to write a login and regrestrate website in the language of choice. One thing to keep in mind was that it must not use any external dependencies or libraries. (An exception was made for Java and Kotlin devs). In addition, the website had to have a mechanism that blocks a user or his IP if he enters his password incorrectly 3 times.  In addition, the user's password could not be stored in plain text, so it had to be encrypted.

### How I proceeded?
---
I used my favorite and everyday language Python for this task. With its builtin library http it is already very well equipped for something like this. So routing, cookies and setting headers is no problem. I wrote myself several helper classes with several helper functions for many functions, like creating users, deleting sessions, tracking broken logins. The session and fails are stored in 2 json files, while the users are stored in a SQLite database.

### How to use the app?
---

1. Step - clone the repo
```
git clone https://github.com/cheetahbyte/bernerdev-codejam-1 codejam
```

2. Step - cd inside the folder
```
cd codejam
```

3. Step - run the server.py file
```
python server.py
```

4. Step - visit the page on your browser
```
http://localhost:8080
```
