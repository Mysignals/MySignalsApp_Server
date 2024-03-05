# MySignalsApp_Server

## TODO 
* add tx confirm from subgraph

## Table Of Contents
- [Set up for Local Machine](#set-up-the-server)
- [Base Uri/Live Deployment](#base-uri)
- [Error Handling](#error-handling)
- [Permissions/Roles](#permissionsroles)
- [EndPoints](#endpoints)
  - [Authentication Routes](#authentication)
  - [Provider Routes](#provider-endpoints)
  - [General Routes](#general-endpoints)
  - [Registrar Routes](#registrar-enpoints)
- [Authors](#authors)
- [Acknowledgments](#acknowledgments)

## **MY SIGNALSAPP API-ENDPOINT DOCUMENTATION**
---
<br>
<br>

### **Set up the server**
#### Install Dependencies
```bash
$ python3 -m venv venv

$ source venv/bin/activate

$ pip install -r requirements.txt
```

#### Set up the Database

With Postgres running, create a `sigs` database:

```bash
$ createdb sigs
```

#### Run the Server
```bash
$ python3 run.py 
```

### **Base Uri**
----
----
hosted for live testing on **https://api.mysignals.app/**
....


<br>

### **Error Handling**
---
---
>Errors are returned as JSON objects in the following format with their error code

```json
{
  "error": "error name",
  "message": "error description"
}
```
The API will return 5 error types, with diffreent descriptions when requests fail;
- 400: Request unprocessable
- 403: Forbidden
- 404: resource not found
- 422: Bad Request
- 429: Too Many Requests(rate limiting)
- 500: Internal server error

<br>

### **Permissions/Roles**
---
---

There are three roles available, role will be provided at login and `base_uri/auth/@me`

- User:["User"]
    * general permissions, regular user
- Provider:["User","Provider"]
    * signal providers,permissions to upload signals for users to trade
- Registrar:["User","Registrar]
    * Admin, grant roles and view users
<br>

### **EndPoints**
---
---
<br>

#### **AUTHENTICATION**
  > server side authentication is Used

  `POST '/auth/register'`

- Register new user,role is set to user and account is marked inactive, sends activation code to user email on success.
- Request Arguements: JSON object containing
```json
{
  "email":"user email",
  "user_name":"user name",
  "password":"password at least 8 characters",
  "confirm_password":"confirm password",
  "referrers_code":"referal code to register",// "" if no ref code
  "wallet":"User wallet address"
}
```
- Returns `message` ,`user name` and `email`
```json
{
    "message": "Success", 
    "user_name": "user_name", 
    "email": "user email"
}
```
---
<br>

  `GET '/auth/activate/${token}'`
- Activates user account
- Request Arguements: `token`- string token/code
- Returns: HTML 


---
<br>

  `POST '/auth/login'`
- login user, Server side sessions is used, cookie is sent to client
- Request Arguements: JSON object containing
```json
{
  "user_name_or_mail":"users username or email address",
  "password":"user password"
}
```
- Returns: JSON, permissions of logged in user and if user account is active

```json
 {
    "message": "Success",
    "id":"user id",
    "has_api_keys": true,
    "user_name": "user_name",
    "referral_code":"90jeu378",
    "is_active": true,//boolean- if account is active or not
    "permission": "User",//string 'User' or array of permissions
}
```
*note:* "permission":["User","Provider"] or "permission":"User"

---
<br>

  `POST '/auth/reset_password'`
- Request password reset, reset code sent to user mail if exists
- Request Arguements: Json object
```json
{
    "email":"user email"
}
```
Returns:
```json
{
    "message": "Reset password token will be sent to {email} if they exist"
}
```

---
<br>

  `POST '/auth/reset_password/${token}'`
- receive sent token and allows password chsnge
- Request Arguements `token`-string jwt token and JSON object
```json
{
  "password":"user password",
  "confirm_password":"confirm password"
}
```
- Returns:
```json
{"message": "Password changed"}
```
---
<br>

  `POST '/auth/logout'`
- Log out user
- Returns: 'message'
```json
{
    "message": "Success",
}
```
---
<br>

  `GET '/auth/@me'`
- gets all data of currenly logged in user
- Requires logged in
- Returns: JSON object
```json
{
    "message": "Success",
    "id":"user id",
    "has_api_keys": false,
    "email": "email",
    "referral_code": "90c44000",// users referral code
    "referrals": 0,
    "referrers_wallet": null,//wallet address of referrer
    "wallet": "0xodn",//wallet address of user
    "unread_notifications":1,
    "user_name": "user_name",
    "is_active": false,
    "roles": "['User','Rgistrar']",
    "created_on": "thu 30 june 2021 12:24:07"
}
```
---
<br>

  `GET '/auth/notifications'` or `GET '/auth/notifications?page=${page}'`
- gets all notifications of a user
- Requires logged in
- Request Arguements:query parameter `page`- integer defaults to `1` if not provided
- Returns: JSON object paginated
```json
{
  "message": "success",
  "notifications": [
    {
      "date_created": "Mon, 15 Jan 2024 17:46:38 GMT",
      "id": 1,
      "message": "test notification",
      "user": "bingoprovider"
    }
  ],
  "pages": 1,
  "status": true,
  "total": 1
}
```
---
<br>

  `GET '/auth/notifications/count'`
- gets total number of unread notifications of logged in user
- Returns: JSON object
```json
{
  "message": "success",
  "status": true,
  "unread_notifications": 1
}
```
---
<br>

`POST '/auth/update_keys'`
- Change api key and secret, Requires logged in
- Request Arguements: JSON object
```json
{
    "api_key":"key...",
    "api_secret":"secret..."
}
```
Returns: Json object
```json
{
    "message": "success",
    "id":"user id",
    "has_api_keys": true,
    "user_name": "user_name",
    "is_active": true,
}
```

---
---
<br>

#### **PROVIDER ENDPOINTS**
>ENDPOINTS only accessible to logged in user with Provider role. These are Signal Providers

  `GET '/provider/signals'` or `GET '/provider/signals?page=${page}'`
- get all signals uploaded by logged in provider
- Request Arguements:query parameter `page`- integer defaults to `1` if not provided
- Returns: JSON object array of signals, total signals and total number of pages,20 signals max per page
```json
{
    "message": "Success",
    "provider_rating": 0.0,
    "signals": [
        {
            "id": 1,
            "signal": {
                "symbol":"BNBUSDT",
                "side":"BUY",
                "quantity":"0.05",
                "price":"360",
                "stops":{
                    "sl":"350",
                    "tp":"380"
                }
            },
            "short_text":"short message from provider",
            "status": true, //is signal is still valid
            "is_spot": true,// if is spot trade
            "provider": "testprovider", // provider user name
            "provider_wallet": "0x0...",//providers wallet address
            "date_created": "sun 31 march 2020 13:42:00",
        },
        {
            "id": 2,
            "signal": {
                "symbol":"LTCUSDT",
                "side":"SELL",
                "quantity":"1",
                "price":"70.05",
                "stops":{
                    "sl":"73.2",
                    "tp":"60"
                }
            },
            "short_text":"short message from provider",
            "status": false, //old or no longer valid
            "is_spot": false,// futures trade
            "provider": "testprovider", // provider user name
            "provider_wallet": "0x0...",//providers wallet address
            "date_created": "sun 31 march 2020 13:42:00",
        },
    ],
    "total": 5,// total signals from this provider
    "pages": 1,// total number of pages available
}
```

---
<br>

  `GET '/provider/spot/pairs'`
- get all available USDT spot trading pairs from binance
- Returns: JSON object
```json
{
    "message":"success",
    "pairs":[
        "BNBUSDT",
        "ETHUSDT",
        "BTCUSDT"]
}
```
---
<br>

  `GET '/provider/futures/pairs'`
- get all available USDT futures trading pairs from binance
- Returns: JSON object
```json
{
    "message":"success",
    "pairs":[
        "BNBUSDT",
        "ETHUSDT",
        "BTCUSDT"]
}
```
---
<br>

  `POST '/provider/spot/new'`
- upload or post new spot trade
- Request Arguements: JSON object 
```json
{
  "symbol":"BNBUSDT",
  "side":"BUY",
  "quantity":"0.5",//type:float
  "price":"336",//type:float
  "tp1":"325",//type:float
  "tp2":"",//float optional
  "tp3":"",//float optional
  "sl":"340",//type:float
  "short_text":"sample short message from provider"
}
```
- Returns: JSON object
```json
{
    "message":"success",
    "signal":{
            "id": 1,
            "signal": {
                "symbol":"BNBUSDT",
                "side":"SELL",
                "quantity":"0.5",
                "price":"366",
                "stops":{
                    "sl":"340",
                    "tp":"325"
                }
            },
            "short_text":"short message from provider",
            "status": true, //is signal is still valid
            "is_spot": true,// if is spot trade
            "provider": "testprovider", // provider user name
            "provider_wallet": "0x0...",//providers wallet address
            "date_created": "sun 31 march 2020 13:42:00",
        }
}
```
---
<br>

  `POST '/provider/futures/new'`
- upload or post new futures trade
- Request Arguements: JSON object 
```json
{
  "symbol":"BNBUSDT",
  "side":"SELL",
  "quantity":"0.5",//type:float
  "price":"336",//type:float
  "leverage":"3",//type:integer
  "tp1":"325",//type:float required
  "tp2":"",//float optional
  "tp3":"",//float optional
  "sl":"340",//type:float
  "short_text":"sample short message from provider"
}
```
- Returns: JSON object
```json
{
    "message":"success",
    "signal":{
            "id": 1,
            "signal": {
                "symbol":"BNBUSDT",
                "side":"SELL",
                "quantity":"0.5",
                "leverage":"5",
                "price":"366",
                "stops":{
                    "sl":"340",
                    "tp":"325"
                }
            },
            "short_text":"short message from provider",
            "status": true, //if signal is still valid
            "is_spot": false,// if is futures trade
            "provider": "testprovider", // provider user name
            "provider_wallet": "0x0...",//providers wallet address
            "date_created": "sun 31 march 2020 13:42:00",
        }
}
```
---
<br>


  `POST '/provider/delete/${signal_id}'`
- Provider deletes a signal he has created before
- Request Arguements: `signal_id`- integer id of the signal to delete
Returns: JSON object
```json
{
    "message":"success",
    "signal_id":1
}
```
---
<br>


  `POST '/provider/deactivate/${signal_id}'`
- Provider marks a signal he has created before as no longer valid 
- Request Arguements: `signal_id`- integer id of the signal to edit
Returns: JSON object
```json
{
    "message":"success",
    "signal_id":1
}
```
---
<br>


  `POST '/provider/update_wallet'`
- allows provider change wallet address the will be paid with requires user is active
- Request Arguements: JSON object
```json
{
    "wallet":"0x12..."
}
```
Returns:JSON object
```json
{
    "message":"wallet changed"
}
```

---
<br>

#### **GENERAL ENDPOINTS**
>ENDPOINTS accessible to any logged in user

  `POST '/spot/trade/${signal_id}'`
- place spot trade on logged in users binance account
- Request Arguements: `signal_id`- integer, id of signal to trade and empty JSON body
```json
{ 
  "tp":"0.876"//selected tp:float
}
```
- Returns:JSON object
```json
{
    "message":"success",
    "signal":{
        "symbol":"BNBUSDT",
        "side":"SELL",
        "quantity":"0.5",
        "price":"336",
        "timeInForce": "GTC",
        "type": "LIMIT",
        "tp":"325",
        "sl":"340",
        "newClientOrderId": "bieuhcfu3y478gi88"
    }
}
```
---
<br>

  `POST '/futures/trade/${signal_id}'`
- place futures trade on logged in users binance account
- Request Arguements: `signal_id`- integer, id of signal to trade and JSON body containig
```json
{ 
  "tp":"0.876"//selected tp:float
}
```
- Returns:JSON object
```json
{
    "message":"success",
    "signal":{
        "symbol":"BNBUSDT",
        "side":"SELL",
        "quantity":"0.5",
        "price":"336",
        "timeInForce": "GTC",
        "type": "LIMIT",
        "tp":"325",
        "sl":"340",
        "leverage":"3",
        "newClientOrderId": "bieuhcfu3y478gi88"
    }
}
```
---
<br>

  `GET or POST '/signal/${signal_id}?tx_hash=${tx_hash}'`
- get complete details of a signal, requires logged in
- Request Arguements: query parameter `signal_id`- integer,`tx_hash` - string; id of signal to get;tx hash of payment made to contract

- Returns: JSON object
```json
{
  "message":"success",
  "signal": {
            "id": 1,
            "signal": {
                "symbol":"BNBUSDT",
                "side":"SELL",
                "quantity":"0.5",
                "price":"366",
                "stops":{
                    "sl":"340",
                    "tp":"325"
                }
            },
            "short_text":"",//short message from provider
            "status": true, //is signal is still valid
            "is_spot": true,// if is spot trade
            "provider": "testprovider", // provider user name
            "provider_wallet": "0x0...",//providers wallet address
            "date_created": "sun 31 march 2020 13:42:00",
        }
}
```

---
<br>

  `POST '/signal/rate/${signal_id}'`
- rate a trade that as user has paid for and has taken before
- Request Arguements: query parameter `signal_id`- integer, id of signal to rate and JSON object:
```json
{
  "rate":5 // integer between 1 and 5
}
```
- Returns: JSON object
```json
{
  "message": "success", 
  "rating": 5
}

```

---
<br>

  `GET '/'` or `GET '?page=${page}'`
- get reduced/summarized form of all active signals(status=true),paginated
- Request Arguements: `page`- integer page number, page defaults to `1` if not given
- Returns:JSON object
```json
{
  "message": "Success",
  "signals":[
    {
      "id": 4,
      "signal": {
          "symbol": "LTCUSDT",
          "side":"SELL",
          "quantity":""
      },
      "is_spot": true,
      "short_text":null,
      "provider":"proider username",
      "provider_wallet": "0x21gh...",
      "provider_rating":4.65,
      "date_created": "Sun 31 march 2020 13:42:00",
    },
    {
      "id": 7,
      "signal": {
          "symbol": "BTCUSDT",
          "side":"BUY",
          "quantity":""
      },
      "is_spot": true,
      "provider":"proider username",
      "short_text":null,
      "provider_wallet": "0x21gh...",
      "provider_rating":4.05,
      "date_created": "Sun 31 march 2020 13:42:00",
    },
    {
      "id": 9,
      "signal": {
          "symbol": "ETHUSDT",
          "side":"SELL",
          "quantity":""
      },
      "is_spot": false,
      "provider":"proider username",
      "short_text":null,
      "provider_wallet": "0x21gh...",
      "provider_rating":3.35,
      "date_created": "Sun 31 march 2020 13:42:00",
    }
  ],
  "total": 40,
  "pages": 3,
}
```

---
<br>

  `GET '/mytrades'` or `GET '/mytrades?page=${page}'`
- get all previously purchased trades of logged in user,paginated
- Request Arguements: `page`- integer page number, page defaults to `1` if not given
- Returns:JSON object
```json
{
  "message": "success",
  "pages": 1,
  "total": 2 ,
  "mytrades": [
    {
      "date_created": "Mon, 27 Nov 2023 00:10:22 GMT",
      "id": 2,
      "is_spot": true,
      "short_text":"", //short message from provider
      "provider": "testprovider", // provider user name
      "provider_wallet": "0x0...",//providers wallet address
      "signal": {
        "price": 336.0,
        "quantity": 0.5,
        "side": "SELL",
        "stops": {
          "sl": 340.0,
          "tp": 325.0
        },
        "symbol": "LTCUSDT"
      },
      "status": true,
      "user_rating": 0 // signal rating given by this logged in user
    },
    {
      "date_created": "Mon, 27 Nov 2023 00:10:07 GMT",
      "id": 1,
      "is_spot": true,
      "short_text":"",//short message from provider
      "provider": "testprovider", // provider user name
      "provider_wallet": "0x0...",//providers wallet address
      "signal": {
        "price": 336.0,
        "quantity": 0.5,
        "side": "SELL",
        "stops": {
          "sl": 340.0,
          "tp": 325.0
        },
        "symbol": "BNBUSDT"
      },
      "status": true,
      "user_rating": 0  // signal rating given by this logged in user
    }
  ],
  "status": true
}
```
---
<br>

---
<br>

  `POST '/apply/provider'`
- submit request to become a signal provider
- Request Arguements: JSON object:
```json
{
  "wallet":"0x40 characters more",
  "experience":"",//providers experience(300 chars max 10 chars min)
  "socials_and_additional":"" //social links and other relevant info(500 chars max 10 chars min)
}
```
- Returns:JSON object
```json
{
  "message": "success",
  "status": true
}
```
---
<br>
#### **REGISTRAR ENPOINTS**
>ENDPOINTS only accessible to logged in user with Registrar role. This is The Admin

  `POST '/registrar/provider/new'`
- Change user role to Provider
- Request Arguements: JSON object
```json
{
  "email":"user@email.com"
}
``` 
- Returns:JSON object
```json
{
  "message": "success", 
  "provider": "user@email.com"
}
```

---
<br>

  `POST '/registrar/registrar/new'`
- Change user role to Registrar
- Request Arguements:JSON object
```json
{
  "email":"user@email.com"
}
```
- Returns:JSON object
```json
{
  "message": "success", 
  "registrar": "user@email.com"
}
```

---
<br>

  `POST '/registrar/drop_role'`
- Drop any special role of back to User
- Request Arguements: JSON object
```json
{
  "email":"user@email.com"
}
```
- RETURNS:JSON object
```json
{
  "message": "success", 
  "registrar": "user@email.com"
}
```
---
<br>

  `GET '/registrar/role/providers'` or `GET '/registrar/role/providers?page=${page}'`
- Get all users with Provider role,paginated
- Request Arguements: `page`-integer, defaults to `1`
- Returns:JSON object
```json
{
    "message": "success",
    "providers": [],
    "pages": 0,
    "total": 0,
}
```
or
```json
{
    "message": "success",
    "providers": [
      {
        "id": 4,
        "email": "user@email.com",
        "user_name": "user name",
        "roles": "Provider",
        "is_active": true,
        "wallet": "0x05tg4...",
        "has_api_keys": true,
        "date_created": "Sun 31 march 2020 13:42:00"
      },
      {
        "id": 5,
        "email": "user@email.com",
        "user_name": "user name",
        "roles": "Provider",
        "is_active": false,
        "wallet": "0x05tg4...",
        "has_api_keys": true,
        "date_created": "Sun 31 march 2020 13:42:00"
      }
    ],
    "pages": 1,
    "total": 2
}
``` 
---
<br>

  `GET '/registrar/role/registrars'` or `GET '/registrar/role/registrars?page=${page}'`
- Get all users with Registrar role,paginated
- Request Arguements: `page`-integer, defaults to `1`
- Returns:JSON object
```json
{
    "message": "success",
    "registrars": [],
    "pages": 0,
    "total": 0,
}
```
or
```json
{
    "message": "success",
    "registrars": [
      {
        "id": 4,
        "email": "user@email.com",
        "user_name": "user name",
        "roles": "Registrars",
        "is_active": true,
        "wallet": "0x05tg4...",
        "has_api_keys": true,
        "date_created": "Sun 31 march 2020 13:42:00"
      },
      {
        "id": 5,
        "email": "user@email.com",
        "user_name": "user name",
        "roles": "Registrar",
        "is_active": false,
        "wallet": "0x05tg4...",
        "has_api_keys": true,
        "date_created": "Sun 31 march 2020 13:42:00"
      }
    ],
    "pages": 1,
    "total": 2
}
``` 
---
<br>

  `GET '/registrar/role/users'` or `GET '/registrar/role/users?page=${page}'`
- Get all regular users, paginated
- Request Arguements: `page`-integer, defaults to `1`
- Returns:JSON object
```json
{
    "message": "success",
    "users": [],
    "pages": 0,
    "total": 0,
}
```
or
```json
{
    "message": "success",
    "users": [
      {
        "id": 4,
        "email": "user@email.com",
        "user_name": "user name",
        "roles": "User",
        "is_active": true,
        "wallet": "0x05tg4...",
        "has_api_keys": true,
        "date_created": "Sun 31 march 2020 13:42:00"
      },
      {
        "id": 5,
        "email": "user@email.com",
        "user_name": "user name",
        "roles": "User",
        "is_active": false,
        "wallet": "0x05tg4...",
        "has_api_keys": true,
        "date_created": "Sun 31 march 2020 13:42:00"
      }
    ],
    "pages": 1,
    "total": 2
}
``` 
---
<br>

  `GET '/registrar/get/users'` or `GET '/registrar/get/users?page=${page}'`
- Get all regardless of role, paginated
- Request Arguements: `page`-integer, defaults to `1`
- Returns:JSON object
```json
{
    "message": "success",
    "users": [],
    "pages": 0,
    "total": 0,
}
```
or
```json
{
    "message": "success",
    "users": [
      {
        "id": 4,
        "email": "user@email.com",
        "user_name": "user name",
        "roles": "User",
        "is_active": true,
        "wallet": "0x05tg4...",
        "has_api_keys": true,
        "date_created": "Sun 31 march 2020 13:42:00"
      },
      {
        "id": 5,
        "email": "user@email.com",
        "user_name": "user name",
        "roles": "Provider",
        "is_active": false,
        "wallet": "0x05tg4...",
        "has_api_keys": true,
        "date_created": "Sun 31 march 2020 13:42:00"
      }
    ],
    "pages": 1,
    "total": 2
}
``` 



## Authors
- [@Godhanded](https://github.com/Godhanded)

## Acknowledgments

- Binance-Python-Connector