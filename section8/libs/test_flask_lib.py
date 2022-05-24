from flask import g

# Every request has its own "g".
# "g" can be used to store data only during a request, and only for that request.
# It does not keep any of its contents from one request to the next.


def function_accessing_global():
    print(g.token)
