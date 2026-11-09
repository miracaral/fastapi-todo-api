# Self-assigned admin role at sign-up (privilege escalation)

A write-up of a bug I found in my own API while cleaning it up, how it worked, and how it is fixed and tested.

| | |
| --- | --- |
| **Type** | Privilege escalation through mass assignment ([CWE-915](https://cwe.mitre.org/data/definitions/915.html), [OWASP API3:2023 Broken Object Property Level Authorization](https://owasp.org/API-Security/editions/2023/en/0xa3-broken-object-property-level-authorization/)) |
| **Where** | `POST /auth/` (registration) |
| **Who could exploit it** | Anyone, no account needed |
| **Fixed in** | This repository's first public version; regression test `test_cannot_choose_own_role` |

## The bug

The registration request model accepted a `role` field from the client and stored it as is:

```python
class CreateUserRequest(BaseModel):
    username: str
    email: str
    first_name: str
    last_name: str
    password: str
    role: str            # chosen by the client

user = User(..., role=create_user_request.role, ...)
```

The role is then copied into every access token the user gets:

```python
payload = {"sub": username, "id": user_id, "role": role}
```

So the server trusted the client to say what kind of user it was.

## Exploit

One request is enough:

```bash
curl -X POST http://127.0.0.1:8000/auth/ \
  -H 'Content-Type: application/json' \
  -d '{"username":"mallory","email":"m@example.com","first_name":"M","last_name":"M",
       "password":"password123","role":"admin"}'
```

Logging in as `mallory` then returns a validly signed JWT whose payload contains `"role": "admin"`. Because the token is signed by the server, every part of the system that checks the token would believe it.

## Impact

In this version of the API there were no admin-only endpoints yet, so the bug was **latent**: nothing could be abused on the day it was found. It would have become a full compromise the moment an admin feature was added (for example "list all users" or "delete any todo") with the usual check:

```python
if user["role"] != "admin":
    raise HTTPException(status_code=403)
```

That check would pass for anyone who registered with `"role": "admin"`. Bugs like this are dangerous precisely because the code that is vulnerable (sign-up) and the code that gets bypassed (a future admin check) are written at different times, often by different people.

## Fix

The role is now decided by the server, never by the client:

```python
class CreateUserRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    first_name: str
    last_name: str
    password: str = Field(min_length=8)
    phone_number: str | None = None
    # No "role" field: a user must not be able to make themselves an admin at sign-up.

user = User(..., role="user", ...)
```

Pydantic ignores fields that are not in the model, so a request that still sends `"role": "admin"` is accepted, but the value is thrown away. Promoting someone to admin would have to be a separate, admin-only action.

## Regression test

```python
def test_cannot_choose_own_role(client):
    register(client, "mallory", role="admin")  # extra field is ignored
    token = login(client, "mallory").json()["access_token"]
    assert jwt.get_unverified_claims(token)["role"] == "user"
```

It runs in CI on every push, so the bug cannot quietly come back.

## Lesson

Request models should list only what the client is allowed to decide. Anything that controls permissions (role, `is_active`, `owner_id`, prices, balances) is set by the server. The same idea protects the todo routes in this API: `owner_id` is taken from the verified token, never from the request body.
