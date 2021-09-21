# MPS_Website

This repo has been updated to work with `Python v3.8` and up.

### How To Run
1. Install `virtualenv`:
```
$ pip install virtualenv
```

2. Open a terminal in the project root directory and run:
```
$ virtualenv env
```

3. Then run the command:
```
$ source env/bin/activate
```

4. Then install the dependencies:
```
$ (env) pip install -r requirements.txt
```
 
5. The backend is the executable from the code at this repo
https://github.com/n-e-sherman/mps.git
and the executable must be called 'main' and placed in the code directory.


6. Finally start the web server:
```
$ (env) python app.py
```

This server will start on port 5000 by default. You can change this in `app.py` by changing the following line to this:

```python
if __name__ == "__main__":
    app.run(debug=True, port=<desired port>)
```